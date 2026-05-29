import Mathlib.Order.Basic

/-!
A minimal public-facing Lean artifact corresponding to the no-progress 3-cycle
obstruction described in the manuscript.

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
