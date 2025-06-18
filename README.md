# QDA Final Project of Team 12
## Topic: Circuit Optimization that allows
 Authors: Cheng-Yeh Yang, Kang-Chieh Fan
 Advisor: Prof. Chung-Yang (Ric) Huang
 
## Structure of this Repository

1. **Con1_H_gate.py**  
   Construction 1: 4-control Toffoli gate using two dirty ancilla, decomposed with relative phase (uses Hadamard gates for phase correction).

2. **Con1_k_MCT_H_gate.py**  
   Extends Construction 1 to support arbitrary k-control Toffoli gates, using **k−2 dirty ancilla** and surrounding Hadamard gates to manage relative phase.

3. **Con1_k_MCT_decom.py**  
   Phase-free decomposition of a k-control Toffoli gate into exactly 4(k−2) Toffoli gates, using **k−2 dirty ancilla**. All ancilla qubits are uncomputed to their original states.

4. **Con1_traditional.py**  
   The k=4 special case of `Con1_k_MCT_decom.py`, matches Construction 1 in the referenced paper(Lemma 7.2 from Barenco et al.).

5. **mct_ancilla_norpcorrect.py**  
   Construction 5: Recursive decomposition of Λk(X) using one dirty ancilla (allows relative phase).

6. **mct_ancilla_withrpcorrect.py**  
   Construction 5 with additional relative phase cleanup (not yet complete).

---

## 🧪 Verification Tests

Each construction is verified using the following 3 tests:

1. **Single-basis test (all-1 input)**  
   Confirms that the decomposed circuit behaves identically to the standard MCX gate for one specific input (e.g., `|111...1⟩`).

2. **Full-matrix equivalence test**  
   Verifies functional equivalence on **all 2ⁿ basis states**, comparing the unitary matrices of the decomposed circuit and the built-in MCX gate.

3. **Relative-phase equivalence test**  
   Compares absolute values of matrix entries (ignoring global and relative phases), confirming correctness for **relative-phase constructions**.

---

## 📌 Notes

- All simulations are implemented using **Qiskit**.
- Dirty ancilla circuits may retain phase errors but match computational output.
- Phase-aware diagnostics are included to visualize per-basis phase deviation.
