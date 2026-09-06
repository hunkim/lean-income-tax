#!/usr/bin/env python3
"""Actual SolarPro4 guided authorship and review; immutable request/response evidence."""
import datetime, hashlib, json, pathlib, re, subprocess, sys
from solar_review import call, LEAN
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/solar'
SYSTEM = 'Astra와 협업하는 SolarPro4입니다. Lean 4.33.1 import Std만 사용합니다. 금지: sorry, admit, axiom, unsafe, native_decide, skipKernelTC. 법률 자문이 아니라 명시적 외부 입력에 대한 산술 모형입니다.'
PROMPT = '''이번은 도구 안내를 제공한 guided round이며 무도움 평가가 아닙니다. Lean 4.33.1 Std의 omega, simp, by decide를 사용할 수 있습니다. omega는 Nat의 잘린 뺄셈과 Int 캐스트 선형 관계를 다룹니다.
하나의 lean 코드블록으로 import Std, namespace IncomeTax.SettlementSolar를 작성하고 다음 정의를 정확히 작성하세요:
def finalTax (assessed credits : Nat) : Nat := assessed - credits
def refund (determined prepaid : Nat) : Nat := prepaid - determined
def additional (determined prepaid : Nat) : Nat := determined - prepaid
서로 다른 이름의 정리 네 개를 증명하세요:
1. 모든 assessed credits에 finalTax assessed credits ≤ assessed
2. assessed ≤ credits이면 finalTax assessed credits = 0
3. 모든 determined prepaid에 ¬ (0 < refund determined prepaid ∧ 0 < additional determined prepaid)
4. 모든 determined prepaid에 (additional determined prepaid : Int) - (refund determined prepaid : Int) = (determined : Int) - (prepaid : Int)
정의는 자연수 입력의 산술 관계만 다룹니다. assessed/credits/determined/prepaid의 법적 적격성, 실제 세액공제 적용 순서나 이월/환급가능공제, 귀속연도별 원단위 처리는 검증하지 않습니다. 그 전제는 외부에서 확정해야 하며 finalTax는 모든 세제에 적용되는 법적 결정세액 정의가 아니라 제한된 비환급성 공제 산술 모델입니다. 한국어 주석에 이 한계를 명시하세요. 법적 적용의 주장을 추가하지 마세요. 마지막 별도 json 코드블록에 korean_review 배열로 해석 한계를 기록하세요.'''

