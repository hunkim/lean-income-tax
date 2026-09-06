import Std

namespace IncomeTax.SettlementSolar

-- 이 정의는 자연수 입력의 산술 관계만 다룹니다. assessed/credits/determined/prepaid의
-- 법적 적격성, 실제 세액공제 적용 순서, 이월·환급가능공제, 귀속연도별 원단위 처리 등은
-- 전혀 검증하지 않습니다. 전제값은 외부 규정·사실관계에 따라 확정되어야 하며, finalTax는
-- 모든 세제에 적용되는 법적 결정세액 정의가 아니라 제한된 비환급성 공제 산술 모델입니다.
def finalTax (assessed credits : Nat) : Nat := assessed - credits
def refund (determined prepaid : Nat) : Nat := prepaid - determined
def additional (determined prepaid : Nat) : Nat := determined - prepaid

theorem finalTax_le_assessed (assessed credits : Nat) : finalTax assessed credits ≤ assessed := by
  simp [finalTax]
  exact Nat.sub_le _ _

theorem finalTax_zero_of_le_credits (assessed credits : Nat) (h : assessed ≤ credits) : finalTax assessed credits = 0 := by
  simp [finalTax]
  exact Nat.sub_eq_of_le h

theorem not_both_refund_and_additional_positive (determined prepaid : Nat) : ¬ (0 < refund determined prepaid ∧ 0 < additional determined prepaid) := by
  intro h
  have h₁ : 0 < prepaid - determined := by
    simpa [refund] using h.1
  have h₂ : 0 < determined - prepaid := by
    simpa [additional] using h.2
  have : (prepaid : Int) > (determined : Int) := by
    apply Int.ofNat_lt_ofNat_of_lt
    exact Nat.sub_pos_of_lt h₁
  have : (determined : Int) > (prepaid : Int) := by
    apply Int.ofNat_lt_ofNat_of_lt
    exact Nat.sub_pos_of_lt h₂
  omega

theorem int_diff_additional_refund (determined prepaid : Nat) :
    (additional determined prepaid : Int) - (refund determined prepaid : Int) =
    (determined : Int) - (prepaid : Int) := by
  cases Nat.le_total determined prepaid with
  | inl h =>
    have h₁ : additional determined prepaid = determined - prepaid := by
      simp [additional, h]
      omega
    have h₂ : refund determined prepaid = 0 := by
      simp [refund, h]
      omega
    simp [h₁, h₂]
    omega
  | inr h =>
    have h₁ : additional determined prepaid = 0 := by
      simp [additional, h]
      omega
    have h₂ : refund determined prepaid = prepaid - determined := by
      simp [refund, h]
      omega
    simp [h₁, h₂]
    omega

end IncomeTax.SettlementSolar
