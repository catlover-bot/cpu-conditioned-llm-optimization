import ast, difflib, hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
old=(root/'legacy_runner.py').read_text()
assert hashlib.sha256(old.encode()).hexdigest()=='d445c3794b3ef748c626dd074e1739188d75b42b177240471a90321dba254182'
new=old
changes=[
 ("REV='polybench-direct-codegen-batch-wave1-en-v2'", "REV='polybench-direct-codegen-resource-amendment-v1'"),
 ("CAPS={'C':4096,'IR':8192}","CAPS={'C':4096,'IR':16384}"),
 ("'planned_requests':180", "'planned_requests':len(plan['tasks'])"),
 ("'requests_pending':180-len(gs)","'requests_pending':len(plan['tasks'])-len(gs)"),
 ("'scope':'P0, one model, one trial, first full-dataset wave, provisional'", "'scope':plan.get('scope','resource-amendment, provisional'),'resource_amendment':plan.get('resource_amendment')"),
 ("plan['requests']==180", "plan['requests']==len(plan['tasks']) and 0<len(plan['tasks'])<=180"),
 ("summary['generation_terminal']==180 and summary['validation_terminal']==180", "summary['generation_terminal']==len(plan['tasks']) and summary['validation_terminal']==len(plan['tasks'])"),
 ("0<to<CAPS[form]", "0<to<=CAPS[form]"),
]
for a,b in changes:
 assert new.count(a)==1,(a,new.count(a))
 new=new.replace(a,b)
node=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name=='generation_phase')
lines=new.splitlines(keepends=True)
lines[node.lineno-1:node.end_lineno]=['def generation_phase(pkg,plan,run,deadline,freeze,binary):\n',
 '    from runtime_support import generation_phase as streaming_generation\n',
 '    return streaming_generation(sys.modules[__name__],pkg,plan,run,deadline,freeze,binary)\n']
new=''.join(lines)
ast.parse(new)
(root/'goal0069_batch_codegen.py').write_text(new)
(root/'runner-change.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='old-en-runner.py',tofile='resource-amendment-runner.py')))
print('Patched SHA256',hashlib.sha256(new.encode()).hexdigest())
