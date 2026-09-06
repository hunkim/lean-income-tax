import Std
namespace IncomeTax
/- 소득세법 제55조 제1항, 시행 2026-07-01 고정본.
과세표준은 원 단위 자연수, 출력은 정확한 세액의 100배입니다.
[주석 T1] 과세표준·거주자 해당성은 외부 확정. 총급여를 넣지 않습니다.
[주석 T2] 공제·감면·기납부세액·지방소득세 및 끝수처리 미구현.
이는 연말정산 환급액이 아닌 기본 세율표의 부분 모델입니다. -/
def tax100 (x : Nat) : Nat :=
  if x ≤ 14000000 then 6*x
  else if x ≤ 50000000 then 84000000 + 15*(x-14000000)
  else if x ≤ 88000000 then 624000000 + 24*(x-50000000)
  else if x ≤ 150000000 then 1536000000 + 35*(x-88000000)
  else if x ≤ 300000000 then 3706000000 + 38*(x-150000000)
  else if x ≤ 500000000 then 9406000000 + 40*(x-300000000)
  else if x ≤ 1000000000 then 17406000000 + 42*(x-500000000)
  else 38406000000 + 45*(x-1000000000)

theorem zero_tax : tax100 0 = 0 := by decide

theorem first_band (x : Nat) (h : x ≤ 14000000) : tax100 x = 6*x := by
  simp [tax100,h]

theorem tax_monotone (x y : Nat) (h : x ≤ y) : tax100 x ≤ tax100 y := by
  unfold tax100
  repeat' split
  all_goals omega

/- [주석 T3] 공제·지원금 등을 포함한 실수령액 전체에 대한 정리가 아닙니다. -/
theorem increase_bounded (x y : Nat) (h : x ≤ y) :
    tax100 y - tax100 x ≤ 45*(y-x) := by
  unfold tax100
  repeat' split
  all_goals omega

theorem first_boundary : tax100 14000000 = 84000000 := by decide
theorem above_first_boundary : tax100 14000001 = 84000015 := by decide
theorem example_20m : tax100 20000000 = 174000000 := by decide
theorem top_boundary : tax100 1000000000 = 38406000000 := by decide
end IncomeTax
