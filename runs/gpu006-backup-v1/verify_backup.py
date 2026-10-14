#!/usr/bin/env python3
"""Verify a GPU006 backup using only local bytes; never extract or follow links."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tarfile
sys.dont_write_bytecode = True

SCHEMA = "gpu006-full-backup-manifest-v1"
MIB = 1024 * 1024
MAX_MANIFEST = 128 * MIB
MAX_READ = 512 * MIB
CHUNK = MIB
SHA_RE = re.compile(r"^[0-9a-f]{64}$")

class VerificationError(RuntimeError):
    pass

def require(ok, message):
    if not ok:
        raise VerificationError(message)

def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def parse(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(VerificationError("Nonfinite JSON value")))
    except (ValueError, UnicodeError, TypeError) as exc:
        raise VerificationError("Invalid JSON") from exc

def safe_name(value):
    require(isinstance(value, str) and value and "\x00" not in value and "\\" not in value,
            "Unsafe archive or backup path")
    require(not value.startswith("/") and not re.match(r"^[A-Za-z]:", value), "Absolute or Windows path refused")
    parts = value.split("/")
    require(all(part not in ("", ".", "..") and ":" not in part for part in parts),
            "Noncanonical, Windows, or escaping path refused")
    return value

def safe_link(path, target):
    require(isinstance(target, str) and target and "\x00" not in target and "\\" not in target,
            "Unsafe symlink target")
    require(not target.startswith("/") and not re.match(r"^[A-Za-z]:", target), "External symlink target refused")
    parts = path.split("/")[:-1]
    for part in target.split("/"):
        require(part != "" and ":" not in part, "Noncanonical or Windows symlink target")
        if part == ".":
            continue
        if part == "..":
            require(parts, "Escaping symlink target refused")
            parts.pop()
        else:
            parts.append(part)
    require(parts, "Symlink to archive root refused")
    return "/".join(parts)

def checked_root(path):
    root = Path(os.path.abspath(path))
    for part in (root, *root.parents):
        require(not part.is_symlink(), "Backup filesystem symlink refused")
    require(root.is_dir(), "Backup directory missing")
    return root

def open_regular(root, relative):
    safe_name(relative)
    path = root.joinpath(*relative.split("/"))
    for part in (path, *path.parents):
        require(not part.is_symlink(), "Backup filesystem symlink refused")
        if part == root:
            break
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as exc:
        raise VerificationError("Backup file unavailable: " + relative) from exc
    stream = os.fdopen(fd, "rb")
    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
        stream.close()
        raise VerificationError("Backup member is not a regular file: " + relative)
    return stream

def read_regular(root, relative, cap=MAX_READ):
    require(type(cap) is int and 0 <= cap <= MAX_READ, "Invalid bounded read cap")
    with open_regular(root, relative) as stream:
        require(os.fstat(stream.fileno()).st_size <= cap, "Backup file read cap exceeded: " + relative)
        data = stream.read(cap + 1)
    require(len(data) <= cap, "Backup file read cap exceeded: " + relative)
    return data

def checked_blob(root, record):
    require(isinstance(record, dict), "Invalid backup artifact record")
    name = safe_name(record.get("path"))
    size, expected = record.get("size"), record.get("sha256")
    require(type(size) is int and size >= 0 and isinstance(expected, str) and SHA_RE.fullmatch(expected),
            "Invalid backup size/hash: " + name)
    with open_regular(root, name) as stream:
        require(os.fstat(stream.fileno()).st_size == size, "Backup archive size mismatch: " + name)
        actual = hashlib.sha256()
        total = 0
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            actual.update(chunk)
            total += len(chunk)
    require(total == size and actual.hexdigest() == expected, "Backup archive hash mismatch: " + name)
    return name

def member_type(member):
    require(not member.sparse and not any(k.startswith("GNU.sparse") for k in member.pax_headers), "Sparse TAR member refused")
    if member.isfile():
        return "file"
    if member.isdir():
        return "directory"
    if member.issym():
        return "symlink"
    raise VerificationError("Hardlink or special TAR member refused")

class ArchiveReader:
    """Read regular current files by TAR offsets without extraction or symlink resolution."""
    def __init__(self, root, current, indexes):
        self.root, self.current, self.indexes = root, current, indexes

    def exists(self, relative):
        safe_name(relative)
        return relative in self.current and self.current[relative]["type"] == "file"

    def iter_paths(self, prefix=""):
        if prefix:
            safe_name(prefix.rstrip("/"))
        return iter(sorted(name for name, item in self.current.items()
                           if item["type"] == "file" and name.startswith(prefix)))

    def read(self, relative, cap=MAX_READ):
        safe_name(relative)
        require(type(cap) is int and 0 <= cap <= MAX_READ, "Invalid bounded archive read cap")
        require(self.exists(relative), "Regular archived file missing: " + relative)
        ref = self.current[relative]
        item = self.indexes[ref["archive"]][ref["member"]]
        require(item["size"] <= cap, "Archived read cap exceeded: " + relative)
        with open_regular(self.root, ref["archive"]) as stream:
            stream.seek(item["offset"])
            data = stream.read(item["size"])
        require(len(data) == item["size"] and digest(data) == item["sha256"], "Archived bytes changed: " + relative)
        return data

def verify_archives(root, manifest):
    archives = manifest.get("archives")
    require(isinstance(archives, list) and archives, "No backup archives declared")
    indexes, labels, ordered_latest, revisions = {}, set(), {}, {}
    summaries = []
    for archive in archives:
        require(isinstance(archive, dict), "Invalid archive declaration")
        label = archive.get("label")
        require(isinstance(label, str) and label and label not in labels, "Duplicate or invalid archive label")
        labels.add(label)
        name = checked_blob(root, archive)
        require(name.endswith(".tar") and name not in indexes, "Outer archive must be a unique uncompressed TAR")
        declared = archive.get("members")
        require(isinstance(declared, list), "Archive member inventory missing")
        by_name = {}
        for item in declared:
            require(isinstance(item, dict), "Invalid member declaration")
            key = safe_name(item.get("path"))
            require(key not in by_name, "Duplicate declared archive member: " + key)
            by_name[key] = item
        index, seen, regular_bytes, last_end = {}, set(), 0, 0
        try:
            with open_regular(root, name) as stream, tarfile.open(fileobj=stream, mode="r:") as tar:
                for member in tar:
                    key = safe_name(member.name.rstrip("/") if member.isdir() else member.name)
                    require(key not in seen, "Duplicate TAR member: " + key)
                    seen.add(key)
                    require(key in by_name, "Undeclared TAR member: " + key)
                    expected = by_name[key]
                    kind = member_type(member)
                    require(expected.get("type") == kind and type(expected.get("size")) is int
                            and expected["size"] == member.size, "TAR type/size mismatch: " + key)
                    for field in ("mode", "uid", "gid", "mtime"):
                        value = expected.get(field)
                        valid_number = type(value) in (int, float) if field == "mtime" else type(value) is int
                        require(valid_number and math.isfinite(value)
                                and value == getattr(member, field), "TAR metadata mismatch: " + key + " " + field)
                    last_end = member.offset_data + ((member.size + 511) // 512) * 512
                    saved = {"type": kind, "size": member.size, "offset": member.offset_data}
                    if kind == "file":
                        expected_hash = expected.get("sha256")
                        require(isinstance(expected_hash, str) and SHA_RE.fullmatch(expected_hash), "Missing member hash: " + key)
                        actual = hashlib.sha256()
                        extracted = tar.extractfile(member)
                        require(extracted is not None, "Cannot read regular TAR bytes")
                        count = 0
                        with extracted:
                            for chunk in iter(lambda: extracted.read(CHUNK), b""):
                                count += len(chunk)
                                actual.update(chunk)
                        require(count == member.size and actual.hexdigest() == expected_hash, "TAR member hash mismatch: " + key)
                        saved["sha256"] = expected_hash
                        regular_bytes += member.size
                    elif kind == "symlink":
                        require(expected.get("link_target") == member.linkname, "TAR symlink target mismatch: " + key)
                        saved["link_target"] = member.linkname
                        saved["resolved_target"] = safe_link(key, member.linkname)
                    index[key] = saved
                    ordered_latest[key] = {"archive": name, "member": key, "type": kind,
                                           **({"sha256": saved["sha256"]} if kind == "file" else {})}
                    revisions.setdefault(key, []).append(name)
                require(seen == set(by_name), "Missing declared TAR member")
                require(archive["size"] % 512 == 0 and archive["size"] - last_end >= 1024,
                        "Missing complete TAR terminator")
                stream.seek(last_end)
                require(all(not any(chunk) for chunk in iter(lambda: stream.read(CHUNK), b"")),
                        "Uninventoried trailing TAR bytes")
        except (tarfile.TarError, OSError, EOFError) as exc:
            raise VerificationError("Invalid or truncated TAR: " + name) from exc
        indexes[name] = index
        summaries.append({"label": label, "path": name, "size": archive["size"], "sha256": archive["sha256"],
                          "members": len(index), "regular_file_bytes": regular_bytes})
    current = manifest.get("current_files")
    require(isinstance(current, dict) and current == ordered_latest,
            "Current-file pointers differ from ordered archived revisions")
    for key, ref in current.items():
        item = indexes[ref["archive"]][ref["member"]]
        if item["type"] == "symlink":
            require(item["resolved_target"] in current, "Symlink target missing from backup: " + key)
    # A retained partial/new archive cannot be mistaken for a fully verified backup.
    for path in root.rglob("*"):
        require(not path.is_symlink(), "Unmanifested filesystem symlink refused")
        if path.is_file() and (".partial" in path.name or path.suffix == ".part"):
            raise VerificationError("Partial backup artifact retained: " + str(path.relative_to(root)))
        if path.is_file() and path.suffix == ".tar":
            require(path.relative_to(root).as_posix() in indexes, "Unmanifested outer TAR archive")
    return ArchiveReader(root, current, indexes), summaries, {key: names for key, names in revisions.items() if len(names) > 1}

def verify_backup(backup_dir, audit_func=None):
    root = checked_root(backup_dir)
    manifest = parse(read_regular(root, "manifest.json", MAX_MANIFEST))
    require(isinstance(manifest, dict) and manifest.get("schema") == SCHEMA, "Backup manifest schema differs")
    reader, archives, revisions = verify_archives(root, manifest)
    for record in manifest.get("standalone_tools", []):
        checked_blob(root, record)
    semantic_ref = manifest.get("semantic_audit")
    require(isinstance(semantic_ref, dict), "Semantic audit reference missing")
    checked_blob(root, semantic_ref)
    recorded = parse(read_regular(root, semantic_ref["path"]))
    if audit_func is None:
        # This is the trusted companion verifier, never an archived experiment module.
        from audit_local import audit_reader
        audit_func = audit_reader
    recomputed = audit_func(reader)
    require(isinstance(recomputed, dict) and recomputed.get("coverage_complete") is True,
            "Archived semantic coverage is incomplete")
    expected_counts = {"planned_ids": 270, "saved_candidates": 255, "invalid_generation": 15,
                       "qwen_archive_count": 54, "cloud_archive_count": 54}
    coverage = recomputed.get("coverage", {})
    require(isinstance(coverage, dict) and all(type(coverage.get(key)) is int and coverage[key] == value
                                            for key, value in expected_counts.items()),
            "Fixed 270/255/15 and 54+54 archive coverage differs")
    require(canonical(recomputed) == canonical(recorded),
            "Semantic audit differs from independently read archived bytes")
    return {"schema": "gpu006-full-backup-verification-v1", "verified": True,
            "manifest_sha256": digest(read_regular(root, "manifest.json", MAX_MANIFEST)),
            "archives": archives, "current_files": len(reader.current), "revisions": revisions,
            "semantic_audit_sha256": digest(canonical(recomputed)), "semantic_audit": recomputed,
            "archive_extraction": False, "symlinks_followed": False,
            "ssh_connections": 0, "api_calls": 0, "generated_code_executed": False}


def verify_finalization(backup_dir):
    """Validate the last receipt without changing pre-finalization archive checks."""
    root = checked_root(backup_dir)
    path = root / "BACKUP_FINALIZATION.json"
    if not path.exists() and not path.is_symlink():
        return {"present": False, "complete": False, "reason": "unfinalized"}
    receipt = parse(read_regular(root, "BACKUP_FINALIZATION.json", MIB))
    require(isinstance(receipt, dict) and receipt.get("schema") == "gpu006-backup-finalization-v1"
            and type(receipt.get("complete")) is bool, "Invalid backup finalization receipt")
    required = {"manifest.json", "SHA256SUMS", "WINDOWS_VERIFICATION.json", "BACKUP_REPORT.md", "MISSING_FILES.json"}
    references = receipt.get("references")
    require(isinstance(references, list) and len(references) == len(required), "Finalization requires exact five references")
    names = []
    for record in references:
        require(isinstance(record, dict), "Invalid finalization reference")
        names.append(safe_name(record.get("path")))
    require(len(set(names)) == len(names) and set(names) == required,
            "Finalization references are missing, duplicate or unexpected")
    for record in references:
        checked_blob(root, record)
    missing = parse(read_regular(root, "MISSING_FILES.json", 16 * MIB))
    require(isinstance(missing, dict) and type(missing.get("complete")) is bool
            and missing["complete"] is receipt["complete"] and isinstance(missing.get("items"), list),
            "Finalization completion differs from missing-file report")
    require(not receipt["complete"] or not missing["items"],
            "Finalization cannot claim completion with missing items")
    try:
        lines = read_regular(root, "SHA256SUMS", 16 * MIB).decode("utf-8").splitlines()
    except UnicodeError as exc:
        raise VerificationError("Invalid SHA256SUMS encoding") from exc
    checksums = {}
    for line in lines:
        require(line, "Blank SHA256SUMS entry refused")
        match = re.fullmatch(r"([0-9a-f]{64}) ([ *])(.+)", line)
        require(match is not None, "Malformed SHA256SUMS entry")
        expected, _, name = match.groups()
        safe_name(name)
        require(name not in checksums, "Duplicate SHA256SUMS path")
        checksums[name] = expected
        with open_regular(root, name) as stream:
            size = os.fstat(stream.fileno()).st_size
        checked_blob(root, {"path": name, "size": size, "sha256": expected})
    require(checksums, "SHA256SUMS has no entries")
    require(required - {"SHA256SUMS"} <= set(checksums), "SHA256SUMS omits final deliverable")
    return {"present": True, "complete": receipt["complete"], "references_verified": len(references),
            "checksum_files_verified": len(checksums),
            "receipt_sha256": digest(read_regular(root, "BACKUP_FINALIZATION.json", MIB))}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup_dir", type=Path)
    args = parser.parse_args(argv)
    result = verify_backup(args.backup_dir)
    result["finalization"] = verify_finalization(args.backup_dir)
    print(canonical(result).decode().strip())
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("Backup verification failed: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
