#!/usr/bin/env bash
set -euo pipefail

echo "=== IDENTITY ==="
hostname
date -u
systemd-detect-virt || true

echo
echo "=== CPU ==="
lscpu

echo
echo "=== MODEL ==="
grep -m1 '^model name' /proc/cpuinfo

echo
echo "=== FLAGS ==="
grep -m1 '^flags' /proc/cpuinfo

echo
echo "=== CACHE ==="
lscpu -C

echo
echo "=== NUMA ==="
numactl --hardware 2>/dev/null || true

echo
echo "=== MEMORY ==="
free -h

echo
echo "=== STORAGE ==="
lsblk -o NAME,SIZE,TYPE,MODEL,MOUNTPOINTS

echo
echo "=== OS ==="
cat /etc/os-release

echo
echo "=== CPUFREQ ==="
for f in \
  /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver \
  /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor \
  /sys/devices/system/cpu/cpufreq/boost \
  /sys/devices/system/cpu/smt/control \
  /sys/devices/system/cpu/smt/active
do
  printf '%s=' "$f"
  cat "$f" 2>/dev/null || echo unavailable
done

echo
echo "=== ONLINE CPUS ==="
cat /sys/devices/system/cpu/online
