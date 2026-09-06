import Std

namespace IncomeTax.Solar

/-- 
외부 전제일: 과세표준이 14000000 이하임을 확정한다.
과세표준 확정은 외부에서 주어지며, 출력은 과세표준의 100배 산출세액이다.
환급액 및 끝수처리는 본 코드에서 구현되지 않는다.
-/
def firstBandTax100 (base : Nat) : Nat := 6 * base

theorem firstBandTax100_zero : firstBandTax100 0 = 0 := by decide

theorem firstBandTax100_14M : firstBandTax100 14000000 = 84000000 := by decide

theorem firstBandTax100_monotone {x y : Nat} (h : x ≤ y) : firstBandTax100 x ≤ firstBandTax100 y :=
  by unfold firstBandTax100; omega

theorem firstBandTax100_diff_bound {x y : Nat} (h : x ≤ y) :
    firstBandTax100 y - firstBandTax100 x ≤ 100 * (y - x) :=
  by unfold firstBandTax100; omega

end IncomeTax.Solar
