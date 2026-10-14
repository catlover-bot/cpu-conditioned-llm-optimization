from pathlib import Path
import base64, gzip, hashlib, sys, types, uuid

HERE = Path(__file__).resolve().parent
MODULES = {name: HERE / name for name in ('assets.py', 'pilot.py', 'numeric_core.py', 'multimodel.py', 'batch_budget.py', 'sanitizer_recovery.py')}
MODULES.update({name: HERE.parent / 'gpu005' / name for name in ('portability.py', 'posix_recovery.py')})

def module_bytes(name):
    if name not in MODULES:
        raise RuntimeError('Unknown public dependency')
    return MODULES[name].read_bytes()

def encoded_module(name):
    return base64.b64encode(gzip.compress(module_bytes(name), mtime=0)).decode()

def encoded_asset(name):
    if name not in ('source-bundle.json', 'registry.json', 'primary-summary.tar.gz'):
        raise RuntimeError('Unknown public data asset')
    raw = (HERE / 'data' / name).read_bytes()
    if name == 'primary-summary.tar.gz':
        return base64.b64encode(raw).decode()
    return base64.b64encode(gzip.compress(raw, mtime=0)).decode()

def load_module(name, expected_sha):
    raw = module_bytes(name)
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise RuntimeError('Public plaintext dependency hash differs')
    modname = 'cpucond_public_' + name.removesuffix('.py') + '_' + uuid.uuid4().hex
    mod = types.ModuleType(modname)
    mod.__file__ = str(MODULES[name])
    sys.modules[modname] = mod
    exec(compile(raw, str(MODULES[name]), 'exec'), mod.__dict__)
    return mod
