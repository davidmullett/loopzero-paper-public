import Mathlib.Order.Basic

universe u

/-!
A minimal public-facing Lean artifact corresponding to the no-progress cycle
obstructions described in the manuscript.

This file is intended as a scientific reference artifact only.
-/

section

variable {α : Type*} [Preorder α]

theorem no_progress_cycle_public {x y z : α}
    (hxy : x < y) (hyz : y ≤ z) (hzx : z ≤ x) : False := by
  have hxz : x < z := lt_of_lt_of_le hxy hyz
  have hxx : x < x := lt_of_lt_of_le hxz hzx
  exact lt_irrefl x hxx

end

/-- Generalized no-progress cycle with the monotone path folded into one `≤` proof. -/
theorem no_progress_kcycle_public {α : Type u} [Preorder α]
    {x y z : α} (hxy : x < y) (hpath : y ≤ z) (hzx : z ≤ x) : False :=
  no_progress_cycle_public hxy hpath hzx

/--
Measurement bridge: if a measurement map sends three states to a strict/weak/weak
cycle in an ordered codomain, the no-progress obstruction applies.
-/
theorem collapse_via_progresscycle_public
    {α : Type u} {β : Type u} [Preorder β]
    (μ : α → β) {x y z : α}
    (hxy : μ x < μ y)
    (hyz : μ y ≤ μ z)
    (hzx : μ z ≤ μ x) : False :=
  no_progress_kcycle_public hxy hyz hzx

#print axioms no_progress_cycle_public
#print axioms no_progress_kcycle_public
#print axioms collapse_via_progresscycle_public
