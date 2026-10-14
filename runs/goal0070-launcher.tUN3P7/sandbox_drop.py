"""Trusted launcher text, executed inside bwrap before the compiler/candidate.
Not a standalone host administrator tool; it only reduces process privileges.
"""
import ctypes
import json
import os
import sys

stage = 'initial'
libc = ctypes.CDLL(None, use_errno=True)

class Header(ctypes.Structure):
    _fields_ = [('version', ctypes.c_uint32), ('pid', ctypes.c_int)]

class Data(ctypes.Structure):
    _fields_ = [('effective', ctypes.c_uint32), ('permitted', ctypes.c_uint32),
                ('inheritable', ctypes.c_uint32)]

libc.capset.argtypes = [ctypes.POINTER(Header), ctypes.POINTER(Data)]
libc.capset.restype = ctypes.c_int
libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                       ctypes.c_ulong, ctypes.c_ulong]
libc.prctl.restype = ctypes.c_int


def snapshot():
    with open('/proc/self/status', encoding='ascii') as f:
        st = dict(line.rstrip().split(':', 1) for line in f if ':' in line)
    return {'uid': list(os.getresuid()), 'gid': list(os.getresgid()),
            'groups': os.getgroups(), 'capabilities': {
                k: int(st[k].strip(), 16)
                for k in ('CapEff', 'CapPrm', 'CapInh', 'CapAmb', 'CapBnd')},
            'no_new_privs': int(st['NoNewPrivs'].strip())}


def checked(rc, op):
    if rc != 0:
        err = ctypes.get_errno()
        raise OSError(err, op + ': ' + os.strerror(err))

try:
    if len(sys.argv) < 2:
        raise RuntimeError('missing trusted executable')
    before = snapshot()
    stage = 'no_new_privs'
    checked(libc.prctl(38, 1, 0, 0, 0), 'PR_SET_NO_NEW_PRIVS')
    stage = 'drop_supplementary_groups'
    os.setgroups([])
    stage = 'drop_gids'
    os.setresgid(65534, 65534, 65534)
    stage = 'drop_uids'
    os.setresuid(65534, 65534, 65534)
    after_uid = snapshot()
    # UID changes do not clear the inheritable capability set. Clear it
    # explicitly together with the permitted/effective sets. No extra caps added.
    stage = 'clear_capability_sets'
    header = Header(0x20080522, 0)  # Linux capability ABI v3, current thread
    zero = (Data * 2)()
    checked(libc.capset(ctypes.byref(header), zero), 'capset(empty)')
    stage = 'clear_ambient_capabilities'
    checked(libc.prctl(47, 4, 0, 0, 0), 'PR_CAP_AMBIENT_CLEAR_ALL')
    stage = 'verify_dropped_privileges'
    after = snapshot()
    checks = {
        'all_uids_65534': after['uid'] == [65534] * 3,
        'all_gids_65534': after['gid'] == [65534] * 3,
        'no_supplementary_groups': after['groups'] == [],
        'cap_eff_prm_inh_amb_zero': all(after['capabilities'][k] == 0
             for k in ('CapEff', 'CapPrm', 'CapInh', 'CapAmb')),
        'no_new_privs': after['no_new_privs'] == 1,
    }
    failed = [k for k, v in checks.items() if not v]
    if failed:
        raise RuntimeError('failed privilege checks: ' + ', '.join(failed))
    if any('__CPUCOND_PREFLIGHT_V2__' in x for x in sys.argv[1:]):
        print('SANDBOX_PRIVILEGE_DIAGNOSTIC ' + json.dumps({
            'before': before, 'after_uid_change': after_uid,
            'after_explicit_clear': after, 'checks': checks}, sort_keys=True),
            file=sys.stderr, flush=True)
    stage = 'exec_unprivileged'
    os.execv(sys.argv[1], sys.argv[1:])
except Exception as exc:
    try:
        current = snapshot()
    except Exception:
        current = None
    print('SANDBOX_LAUNCHER_FAILED ' + json.dumps({
        'stage': stage, 'error': type(exc).__name__ + ': ' + str(exc),
        'current': current}, sort_keys=True), file=sys.stderr, flush=True)
    sys.exit(125)