def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def attempt(name, messages):
    path=OUT / (name+'.json')
    if path.exists(): return json.loads(path.read_text())
    record=call(messages, max_tokens=12000)
    record['evaluation_mode']='guided: Std omega/simp/decide provided; not unaided'
    content=record['response']['choices'][0]['message'].get('content') or ''
    match=re.search(r'```lean(?:4)?\s*\n([\s\S]*?)```',content)
    record['code']=match.group(1) if match else None
    record['accepted']=False
    if match:
        code=record['code']; leanpath=OUT/(name+'.lean'); leanpath.write_text(code)
        code_only=re.sub(r'/\-[\s\S]*?\-/|--[^\n]*','',code)
        forbidden=re.findall(r'\b(?:axiom|sorry|admit|unsafe|native_decide|skipKernelTC)\b',code_only)
        p=subprocess.run([LEAN,str(leanpath)],capture_output=True,text=True,timeout=90)
        record['compiler']={'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'prohibited_tokens':forbidden}
        record['source_sha256']=hashlib.sha256(code.encode()).hexdigest()
        record['accepted']=p.returncode==0 and not forbidden
    write(path,record); return record

def author():
    messages=[{'role':'system','content':SYSTEM},{'role':'user','content':PROMPT}]
    first=attempt('settlement-guided-01',messages); accepted=first
    if not first['accepted']:
        messages += [{'role':'assistant','content':first['response']['choices'][0]['message'].get('content') or ''},{'role':'user','content':'동일 정의와 정리 명제를 유지하고 컴파일 오류만 수정하세요:\n'+json.dumps(first.get('compiler'),ensure_ascii=False)}]
        accepted=attempt('settlement-guided-02',messages)
    stronger_guidance_used = False
    if not accepted['accepted']:
        stronger_guidance_used = True
        messages += [{'role':'assistant','content':accepted['response']['choices'][0]['message'].get('content') or ''},{'role':'user','content':'더 구체적인 Astra 증명 지원입니다. 첫 두 정리는 unfold finalTax 후 omega, 세 번째는 unfold refund additional 후 omega, 네 번째는 unfold additional refund 후 omega로 직접 증명하세요. 보조정리나 cases 분기는 불필요합니다. 이 안내를 받은 공동 증명으로 기록됩니다. 정확히 같은 네 명제를 유지하세요.'}]
        accepted=attempt('settlement-guided-03',messages)
    syntax_retry_used = False
    if not accepted['accepted']:
        syntax_retry_used = True
        messages += [{'role':'assistant','content':accepted['response']['choices'][0]['message'].get('content') or ''},{'role':'user','content':'마지막 문법 수정: Lean unfold에는 쉼표가 없습니다. unfold refund additional 및 unfold additional refund처럼 공백으로 구분하세요. 나머지 코드는 그대로 유지하고 전체 코드를 반환하세요.'}]
        accepted=attempt('settlement-guided-04',messages)
    if accepted['accepted']:
        (ROOT/'lean/IncomeTax/SettlementSolar.lean').write_text(accepted['code'])
        names=re.findall(r'^theorem (\w+)',accepted['code'],re.M)
        auditpath=OUT/'settlement-audit.lean'
        auditpath.write_text(accepted['code']+'\n'+'\n'.join('#print axioms IncomeTax.SettlementSolar.'+n for n in names)+'\n')
        audit=subprocess.run([LEAN,str(auditpath)],capture_output=True,text=True,timeout=90)
        auditpath.unlink()
        if audit.returncode or 'sorryAx' in audit.stdout: raise RuntimeError(audit.stdout+audit.stderr)
        write(OUT/'settlement-audit.json',{'accepted_source_sha256':accepted['source_sha256'],'theorems':names,'compiler_exit_code':audit.returncode,'axioms':audit.stdout,'stderr':audit.stderr})
    summary={'requested_model':'solar-pro4','response_model':accepted['response'].get('model'),'evaluation_mode':accepted['evaluation_mode'],'first_guided_attempt_passed':first['accepted'],'compiler_retry_used':accepted is not first,'stronger_guidance_used':stronger_guidance_used,'syntax_retry_used':syntax_retry_used,'accepted':accepted['accepted'],'accepted_sha256':accepted.get('source_sha256'),'scope':'External-input nonrefundable-credit subtraction, refund/additional arithmetic. No legal eligibility or rounding theorem.'}
    write(OUT/'settlement-evaluation.json',summary); print(json.dumps(summary,ensure_ascii=False))

def review():
    target=ROOT/'lean/IncomeTax/Settlement.lean'; code=target.read_text(); digest=hashlib.sha256(code.encode()).hexdigest()
    path=OUT/('settlement-astra-review-'+digest[:12]+'.json')
    if path.exists(): print(path); return
    prompt='다음 Astra 작성 Lean 산술 모델을 검토하세요. 수학 정의와 한국어 한계가 일치하는지, 명백한 계산 오류 또는 법적 주장 과장이 있는지 구체적인 식/정리명을 근거로 지적하세요. 법령 원문 자체를 제공하지 않으므로 법적 충실성의 확정 검증은 불가하다고 명시하고 추측하지 마세요. 특히 Nat 잘린 뺄셈, 세액공제 한도, 과세표준/총급여 혼동, 원단위 처리, 비환급성 공제의 경계를 살펴보세요. JSON만 반환: verdict, issues 배열(severity,symbol,reason), limitations 배열.\n```lean\n'+code+'\n```'
    record=call([{'role':'system','content':SYSTEM},{'role':'user','content':prompt}],max_tokens=12000)
    record['reviewed_source_sha256']=digest; record['reviewed_source']='lean/IncomeTax/Settlement.lean';write(path,record);print(path)

def fidelity_review():
    target=ROOT/'lean/IncomeTax/Settlement.lean'; code=target.read_text(); digest=hashlib.sha256(code.encode()).hexdigest()
    rulespath=ROOT/'data/settlement-2025-rules.json'; rules=rulespath.read_text()
    path=OUT/('settlement-fidelity-final-'+digest[:12]+'.json')
    if path.exists(): print(path); return
    lines=(ROOT/'data/settlement-sources/nts-2025-guide.txt').read_text().splitlines()
    excerpts='\n'.join(lines[11546:11582]+lines[11788:11793])
    prompt='아래는 국세청 2025귀속 안내서에서 확인한 규칙 명세와 원 단위 서식 발췌, Astra 최종 Lean 코드입니다. 코드와 명세의 산술 대응, 원단위 절사 시점, 외부 적격성 한계의 정확성을 검토하세요. 없는 오류를 추측하지 말고 구체적 반례가 있으면 제시하세요. /1000과 /100 혼용 자체는 오류가 아닙니다. 함수명100은 100배 출력, 나머지는 원 단위인지 확인하세요. Nat 뺄셈은 0으로 잘리고 비음수이며 a-b-c=a-(b+c)입니다. 직접 컴파일 도구를 사용하지 않았으므로 컴파일 통과를 주장하지 마세요. 제공된 명세와 코드의 충실성 검토이며 원 법령 전부의 독립 검증은 아닙니다. JSON만 반환: verdict, issues 배열(severity,symbol,reason,counterexample), limitations 배열.\n규칙:\n'+rules+'\n서식 발췌:\n'+excerpts+'\nLean:\n```lean\n'+code+'\n```'
    record=call([{'role':'system','content':SYSTEM},{'role':'user','content':prompt}],max_tokens=12000)
    record['reviewed_source_sha256']=digest; record['reviewed_source']='lean/IncomeTax/Settlement.lean'
    record['rules_source_sha256']=hashlib.sha256(rules.encode()).hexdigest();record['rules_source']='data/settlement-2025-rules.json'
    write(path,record);print(path)

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    fidelity_review() if '--fidelity' in sys.argv else review() if '--review' in sys.argv else author()
