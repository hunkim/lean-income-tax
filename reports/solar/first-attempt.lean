import Std

namespace IncomeTax.Solar

/-
법문: 소득세법 제55조 제1항 첫 구간(과세표준 1,400만원 이하)에 대한 세율은
"과세표준의 6%"이다. 이 정의는 해당 세율 구간을 수학적으로 단순화한 함수로,
원 단위 과세표준 `base`에 대해 세액을 100배한 정수 값을 반환한다.
반올림은 수행하지 않으며, 그 값은 다른 구간의 세액이 아니다.
이 함수는 공제 자격, 결정세액, 지방소득세, 원단위 처리, 기납부세액,
연말정산 환급액을 정의하지 않는다.
-/
def firstBandTax100 (base : Nat) : Nat := 6 * base

/-
`base = 0`일 때 세액은 0이다.
-/
theorem first_band_tax_at_zero : firstBandTax100 0 = 0 := by
  rw [firstBandTax100]
  simp

/-
`base = 14000000`일 때 세액은 84000000이다.
(1,400만원 × 6% × 100 = 84,000,000)
이 값은 첫 구간 상한에 해당하며, 실제 과세표준 확정 및 상한 적합 여부는
법적 적용의 외부 전제이다.
-/
theorem first_band_tax_at_upper_limit : firstBandTax100 14000000 = 84000000 := by
  rw [firstBandTax100]
  norm_num

/-
첫 구간 세율 함수는 자연수의 순서와 보존된다: x ≤ y이면
firstBandTax100 x ≤ firstBandTax100 y. 즉, 과세표준이 클수록 (이 구간 내)
세액도 커진다.
-/
theorem firstBandTax100_monotone (x y : Nat) (h : x ≤ y) :
  firstBandTax100 x ≤ firstBandTax100 y := by
  rw [firstBandTax100, firstBandTax100]
  exact Nat.mul_le_mul_left 6 h

/-
x ≤ y일 때, 두 과세표준에 대한 세액 차이(100배 단위)는
100 × (y - x)를 넘지 않는다. 이는 (6% 세율이 적용된) 증가분이
100배 단위로 원 차이보다 크지 않음을 나타낸다.
-/
theorem firstBandTax100_diff_bound (x y : Nat) (h : x ≤ y) :
  firstBandTax100 y - firstBandTax100 x ≤ 100 * (y - x) := by
  rw [firstBandTax100, firstBandTax100]
  have h₁ : 6 * y - 6 * x = 6 * (y - x) := by
    apply Nat.mul_sub_left
    exact h
  rw [h₁]
  have h₂ : 6 ≤ 100 := by norm_num
  exact Nat.mul_le_mul_left h₂ (by linarith)

end IncomeTax.Solar
