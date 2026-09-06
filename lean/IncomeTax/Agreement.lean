import IncomeTax.Basic
import IncomeTax.Solar
namespace IncomeTax
-- 첫 구간에서 공동 작성한 두 정의의 결과가 일치합니다.
theorem first_band_agreement (x : Nat) (h : x ≤ 14000000) :
    tax100 x = Solar.firstBandTax100 x := by
  simp [first_band x h, Solar.firstBandTax100]
end IncomeTax
