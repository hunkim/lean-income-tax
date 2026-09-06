#!/usr/bin/env python3
"""Reproducible bounded SolarPro4 contribution; exact attempts are immutable records."""
import datetime, hashlib, json, os, pathlib, re, subprocess, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/solar'
LEAN = os.environ.get('LEAN_BIN', '/tmp/lean-ai-toolchain/lean-4.33.1-darwin_aarch64/bin/lean')
SOURCE = 'https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7873&mi=6437'
SYSTEM = '''당신은 실제 SolarPro4로서 Astra와 소득세법 형식화 연구에 함께 참여합니다. Lean 4.33.1, import Std만 사용하고 Mathlib는 없습니다. axiom, sorry, admit, unsafe, native_decide, skipKernelTC는 금지합니다. 정의나 정리를 약화하지 마세요. 응답은 하나의 lean 코드블록과 하나의 json 코드블록으로 구성하세요. json에는 korean_review 배열(법문과 모형 관계 및 한계 4개 이하)을 넣으세요. 법률·세무 자문이 아닙니다.'''
PROMPT = f'''국세청 공식 출처를 Astra가 2026-09-06 확인했습니다: {SOURCE}
인용: "1,400만원 이하 | 과세표준의 6%". 소득세법 제55조 제1항 첫 구간만 연구합니다.
namespace IncomeTax.Solar에서 def firstBandTax100 (base : Nat) : Nat := 6 * base 를 직접 작성하세요. 값은 원 단위 과세표준에 대한 세액을 100배한 정수로, 반올림을 수행하지 않습니다.
네 정리를 직접 증명하세요: firstBandTax100 0 = 0; firstBandTax100 14000000 = 84000000; 모든 x y : Nat에 x ≤ y 이면 firstBandTax100 x ≤ firstBandTax100 y; x ≤ y 이면 firstBandTax100 y - firstBandTax100 x ≤ 100 * (y - x).
모든 정리에 고유한 이름을 붙이세요. 첫 구간 상한 14000000 이하 여부와 과세표준 확정은 법적 적용의 외부 전제입니다. 수학 함수는 그 밖의 자연수에도 정의되지만 그 값은 다른 구간의 세금이 아닙니다. 총급여/연봉과 과세표준은 다릅니다. 이 함수는 공제 자격, 결정세액, 지방소득세, 원단위 처리, 기납부세액, 연말정산 환급액을 정의하지 않습니다. 이를 한국어 코드 주석과 json 검토에 정확하게 설명하세요.'''

def call(messages, max_tokens=4500):
    payload = dict(model='solar-pro4', reasoning_effort='low', max_tokens=max_tokens, messages=messages)
    request = urllib.request.Request('https://api.upstage.ai/v1/chat/completions', data=json.dumps(payload).encode(), headers={'Authorization': 'Bearer ' + os.environ['SOLAR_API_KEY'], 'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=180) as response:
        body = json.load(response)
    return {'request': payload, 'response': body, 'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()}

def attempt(name, messages):
    record_path = OUT / (name + '.json')
    if record_path.exists():
        return json.loads(record_path.read_text())
    record = call(messages)
    content = record['response']['choices'][0]['message'].get('content') or ''
    match = re.search(r'```lean(?:4)?\s*\n([\s\S]*?)```', content)
    record['code'] = match.group(1) if match else None
    if match:
        path = OUT / (name + '.lean')
        path.write_text(record['code'])
        forbidden = re.findall(r'\b(?:axiom|sorry|admit|unsafe|native_decide|skipKernelTC)\b', record['code'])
        result = subprocess.run([LEAN, str(path)], capture_output=True, text=True, timeout=60)
        record['compiler'] = dict(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr, prohibited_tokens=forbidden)
        record['accepted'] = result.returncode == 0 and not forbidden
    else:
        record['accepted'] = False
        record['compiler'] = {'error': 'Missing Lean code block'}
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    return record

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    messages = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': PROMPT}]
    first = attempt('first-attempt', messages)
    accepted = first
    if not first['accepted']:
        content = first['response']['choices'][0]['message'].get('content') or ''
        messages += [{'role': 'assistant', 'content': content}, {'role': 'user', 'content': '원래 정의와 네 정리 및 한국어 검토 범위를 그대로 유지하고, 다음 컴파일러 오류만 수정하세요. 한 번의 재시도입니다.\n' + json.dumps(first['compiler'], ensure_ascii=False)}]
        accepted = attempt('compiler-retry', messages)
    if accepted['accepted']:
        target = ROOT / 'lean/IncomeTax/Solar.lean'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(accepted['code'])
    summary = dict(source=SOURCE, checked_at='2026-09-06', requested_model='solar-pro4', response_model=accepted['response'].get('model'), first_attempt_passed=first['accepted'], retry_used=accepted is not first, accepted=accepted['accepted'], theorem_count=len(re.findall(r'^theorem\s', accepted['code'] or '', re.M)) if accepted['accepted'] else 0, accepted_sha256=hashlib.sha256(accepted['code'].encode()).hexdigest() if accepted['accepted'] else None, scope='제55조 제1항 첫 구간의 산출세액 ×100 산술 모형. 법적 적용 전제와 연말정산 전체는 미구현.')
    (OUT / 'evaluation.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False))

def review_astra():
    """Replay the preserved independent Korean fidelity review without rebuilding its prompt."""
    path = OUT / 'astra-review.json'
    if not path.exists():
        raise SystemExit('The initial Korean review record must exist before replay.')
    record = json.loads(path.read_text())
    target = OUT / ('astra-review-replay-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json')
    replay = call(record['request']['messages'])
    replay['reviewed_source_sha256'] = record['reviewed_source_sha256']
    target.write_text(json.dumps(replay, ensure_ascii=False, indent=2) + '\n')
    print(target.relative_to(ROOT))

if __name__ == '__main__':
    review_astra() if '--replay-astra-review' in sys.argv else main()
