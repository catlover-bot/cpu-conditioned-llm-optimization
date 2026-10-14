"""Offline corruption regressions for the standalone backup verifier."""
from __future__ import annotations
import copy
import io
import json
import os
from pathlib import Path
import sys
import subprocess
import tarfile
import tempfile
import unittest
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_backup import SCHEMA, VerificationError, canonical, digest, parse, verify_backup, verify_archives, checked_root, verify_finalization

COVERAGE = {"planned_ids":270,"saved_candidates":255,"invalid_generation":15,
            "qwen_archive_count":54,"cloud_archive_count":54}

def fixture_audit(reader):
    coverage = parse(reader.read("research/coverage.json"))
    return {"coverage_complete": coverage == COVERAGE, "coverage":coverage,
            "source_sha256":digest(reader.read("research/source.cu"))}

class BackupVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gpu006-backup-verifier-")
        self.root = Path(self.temp.name)
        self.manifest = {"schema":SCHEMA,"archives":[],"current_files":{}}
        self.add_archive("local-research-0001.tar", [
            {"path":"research/coverage.json","data":canonical(COVERAGE)},
            {"path":"research/source.cu","data":b"// original saved source\n"}])
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def add_archive(self, name, rows):
        members = []
        with tarfile.open(self.root/name,"w:",format=tarfile.PAX_FORMAT) as tar:
            for row in rows:
                info = tarfile.TarInfo(row["path"])
                info.mode,info.uid,info.gid,info.mtime = 0o644,65534,65534,123456.5
                kind = row.get("type","file")
                data = row.get("data",b"")
                if kind == "directory":
                    info.type = tarfile.DIRTYPE
                elif kind == "symlink":
                    info.type = tarfile.SYMTYPE
                    info.linkname = row["link_target"]
                elif kind == "hardlink":
                    info.type = tarfile.LNKTYPE
                    info.linkname = row["link_target"]
                elif kind == "fifo":
                    info.type = tarfile.FIFOTYPE
                else:
                    info.size = len(data)
                tar.addfile(info,io.BytesIO(data) if kind == "file" else None)
                item = {"path":row["path"],"type":kind,"size":info.size,
                        "mode":info.mode,"uid":info.uid,"gid":info.gid,"mtime":info.mtime}
                ref = {"archive":name,"member":row["path"],"type":kind}
                if kind == "file":
                    item["sha256"] = ref["sha256"] = digest(data)
                if kind in ("symlink","hardlink"):
                    item["link_target"] = info.linkname
                members.append(item)
                self.manifest["current_files"][row["path"]] = ref
        raw = (self.root/name).read_bytes()
        self.manifest["archives"].append({"label":name[:-4],"path":name,
                                         "size":len(raw),"sha256":digest(raw),"members":members})

    def save(self, recorded=None):
        if recorded is None:
            reader,_,_ = verify_archives(checked_root(self.root),self.manifest)
            recorded = fixture_audit(reader)
        raw = canonical(recorded)
        (self.root/"semantic-audit.json").write_bytes(raw)
        self.manifest["semantic_audit"] = {"path":"semantic-audit.json","size":len(raw),"sha256":digest(raw)}
        (self.root/"manifest.json").write_bytes(canonical(self.manifest))

    def assert_refused(self, message=None):
        with self.assertRaisesRegex(VerificationError,message or "."):
            verify_backup(self.root,audit_func=fixture_audit)

    def test_regular_backup_and_internal_link_are_verified_without_following(self):
        self.add_archive("remote-results-0001.tar",[
            {"path":"research/source-link","type":"symlink","link_target":"source.cu"}])
        self.save()
        result = verify_backup(self.root,audit_func=fixture_audit)
        self.assertTrue(result["verified"])
        self.assertFalse(result["archive_extraction"])
        self.assertFalse(result["symlinks_followed"])
        self.assertEqual(result["current_files"],3)
        self.assertFalse((self.root/"research").exists())
        reader,_,_=verify_archives(checked_root(self.root),self.manifest)
        self.assertFalse(reader.exists("research/source-link"))
        with self.assertRaisesRegex(VerificationError,"Regular archived file missing"):
            reader.read("research/source-link")

    def test_incremental_revision_selects_latest_without_discarding_previous(self):
        self.add_archive("local-research-0002.tar",[{"path":"research/source.cu","data":b"// newer saved source\n"}])
        self.save()
        result=verify_backup(self.root,audit_func=fixture_audit)
        self.assertEqual(result["revisions"],{"research/source.cu":["local-research-0001.tar","local-research-0002.tar"]})
        self.assertEqual(result["semantic_audit"]["source_sha256"],digest(b"// newer saved source\n"))

    def test_outer_bytes_size_and_missing_archive_are_refused(self):
        path=self.root/"local-research-0001.tar"
        original=path.read_bytes()
        for raw in (original+b"x",b"x"+original[1:]):
            with self.subTest(size=len(raw)):
                path.write_bytes(raw)
                self.assert_refused("size mismatch|hash mismatch")
        path.unlink()
        self.assert_refused("unavailable")

    def test_inner_hash_and_metadata_are_checked_even_when_outer_is_valid(self):
        original=copy.deepcopy(self.manifest)
        for field,value in (("sha256","0"*64),("mode",0o777),("uid",0),("gid",0),("mtime",0),("size",1),("type","directory")):
            with self.subTest(field=field):
                self.manifest=copy.deepcopy(original)
                self.manifest["archives"][0]["members"][0][field]=value
                self.save(recorded={"coverage_complete":True,"coverage":COVERAGE})
                self.assert_refused("hash mismatch|metadata mismatch|type/size mismatch")

    def test_unsafe_posix_and_windows_archive_names_are_refused(self):
        for name in ("../escape","/absolute","C:/Users/secret","research/C:/Users/secret","research/file:stream","C:\\Users\\secret","research//double","research/./dot"):
            with self.subTest(name=name):
                self.manifest={"schema":SCHEMA,"archives":[],"current_files":{}}
                for path in self.root.glob("*.tar"):
                    path.unlink()
                self.add_archive("local-research-0001.tar",[{"path":name,"data":b"x"}])
                self.save(recorded={"coverage_complete":True,"coverage":COVERAGE})
                self.assert_refused("path")
        self.assertFalse((self.root.parent/"escape").exists())

    def test_duplicate_headers_and_duplicate_declared_members_are_refused(self):
        self.manifest={"schema":SCHEMA,"archives":[],"current_files":{}}
        (self.root/"local-research-0001.tar").unlink()
        self.add_archive("local-research-0001.tar",[{"path":"research/same","data":b"a"},{"path":"research/same","data":b"b"}])
        self.manifest["archives"][0]["members"].pop()
        self.save(recorded={"coverage_complete":True,"coverage":COVERAGE})
        self.assert_refused("Duplicate TAR")
        self.manifest["archives"][0]["members"].append(copy.deepcopy(self.manifest["archives"][0]["members"][0]))
        self.save(recorded={"coverage_complete":True,"coverage":COVERAGE})
        self.assert_refused("Duplicate declared")

    def test_duplicate_labels_and_archive_names_are_refused(self):
        self.manifest["archives"].append(copy.deepcopy(self.manifest["archives"][0]))
        self.save(recorded={"coverage_complete":True,"coverage":COVERAGE})
        self.assert_refused("Duplicate")
        self.manifest["archives"][1]["label"]="different"
        self.save(recorded={"coverage_complete":True,"coverage":COVERAGE})
        self.assert_refused("unique uncompressed")

    def test_external_escaping_hard_and_special_links_are_refused(self):
        base=copy.deepcopy(self.manifest)
        for kind,target in (("symlink","/etc/passwd"),("symlink","../../escape"),("symlink","C:/secret"),("hardlink","research/source.cu"),("fifo",None)):
            with self.subTest(kind=kind,target=target):
                self.manifest=copy.deepcopy(base)
                row={"path":"research/link","type":kind}
                if target is not None: row["link_target"]=target
                self.add_archive("remote-results-0001.tar",[row])
                self.save(recorded={"coverage_complete":True,"coverage":COVERAGE})
                self.assert_refused("symlink|Hardlink or special")
                (self.root/"remote-results-0001.tar").unlink()

    def test_dangling_internal_link_is_refused(self):
        self.add_archive("remote-results-0001.tar",[{"path":"research/link","type":"symlink","link_target":"missing"}])
        self.save(recorded={"coverage_complete":True,"coverage":COVERAGE})
        self.assert_refused("target missing")

    def test_filesystem_links_never_open_external_bytes(self):
        path=self.root/"local-research-0001.tar"
        path.unlink()
        path.symlink_to("/etc/passwd")
        self.assert_refused("filesystem symlink")

    def test_partial_unlisted_and_trailing_payload_archives_are_refused(self):
        (self.root/"pending.tar.partial").write_bytes(b"partial")
        self.assert_refused("Partial backup")
        (self.root/"pending.tar.partial").unlink()
        (self.root/"extra.tar").write_bytes(b"unlisted")
        self.assert_refused("Unmanifested outer")
        (self.root/"extra.tar").unlink()
        archive=self.manifest["archives"][0]
        path=self.root/archive["path"]
        raw=path.read_bytes()+b"hidden"+bytes(506)
        path.write_bytes(raw)
        archive.update(size=len(raw),sha256=digest(raw))
        self.save(recorded={"coverage_complete":True,"coverage":COVERAGE})
        self.assert_refused("trailing TAR")

    def test_rehashed_truncated_tar_without_terminator_is_refused(self):
        archive=self.manifest["archives"][0]
        path=self.root/archive["path"]
        with tarfile.open(path,"r:") as tar:
            last=tar.getmembers()[-1]
            end=last.offset_data+((last.size+511)//512)*512
        raw=path.read_bytes()[:end]
        path.write_bytes(raw)
        archive.update(size=len(raw),sha256=digest(raw))
        self.save(recorded={"coverage_complete":True,"coverage":COVERAGE})
        self.assert_refused("terminator")

    def test_current_file_pointer_cannot_choose_stale_or_wrong_revision(self):
        old=copy.deepcopy(self.manifest["current_files"]["research/source.cu"])
        self.add_archive("local-research-0002.tar",[{"path":"research/source.cu","data":b"new"}])
        self.manifest["current_files"]["research/source.cu"]=old
        self.save(recorded={"coverage_complete":True,"coverage":COVERAGE})
        self.assert_refused("Current-file pointers")

    def test_recorded_semantic_counts_cannot_forge_success(self):
        forged=fixture_audit(verify_archives(checked_root(self.root),self.manifest)[0])
        forged["coverage"]["saved_candidates"]=270
        self.save(recorded=forged)
        self.assert_refused("Semantic audit differs")

    def test_recomputed_incomplete_counts_are_refused_even_if_record_matches(self):
        self.add_archive("local-research-0002.tar",[{"path":"research/coverage.json","data":canonical(dict(COVERAGE,planned_ids=269))}])
        self.save()
        self.assert_refused("coverage is incomplete")

    def test_coverage_true_cannot_bypass_fixed_counts(self):
        def malicious_counts(reader):
            return {"coverage_complete":True,"coverage":dict(COVERAGE,saved_candidates=270)}
        self.save(recorded=malicious_counts(None))
        with self.assertRaisesRegex(VerificationError,"Fixed 270/255/15"):
            verify_backup(self.root,audit_func=malicious_counts)

    def test_audit_and_standalone_tool_bytes_are_pinned(self):
        audit=self.root/"semantic-audit.json"
        audit.write_bytes(audit.read_bytes()+b" ")
        self.assert_refused("size mismatch")
        self.save()
        (self.root/"audit_local.py").write_bytes(b"# trusted companion\n")
        self.manifest["standalone_tools"]=[{"path":"audit_local.py","size":1,"sha256":"0"*64}]
        self.save()
        self.assert_refused("size mismatch")

    def test_duplicate_json_fields_and_read_limit_are_refused(self):
        (self.root/"manifest.json").write_bytes(b'{"schema":"x","schema":"y"}')
        self.assert_refused("Duplicate JSON")
        self.save()
        reader,_,_=verify_archives(checked_root(self.root),self.manifest)
        with self.assertRaisesRegex(VerificationError,"cap exceeded"):
            reader.read("research/source.cu",1)

    def test_actual_cli_corrupt_manifest_stops_without_writes_or_extraction(self):
        (self.root/"manifest.json").write_bytes(b'{"schema":"wrong"}')
        before={p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result=subprocess.run([sys.executable,"-I",str(Path(__file__).with_name("verify_backup.py")),str(self.root)],
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,check=False)
        self.assertEqual(result.returncode,2)
        self.assertIn(b"manifest schema differs",result.stderr)
        self.assertNotIn(b"Traceback",result.stderr)
        after={p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before,after)

    def test_semantic_audit_reference_is_required_for_complete_verification(self):
        self.manifest.pop("semantic_audit")
        (self.root/"manifest.json").write_bytes(canonical(self.manifest))
        self.assert_refused("Semantic audit reference missing")


class FinalizationReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="gpu006-finalization-test-")
        self.root=Path(self.temp.name)
        self.required=("manifest.json","SHA256SUMS","WINDOWS_VERIFICATION.json","BACKUP_REPORT.md","MISSING_FILES.json")
        for name in self.required:
            if name != "SHA256SUMS":
                (self.root/name).write_bytes(("saved "+name+"\n").encode())
        (self.root/"MISSING_FILES.json").write_bytes(canonical({"complete":True,"items":[],"completion_requires_valid_finalization":True}))
        (self.root/"archives").mkdir()
        (self.root/"archives/data.tar").write_bytes(b"saved archive bytes")
        rows=[name for name in self.required if name != "SHA256SUMS"]+["archives/data.tar"]
        (self.root/"SHA256SUMS").write_text("".join(digest((self.root/name).read_bytes())+"  "+name+"\n" for name in rows))

    def tearDown(self):
        self.temp.cleanup()

    def update_missing(self,complete,items=None):
        (self.root/"MISSING_FILES.json").write_bytes(canonical({"complete":complete,"items":items or [],"completion_requires_valid_finalization":True}))
        rows=(self.root/"SHA256SUMS").read_text().splitlines()
        rows=[digest((self.root/"MISSING_FILES.json").read_bytes())+"  MISSING_FILES.json" if row.endswith("  MISSING_FILES.json") else row for row in rows]
        (self.root/"SHA256SUMS").write_text("\n".join(rows)+"\n")

    def receipt(self,complete=True):
        references=[]
        for name in self.required:
            raw=(self.root/name).read_bytes()
            references.append({"path":name,"size":len(raw),"sha256":digest(raw)})
        return {"schema":"gpu006-backup-finalization-v1","complete":complete,"references":references}

    def write_receipt(self,value=None):
        (self.root/"BACKUP_FINALIZATION.json").write_bytes(canonical(value if value is not None else self.receipt()))

    def test_missing_receipt_is_unfinalized_without_claiming_completion(self):
        self.assertEqual(verify_finalization(self.root),{"present":False,"complete":False,"reason":"unfinalized"})

    def test_valid_complete_and_valid_partial_receipts_check_all_deliverables(self):
        for complete in (False,True):
            with self.subTest(complete=complete):
                self.update_missing(complete)
                self.write_receipt(self.receipt(complete))
                result=verify_finalization(self.root)
                self.assertTrue(result["present"])
                self.assertIs(result["complete"],complete)
                self.assertEqual(result["references_verified"],5)
                self.assertEqual(result["checksum_files_verified"],5)

    def test_completion_must_match_missing_report_and_have_no_missing_items(self):
        self.write_receipt(self.receipt(False))
        with self.assertRaisesRegex(VerificationError,"completion differs"): verify_finalization(self.root)
        self.update_missing(True,[{"path":"remote runtime","reason":"pending"}])
        self.write_receipt(self.receipt(True))
        with self.assertRaisesRegex(VerificationError,"with missing items"): verify_finalization(self.root)
        self.update_missing("true")
        self.write_receipt(self.receipt(True))
        with self.assertRaisesRegex(VerificationError,"completion differs"): verify_finalization(self.root)

    def test_bad_schema_nonboolean_and_missing_or_duplicate_references_are_refused(self):
        baseline=self.receipt()
        variants=[]
        for field,value in (("schema","wrong"),("complete",1),("references",baseline["references"][:-1])):
            variant=copy.deepcopy(baseline);variant[field]=value;variants.append(variant)
        variant=copy.deepcopy(baseline);variant["references"][-1]=variant["references"][0];variants.append(variant)
        for variant in variants:
            with self.subTest(value=variant):
                self.write_receipt(variant)
                with self.assertRaises(VerificationError): verify_finalization(self.root)

    def test_stale_receipt_reference_or_missing_delivery_is_refused(self):
        self.write_receipt()
        (self.root/"BACKUP_REPORT.md").write_bytes(b"changed report")
        with self.assertRaisesRegex(VerificationError,"mismatch"): verify_finalization(self.root)
        self.write_receipt()
        (self.root/"WINDOWS_VERIFICATION.json").unlink()
        with self.assertRaisesRegex(VerificationError,"unavailable"): verify_finalization(self.root)

    def test_stale_archived_file_is_refused_even_with_current_five_references(self):
        (self.root/"archives/data.tar").write_bytes(b"corrupt saved archive")
        self.write_receipt()
        with self.assertRaisesRegex(VerificationError,"hash mismatch"): verify_finalization(self.root)

    def test_unsafe_duplicate_and_missing_checksum_entries_are_refused(self):
        original=(self.root/"SHA256SUMS").read_text()
        variants=[original+original.splitlines()[0]+"\n",
                  original+"0"*64+"  ../escape\n",
                  original+"0"*64+"  C:/Users/secret\n",
                  "malformed\n", "", "\n",
                  "\n".join(line for line in original.splitlines() if not line.endswith("manifest.json"))+"\n"]
        for text in variants:
            with self.subTest(text=text):
                (self.root/"SHA256SUMS").write_text(text)
                self.write_receipt()
                with self.assertRaises(VerificationError): verify_finalization(self.root)

    def test_receipt_filesystem_symlink_is_never_followed(self):
        (self.root/"BACKUP_FINALIZATION.json").symlink_to("/etc/passwd")
        with self.assertRaisesRegex(VerificationError,"filesystem symlink"): verify_finalization(self.root)

if __name__ == "__main__":
    unittest.main(verbosity=2)
