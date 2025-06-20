from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library.standard_gates import XGate, CXGate
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Operator, state_fidelity
from qiskit.circuit.library import MCXGate
from qiskit_aer import Aer
import numpy as np

def apply_mct_with_dirty_ancilla(circuit, controls, target, dirty_ancilla):
    """
    實作 Construction 5: Implements Λ_k(X) using a single dirty ancilla.
    Args:
        circuit: QuantumCircuit to which the gates are added.
        controls: List of control qubits (k ≥ 2).
        target: Target qubit.
        dirty_ancilla: A single dirty ancilla qubit.
    """
    k = len(controls)
    assert k >= 2, "Need at least 2 control qubits"
    c = controls
    a = dirty_ancilla
    t = target

    # Step 1: Apply Hadamard to dirty ancilla
    circuit.h(a)
    # Step 2: Toffoli with controls a and c[k-1], target t
    circuit.ccx(a, c[-1], t)
    # Step 3: Apply Λ_{k-1}(X) with controls c[0:k-1] ,new target and dirty ancilla
    apply_recursive_mct_with_dirty(circuit, c[:-1], t-1, a-1)
    # Step 4: Toffoli with controls a and c[k-1], target t
    circuit.ccx(a, c[-1], t)
    # Step 5: Apply Hadamard to dirty ancilla
    circuit.h(a)

def apply_recursive_mct_with_dirty(circuit, controls, target, dirty_ancilla):
    """
    Recursively builds Λ_{k}(X) with a single dirty ancilla.
    For k=2, uses CCX directly.
    For k=3, use recursive construction.
    """
    k = len(controls)
    if k == 1:
        circuit.cx(controls[0], target)
    elif k == 2:
        circuit.ccx(controls[0], controls[1], target)
    else:
        # recurse: treat target as dirty ancilla, use dirty_ancilla to compute intermediate
        apply_mct_with_dirty_ancilla(circuit, controls, target, dirty_ancilla)

def generate_phase_table(custom_unitary, reference_unitary, num_controls, tol=1e-8):
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
    # Configuration
    num_controls = 4
    total_qubits = num_controls + 2  # target + dirty ancilla
    controls = list(range(num_controls))
    target = num_controls + 1
    dirty_ancilla = num_controls 

    # Initialize circuit with test input (set all controls to |1⟩)
    qc_test = QuantumCircuit(total_qubits)
    for i in controls:
        qc_test.x(i)  # Set controls to |1⟩
    qc_test.x(dirty_ancilla)  # Set dirty ancilla to |1⟩ (arbitrary non-|0⟩ state)
    input_state = Statevector.from_instruction(qc_test)     # Save original state
    apply_mct_with_dirty_ancilla(qc_test, controls, target, dirty_ancilla)     # Apply custom MCT (Λₖ(X)) using your decomposition
    output_state = Statevector.from_instruction(qc_test)     # Simulate final state
    custom_unitary = Operator(qc_test).data # Get the unitary matrix for the custom MCT circuit

    # Compare against built-in MCT for verification
    qc_reference = QuantumCircuit(total_qubits)
    for i in controls:
        qc_reference.x(i)
    qc_reference.x(dirty_ancilla)
    qc_reference.append(MCXGate(num_controls), controls + [target])
    ref_state = Statevector.from_instruction(qc_reference)
    reference_unitary = Operator(qc_reference).data # Get the unitary matrix for the reference MCT circuit
    
    ### TEST ONLY ###
    # Print state results
    # print("Input state:")
    # print(input_state)
    # print("\nOutput state after custom MCT:")
    # print(output_state)
    # print("\nBuilt-in MCT reference output:")
    # print(ref_state)
    ### END ###

    # Print circuits
    print("Reference Circuit:")
    print(qc_reference)
    print("Output Circuit:")
    print(qc_test)
    
    # Set NumPy to print the full array
    np.set_printoptions(threshold=np.inf)
    # Print unitaries
    # print("Custom MCT Unitary:")
    # print(custom_unitary)
    # print("Reference MCT Unitary:")
    # print(reference_unitary)

    ### Phase free (test only) ###
    # Compute global relative phase between the two unitaries
    relative_phase = np.angle(np.vdot(custom_unitary.flatten(), reference_unitary.flatten()))
    print(f"\nGlobal relative phase: {relative_phase:.4f} rad")
    # Apply global phase (if desired)
    qc_test.global_phase += relative_phase
    custom_unitary = Operator(qc_test).data
    ### test end ###

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
    	phase_table = generate_phase_table(custom_unitary, reference_unitary, num_controls)
    	for bits, phase in phase_table.items():
    		print(f"{bits}: phase = {phase:.4f} rad")
    else:
    	print("\n❌ Entries differ in magnitude:")
    	mismatch_indices = np.argwhere(abs_diff >= tolerance)
    	for i, j in mismatch_indices:
        	print(f"Mismatch at ({i},{j}): |custom|={abs_custom[i,j]:.4g}, |reference|={abs_reference[i,j]:.4g}")



if __name__ == "__main__":
    main()
