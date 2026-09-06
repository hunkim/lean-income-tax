import IncomeTax.Basic
namespace IncomeTax.Settlement
/- 2025 귀속 근로소득 연말정산의 수치 구성요소.
자격·증빙·총급여/비과세 구분은 외부 사실입니다.
이름이 100으로 끝나는 함수만 금액의 100배이며, 다른 함수는 원 단위입니다.
정수 원으로 입력하는 다음 단계에서는 나눗셈의 절사를 별도로 표시합니다. -/
def earnedDeduction100 (salary : Nat) : Nat :=
  min 2000000000
    (if salary ≤ 5000000 then 70*salary
     else if salary ≤ 15000000 then 350000000 + 40*(salary-5000000)
     else if salary ≤ 45000000 then 750000000 + 15*(salary-15000000)
     else if salary ≤ 100000000 then 1200000000 + 5*(salary-45000000)
     else 1475000000 + 2*(salary-100000000))
-- 제50조: 공제 대상 인원은 요건 충족과 중복 여부가 외부에서 확정된 수입니다.
def personalBasic (eligiblePeople : Nat) : Nat := 1500000*eligiblePeople
-- 공제 후 음수 과세표준은 0으로 모델링합니다.
def taxableBase (salary earnedDeduction otherDeductions : Nat) : Nat :=
  salary-earnedDeduction-otherDeductions
-- 제59조: 일반 근로소득만 있고 별도 감면 조정이 없는 모델입니다.
def earnedCredit100 (assessed : Nat) : Nat :=
  if assessed ≤ 1300000 then 55*assessed
  else 71500000 + 30*(assessed-1300000)
def earnedCreditCap (salary : Nat) : Nat :=
  if salary ≤ 33000000 then 740000
  else if salary ≤ 70000000 then max 660000 ((740000000 - 8*(salary-33000000))/1000)
  else if salary ≤ 120000000 then max 500000 ((66000000-50*(salary-70000000))/100)
  else max 200000 ((50000000-50*(salary-120000000))/100)
def earnedCredit (salary assessed : Nat) : Nat :=
  min (earnedCredit100 assessed / 100) (earnedCreditCap salary)
-- 제59조의4: 특별소득·특별세액·월세 공제를 적용하지 않는 경로만 선택합니다.
def standardCredit (eligible : Bool) : Nat := if eligible then 130000 else 0
-- 제59조의3 일반 연금계좌: 적격 연금저축/IRP 본인 납입액만 입력합니다.
def pensionEligible (savings irp : Nat) : Nat := min 9000000 (min 6000000 savings + irp)
def pensionCredit (salary savings irp : Nat) : Nat :=
  let savingsPart := min 6000000 savings
  let irpPart := min (9000000-savingsPart) irp
  let rate := if salary ≤ 55000000 then 15 else 12
  savingsPart*rate/100 + irpPart*rate/100
-- 다른 소득/세액감면 등 복합 사례의 계산 순서는 이 모형에서 지원하지 않습니다.
def determinedTax (assessed credits : Nat) : Nat := assessed-credits
def settlementBalance (determined prepaid : Nat) : Int := (determined : Int)-(prepaid : Int)

theorem earned_deduction_cap (s : Nat) : earnedDeduction100 s ≤ 2000000000 := by
  exact Nat.min_le_left _ _
theorem taxable_base_le_salary (s e d : Nat) : taxableBase s e d ≤ s := by
  unfold taxableBase; omega
theorem deduction_monotone_base (s e d d' : Nat) (h : d ≤ d') :
    taxableBase s e d' ≤ taxableBase s e d := by
  unfold taxableBase; omega
theorem credit_bounded_by_cap (s a : Nat) : earnedCredit s a ≤ earnedCreditCap s := by
  exact Nat.min_le_right _ _
theorem pension_eligible_cap (s i : Nat) : pensionEligible s i ≤ 9000000 := by
  exact Nat.min_le_left _ _
theorem credits_cannot_make_negative (a c : Nat) (h : a ≤ c) : determinedTax a c = 0 := by
  unfold determinedTax; omega
theorem prepaid_increase_reduces_balance (d p q : Nat) (h : p ≤ q) :
    settlementBalance d q ≤ settlementBalance d p := by
  unfold settlementBalance; omega
