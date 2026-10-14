#!/usr/bin/env python3
"""既存のCPU実験記録を読み、凍結済み規則で比較する（ネットワーク不要）。

元のアーカイブ、解析用束、抽出結果、解析契約は変更しない。
新しい実行ディレクトリへ、検証記録・現時点のハッシュ一覧・比較表を保存する。
ハッシュ一覧の事後作成を、抽出時点の検証済み記録と偽って扱わない。
--self-test は合成データだけを使い、利用者の実験結果を読まない。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import statistics
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

CONTRACT_HASH = 'c32334a68d8fd43d081af5b292a772c50b08628e7b40ffce116373379b3ece7d'
MANIFEST_HASH = 'a6c6423984aab7a26f90b86aab36ab3962fd208fb6f977ad068b80d4fc31c7a1'
HOST_A = 'haswell-e3-1241v3'
HOST_B = 'zen2-2x-epyc-7402'
SIZE_MACROS = {'MINI': 'MINI_DATASET', 'SMALL': 'SMALL_DATASET', 'MEDIUM': 'MEDIUM_DATASET'}
ZEN_ARCHIVE_HASH = '3eeb3114d15420c72c0e725af14d6cba358d35ca81856b768432db380542f229'
ZEN_RUN_ID = '20260911T184737.403148Z-4fddf03c'
REQUIRED_BUNDLE_FILES = {'instance-summary.json', 'gate.json', 'alias-map.json',
                         'final-timing.json', 'final-timing-summary.json'}


class AuditError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AuditError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def unique_object(pairs):
    out = {}
    for k, v in pairs:
        require(k not in out, f'JSONキーの重複: {k}')
        out[k] = v
    return out


def reject_constant(value):
    raise AuditError(f'有限数でないJSON値: {value}')


def json_text(text: str):
    return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)


def load(path: Path):
    return json_text(path.read_text(encoding='utf-8'))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def positive(value, where: str) -> float:
    require(not isinstance(value, bool), f'{where}: 真偽値は数値にできません')
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise AuditError(f'{where}: 数値がありません') from None
    require(math.isfinite(v) and v > 0, f'{where}: 正の有限数でありません')
    return v


def boolean(value: str) -> bool:
    require(value in ('True', 'False', 'true', 'false'), f'不正な真偽値: {value!r}')
    return value.lower() == 'true'


def close(a: float, b: float, where: str) -> None:
    require(math.isfinite(a) and math.isfinite(b) and
            math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-15), f'{where}: 数値が一致しません')


def geometric_mean(values) -> float:
    xs = [positive(x, '幾何平均') for x in values]
    require(bool(xs), '空集合の幾何平均')
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def safe_relative(name: str) -> Path:
    p = PurePosixPath(name)
    require(bool(p.parts) and not p.is_absolute() and '..' not in p.parts and
            '\\' not in name and '\n' not in name and '\r' not in name,
            f'安全でない相対パス: {name!r}')
    return Path(*p.parts)


def snapshot(root: Path) -> dict[str, str]:
    require(root.is_dir() and not root.is_symlink(), f'ディレクトリがありません: {root}')
    result = {}
    for parent, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            require(not (Path(parent) / name).is_symlink(), '入力のシンボリックリンクを拒否しました')
        for name in names:
            p = Path(parent) / name
            require(p.is_file(), f'通常ファイルでありません: {p}')
            rel = p.relative_to(root).as_posix()
            safe_relative(rel)
            result[rel] = sha(p)
    return dict(sorted(result.items()))


def manifest_bytes(files: dict[str, str]) -> bytes:
    return ''.join(f'{v}  ./{k}\n' for k, v in sorted(files.items())).encode('utf-8')


def verify_existing_hashes(root: Path, files: dict[str, str]) -> bool:
    p = root / 'SHA256SUMS'
    if not p.exists():
        return False
    found = {}
    for line in p.read_text(encoding='utf-8').splitlines():
        match = re.fullmatch(r'([0-9a-f]{64}) [ *](.+)', line)
        require(match is not None, f'{p}: ハッシュ一覧の書式が不正です')
        value, raw_name = match.groups()
        name = safe_relative(raw_name).as_posix()
        require(name != 'SHA256SUMS' and name not in found, 'ハッシュ一覧の重複・自己参照')
        require(files.get(name) == value, f'ハッシュ不一致: {root / name}')
        found[name] = value
    require(set(found) == set(files) - {'SHA256SUMS'}, f'{root}: ハッシュ一覧の対象不足・過剰')
    return True


def csv_rows(path: Path) -> list[dict]:
    with path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        require(reader.fieldnames is not None and len(reader.fieldnames) == len(set(reader.fieldnames)),
                f'{path}: CSV見出しが不正です')
        rows = list(reader)
    require(bool(rows) and all(None not in r and None not in r.values() for r in rows),
            f'{path}: 空CSVまたは列数不一致')
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    require(bool(rows), '空の比較表は保存しません')
    with path.open('x', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def candidate_plan(manifest: dict) -> dict[tuple[str, str], set[str]]:
    require(manifest['kernel_count'] == 30 and len(manifest['kernels']) == 30, 'カーネル数不一致')
    result = {}
    for k in manifest['kernels']:
        ids = ['identity'] + [c['candidate_id'] for loop in k['loops'] for c in loop['candidates']]
        require(len(ids) == len(set(ids)) == k['candidate_count_including_identity'], '候補数不一致')
        for size in SIZE_MACROS:
            key = (k['kernel_id'], size)
            require(key not in result, 'カーネルの重複')
            result[key] = set(ids)
    require(len(result) == 90 and sum(map(len, result.values())) == 4740, '90条件・4740候補と不一致')
    return result


def audit_measurements(rep: str, rows: list, sessions: list, k: int,
                       invalid: set[str], where: str) -> tuple[bool, float | None]:
    require(isinstance(rows, list) and isinstance(sessions, list) and bool(sessions), f'{where}: 測定形式不正')
    require(all(isinstance(s, dict) and isinstance(s.get('quality_warnings'), list) for s in sessions),
            f'{where}: 警告記録が不正です')
    bad = any(s.get('measurement_valid') is not True or s['quality_warnings'] for s in sessions)
    require((rep in invalid) == bool(bad), f'{where}: 無効化記録と測定記録が不一致')
    require(rep != 'identity' or not bad, f'{where}: 基準測定が無効です')

    complete = len(sessions) == 2 and all(s.get('measurement_valid') is True for s in sessions)
    if not complete:
        require(bad, f'{where}: 未完了なのに有効扱い')
        return False, None
    require([s.get('session') for s in sessions] == [0, 1], f'{where}: セッション番号不一致')
    require(len(rows) == 16, f'{where}: 16ペアありません')
    medians = []
    for session in (0, 1):
        selected = [r for r in rows if r.get('session') == session]
        require(len(selected) == 8 and {r.get('trial') for r in selected} == set(range(8)),
                f'{where}: 試行番号が重複または欠落しています')
        ratios = []
        first = []
        for r in selected:
            require(r.get('candidate_id') == rep and r.get('measurement_valid') is True and
                    r.get('batch_count') == k, f'{where}: 候補ID・有効性・反復数が不一致')
            require(r.get('order') in (['reference', rep], [rep, 'reference']), f'{where}: 実行順序不正')
            first.append(r['order'][0])
            a = positive(r['reference_ns'], where)
            b = positive(r['candidate_ns'], where)
            ratio = a / b
            close(ratio, positive(r['speedup'], where), where + '/比率')
            ratios.append(ratio)
        require(first.count('reference') == 4, f'{where}: 実行順序が4対4でありません')
        s = sessions[session]
        require(s.get('candidate_id') == rep and s.get('pairs') == 8 and s.get('batch_count') == k,
                f'{where}: セッション要約の条件不一致')
        med = positive(s['median_paired_speedup'], where)
        close(statistics.median(ratios), med, where + '/中央値')
        medians.append(med)
    if bad:
        return False, None
    # 元の抽出器と同じ式・同じ記録中央値を使う。計算規則を変更しない。
    return True, 1.0 if rep == 'identity' else geometric_mean(medians)


def audit_instance(directory: Path, ids: set[str], candidates: dict[str, dict],
                   kernel: str, size: str) -> tuple[dict[str, float | None], dict[str, bool]]:
    inst = load(directory / 'instance-summary.json')
    gate = load(directory / 'gate.json')['candidate_rows']
    aliases = load(directory / 'alias-map.json')
    timing = load(directory / 'final-timing.json')
    sums = load(directory / 'final-timing-summary.json')
    where = f'{kernel}/{size}'
    require(inst['kernel_id'] == kernel and inst['size_label'] == size and
            inst['size'] == SIZE_MACROS[size] and inst['instance_valid'] is True, f'{where}: 条件不一致')
    require(inst['candidate_ids_requested'] == len(ids), f'{where}: 候補数不一致')
    gate_by_id = {r['candidate_id']: r for r in gate}
    require(len(gate) == len(gate_by_id) and set(gate_by_id) == ids == set(candidates), f'{where}: 候補ID不一致')
    require(all(type(r.get('admitted')) is bool for r in gate), f'{where}: 正しさ判定の型が不正')
    admitted = {cid for cid, r in gate_by_id.items() if r['admitted']}
    require(len(admitted) == inst['candidates_admitted'] and 'identity' in admitted and
            set(aliases) == admitted, f'{where}: 正しさ判定と対応表が不一致')
    hashes = {}
    for cid in admitted:
        h = gate_by_id[cid]['function']['bytes_sha256']
        require(re.fullmatch('[0-9a-f]{64}', h) is not None, f'{where}: 機械語ハッシュ不正')
        hashes.setdefault(h, []).append(cid)
    for h, members in hashes.items():
        rep = 'identity' if 'identity' in members else min(members)
        require(all(aliases[cid] == rep for cid in members), f'{where}: 機械語代表の対応不一致')
    reps = set(aliases.values())
    require(reps == set(timing) == set(sums), f'{where}: 代表候補・測定ファイル不一致')
    require(len(reps) == inst['unique_machine_code_groups'] and
            len(reps) - 1 == inst['nonidentity_representatives_measured'], f'{where}: 機械語群の件数不一致')
    require(sum(v == 'identity' for v in aliases.values()) == inst['aliases_to_identity'], f'{where}: 無変更件数不一致')
    require(sums['identity'] == inst['identity_summaries'], f'{where}: 基準要約不一致')
    invalid_list = inst['candidate_representatives_invalid_no_rerun']
    invalid = set(invalid_list)
    require(len(invalid) == len(invalid_list) and invalid <= reps - {'identity'}, f'{where}: 無効代表候補不正')
    k = inst['final_k']
    require(type(k) is int and k > 0, f'{where}: 反復数不正')
    status = {rep: audit_measurements(rep, timing[rep], sums[rep], k, invalid, where + '/' + rep)
              for rep in sorted(reps)}
    score = {}
    correctness = {}
    for cid in sorted(ids):
        r = candidates[cid]
        good = cid in admitted
        valid, v = status[aliases[cid]] if good else (False, None)
        require(boolean(r['correctness_admitted']) == good and
                boolean(r['measurement_valid']) == valid and boolean(r['oracle_eligible']) == valid,
                f'{where}/{cid}: CSVの有効性が実験記録と不一致')
        require(r['machine_code_representative'] == (aliases[cid] if good else ''), f'{where}/{cid}: CSV代表不一致')
        require(boolean(r['machine_code_noop']) == (good and cid != 'identity' and aliases[cid] == 'identity'),
                f'{where}/{cid}: 無変更判定不一致')
        if good:
            require(r['machine_code_sha256'] == gate_by_id[cid]['function']['bytes_sha256'], f'{where}/{cid}: ハッシュ不一致')
        if valid:
            close(positive(r['speedup'], where), v, where + '/' + cid)
            score[cid] = positive(r['speedup'], where)
        else:
            require(r['speedup'] == '', f'{where}/{cid}: 無効候補に速度値があります')
            score[cid] = None
        correctness[cid] = good
    require(score['identity'] == 1.0, f'{where}: 基準候補は1倍である必要があります')
    return score, correctness


def best_sets(scores: dict[str, float | None]) -> tuple[float, set[str], set[str]]:
    valid = {cid: positive(v, cid) for cid, v in scores.items() if v is not None}
    require(bool(valid), '有効候補がありません')
    best = max(valid.values())
    exact = {cid for cid, v in valid.items() if v == best}
    near = {cid for cid, v in valid.items() if v >= best / 1.01}
    return best, exact, near


def source_set(raw: str) -> set[str]:
    xs = json_text(raw)
    require(isinstance(xs, list) and all(isinstance(x, str) for x in xs) and len(xs) == len(set(xs)), '候補集合の形式不正')
    return set(xs)


def validate_oracle(row: dict, scores: dict[str, float | None], candidates: dict[str, dict]) -> None:
    best, exact, near = best_sets(scores)
    # 同率・1%判定は凍結契約どおり。比較用に丸めたり許容幅を変えたりしない。
    require(positive(row['oracle_speedup'], '最良速度') == best, '最良速度の再計算不一致')
    require(source_set(row['oracle_candidates_json']) == exact and
            source_set(row['near_oracle_candidates_json']) == near, '最良集合の再計算不一致')
    require(row['canonical_oracle_candidate'] == min(exact), '代表最良候補不一致')
    require(int(row['candidate_count']) == len(scores) and int(row['oracle_candidate_count']) == len(exact) and
            int(row['near_oracle_candidate_count']) == len(near), '最良集合の件数不一致')
    require(boolean(row['oracle_includes_identity']) == ('identity' in exact) and
            boolean(row['near_oracle_includes_identity']) == ('identity' in near), '基準候補の集合所属不一致')
    close(float(row['near_oracle_threshold']), best / 1.01, '1%境界')
    for cid, c in candidates.items():
        require(boolean(c['is_oracle']) == (cid in exact) and boolean(c['near_oracle']) == (cid in near),
                'CSV内の最良候補フラグ不一致')
        expected = 1.0 if scores[cid] is None else 1 - scores[cid] / best
        close(float(c['oracle_regret']), expected, '損失再計算')


def verify_zen_source(bundle: Path, files: dict[str, str]) -> dict:
    evidence = load(bundle / 'bundle-source-v1.json')
    require(evidence['source_archive_sha256'] == ZEN_ARCHIVE_HASH and evidence['run_id'] == ZEN_RUN_ID,
            'Zen 2原本の来歴が不一致')
    require(evidence['counts'] == {name: 90 for name in REQUIRED_BUNDLE_FILES}, 'Zen 2原本件数の不一致')
    entries = evidence['files']
    seen = set()
    for e in entries:
        rel = safe_relative(e['bundle_path']).as_posix()
        require(rel not in seen and files.get(rel) == e['sha256'], f'原本由来ハッシュと不一致: {rel}')
        require((bundle / rel).stat().st_size == e['bytes'], f'原本由来サイズと不一致: {rel}')
        seen.add(rel)
    require(len(seen) == 450, 'Zen 2の450ファイルが揃っていません')
    return {'matched_files': len(seen), 'archive_hash_recorded': ZEN_ARCHIVE_HASH,
            'archive_rehashed_in_this_step': False,
            'note': '過去のアーカイブ抽出記録にある個別ハッシュと今回のファイルを照合した。'}


def audit_host(repo: Path, host: str, plan: dict) -> tuple[dict, dict, dict, dict]:
    base = repo / 'external-results' / host
    bundle = base / 'final-atlas' / 'analysis-bundle'
    output = base / 'hidden-oracle-v1'
    bs, osnap = snapshot(bundle), snapshot(output)
    bundle_had_manifest = verify_existing_hashes(bundle, bs)
    output_had_manifest = verify_existing_hashes(output, osnap)
    existing_summary = load(output / 'summary.json')
    metadata = load(output / 'metadata.json')
    require(existing_summary['host_id'] == metadata['host_id'] == host, 'ホスト名不一致')
    require(existing_summary['analysis_contract_sha256'] == metadata['contract_sha256'] == CONTRACT_HASH,
            '解析契約ハッシュ不一致')
    historical = existing_summary.get('bundle_SHA256SUMS_sha256')
    if historical is not None:
        require(bs.get('SHA256SUMS') == historical, '抽出時の束ハッシュと不一致')
    zen_source = verify_zen_source(bundle, bs) if host == HOST_B else None

    candidate_groups = {}
    for r in csv_rows(output / 'candidate-scores.csv'):
        require(r['host_id'] == host, '候補CSVに別ホストが混在しています')
        key = (r['kernel'], r['size'])
        xs = candidate_groups.setdefault(key, {})
        require(r['candidate_id'] not in xs, '候補CSVのID重複')
        xs[r['candidate_id']] = r
    oracle_groups = {}
    for r in csv_rows(output / 'hidden-oracle.csv'):
        key = (r['kernel'], r['size'])
        require(r['host_id'] == host and key not in oracle_groups, '最良候補CSVのホスト・重複不正')
        oracle_groups[key] = r
    require(set(candidate_groups) == set(oracle_groups) == set(plan), '90条件の対応不一致')
    scores, correctness = {}, {}
    for (kernel, size), ids in plan.items():
        key = (kernel, size)
        scores[key], correctness[key] = audit_instance(bundle / kernel / SIZE_MACROS[size], ids,
                                                       candidate_groups[key], kernel, size)
        validate_oracle(oracle_groups[key], scores[key], candidate_groups[key])
    admitted = sum(sum(x.values()) for x in correctness.values())
    valid = sum(sum(v is not None for v in x.values()) for x in scores.values())
    totals = {'instances': len(plan), 'candidate_rows': sum(map(len, plan.values())),
              'correctness_admitted': admitted, 'correctness_rejected': sum(map(len, plan.values())) - admitted,
              'oracle_eligible_candidates': valid, 'measurement_invalid_candidates': admitted - valid}
    for name, value in totals.items():
        require(existing_summary[name] == value, f'{host}: 集計値不一致: {name}')
    info = {**totals, 'host_id': host, 'bundle_had_SHA256SUMS': bundle_had_manifest,
            'extraction_had_SHA256SUMS': output_had_manifest,
            'bundle_SHA256SUMS_at_extraction': historical,
            'zen_source_receipt_check': zen_source,
            'notes': ['今回のハッシュ記録は事後の監査記録。元のsummary.jsonは変更しない。',
                      '保存済みペア時間から比率と中央値を再計算し、既存CSVと照合した。']}
    return scores, correctness, info, {'bundle': (bundle, bs), 'extraction': (output, osnap)}


def transfer(source_exact: set[str], target_scores: dict[str, float | None], target_best: float) -> dict:
    require(bool(source_exact) and source_exact <= set(target_scores), '移植元IDが移植先に存在しません')
    eligible = {cid: target_scores[cid] for cid in source_exact if target_scores[cid] is not None}
    if not eligible:
        return {'regret': 1.0, 'eligible_count': 0, 'source_count': len(source_exact), 'best_speedup': None}
    v = max(eligible.values())
    require(v <= target_best, '移植候補が移植先の最良値を超えています')
    return {'regret': 1 - v / target_best, 'eligible_count': len(eligible),
            'source_count': len(source_exact), 'best_speedup': v}


def comparison(key: tuple[str, str], a: dict, b: dict, ca: dict, cb: dict) -> dict:
    require(set(a) == set(b) == set(ca) == set(cb), 'CPU間で候補IDが一致しません')
    av, ae, an = best_sets(a)
    bv, be, bn = best_sets(b)
    ab, ba = transfer(ae, b, bv), transfer(be, a, av)
    return {'kernel': key[0], 'size': key[1], 'candidate_count': len(a),
            'haswell_best_speedup': av, 'zen2_best_speedup': bv,
            'canonical_best_equal': min(ae) == min(be),
            'exact_sets_equal': ae == be, 'exact_sets_overlap': bool(ae & be),
            'near_sets_equal': an == bn, 'near_sets_overlap': bool(an & bn),
            'near_set_intersection_count': len(an & bn),
            'near_set_union_count': len(an | bn),
            'near_set_jaccard_distance': 1 - len(an & bn) / len(an | bn),
            'haswell_to_zen2_regret': ab['regret'], 'zen2_to_haswell_regret': ba['regret'],
            'symmetric_transfer_regret': (ab['regret'] + ba['regret']) / 2,
            'haswell_to_zen2_eligible_ties': ab['eligible_count'],
            'haswell_to_zen2_total_ties': ab['source_count'],
            'zen2_to_haswell_eligible_ties': ba['eligible_count'],
            'zen2_to_haswell_total_ties': ba['source_count'],
            'haswell_to_zen2_best_speedup': ab['best_speedup'],
            'zen2_to_haswell_best_speedup': ba['best_speedup'],
            'correctness_disagreement_count': sum(ca[c] != cb[c] for c in a),
            'performance_validity_disagreement_count': sum((a[c] is None) != (b[c] is None) for c in a),
            'haswell_exact_candidates_json': json.dumps(sorted(ae), separators=(',', ':')),
            'zen2_exact_candidates_json': json.dumps(sorted(be), separators=(',', ':'))}


def summarize_comparison(rows: list[dict]) -> dict:
    return {'instances': len(rows),
            'candidate_ids_matched_per_host': sum(r['candidate_count'] for r in rows),
            'canonical_best_equal_instances': sum(r['canonical_best_equal'] for r in rows),
            'exact_sets_equal_instances': sum(r['exact_sets_equal'] for r in rows),
            'exact_sets_overlap_instances': sum(r['exact_sets_overlap'] for r in rows),
            'near_sets_equal_instances': sum(r['near_sets_equal'] for r in rows),
            'near_sets_overlap_instances': sum(r['near_sets_overlap'] for r in rows),
            'no_shared_near_oracle_instances': sum(not r['near_sets_overlap'] for r in rows),
            'near_set_jaccard_distance_mean': statistics.fmean(r['near_set_jaccard_distance'] for r in rows),
            'haswell_to_zen2_regret_mean': statistics.fmean(r['haswell_to_zen2_regret'] for r in rows),
            'zen2_to_haswell_regret_mean': statistics.fmean(r['zen2_to_haswell_regret'] for r in rows),
            'symmetric_transfer_regret_mean': statistics.fmean(r['symmetric_transfer_regret'] for r in rows),
            'symmetric_transfer_regret_median': statistics.median(r['symmetric_transfer_regret'] for r in rows),
            'symmetric_transfer_regret_max': max(r['symmetric_transfer_regret'] for r in rows),
            'haswell_to_zen2_no_valid_destination_instances': sum(r['haswell_to_zen2_eligible_ties'] == 0 for r in rows),
            'zen2_to_haswell_no_valid_destination_instances': sum(r['zen2_to_haswell_eligible_ties'] == 0 for r in rows),
            'correctness_disagreement_candidates': sum(r['correctness_disagreement_count'] for r in rows),
            'performance_validity_disagreement_candidates': sum(r['performance_validity_disagreement_count'] for r in rows),
            'statistical_significance_tested': False,
            'inference_scope': '測定した2ホスト・固定候補集合に対する記述統計。CPU世代全体への一般化ではない。'}


def japanese_report(summary: dict) -> str:
    s = summary
    return '\n'.join([
        '=== CPU間の比較（保存済み測定値に基づく集計） ===',
        f"比較条件数: {s['instances']}",
        f"対応した候補数（各CPU）: {s['candidate_ids_matched_per_host']}",
        f"代表の最良候補IDが同じ: {s['canonical_best_equal_instances']}/90",
        f"同率を含む最良候補集合が完全一致: {s['exact_sets_equal_instances']}/90",
        f"両CPUで最良となる候補が少なくとも1つある: {s['exact_sets_overlap_instances']}/90",
        f"両CPUで最良から1%以内の共通候補がある: {s['near_sets_overlap_instances']}/90",
        f"その共通候補がない: {s['no_shared_near_oracle_instances']}/90",
        f"1%以内候補集合の違い（0=同じ、1=共通なし）: {s['near_set_jaccard_distance_mean']:.6f}",
        f"Haswellで選んだ最良候補をZen 2へ移す損失: {100*s['haswell_to_zen2_regret_mean']:.4f}%",
        f"Zen 2で選んだ最良候補をHaswellへ移す損失: {100*s['zen2_to_haswell_regret_mean']:.4f}%",
        f"双方向の平均損失: {100*s['symmetric_transfer_regret_mean']:.4f}%",
        f"正しさの採否が異なる候補: {s['correctness_disagreement_candidates']}",
        f"測定採用の可否が異なる候補: {s['performance_validity_disagreement_candidates']}",
        '',
        '注意: 損失は1−移植候補の速度倍率/移植先の最良速度倍率。実行時間増加率とは異なる。',
        '注意: 同率候補は移植先で最も良いものを選ぶ既定規則。移植に有利な評価である。',
        '注意: 統計的有意差を検定した結果ではない。近い測定値の順位逆転だけでCPU依存性を断定しない。',
    ]) + '\n'


def execute(repo: Path) -> Path:
    repo = repo.resolve()
    contract = repo / 'configs/final-analysis-contract-v1.json'
    manifest = repo / 'configs/final-candidate-manifest-v1.json'
    require(sha(contract) == CONTRACT_HASH, '固定された解析契約と一致しません')
    require(sha(manifest) == MANIFEST_HASH, '固定された候補一覧と一致しません')
    plan = candidate_plan(load(manifest))
    host_scores, host_correctness, receipts, originals = {}, {}, {}, {}
    for host in (HOST_A, HOST_B):
        print(f'{host}: 原本由来ファイルと既存集計を照合中...', flush=True)
        scores, correctness, receipt, snapshots = audit_host(repo, host, plan)
        host_scores[host], host_correctness[host], receipts[host], originals[host] = scores, correctness, receipt, snapshots
        print(f'{host}: 90条件の照合完了', flush=True)
    rows = [comparison(key, host_scores[HOST_A][key], host_scores[HOST_B][key],
                       host_correctness[HOST_A][key], host_correctness[HOST_B][key])
            for key in sorted(plan, key=lambda x: (x[0], list(SIZE_MACROS).index(x[1])))]
    summary = summarize_comparison(rows)
    by_kernel = []
    for kernel in sorted({r['kernel'] for r in rows}):
        xs = [r for r in rows if r['kernel'] == kernel]
        require(len(xs) == 3, 'カーネル内のサイズ数不一致')
        by_kernel.append({'kernel': kernel, 'sizes': 3,
                          'symmetric_transfer_regret_mean': statistics.fmean(x['symmetric_transfer_regret'] for x in xs),
                          'near_set_jaccard_distance_mean': statistics.fmean(x['near_set_jaccard_distance'] for x in xs),
                          'no_shared_near_oracle_sizes': sum(not x['near_sets_overlap'] for x in xs)})
    # 入力が実行中に変わっていないことを再確認。入力側には何も書かない。
    for host, locations in originals.items():
        for kind, (root, before) in locations.items():
            require(snapshot(root) == before, f'{host}/{kind}: 実行中に入力が変更されました')
    require(sha(contract) == CONTRACT_HASH and sha(manifest) == MANIFEST_HASH, '契約が実行中に変わりました')
    now = datetime.now(timezone.utc)
    output = repo / 'external-results/cpu-comparison-v1' / (now.strftime('%Y%m%dT%H%M%S.%fZ') + '-' + uuid.uuid4().hex[:8])
    output.mkdir(parents=True, exist_ok=False)
    receipt_dir = output / 'input-hashes'
    receipt_dir.mkdir()
    for host, locations in originals.items():
        for kind, (root, before) in locations.items():
            (receipt_dir / f'{host}-{kind}.sha256').write_bytes(manifest_bytes(before))
    (output / 'comparison-script.py').write_bytes(Path(__file__).read_bytes())
    write_csv(output / 'instances.csv', rows)
    write_csv(output / 'kernels.csv', by_kernel)
    write_json(output / 'summary.json', summary)
    report = japanese_report(summary)
    (output / 'report-ja.txt').write_text(report, encoding='utf-8')
    write_json(output / 'integrity-receipt.json', {
        'created_utc': now.isoformat(), 'receipt_timing': 'post_extraction',
        'source_files_unchanged': True, 'original_summaries_unchanged': True,
        'hash_at_extraction_null_is_not_rewritten': True, 'hosts': receipts,
        'analysis_contract_sha256': CONTRACT_HASH, 'candidate_manifest_sha256': MANIFEST_HASH,
        'comparison_script_sha256': sha(Path(__file__).resolve()),
        'new_model_requests': 0, 'new_benchmark_executions': 0, 'network_requests': 0,
        'aggregate_rules': '固定契約の条件別指標を90条件で単純平均。3サイズのカーネル別平均も併記。',
        'limitations': ['この比較は既存の測定最良値を用いる記述的評価。独立した性能再確認ではない。',
                        '最良値の選択と評価に同じ測定を使う影響を除去したわけではない。',
                        '機械語同一性は既存実験の関数範囲ハッシュによる分類を継承。再証明はしない。',
                        'ハッシュ記録がない過去時点のファイル状態を今回の処理で証明することはできない。']})
    (output / 'SHA256SUMS').write_bytes(manifest_bytes(snapshot(output)))
    print(report)
    print('CPU_COMPARISON_COMPLETE')
    print(f'保存先: {output}')
    print(f'結果ハッシュ一覧: {sha(output / "SHA256SUMS")}')
    return output


class Tests(unittest.TestCase):
    def setUp(self):
        self.a = {'identity': 1.0, 'x': 1.2, 'y': 1.2, 'bad': None}
        self.b = {'identity': 1.0, 'x': 0.9, 'y': 1.1, 'bad': None}

    def test_geometric_mean(self):
        self.assertAlmostEqual(geometric_mean([1.0, 4.0]), 2.0)

    def test_nonfinite_rejected(self):
        for x in [float('nan'), float('inf'), 0, -1, True]:
            with self.assertRaises(AuditError):
                positive(x, 'test')

    def test_json_duplicate_rejected(self):
        with self.assertRaises(AuditError):
            json_text('{"a":1,"a":2}')

    def test_json_nan_rejected(self):
        with self.assertRaises(AuditError):
            json_text('{"a":NaN}')

    def test_bool_strict(self):
        self.assertTrue(boolean('True'))
        with self.assertRaises(AuditError):
            boolean('')

    def test_path_traversal_rejected(self):
        for s in ['/a', '../a', 'a/../../b']:
            with self.assertRaises(AuditError):
                safe_relative(s)

    def test_exact_ties(self):
        _, exact, _ = best_sets(self.a)
        self.assertEqual(exact, {'x', 'y'})

    def test_near_boundary(self):
        best, _, near = best_sets({'identity': 1.0, 'a': 1.01, 'b': 0.999})
        self.assertEqual(best, 1.01)
        self.assertEqual(near, {'identity', 'a'})

    def test_transfer_ties_best_destination(self):
        self.assertEqual(transfer({'x', 'y'}, self.b, 1.1)['regret'], 0.0)

    def test_transfer_invalid_destination(self):
        result = transfer({'bad'}, self.b, 1.1)
        self.assertEqual(result['regret'], 1.0)
        self.assertEqual(result['eligible_count'], 0)

    def test_transfer_missing_id_rejected(self):
        with self.assertRaises(AuditError):
            transfer({'missing'}, self.b, 1.1)

    def test_symmetric_directions(self):
        c = {k: True for k in self.a}
        r = comparison(('k', 'MINI'), self.a, self.b, c, c)
        rr = comparison(('k', 'MINI'), self.b, self.a, c, c)
        self.assertEqual(r['symmetric_transfer_regret'], rr['symmetric_transfer_regret'])

    def test_canonical_difference_can_share_best(self):
        b = {'identity': 1.0, 'x': 1.1, 'y': 1.2, 'bad': None}
        c = {k: True for k in self.a}
        r = comparison(('k', 'MINI'), self.a, b, c, c)
        self.assertFalse(r['canonical_best_equal'])
        self.assertTrue(r['exact_sets_overlap'])

    def test_same_reject_count_different_ids(self):
        a = {'identity': True, 'x': False, 'y': True, 'bad': True}
        b = {'identity': True, 'x': True, 'y': False, 'bad': True}
        r = comparison(('k', 'MINI'), self.a, self.b, a, b)
        self.assertEqual(r['correctness_disagreement_count'], 2)

    def test_manifest_existing_and_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'a').write_bytes(b'x')
            (root / 'SHA256SUMS').write_bytes(manifest_bytes({'a': digest(b'x')}))
            self.assertTrue(verify_existing_hashes(root, snapshot(root)))
            (root / 'a').write_bytes(b'y')
            with self.assertRaises(AuditError):
                verify_existing_hashes(root, snapshot(root))

    def test_no_manifest_is_recordable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertFalse(verify_existing_hashes(root, snapshot(root)))

    def test_synthetic_instance_end_to_end(self):
        with tempfile.TemporaryDirectory() as td:
            directory, candidates = synthetic_instance(Path(td))
            score, correctness = audit_instance(directory, set(candidates), candidates, 'k', 'MINI')
            self.assertAlmostEqual(score['loop_00_unroll_count_2'], 1.2)
            self.assertEqual(score['loop_00_interleave_count_2'], 1.0)
            self.assertIsNone(score['loop_00_vectorize_width_2'])
            self.assertTrue(all(correctness.values()))

    def test_raw_ratio_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            directory, candidates = synthetic_instance(Path(td))
            p = directory / 'final-timing.json'
            x = load(p)
            x['identity'][0]['reference_ns'] += 100000
            p.write_text(json.dumps(x))
            with self.assertRaises(AuditError):
                audit_instance(directory, set(candidates), candidates, 'k', 'MINI')

    def test_duplicate_trial_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            directory, candidates = synthetic_instance(Path(td))
            p = directory / 'final-timing.json'
            x = load(p)
            x['identity'][0]['trial'] = 1
            p.write_text(json.dumps(x))
            with self.assertRaises(AuditError):
                audit_instance(directory, set(candidates), candidates, 'k', 'MINI')

    def test_invalid_alias_inherits_invalid(self):
        with tempfile.TemporaryDirectory() as td:
            directory, candidates = synthetic_instance(Path(td))
            candidates['loop_00_vectorize_width_2']['measurement_valid'] = 'True'
            with self.assertRaises(AuditError):
                audit_instance(directory, set(candidates), candidates, 'k', 'MINI')


def synthetic_instance(root: Path):
    ids = ['identity', 'loop_00_unroll_count_2', 'loop_00_interleave_count_2', 'loop_00_vectorize_width_2']
    reps = {ids[0]: ids[0], ids[1]: ids[1], ids[2]: ids[0], ids[3]: ids[3]}
    timings, summaries, candidates = {}, {}, {}
    invalid = {ids[3]}
    for rep in set(reps.values()):
        cn = 5_000_000 if rep == ids[1] else 6_000_000
        ratios, ss = [], []
        for session in (0, 1):
            for trial in range(8):
                ratios.append({'candidate_id': rep, 'session': session, 'trial': trial,
                               'order': ['reference', rep] if trial % 2 == 0 else [rep, 'reference'],
                               'measurement_valid': True, 'batch_count': 8,
                               'reference_ns': 6_000_000, 'candidate_ns': cn,
                               'speedup': 6_000_000 / cn})
            ss.append({'candidate_id': rep, 'session': session, 'pairs': 8, 'batch_count': 8,
                       'measurement_valid': True, 'median_paired_speedup': 6_000_000 / cn,
                       'quality_warnings': ['test_warning'] if rep in invalid else []})
        timings[rep], summaries[rep] = ratios, ss
    gate = []
    for cid in ids:
        rep = reps[cid]
        h = digest(rep.encode())
        gate.append({'candidate_id': cid, 'admitted': True, 'function': {'bytes_sha256': h}})
        valid = rep not in invalid
        v = '' if not valid else ('1.2' if rep == ids[1] else '1.0')
        candidates[cid] = {'correctness_admitted': 'True', 'measurement_valid': str(valid),
                           'oracle_eligible': str(valid), 'machine_code_noop': str(cid == ids[2]),
                           'machine_code_representative': rep, 'machine_code_sha256': h, 'speedup': v}
    inst = {'kernel_id': 'k', 'size': 'MINI_DATASET', 'size_label': 'MINI', 'instance_valid': True,
            'candidate_ids_requested': 4, 'candidates_admitted': 4, 'unique_machine_code_groups': 3,
            'nonidentity_representatives_measured': 2, 'aliases_to_identity': 2, 'final_k': 8,
            'identity_summaries': summaries['identity'], 'candidate_representatives_invalid_no_rerun': list(invalid)}
    for name, value in [('instance-summary.json', inst), ('gate.json', {'candidate_rows': gate}),
                        ('alias-map.json', reps), ('final-timing.json', timings), ('final-timing-summary.json', summaries)]:
        write_json(root / name, value)
    return root, candidates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if result.wasSuccessful() else 1
    try:
        execute(args.repo)
        return 0
    except (AuditError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f'比較を停止しました: {type(exc).__name__}: {exc}', file=sys.stderr)
        print('元のデータは変更していません。再測定や既存結果の上書きは行わないでください。', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
