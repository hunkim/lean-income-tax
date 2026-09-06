import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {settle2025,earnedDeduction,earnedCap,earnedCredit,cardDeduction} from '../web/settlement.js';
const base={year:'2025',scopeConfirmed:true,factsConfirmed:true,route:'itemized',salary:'50000000',prepaid:'3000000',people:'1'};
const report=()=>JSON.parse(readFileSync('reports/verification.json','utf8')).settlementCases;
test('settlement components and card formulas match actual Lean executions',()=>{
 const v=report();assert.ok(v.components.length>=40);assert.ok(v.cards.length>=25);
 for(const r of v.components){const s=BigInt(r.salary);assert.equal(earnedDeduction(s).toString(),r.deduction);assert.equal(earnedCap(s).toString(),r.earnedCap);const x=settle2025({...base,salary:r.salary,pensionSavings:'6000000',irp:'3000000',rent:s<=80000000n?'10000000':'0'});assert.equal(x.pension.toString(),r.pension);assert.equal(x.rent.toString(),r.rent);}
 for(const r of v.credits)assert.equal(earnedCredit(BigInt(r.salary),BigInt(r.assessed)).toString(),r.credit);
 for(const r of v.cards)assert.equal(cardDeduction(...['salary','a','b','c','d','e'].map(k=>BigInt(r[k]))).toString(),r.deduction);
});
test('end-to-end salary chain matches Lean, including capped credits and signed balances',()=>{
 for(const r of report().chains){const x=settle2025({...base,salary:r.salary,prepaid:r.prepaid,otherIncomeDeduction:(BigInt(r.deductions)-1500000n).toString(),externalSpecialCredit:r.extraCredits});assert.equal(x.determined.toString(),r.determined);assert.equal(x.collectible.toString(),r.collectible);}
});
test('2025 NTS independent worked example agrees through earned tax credit',()=>{
 const r=settle2025({...base,salary:'65400000',otherIncomeDeduction:'14595000'});
 assert.equal(r.deduction,13020000n);assert.equal(r.income,52380000n);assert.equal(r.base,36285000n);assert.equal(r.assessed,4182750n);assert.equal(r.earned,660000n);
});
test('rounding follows separate receipt entries and full cap expression',()=>{
 assert.equal(earnedCap(33000001n),739999n);
 const r=settle2025({...base,pensionSavings:'100004',irp:'100004',insurance:'100004',disabledInsurance:'100004'});
 assert.equal(r.pension,30000n);assert.equal(r.insurance,27000n);
});
test('standard route refuses incompatible special deductions and preserves eligible pension',()=>{
 assert.throws(()=>settle2025({...base,route:'standard',healthInsurance:'1'}));
 assert.throws(()=>settle2025({...base,route:'standard',rent:'1'}));
 const r=settle2025({...base,route:'standard',nationalPension:'1000000',pensionSavings:'6000000'});assert.equal(r.standard,130000n);assert.equal(r.pension,900000n);
});
test('2025 family, education, rent caps and unsupported situations',()=>{
 const r=settle2025({...base,people:'3',children:'2',educationSchool:'4000000,2000000',educationUniversity:'10000000',rent:'20000000',marriage:true});
 assert.equal(r.child,550000n);assert.equal(r.education,2100000n);assert.equal(r.rent,1700000n);assert.equal(r.marriage,500000n);
 for(const changes of [{year:'2026'},{scopeConfirmed:false},{factsConfirmed:false},{complexCase:true},{woman:true,singleParent:true},{salary:'80000001',rent:'1'},{salary:'70000001',cardCulture:'1'},{prepaid:''}])assert.throws(()=>settle2025({...base,...changes}));
});
test('small positive difference is not collected; equally small refund remains',()=>{
 const d=settle2025(base).determined;
 assert.equal(settle2025({...base,prepaid:(d-999n).toString()}).collectible,0n);
 assert.equal(settle2025({...base,prepaid:(d+999n).toString()}).refund,999n);
 assert.equal(settle2025({...base,prepaid:(d-1000n).toString()}).additional,1000n);
});
test('only capped deductions share 25m ceiling; credits cannot create negative determined tax',()=>{
 const r=settle2025({...base,otherCappedIncomeDeduction:'30000000',otherIncomeDeduction:'1000000',externalSpecialCredit:'99999999'});
 assert.equal(r.addback,5000000n);assert.equal(r.determined,0n);assert.equal(r.refund,3000000n);
});
test('special housing amount is exclusive with standard route and included in aggregate cap',()=>{
 assert.throws(()=>settle2025({...base,route:'standard',specialCappedIncome:'1'}));
 const r=settle2025({...base,specialCappedIncome:'30000000'});assert.equal(r.addback,5000000n);assert.equal(r.base,11250000n);
});
