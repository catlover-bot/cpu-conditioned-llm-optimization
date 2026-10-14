import pytest

from cpucond import __main__ as cli


def test_doctor_failure_exit_code(monkeypatch, capsys):
    monkeypatch.setattr(cli, "doctor", lambda: {"ready": False})
    assert cli.main(["doctor"]) == 1
    assert '"ready": false' in capsys.readouterr().out


def test_missing_manifest_does_not_report_success(tmp_path, capsys):
    assert cli.main(["check-artifacts", str(tmp_path)]) == 1
    assert '"passed": false' in capsys.readouterr().out


def test_cli_rejects_ir_before_run(tmp_path, capsys):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["smoke", "--input-kind", "llvm_ir", "--output", str(tmp_path)])
    assert exit_info.value.code == 1
    assert "not implemented" in capsys.readouterr().err
    assert not list(tmp_path.iterdir())
