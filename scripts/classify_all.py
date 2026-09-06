#!/usr/bin/env python3
"""Preserve actual model review of every active article; never treat classification as proof."""
import concurrent.futures, datetime, hashlib, json, os, pathlib, re, time, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/classification'; OUT.mkdir(parents=True,exist_ok=True)
SYSTEM='''당신은 Upstage SolarPro4이며 Astra와 소득세법의 수학적 형식화 가능성을 함께 연구한다. 법률자문이 아니다. 각 조문 전체 텍스트를 읽고 조문 단위의 지배적 분류를 하라. direct=주요 규칙을 명시적 산술/논리/기한으로 표현 가능(입력사실 확정은 별개); conditional=계산 또는 논리구조가 있으나 위임법령/외부 요건/해석을 명시해야 함; structural=목적 외 조직/권한/절차/연결구조를 모형화할 수 있지만 숫자계산 중심 아님; unformalized=가치/목적 등 독립적으로 판정할 의미를 이 텍스트만으로 정하지 못함. 이는 형식화 불가능의 증명이 아니고 조문 전체 구현 여부도 아니다. 이미지 alt는 검증되지 않아 실제 수식/표로 신뢰하지 마라(제55조 세율표만 별도 전사검증). image 미검증이면 반드시 unresolved에 기록하라. 입력된 모든 id를 정확히 1회 출력. 마크다운 없이 JSON {"articles":[{"id":"...","category":"...","evidence":"원문에서 정확히 연속된 20~100자 인용, 생략부호나 번역금지","rationale":"이 조문 고유의 분류 이유 1문장","formalizable":["정의할 수 있는 구체적 요소"],"unresolved":["남는 구체적 해석/위임/외부사실"],"dependencies":["위임법령이나 참조조문"]}]}만 출력. 문장은 간결하게, 인용문은 반드시 제공 원문의 부분문자열이어야 함. Lean 코드나 이미 검증했다는 주장은 금지.'''
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def call(batch,index):
 p=OUT/f'batch-{index:03}.json'
 if p.exists():return p
 prompt=json.dumps([{'id':a['id'],'label':a['label'],'text':a['text'],'unverifiedImages':bool(a['images']) and a['id']!='art-55'} for a in batch],ensure_ascii=False)
 payload={'model':'solar-pro4','reasoning_effort':'low','max_tokens':12000,'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':prompt}]}
 for attempt in range(3):
  record={'request':payload,'requestSha256':digest(json.dumps(payload,ensure_ascii=False,sort_keys=True)),'articleIds':[a['id'] for a in batch],'sourceTextSha256':{a['id']:digest(a['text']) for a in batch},'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  try:
   req=urllib.request.Request('https://api.upstage.ai/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+os.environ['SOLAR_API_KEY'],'Content-Type':'application/json'})
   with urllib.request.urlopen(req,timeout=240) as r: raw=r.read().decode()
   record['responseRawSha256']=digest(raw);record['responseRaw']=raw;record['response']=json.loads(raw)
   content=record['response']['choices'][0]['message'].get('content') or ''
   parsed=json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',content.strip()))
   rows=parsed['articles'];ids=[x['id'] for x in rows]
   if sorted(ids)!=sorted(record['articleIds']):raise ValueError('id coverage mismatch')
   byid={a['id']:a for a in batch}
   for row in rows:
    if row['category'] not in ['direct','conditional','structural','unformalized']:raise ValueError('category')
    if not row.get('evidence') or not row.get('rationale') or not all(isinstance(row.get(k),list) for k in ['formalizable','unresolved','dependencies']):raise ValueError('missing review content')
    row['exactEvidence']=row['evidence'] in byid[row['id']]['text']
   record['parsed']=rows
   archive=OUT/'preserved';archive.mkdir(exist_ok=True)
   dump(archive/(p.stem+'-'+record['responseRawSha256'][:12]+'.json'),record)
   try:
    with p.open('x') as target:json.dump(record,target,ensure_ascii=False,indent=2);target.write('\n')
   except FileExistsError:pass
   print(f'completed {index} articles={len(rows)} quotes={sum(x["exactEvidence"] for x in rows)}',flush=True);return p
  except Exception as e:
   record['error']=str(e);dump(OUT/f'batch-{index:03}-attempt-{attempt+1}-error.json',record);print(f'error {index} {e}',flush=True)
 raise RuntimeError(f'Failed batch {index}')
def main():
 corpus=json.loads((ROOT/'data/corpus.json').read_text());batches=[];batch=[];size=0
 for a in corpus['articles']:
  if a['deleted']:continue
  if batch and (len(batch)>=9 or size+len(a['text'])>22000):batches.append(batch);batch=[];size=0
  batch.append(a);size+=len(a['text'])
 if batch:batches.append(batch)
 print(f'{len(batches)} batches',flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:list(ex.map(lambda pair:call(pair[1],pair[0]),enumerate(batches,1)))
 print('All actual reviews persisted; run classify_finalize.py after Astra gap audit.',flush=True)
if __name__=='__main__':main()
