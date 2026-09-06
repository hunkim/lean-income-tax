#!/usr/bin/env python3
"""Reproduce a pinned official corpus. pip install beautifulsoup4; --offline uses saved HTML."""
import argparse, collections, hashlib, json, re, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup
ROOT = Path(__file__).resolve().parents[1]
VERSIONS = [
 ('current', '280405', '20260701', '21221', '20251223'),
 ('historical-20260421', '285523', '20260421', '21548', '20260421'),
 ('future-20270101', '280405', '20270101', '21221', '20251223'),
]
def clean(node):
 clone = BeautifulSoup(str(node), 'html.parser')
 for img in clone.find_all('img'):
  img.replace_with('[공식 이미지 대체텍스트: '+img.get('alt','대체텍스트 없음')+']')
 return re.sub(r'\s+', ' ', clone.get_text()).strip()
def write(path, data):
 path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
def parse(html, version, source_url, retrieved):
 name, seq, effective, act, promulgated = version
 soup = BeautifulSoup(html, 'html.parser')
 for ui in soup.select('.rule_area'): ui.decompose()
 for key, expected in [('lsNm','소득세법'),('lsiSeq',seq),('efYd',effective),('ancNo',act),('ancYd',promulgated)]:
  assert soup.find('input',id=key)['value'] == expected, (key, expected)
 articles=[]; hierarchy={}; headings=[]
 for group in soup.select('#conScroll > .pgroup'):
  heading=group.select_one('.gtit')
  if heading:
   text=clean(heading); m=re.match(r'제\d+(?:의\d+)?(편|장|절|관)',text)
   if m:
    levels=['편','장','절','관']; keys=['part','chapter','section','subsection']; idx=levels.index(m[1])
    for k in keys[idx:]: hierarchy.pop(k,None)
    hierarchy[keys[idx]]=text
   headings.append(text); continue
  inp=group.select_one('input[name=joNoList]')
  if not inp: continue
  number,suffix,joid,joseq=inp['value'].split(':'); number=int(number);suffix=int(suffix)
  aid=f'art-{number}'+(f'-{suffix}' if suffix else '')
  law=group.select_one('.lawcon'); label=clean(law.select_one('label')); title=re.search(r'\((.*)\)',label)
  units=[]
  for p in law.find_all('p',recursive=False):
   txt=clean(p)
   if not txt:continue
   kind='annotation' if txt.startswith('[') else 'paragraph' if re.match(r'^[①-⑳]',txt) or (not units) else 'item' if re.match(r'^\d+\.',txt) else 'subitem' if re.match(r'^[가-하]\.',txt) else 'continuation'
   units.append({'id':f'{aid}-unit-{len(units)+1}','kind':kind,'text':txt})
  text='\n'.join(x['text'] for x in units)
  assert re.sub(r'\s','',clean(law)) == re.sub(r'\s','',text), ('unparsed body text',aid)
  articles.append({'id':aid,'number':number,'suffix':suffix,'label':label,'title':title[1] if title else '', 'text':text,'paragraphs':units,'hierarchy':dict(hierarchy),'sourceUrl':source_url+f'#J{number}:{suffix}', 'images':[{'sourceUrl':'https://law.go.kr'+i['src'],'alt':i.get('alt',''),'localPath':'data/sources/images/'+i['src'].split('flSeq=')[-1]+'.gif','reviewStatus':'unreviewed'} for i in law.find_all('img')], 'reviewStatus':'unreviewed','formalizationStatus':'unimplemented','officialArticleId':joid,'officialSequence':joseq,'deleted':bool(re.match(r'^'+re.escape(label)+r'\s*삭제',text))})
 addenda=[]
 for group in soup.select('#arDivArea > .pgroup'):
  inp=group.select_one('input[name=arInf]')
  if not inp:continue
  header=group.select_one('.pty3'); label=clean(header)
  ps=[p for p in group.find_all('p') if p != header and clean(p)]
  addenda.append({'id':'addendum-'+inp['value'],'label':label,'text':'\n'.join(clean(p) for p in ps),'units':[{'id':f'addendum-{inp["value"]}-unit-{i+1}','text':clean(p)} for i,p in enumerate(ps)],'sourceUrl':source_url+'#J'+inp['value']})
 ids=[a['id'] for a in articles]
 missing=sorted(set(range(1,178))-{a['number'] for a in articles if not a['suffix']})
 assert len(ids)==len(set(ids)), 'duplicate article ids'
 assert not missing, ('missing base article numbers',missing)
 assert len(articles)==len(soup.select('input[name=joNoList]')), 'not all body articles parsed'
 assert len(addenda)==len(soup.select('input[name=arInf]')), 'not all addenda parsed'
 assert all(a['text'] for a in articles+addenda)
 stats={'articles':len(articles),'activeArticles':sum(not a['deleted'] for a in articles),'deletedArticles':sum(a['deleted'] for a in articles),'insertedArticles':sum(bool(a['suffix']) for a in articles),'bodyTextUnits':sum(len(a['paragraphs']) for a in articles),'unitKinds':dict(collections.Counter(u['kind'] for a in articles for u in a['paragraphs'])),'addenda':len(addenda),'addendumTextUnits':sum(len(a['units']) for a in addenda),'imageReferences':sum(len(a['images']) for a in articles),'headings':len(headings),'missingBaseArticleNumbers':missing,'duplicateArticleIds':0,'matchedSourceArticleTextIgnoringWhitespace':True,'matchedSourceArticleInputs':True,'matchedSourceAddendumInputs':True}
 return {'metadata':{'title':'소득세법','englishTitle':'Income Tax Act','jurisdiction':'KR','asOfDate':'2026-09-06','version':name,'effectiveDate':effective,'promulgationDate':promulgated,'actNumber':act,'lsiSeq':seq,'lawId':'001565','sourceUrl':source_url,'publisher':'법제처 국가법령정보센터','retrievedAt':retrieved,'sourceSha256':hashlib.sha256(html.encode()).hexdigest(),'status':'current-as-of-2026-09-06' if name=='current' else 'historical-separate-snapshot' if name.startswith('historical') else 'future-separate-snapshot','scope':'본문 및 해당 공식 통합본에 실린 부칙. 시행령·판례는 포함하지 않음.','formalizationStatus':'Source inventory only; no semantic formalization claim.','parsingNotes':'이미지 수식·표는 별도 원본 파일과 공식 alt를 보존한다. alt 정확성은 검증하지 않았으며 제55조 표에서 최상위 구간 기초세액 누락이 확인되어 별도 전사본을 제공한다. HTML 공백을 정규화했으며 삭제조문·개정주석을 보존. text units는 HTML 문단 단위로 법률상 항/호 개수와 동일하지 않음. 과거 부칙 중 원문이 생략한 타법개정 내용은 복원하지 않음.'},'statistics':stats,'headings':headings,'articles':articles,'addenda':addenda}
