from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library.standard_gates import XGate, CXGate
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Operator, state_fidelity
from qiskit.circuit.library import MCXGate
from qiskit_aer import Aer
import numpy as np
 
def construction_1_mct(circuit, controls, target, ancilla_a, ancilla_b):
    """
    實作 Construction 1：4-control Toffoli gate 使用 2 個 dirty ancilla。
    controls: x1, x2, x3, x4
    ancilla_a: a
    ancilla_b: b
    target: y
    """
    x1, x2, x3, x4 = controls
 
    # a ^= x1 & x2
    circuit.h(ancilla_a)
    circuit.h(ancilla_b)
    
    circuit.ccx(x4, ancilla_b, target)
    
    circuit.ccx(x3, ancilla_a, ancilla_b)
    
    circuit.ccx(x1, x2, ancilla_a)

    circuit.ccx(x3, ancilla_a, ancilla_b)
    
    circuit.ccx(x4, ancilla_b, target)
    
    circuit.h(ancilla_a)
    circuit.h(ancilla_b)
 
    # y ^= x1 & x2 & x3 & x4

def generate_phase_table(custom_unitary, reference_unitary, num_controls=4, tol=1e-8):
    phase_table = {}
    num_qubits = int(np.log2(custom_unitary.shape[0]))
    
    
    for i in range(custom_unitary.shape[0]):
        for j in range(custom_unitary.shape[1]):
            u_elem = custom_unitary[i, j]
            r_elem = reference_unitary[i, j]
 
            # 如果兩個都近似 0，就忽略
            if np.abs(u_elem) < tol and np.abs(r_elem) < tol:
                continue
            # 如果 reference 為 0，但 custom 不為 0，就跳過（無法計 phase 差）
            if np.abs(r_elem) < tol:
                continue
 
            phase = np.angle(u_elem / r_elem)
            key = (format(i, f'0{num_qubits}b'), format(j, f'0{num_qubits}b'))
            phase_table[key] = phase
 
    return phase_table
 
def main():
    # x1, x2, x3, x4, a, b, y
    qc = QuantumCircuit(7)
    controls = [0, 1, 2, 3]
    ancilla_a = 4
    ancilla_b = 5
    target = 6
 
    # 初始化 |x⟩ = |1111⟩, a = |1⟩, b = |1⟩, y = |1⟩
    for i in controls + [ancilla_a, ancilla_b]:
        qc.x(i)
 
    construction_1_mct(qc, controls, target, ancilla_a, ancilla_b)
    output_state = Statevector.from_instruction(qc)
    # Get the unitary matrix for the custom MCT circuit
    custom_unitary = Operator(qc).data


    
    # Print circuits

    print("Output Circuit:")
    print(qc)
    
    qc_reference = QuantumCircuit(7)
    for i in controls:
        qc_reference.x(i)
    qc_reference.x(4)
    qc_reference.x(5)
    qc_reference.append(MCXGate(4), controls + [target])
    ref_state = Statevector.from_instruction(qc_reference)
    # Get the unitary matrix for the reference MCT circuit
    reference_unitary = Operator(qc_reference).data
    print("Reference Circuit:")
    print(qc_reference)
    
    ref_state = Statevector.from_instruction(qc_reference)
    # Get the unitary matrix for the reference MCT circuit
    reference_unitary = Operator(qc_reference).data
    
    
    
    # Check if the unitaries are equivalent (up to a global phase)
    # Normalize the unitaries to remove global phase differences
    custom_unitary_normalized = custom_unitary / np.linalg.norm(custom_unitary)
    reference_unitary_normalized = reference_unitary / np.linalg.norm(reference_unitary)



    # Compare the normalized unitaries
    unitary_fidelity = np.abs(np.trace(custom_unitary_normalized.conj().T @ reference_unitary_normalized)) / custom_unitary.shape[0]
    
    print("\n✅ States match?" , output_state.equiv(ref_state))
    print("\n✅ Unitaries match?" , abs(unitary_fidelity - 1.0) < 1e-10)
    
    print("\n✅ Unitaries match?(Allow relative phase)" )
    abs_custom = np.abs(custom_unitary)
    abs_reference = np.abs(reference_unitary)
    abs_diff = np.abs(abs_custom - abs_reference)
    tolerance = 1e-10
    if np.all(abs_diff < tolerance):
    	print("True")
    else:
    	print("\n❌ Entries differ in magnitude:")
    	mismatch_indices = np.argwhere(abs_diff >= tolerance)
    	for i, j in mismatch_indices:
        	print(f"Mismatch at ({i},{j}): |custom|={abs_custom[i,j]:.4g}, |reference|={abs_reference[i,j]:.4g}")
    phase_table = generate_phase_table(custom_unitary, reference_unitary, num_controls=4)
    for bits, phase in phase_table.items():
    	print(f"{bits}: phase = {phase:.4f} rad")

 
if __name__ == "__main__":
    main()
