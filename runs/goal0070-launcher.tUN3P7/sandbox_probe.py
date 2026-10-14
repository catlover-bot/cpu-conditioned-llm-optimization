# __CPUCOND_PREFLIGHT_V2__
# HOST_NAMESPACES is supplied by the trusted parent as a literal mapping.
import json
import os
import socket
import sys
import tempfile

checks = {}
evidence = {}
errors = {}

def test(name, fn):
    try:
        value = fn()
        checks[name] = value is True
        if value is not True:
            errors[name] = repr(value)
    except Exception as exc:
        checks[name] = False
        errors[name] = type(exc).__name__ + ': ' + str(exc)

try:
    with open('/proc/self/status', encoding='ascii') as f:
        status = dict(line.rstrip().split(':', 1) for line in f if ':' in line)
    evidence['capabilities'] = {k: int(status[k].strip(), 16)
       for k in ('CapEff', 'CapPrm', 'CapInh', 'CapAmb', 'CapBnd')}
    evidence['uid'] = list(os.getresuid())
    evidence['gid'] = list(os.getresgid())
    evidence['groups'] = os.getgroups()
    evidence['no_new_privs'] = int(status['NoNewPrivs'].strip())
    evidence['namespaces'] = {k: os.readlink('/proc/self/ns/' + k)
       for k in ('net', 'pid', 'mnt', 'ipc', 'uts')}
    evidence['network_interfaces'] = [name for _, name in socket.if_nameindex()]
    evidence['cwd'] = os.getcwd()
    evidence['cpu_affinity'] = sorted(os.sched_getaffinity(0))
    test('all_uids_65534', lambda: evidence['uid'] == [65534] * 3)
    test('all_gids_65534', lambda: evidence['gid'] == [65534] * 3)
    test('no_supplementary_groups', lambda: evidence['groups'] == [])
    test('cap_eff_prm_inh_amb_zero', lambda: all(evidence['capabilities'][k] == 0
        for k in ('CapEff', 'CapPrm', 'CapInh', 'CapAmb')))
    test('no_new_privs', lambda: evidence['no_new_privs'] == 1)
    test('root_directory_absent', lambda: not os.path.lexists('/root'))
    test('model_store_absent', lambda: not os.path.lexists('/var/lib/cpucond-infer'))
    test('working_directory_tmp', lambda: evidence['cwd'] == '/tmp')
    test('cpu_affinity_2', lambda: evidence['cpu_affinity'] == [2])
    for name in ('net', 'pid', 'mnt', 'ipc', 'uts'):
        test(name + '_namespace_separate', lambda n=name:
             evidence['namespaces'][n] != HOST_NAMESPACES[n])
    test('no_host_network_interface', lambda: set(evidence['network_interfaces']) <= {'lo'})
    def writable_tmp():
        with tempfile.TemporaryFile(dir='/tmp') as f:
            f.write(b'test')
        return True
    def writable_scratch():
        with open('/out/write-probe', 'xb') as f:
            f.write(b'CPUCOND_SCRATCH_OK\n')
        return True
    def readonly_usr():
        path = '/usr/.cpucond-readonly-probe-' + str(os.getpid())
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except OSError as exc:
            return exc.errno in (13, 30, 1)
        else:
            os.close(fd)
            os.unlink(path)
            return False
    test('tmp_writable', writable_tmp)
    test('scratch_writable', writable_scratch)
    test('usr_not_writable', readonly_usr)
except Exception as exc:
    checks['probe_completed'] = False
    errors['probe_completed'] = type(exc).__name__ + ': ' + str(exc)

result = {'checks': checks, 'failed_checks': [k for k, v in checks.items() if not v],
          'evidence': evidence, 'errors': errors}
print(json.dumps(result, sort_keys=True), flush=True)
sys.exit(0 if checks and all(checks.values()) else 125)