def main():
 p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');args=p.parse_args()
 out=ROOT/'data';src=out/'sources';src.mkdir(parents=True,exist_ok=True);versions=[]
 for v in VERSIONS:
  name,seq,effective,_,_=v;url=f'https://law.go.kr/LSW/lsInfoR.do?lsiSeq={seq}&efYd={effective}&ancYnChk=0&chrClsCd=010202';path=src/f'{name}.html'
  if args.offline:
   html=path.read_bytes().decode('utf-8'); provenance=json.loads((src/f'{name}.provenance.json').read_text()); retrieved=provenance['retrievedAt']
   assert hashlib.sha256(html.encode()).hexdigest()==provenance['sha256'], ('source hash mismatch',name)
  else:
   html=urllib.request.urlopen(url,timeout=60).read().decode('utf-8');path.write_text(html);retrieved=datetime.now(timezone.utc).isoformat()
   write(src/f'{name}.provenance.json',{'url':url,'retrievedAt':retrieved,'sha256':hashlib.sha256(html.encode()).hexdigest()})
  corpus=parse(html,v,url.replace('lsInfoR.do','lsInfoP.do'),retrieved)
  file='corpus.json' if name=='current' else name+'.json';write(out/file,corpus)
  versions.append({'file':file,**corpus['metadata'],'statistics':corpus['statistics']}); print(file,corpus['statistics'])
 write(out/'versions.json',versions)
 images={x['sourceUrl']:x for v in versions for a in json.loads((out/v['file']).read_text())['articles'] for x in a['images']}
 (src/'images').mkdir(exist_ok=True)
 def fetch_image(item):
  url,row=item; target=ROOT/row['localPath']
  if args.offline:
   b=target.read_bytes(); old=next(x for x in json.loads((src/'image-provenance.json').read_text()) if x['sourceUrl']==url)
   assert hashlib.sha256(b).hexdigest()==old['sha256'], ('image hash mismatch',url)
   return old
  b=urllib.request.urlopen(url,timeout=60).read(); target.write_bytes(b)
  return {**row,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'retrievedAt':datetime.now(timezone.utc).isoformat()}
 with ThreadPoolExecutor(max_workers=5) as pool: image_records=list(pool.map(fetch_image,images.items()))
 write(src/'image-provenance.json',image_records)
 current=json.loads((out/'corpus.json').read_text())
 write(out/'classification.json',{'metadata':{'status':'unreviewed-inventory','notice':'원문 수집 목록이며 수학적 분류나 조문 검토 완료를 뜻하지 않는다.'},'articles':[{'id':a['id'],'category':'deleted' if a['deleted'] else 'pending','reviewStatus':'unreviewed','formalizationStatus':'unimplemented'} for a in current['articles']]})
if __name__=='__main__':main()
