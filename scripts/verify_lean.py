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
salary_points=sorted({0,1,33000001,65400000,*[v+d for v in [5000000,15000000,33000000,43000000,45000000,55000000,70000000,70320000,80000000,100000000,120000000,120600000,362500000] for d in [-1,0,1]]})
for x in salary_points:
 code+=f'\n#eval IO.println s!"COMP,{x},{{IncomeTax.Settlement.earnedDeduction100 {x} / 100}},{{IncomeTax.Settlement.earnedCreditCap {x}}},{{IncomeTax.Settlement.pensionCredit {x} 6000000 3000000}},{{IncomeTax.Settlement.rentCredit {x} 10000000}}"'
credit_points=[(s,t) for s in [33000000,33000001,70000000,70000001,120000000,120000001] for t in [0,1,1299999,1300000,1300001,4182750]]
for s0,t in credit_points:
 code+=f'\n#eval IO.println s!"CREDIT,{s0},{t},{{IncomeTax.Settlement.earnedCredit {s0} {t}}}"'
chain_points=[(0,1500000,130000,0),(50000000,1500000,0,3000000),(65400000,16095000,0,4000000),(50000000,6000000,1350000,3000000),(14000001,1500000,10000000,999)]
for sal,ded,cred,pre in chain_points:
 code+=f'\n#eval IO.println s!"CHAIN,{sal},{ded},{cred},{pre},{{IncomeTax.Settlement.salaryToDetermined {sal} {ded} {cred}}},{{IncomeTax.Settlement.collectibleBalance (IncomeTax.Settlement.salaryToDetermined {sal} {ded} {cred}) {pre}}}"'
card_points=[(s,a,b,c,d,e) for s in [40000000,40000001,70000000,70000001] for a,b,c,d,e in [(0,0,0,0,0),(20000000,0,0,0,0),(0,20000000,0,0,0),(5000000,5000000,0,5000000,5000000),(1000000,1000000,0,1000000,1000000),(100000000,100000000,0,100000000,100000000)]]+[(40000000,5000000,5000000,3000000,2000000,1000000)]
for row in card_points:
 args=' '.join(map(str,row));prefix=','.join(map(str,row))
 code+=f'\n#eval IO.println s!"CARD,{prefix},{{IncomeTax.Settlement.cardDeduction {args}}}"'
p=ROOT/'lean/VerificationGenerated.lean'
try:
 p.write_text(code);out=run(['lake','env','lean',p.name])
finally:p.unlink(missing_ok=True)
assert 'sorryAx' not in out
rows=[{'base':m[0],'scaled':m[1]} for m in re.findall(r'^ROW,(\d+),(\d+)$',out,re.M)]
assert len(rows)==len(points)
report={'leanVersion':run(['lean','--version']).strip(),'theoremCount':len(names),'theorems':names,'sourceHashes':hashes,'axioms':out.split('ROW,')[0].strip(),'cases':rows,'scope':'Basic schedule and 2025 resident employee settlement numeric components; external eligibility and supported-case limitations apply.', 'settlementCases':{'components':[dict(zip(['salary','deduction','earnedCap','pension','rent'],line.split(',')[1:])) for line in out.splitlines() if line.startswith('COMP,')],'credits':[dict(zip(['salary','assessed','credit'],line.split(',')[1:])) for line in out.splitlines() if line.startswith('CREDIT,')],'chains':[dict(zip(['salary','deductions','extraCredits','prepaid','determined','collectible'],line.split(',')[1:])) for line in out.splitlines() if line.startswith('CHAIN,')],'cards':[dict(zip(['salary','a','b','c','d','e','deduction'],line.split(',')[1:])) for line in out.splitlines() if line.startswith('CARD,')]}}
(ROOT/'reports/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(f"Verified {len(names)} theorems and {len(rows)+sum(len(x) for x in report['settlementCases'].values())} exact Lean outputs.")
