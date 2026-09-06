import Std

namespace IncomeTax.Solar

/-- 
외부 전제: 확정된 과세표준이 14000000원 이하일 때만 첫 구간에 적용한다.
과세표준 확정은 외부에서 주어지며, 출력은 산출세액의 100배이다.
함수는 모든 자연수에 정의되지만 상한 초과 입력은 다른 구간 세금이 아니다.
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
