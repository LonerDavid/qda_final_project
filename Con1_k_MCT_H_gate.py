from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library.standard_gates import XGate, CXGate
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Operator, state_fidelity
from qiskit.circuit.library import MCXGate
from qiskit_aer import Aer
import numpy as np
from qiskit.quantum_info import Operator 
    
    
def k_MCT_with_H_gate(k: int)-> QuantumCircuit:
    """
    Implements a C^kX (multi-control Toffoli) gate using Barenco's Lemma 7.2.
    Requires (k-2) clean ancilla. Decomposes into 4(k-2) Toffoli gates.
 
    Args:
        k (int): Number of control qubits (k >= 3)
 
    Returns:
        QuantumCircuit: circuit with controls [0:k-1], ancilla [k:k+(k-2)], target at -1
    """
    assert k >= 3, "Lemma 7.2 requires at least 3 control qubits"
    
    n_ancilla = k - 2
    n_qubits = k + n_ancilla + 1  # controls + ancilla + target
    qc = QuantumCircuit(n_qubits)
 
    controls = list(range(k))
    ancilla = list(range(k, k + n_ancilla))
    target = n_qubits - 1
    
    
    qc.h(ancilla)
    # Step 1: forward encoding
    qc.ccx(controls[k-1], ancilla[n_ancilla-1], target)
    for i in range(2, k-1):
        qc.ccx(controls[k - i], ancilla[n_ancilla - i],n_qubits-i)
 
    # Step 2: target operation
    qc.ccx(controls[0], controls[1], ancilla[0])
 
    # Step 3: backward decoding (inverse of Step 1)
    
    for i in reversed(range(2, k-1)):
        qc.ccx(controls[k - i], ancilla[n_ancilla - i], n_qubits-i)
            
    qc.ccx(controls[k-1], ancilla[n_ancilla-1], target)
    
    for i in ancilla:
    	qc.h(i)
 
    return qc

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
    num_controls = 5
    k = num_controls;
    total_qubits = num_controls * 2 - 1  # target + dirty ancilla
    controls = list(range(num_controls))
    target = num_controls * 2 - 2;
    dirty_ancilla = num_controls - 2;
    

    #qc = QuantumCircuit(total_qubits)


    
    
    qc=k_MCT_with_H_gate(k);
 
    output_state = Statevector.from_instruction(qc)
    # Get the unitary matrix for the custom MCT circuit
    custom_unitary = Operator(qc).data


    
    # Print circuits

    print("Output Circuit:")
    print(qc)
    
    qc_reference = QuantumCircuit(total_qubits)
    
    qc_reference.append(MCXGate(k), controls + [target])
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
    
    mat_diff = custom_unitary - reference_unitary
    tolerance = 1e-10    





    print("\n✅ States match?" , output_state.equiv(ref_state))
    if Operator(custom_unitary).equiv(Operator(reference_unitary)):
    	print("✅ Unitaries are equivalent up to global phase")
    else:
    	print("❌ Unitaries are not equivalent (even with global phase)")

    
    print("\n✅ Unitaries match?(Allow relative phase)" )
    abs_custom = np.abs(custom_unitary)
    abs_reference = np.abs(reference_unitary)
    abs_diff = np.abs(abs_custom - abs_reference)
    tolerance = 1e-10
    if np.all(abs_diff < tolerance):
    	print("True")
    	phase_table = generate_phase_table(custom_unitary, reference_unitary, num_controls=4)
    	for bits, phase in phase_table.items():
    		print(f"{bits}: phase = {phase:.4f} rad")
    else:
    	print("\n❌ Entries differ in magnitude:")
    	mismatch_indices = np.argwhere(abs_diff >= tolerance)
    	for i, j in mismatch_indices:
        	print(f"Mismatch at ({i},{j}): |custom|={abs_custom[i,j]:.4g}, |reference|={abs_reference[i,j]:.4g}")


 
if __name__ == "__main__":
    main()
