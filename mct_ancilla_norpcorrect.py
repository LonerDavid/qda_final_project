from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library.standard_gates import XGate, CXGate
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Operator, state_fidelity
from qiskit.circuit.library import MCXGate
from qiskit_aer import Aer
import numpy as np

def apply_mct_with_dirty_ancilla(circuit, controls, target, dirty_ancilla):
    """
    Implements Λ_k(X) using a single dirty ancilla.
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


def main():
    # Configuration
    num_controls = 5
    total_qubits = num_controls + 2  # target + dirty ancilla
    controls = list(range(num_controls))
    target = num_controls + 1
    dirty_ancilla = num_controls 



    # Initialize circuit with test input (set all controls to |1⟩)
    qc_test = QuantumCircuit(total_qubits)
    for i in controls:
        qc_test.x(i)  # Set controls to |1⟩
    qc_test.x(dirty_ancilla)  # Set dirty ancilla to |1⟩ (arbitrary non-|0⟩ state)
    # Save original state
    input_state = Statevector.from_instruction(qc_test)
    # Apply custom MCT (Λₖ(X)) using your decomposition
    apply_mct_with_dirty_ancilla(qc_test, controls, target, dirty_ancilla)
    # Simulate final state
    output_state = Statevector.from_instruction(qc_test)
    # Get the unitary matrix for the custom MCT circuit
    custom_unitary = Operator(qc_test).data


    # Compare against built-in MCT for verification
    qc_reference = QuantumCircuit(total_qubits)
    for i in controls:
        qc_reference.x(i)
    qc_reference.x(dirty_ancilla)
    qc_reference.append(MCXGate(num_controls), controls + [target])
    ref_state = Statevector.from_instruction(qc_reference)
    # Get the unitary matrix for the reference MCT circuit
    reference_unitary = Operator(qc_reference).data

    
    # Print state results
    # print("Input state:")
    # print(input_state)
    # print("\nOutput state after custom MCT:")
    # print(output_state)
    # print("\nBuilt-in MCT reference output:")
    # print(ref_state)

    # Print circuits
    print("Input Circuit:")
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

if __name__ == "__main__":
    main()
