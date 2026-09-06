#!/usr/bin/env python3
import hashlib,json,os,pathlib,re,shutil,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
bin_dir=os.getenv('LEAN_BIN_DIR','/tmp/lean-ai-toolchain/lean-4.33.1-darwin_aarch64/bin')
env=dict(os.environ);env['PATH']=bin_dir+os.pathsep+env.get('PATH','')
def run(args):
 p=subprocess.run(args,cwd=ROOT/'lean',env=env,capture_output=True,text=True,timeout=180)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout
run(['lake','build'])
files=sorted((ROOT/'lean/IncomeTax').glob('*.lean'));names=[];hashes={}
for f in files:
 text=f.read_text(); stripped=re.sub(r'/\-[\s\S]*?\-/|--[^\n]*','',text)
 assert not re.search(r'\b(sorry|admit|axiom|unsafe|native_decide)\b',stripped),f
 ns=re.search(r'^namespace ([\w.]+)',text,re.M)[1]
 names.extend(ns+'.'+x for x in re.findall(r'^theorem (\w+)',text,re.M))
 hashes[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
points=sorted({0,1,20000000,1000000000000,*[v+d for v in [14000000,50000000,88000000,150000000,300000000,500000000,1000000000] for d in [-1,0,1]]})
code='import IncomeTax\n'+ '\n'.join('#print axioms '+n for n in names)+'\n'+'\n'.join(f'#eval IO.println s!"ROW,{x},{{IncomeTax.tax100 {x}}}"' for x in points)
p=ROOT/'lean/VerificationGenerated.lean'
try:
 p.write_text(code);out=run(['lake','env','lean',p.name])
finally:p.unlink(missing_ok=True)
assert 'sorryAx' not in out
rows=[{'base':m[0],'scaled':m[1]} for m in re.findall(r'^ROW,(\d+),(\d+)$',out,re.M)]
assert len(rows)==len(points)
report={'leanVersion':run(['lean','--version']).strip(),'theoremCount':len(names),'theorems':names,'sourceHashes':hashes,'axioms':out.split('ROW,')[0].strip(),'cases':rows,'scope':'Article55(1) basic schedule only; no annual-settlement, rounding or eligibility claim.'}
(ROOT/'reports/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(f'Verified {len(names)} theorems and {len(rows)} exact Lean outputs.')
