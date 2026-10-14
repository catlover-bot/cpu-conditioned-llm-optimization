#!/usr/bin/env bash
set -euo pipefail

out="${1:-host-observation}"
mkdir -p "$out"

run_capture() {
  local name="$1"; shift
  {
    printf '$'
    printf ' %q' "$@"
    printf '\n'
    "$@"
  } >"$out/$name.txt" 2>&1 || true
}

date -u +"%Y-%m-%dT%H:%M:%SZ" > "$out/observed_at_utc.txt"
uname -a > "$out/uname.txt"
cat /etc/os-release > "$out/os-release.txt" 2>/dev/null || true
cat /proc/cpuinfo > "$out/proc-cpuinfo.txt"
lscpu > "$out/lscpu.txt"
lscpu -J > "$out/lscpu.json" 2>/dev/null || true
systemd-detect-virt > "$out/virtualization.txt" 2>&1 || true

if command -v numactl >/dev/null 2>&1; then
  run_capture numactl numactl --hardware
fi
if command -v clang >/dev/null 2>&1; then
  run_capture clang-version clang --version
fi
if command -v gcc >/dev/null 2>&1; then
  run_capture gcc-version gcc --version
fi
if command -v perf >/dev/null 2>&1; then
  run_capture perf-version perf --version
  run_capture perf-permission perf stat -e cycles,instructions -- true
fi

taskset -pc $$ > "$out/current-affinity.txt" 2>&1 || true

for f in \
  /sys/devices/system/cpu/smt/control \
  /sys/devices/system/cpu/smt/active \
  /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor \
  /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver \
  /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq \
  /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq \
  /sys/kernel/mm/transparent_hugepage/enabled
do
  if [ -r "$f" ]; then
    safe="$(printf '%s' "$f" | sed 's#/#_#g')"
    cat "$f" > "$out/${safe}.txt"
  fi
done

python3 - "$out" <<'PY'
from pathlib import Path
import hashlib, json, sys
root = Path(sys.argv[1])
files = {}
for p in sorted(root.iterdir()):
    if p.is_file() and p.name != "manifest.json":
        data = p.read_bytes()
        files[p.name] = {
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
(root / "manifest.json").write_text(
    json.dumps({"files": files}, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

echo "HOST_ACCEPTANCE_CAPTURE_COMPLETE"
echo "output: $out"
echo "This command only observes the host; it does not change CPU frequency, SMT, governor, or kernel settings."
