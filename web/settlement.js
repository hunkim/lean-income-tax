import {calculate} from './domain.js';
const min=(a,b)=>a<b?a:b,max=(a,b)=>a>b?a:b,sub=(a,b)=>a>b?a-b:0n;
export function money(value,label='금액'){if(!/^\d+$/.test(String(value??'')))throw Error(`${label}: 0 이상의 원 단위 정수가 필요합니다.`);const n=BigInt(value);if(n>1000000000000n)throw Error(`${label}: 1조 원 이하만 지원합니다.`);return n;}
export function earnedDeduction(s){return min(20000000n,s<=5000000n?s*70n/100n:s<=15000000n?(350000000n+40n*(s-5000000n))/100n:s<=45000000n?(750000000n+15n*(s-15000000n))/100n:s<=100000000n?(1200000000n+5n*(s-45000000n))/100n:(1475000000n+2n*(s-100000000n))/100n);}
export function earnedCap(s){return s<=33000000n?740000n:s<=70000000n?max(660000n,sub(740000000n,8n*(s-33000000n))/1000n):s<=120000000n?max(500000n,sub(66000000n,50n*(s-70000000n))/100n):max(200000n,sub(50000000n,50n*(s-120000000n))/100n);}
export function earnedCredit(s,a){return min(a<=1300000n?a*55n/100n:(71500000n+30n*(a-1300000n))/100n,earnedCap(s));}
// 조특법126의2: threshold=S/4 remains rational until the complete deduction is floored.
export function cardDeduction(s,a,b,c,d,e){
 if(s>70000000n&&c>0n)throw Error('총급여 7천만 원 초과 문화체육 사용액은 일반 결제수단별로 분류하세요.');
 const weighted=60n*a+120n*(b+c)+160n*(d+e);
 const subtraction=15n*min(s,4n*a)+30n*min(sub(s,4n*a),4n*(b+c))+40n*sub(s,4n*(a+b+c));
 const raw=sub(weighted,subtraction),cap=400n*(s<=70000000n?3000000n:2500000n),extra=400n*(s<=70000000n?3000000n:2000000n);
 return (min(raw,cap)+min(min(sub(raw,cap),120n*c+160n*(d+e)),extra))/400n;
}
const count=(x,label)=>{const n=money(x,label);if(n>30n)throw Error(`${label}: 30명 이하만 지원합니다.`);return n;};
const list=(text,label)=>String(text??'').trim()===''?[]:String(text).split(',').map(x=>money(x.trim(),label));
export function settle2025(input){
 if(input.year!=='2025')throw Error('2025년 귀속 계산만 지원합니다.');
 if(input.scopeConfirmed!==true||input.factsConfirmed!==true)throw Error('지원 범위와 공제 자격·증빙 확인이 필요합니다.');
 if(!['standard','itemized'].includes(input.route))throw Error('표준 또는 특별공제 경로를 선택해 주세요.');
 if(input.complexCase===true)throw Error('다른 종합소득·세액감면·외국인 단일세율 등은 지원하지 않습니다. 이 모형으로 정산 결과를 판단할 수 없습니다.');
 const m=k=>money(input[k]??'0',k),c=k=>count(input[k]??'0',k);
 const salary=money(input.salary,'총급여'),prepaid=money(input.prepaid,'기납부 소득세');
 const people=c('people'),aged=c('aged'),disabled=c('disabled'),children=c('children');
 if(people<1n||aged>people||disabled>people||children>=people)throw Error('기본공제 인원에는 본인 1명을 포함하고, 추가공제 인원은 해당 기본공제 인원 범위에서 확인해 주세요.');
 const deduction=earnedDeduction(salary),income=sub(salary,deduction);
 if(input.woman&&input.singleParent)throw Error('부녀자공제와 한부모공제는 중복할 수 없습니다.');
 if(input.woman&&income>30000000n)throw Error('부녀자공제의 소득 요건을 충족하지 않습니다.');
 const personal=1500000n*people+1000000n*aged+2000000n*disabled+(input.singleParent?1000000n:input.woman?500000n:0n);
 const national=m('nationalPension'),health=input.route==='itemized'?m('healthInsurance')+m('employmentInsurance')+m('specialCappedIncome'):0n;
 const card=cardDeduction(salary,m('cardCredit'),m('cardDebit'),m('cardCulture'),m('cardMarket'),m('cardTransport'));
 const other=m('otherIncomeDeduction')+m('otherCappedIncomeDeduction'),addback=sub(card+m('otherCappedIncomeDeduction')+(input.route==='itemized'?m('specialCappedIncome'):0n),25000000n);
 const base=sub(income,personal+national+sub(health+other+card,addback));
 const assessed=BigInt(calculate(base.toString()).scaled)/100n;
 const earned=earnedCredit(salary,assessed);
 const savingsEligible=min(6000000n,m('pensionSavings')),irpEligible=min(9000000n-savingsEligible,m('irp'));
 const pensionRate=salary<=55000000n?15n:12n;
 const pension=savingsEligible*pensionRate/100n+irpEligible*pensionRate/100n;
 const child=children===0n?0n:children===1n?250000n:550000n+400000n*(children-2n);
 const birth=300000n*c('birthFirst')+500000n*c('birthSecond')+700000n*c('birthThirdPlus');
 if(c('birthFirst')+c('birthSecond')+c('birthThirdPlus')>=people)throw Error('출산·입양 공제 인원과 기본공제 인원을 다시 확인해 주세요.');
 const marriage=input.marriage?500000n:0n;
 let insurance=0n,education=0n,rent=0n,externalSpecial=0n,standard=0n;
 if(input.route==='standard'){
  const excluded=['healthInsurance','employmentInsurance','specialCappedIncome','insurance','disabledInsurance','educationSelf','educationDisabled','rent','externalSpecialCredit'];
  if(excluded.some(k=>m(k)>0n)||list(input.educationSchool,'교육비').length||list(input.educationUniversity,'교육비').length)throw Error('표준세액공제 경로에서는 특별소득·특별세액·월세 항목을 비우세요. 중복 적용하지 않습니다.');
  standard=130000n;
 }else{
  insurance=min(1000000n,m('insurance'))*12n/100n+min(1000000n,m('disabledInsurance'))*15n/100n;
  education=(m('educationSelf')+m('educationDisabled')+list(input.educationSchool,'학생별 교육비').reduce((a,x)=>a+min(3000000n,x),0n)+list(input.educationUniversity,'대학생별 교육비').reduce((a,x)=>a+min(9000000n,x),0n))*15n/100n;
  if(m('rent')>0n&&salary>80000000n)throw Error('총급여 8천만 원 초과는 이 월세 공제 모델의 범위 밖입니다.');
  rent=min(10000000n,m('rent'))*(salary<=55000000n?17n:15n)/100n;
  externalSpecial=m('externalSpecialCredit');
 }
 const credits=earned+pension+child+birth+marriage+insurance+education+rent+externalSpecial+standard;
 const determined=sub(assessed,credits),balance=determined-prepaid;
 const collectible=balance>0n&&balance<1000n?0n:balance;
 return {year:'2025',route:input.route,salary,deduction,income,personal,national,health,card,other,addback,base,assessed,earned,pension,child,birth,marriage,insurance,education,rent,externalSpecial,standard,credits,determined,prepaid,balance,collectible,refund:balance<0n?-balance:0n,additional:collectible>0n?collectible:0n,unusedCredits:sub(credits,assessed)};
}