theorem salary_50m_deduction : earnedDeduction100 50000000 = 1225000000 := by decide
theorem pension_boundary : pensionCredit 55000000 6000000 3000000 = 1350000 := by decide
theorem pension_above_boundary : pensionCredit 55000001 6000000 3000000 = 1080000 := by decide
-- 2025년 소득세법59조의2: 적격 자녀·출산입양 대상은 외부에서 확인합니다.
def childCredit (n : Nat) : Nat :=
  if n = 0 then 0 else if n = 1 then 250000 else 550000+400000*(n-2)
def birthCredit (first second later : Nat) : Nat := 300000*first+500000*second+700000*later
-- 조특법92조 혼인세액공제: 2025 혼인신고 및 생애1회 등은 외부 전제.
def marriageCredit (eligible : Bool) : Nat := if eligible then 500000 else 0
-- 제59조의4: 각각의 적격 보험료를 독립된 공제금액 칸으로 계산합니다.
def insuranceCredit (ordinary disabledDedicated : Nat) : Nat :=
  min 1000000 ordinary * 12 / 100 + min 1000000 disabledDedicated * 15 / 100
-- 조특법95조의2: 주택·세대·주소·증빙 적격성을 별도 확인한 월세만.
def rentCredit (salary eligibleRent : Nat) : Nat :=
  if salary ≤ 80000000 then min 10000000 eligibleRent * (if salary ≤ 55000000 then 17 else 15) / 100 else 0
-- 조특법126조의2: 25% 문턱의 분수를 보존하기 위해 전체식을400배로 계산.
def cardDeduction (s a b c d e : Nat) : Nat :=
  let weighted := 60*a+120*(b+c)+160*(d+e)
  let removed := 15*min s (4*a)+30*min (s-4*a) (4*(b+c))+40*(s-4*(a+b+c))
  let raw := weighted-removed
  let cap := 400*(if s ≤ 70000000 then 3000000 else 2500000)
  let extra := 400*(if s ≤ 70000000 then 3000000 else 2000000)
  (min raw cap + min (min (raw-cap) (120*c+160*(d+e))) extra)/400
-- c는 총급여7000만원 이하 문화체육 적격액. 초과하면 결제수단별a/b로 재분류해야 합니다.
def collectibleBalance (determined prepaid : Nat) : Int :=
  let delta := settlementBalance determined prepaid
  if 0 < delta ∧ delta < 1000 then 0 else delta

theorem no_child_no_credit : childCredit 0 = 0 := by decide
theorem two_children_2025 : childCredit 2 = 550000 := by decide
theorem no_rent_above_limit (s r : Nat) (h : 80000000 < s) : rentCredit s r = 0 := by
  simp [rentCredit]; omega
theorem cap_fraction_boundary : earnedCreditCap 33000001 = 739999 := by decide
theorem small_positive_not_collected : collectibleBalance 100000 99001 = 0 := by decide
theorem small_refund_preserved : collectibleBalance 99001 100000 = -999 := by decide
theorem thousand_collected : collectibleBalance 100000 99000 = 1000 := by decide
-- 교육비는 사람별 한도를 적용한 적격금액 합계가 한 개의 세액 칸입니다.
def schoolEligible (payments : List Nat) : Nat := (payments.map (min 3000000)).sum
def universityEligible (payments : List Nat) : Nat := (payments.map (min 9000000)).sum
def educationCredit (self special school university : Nat) : Nat := (self+special+school+university)*15/100
-- 총급여 → 과세표준 → 산출세액 → 근로세액공제 → 결정세액의 합성.
-- deductions는 인적/연금/선택한 특별/그밖의 공제 및 종합한도를 반영한 합계,
-- extraCredits는 별도로 계산·확인한 다른 당해연도 세액공제 합계입니다.
def salaryToDetermined (salary deductions extraCredits : Nat) : Nat :=
  let base := taxableBase salary (earnedDeduction100 salary / 100) deductions
  let assessed := IncomeTax.tax100 base / 100
  determinedTax assessed (earnedCredit salary assessed + extraCredits)
theorem separate_pension_rounding : pensionCredit 50000000 100004 100004 = 30000 := by decide
theorem separate_insurance_rounding : insuranceCredit 100004 100004 = 27000 := by decide
theorem no_salary_no_tax (deductions credits : Nat) : salaryToDetermined 0 deductions credits = 0 := by
  simp [salaryToDetermined, taxableBase, earnedDeduction100, IncomeTax.tax100, determinedTax]
end IncomeTax.Settlement
