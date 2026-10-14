"""Local Ollama NDJSON transport; fixed-budget, append-only, no code execution.
Only /api/generate at numeric loopback is used. No proxy/redirect/retry.
"""
from __future__ import annotations
import http.client
import json
import os
from pathlib import Path
import socket
import threading
import time

MAX_LINE = 1024 * 1024
MAX_BYTES = 64 * 1024 * 1024

class StreamFailure(RuntimeError):
    pass


def decode(raw):
    def pairs(items):
        d = {}
        for k, v in items:
            if k in d:
                raise StreamFailure('duplicate JSON key: ' + k)
            d[k] = v
        return d
    def bad(x):
        raise StreamFailure('nonfinite JSON: ' + x)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


class Collector:
    def __init__(self, model):
        self.model = model
        self.fragments = []
        self.records = 0
        self.complete = False
        self.final = None

    def add(self, raw):
        if self.complete:
            raise StreamFailure('record after terminal message')
        obj = decode(raw)
        if not isinstance(obj, dict) or obj.get('error'):
            raise StreamFailure('model error or malformed response: ' + str(obj)[:1000])
        if obj.get('model') != self.model or type(obj.get('done')) is not bool:
            raise StreamFailure('wrong model or missing done flag')
        piece = obj.get('response', '')
        if not isinstance(piece, str) or obj.get('thinking'):
            raise StreamFailure('unexpected response/thinking field')
        self.fragments.append(piece)
        self.records += 1
        if obj['done']:
            if obj.get('done_reason') not in ('stop', 'length'):
                raise StreamFailure('unknown completion reason')
            self.complete = True
            self.final = obj
        return piece

    def finish(self):
        if not self.complete:
            raise StreamFailure('stream ended without a terminal message')
        obj = dict(self.final)
        obj['response'] = ''.join(self.fragments)
        return obj


def receive(payload, directory, timeout_seconds, idle_seconds=1800,
            port=11469, connection_factory=http.client.HTTPConnection,
            heartbeat=None):
    """Persist every received line and text fragment, even on failure.
    Returned object is reconstructed; it is not claimed to be the raw wire JSON.
    Absolute watchdog limits header wait and slow/partial lines as well.
    """
    if payload.get('stream') is not True or payload.get('raw') is not True:
        raise StreamFailure('expected raw streaming request')
    if not 0 < timeout_seconds <= 7200 or not 0 < idle_seconds <= 1800:
        raise StreamFailure('invalid time budget')
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    wire = d / 'response.stream.jsonl'
    partial = d / 'response.partial.txt'
    if wire.exists() or partial.exists():
        raise StreamFailure('previous stream exists; no resubmission')
    start = time.monotonic()
    timed_out = threading.Event()
    conn = connection_factory('127.0.0.1', port,
                              timeout=min(idle_seconds, timeout_seconds))
    sock_holder = []
    def expire():
        timed_out.set()
        for s in sock_holder:
            try: s.shutdown(socket.SHUT_RDWR)
            except OSError: pass
            try: s.close()
            except OSError: pass
    timer = threading.Timer(timeout_seconds, expire)
    timer.daemon = True
    collector = Collector(payload['model'])
    total = 0
    last = 0.0
    timer.start()
    try:
        conn.connect()
        if getattr(conn, 'sock', None) is not None:
            sock_holder.append(conn.sock)
        if timed_out.is_set():
            raise TimeoutError('absolute request timeout before send')
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8')
        conn.request('POST', '/api/generate', body=body,
                     headers={'Content-Type': 'application/json'})
        response = conn.getresponse()
        if response.status != 200:
            error = response.read(4096)
            with (d/'response.http-error.txt').open('xb') as f:
                f.write(error)
            raise StreamFailure('HTTP status ' + str(response.status))
        with wire.open('xb') as wf, partial.open('xb') as pf:
            while True:
                if timed_out.is_set():
                    raise TimeoutError('absolute request timeout')
                raw = response.readline(MAX_LINE + 1)
                if not raw:
                    break
                total += len(raw)
                if len(raw) > MAX_LINE or total > MAX_BYTES:
                    raise StreamFailure('oversized stream')
                wf.write(raw); wf.flush()
                if not raw.strip():
                    continue
                piece = collector.add(raw)
                pf.write(piece.encode('utf-8')); pf.flush()
                elapsed = time.monotonic() - start
                if heartbeat and (elapsed - last >= 30 or collector.complete):
                    heartbeat({'elapsed_seconds': elapsed,
                               'received_json_records': collector.records,
                               'partial_text_bytes': pf.tell(),
                               'done_received': collector.complete})
                    last = elapsed
                if collector.complete:
                    os.fsync(wf.fileno()); os.fsync(pf.fileno())
                    break
        if timed_out.is_set():
            raise TimeoutError('absolute request timeout')
        obj = collector.finish()
        return obj, {'transport': 'streaming_ndjson',
                     'reconstructed_response': True,
                     'raw_stream': wire.name,
                     'partial_text': partial.name,
                     'stream_records': collector.records,
                     'wall_seconds': time.monotonic() - start,
                     'timeout_seconds': timeout_seconds,
                     'idle_timeout_seconds': idle_seconds,
                     'automatic_retry': False}
    finally:
        timer.cancel()
        conn.close()
