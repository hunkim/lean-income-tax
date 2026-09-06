export const bands=[{upper:14000000,rate:6},{upper:50000000,rate:15},{upper:88000000,rate:24},{upper:150000000,rate:35},{upper:300000000,rate:38},{upper:500000000,rate:40},{upper:1000000000,rate:42},{upper:null,rate:45}];
// Exact integer arithmetic: output = tax in won × 100, no statutory rounding assumed.
export function calculate(base){
 if(!/^\d+$/.test(String(base)))throw new Error('과세표준은 0 이상의 원 단위 정수로 입력해 주세요.');
 const x=BigInt(base);if(x>1000000000000n)throw new Error('이 화면은 과세표준 1조 원 이하만 지원합니다.');
 let lower=0n,total=0n;const rows=[];
 for(const b of bands){const upper=b.upper===null?x:BigInt(b.upper);const width=x>lower?(x<upper?x:upper)-lower:0n;const scaled=width*BigInt(b.rate);total+=scaled;if(width>0n)rows.push({lower:lower.toString(),amount:width.toString(),rate:b.rate,scaled:scaled.toString()});lower=upper;if(x<=upper)break;}
 return {base:x.toString(),scaled:total.toString(),rows};
}
export function won(scaled){const x=BigInt(scaled);return (x/100n).toLocaleString('ko-KR')+'.'+(x%100n).toString().padStart(2,'0');}
