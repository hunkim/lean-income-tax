#!/usr/bin/env python3
"""Validate source evidence, retain provenance, and publish possibility classifications."""
import collections,datetime,difflib,hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'reports/classification'
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 corpus=json.loads((ROOT/'data/corpus.json').read_text());byid={a['id']:a for a in corpus['articles']};reviews={}
 for p in sorted(OUT.glob('batch-*.json')):
  record=json.loads(p.read_text())
  if 'parsed' not in record:continue
  for row in record['parsed']:
   if row['id'] in reviews:raise ValueError('Duplicate review '+row['id'])
   reviews[row['id']]=(row,record,p)
 active={a['id'] for a in corpus['articles'] if not a['deleted']}
 assert set(reviews)==active,{'missing':sorted(active-set(reviews)),'extra':sorted(set(reviews)-active)}
 audit=json.loads((OUT/'astra-audit.json').read_text()); audits={r['id']:r for r in audit['articles']}
 rows=[];gaps=[];normalized=[]
 for a in corpus['articles']:
  base={'id':a['id'],'formalizationStatus':'unimplemented','sourceTextSha256':sha(a['text'])}
  if a['deleted']:
   base.update(category='deleted',reviewStatus='deletion-marker-checked',evidence=a['text'],rationale='공식 통합본에 삭제로 표시된 조문이다. 현행 실체 규칙의 형식화 대상에서 제외한다.',formalizable=[],unresolved=[],dependencies=[],imageStatus='not-applicable');rows.append(base);continue
  r,record,p=reviews[a['id']];base.update({k:r[k] for k in ['category','evidence','rationale','formalizable','unresolved','dependencies']})
  assert record['sourceTextSha256'][a['id']]==base['sourceTextSha256']
  ev=r['evidence'];method='exact'
  if a['id'] in audits and 'evidence' in audits[a['id']]:
   base['evidence']=audits[a['id']]['evidence'];assert base['evidence'] in a['text'];method='astra-source-correction'
  if ev not in a['text'] and method!='astra-source-correction':
   # Match only whitespace variation; never paraphrase a source quote into evidence.
   match=re.search(r'\s*'.join(re.escape(c) for c in re.sub(r'\s','',ev)),a['text'])
   if match:base['evidence']=match.group();method='whitespace-normalized';normalized.append(a['id'])
   else:
    common=difflib.SequenceMatcher(None,ev,a['text'],autojunk=False).find_longest_match()
    if common.size>=40:
     base['evidence']=a['text'][common.b:common.b+common.size];method='exact-common-excerpt'
    else:gaps.append(a['id']);method='unmatched'
  base['reviewStatus']='source-reviewed' if method!='unmatched' else 'evidence-needs-review'
  base['review']={'collaboration':'Astra · SolarPro4','semanticReviewer':record['response'].get('model'),'record':str(p.relative_to(ROOT)),'recordSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'evidenceMatch':method,'originalModelEvidence':ev,'evidenceNotice':'원응답의 인용문이 불일치하면 원문과 실제로 일치하는 연속 발췌만 채택한다. 원응답 전체는 별도 보존하며 일치 발췌가 해석의 정확성을 증명하지는 않는다.','astraAudit':'provenance-and-coverage; individual semantic audit only where separately recorded'}
  if a['id'] in audits:
   ar=audits[a['id']];assert ar['sourceTextSha256']==base['sourceTextSha256']
   base['review']['astraAudit']='independent-selected-article-semantic-review'
   base['review']['astraAuditRecord']='reports/classification/astra-audit.json'
   base['unresolved'].append(ar['note'])
   if 'category' in ar:base['review']['originalCategory']=base['category'];base['category']=ar['category'];base['rationale']=ar['note']
   if 'dependencies' in ar:base['dependencies']=ar['dependencies']
  base['imageStatus']='verified-rate-table' if a['id']=='art-55' else 'unverified-image-content' if a['images'] else 'no-images'
  if a['images'] and a['id']!='art-55':
   base['unresolved'].append('원문 이미지 수식·표의 시각 내용은 이 분류에서 검증하지 않았다. 보존된 alt만으로 수식의 정확성이나 전체 의미 검토 완료를 주장할 수 없다.')
   if base['category']=='direct':base['category']='conditional';base['review']['categoryAdjustment']='검증되지 않은 이미지 수식·표가 있어 직접 분류를 조건부로 보수적 조정.'
  base['unresolved'].append('이 분류는 가능성 검토이며 조문 전체의 Lean 구현·법적 적용의 검증을 뜻하지 않는다.')
  rows.append(base)
 summary={'status':'semantic-possibility-reviewed' if not gaps else 'semantic-review-evidence-gaps','sourceEffectiveDate':corpus['metadata']['effectiveDate'],'sourceSha256':corpus['metadata']['sourceSha256'],'articles':len(rows),'activeArticles':len(active),'deletedArticles':len(rows)-len(active),'semanticReviewedArticles':len(reviews),'astraIndependentlyAuditedArticles':len(audits),'responseModels':sorted({record['response'].get('model','unknown') for _,record,_ in reviews.values()}),'astraCorrectedEvidenceArticles':sum(x.get('review',{}).get('evidenceMatch')=='astra-source-correction' for x in rows),'exactEvidenceArticles':sum(x.get('review',{}).get('evidenceMatch')=='exact' for x in rows),'exactCommonExcerptArticles':sum(x.get('review',{}).get('evidenceMatch')=='exact-common-excerpt' for x in rows),'whitespaceNormalizedEvidence':normalized,'unmatchedEvidence':gaps,'categories':dict(collections.Counter(x['category'] for x in rows)),'notice':'본문 전체의 조문 단위 형식화 가능성 분류. 부칙·시행령·판례의 의미 검토와 조문 전체 Lean 구현은 별도다. direct도 사실 확정이나 법률 적용의 자동 판정을 뜻하지 않는다. 이미지 수식·표는 제55조 별도 전사표를 제외하고 시각 내용 미검증. 모델별 기록은 연구 재현을 위해 보존하며 모두 개별 이중 검토를 완료했다고 주장하지 않는다.','categoryDefinitions':{'direct':'주요 규칙을 명시적 산술·논리·기한으로 표현 가능','conditional':'외부 요건·위임법령·해석 또는 이미지 검증이 필요','structural':'권한·의무·절차·연결 구조를 표현 가능','unformalized':'목적·가치 등의 판정 의미가 현재 명시되지 않음','deleted':'삭제 조문'}}
 dump(ROOT/'data/classification.json',{'metadata':summary,'articles':rows});dump(OUT/'coverage.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
 if gaps:raise SystemExit('Unmatched evidence requires manual audit')
if __name__=='__main__':main()
