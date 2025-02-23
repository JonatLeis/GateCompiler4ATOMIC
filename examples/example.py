#!/usr/bin/env python3
"""
Complete Pipeline Example:
1. Define a custom circuit using the provided gate classes.
2. Generate a JSON configuration file (config.json) describing the circuit.
3. Compile the configuration into ATOMIC imply logic and output it to a file.
4. Print which memristors (by index) have to be measured to obtain the result
"""

import os
from gates import NumToBinRegisters, OR_GATE, AND_GATE, NOT_GATE, OUT_GATE, CircuitConfig, Register
from compiler import compile_circuit, getOutputIndices

# ----- Step 1: Define the Custom Circuit -----
# Clear previous state to ensure a clean circuit setup.
Register.reset()

# Create two 1-bit input registers. Input_a represents logical HIGH (1) and input_b represents logical LOW (0).
input_a = NumToBinRegisters(1, wordsize=1, label="IN")[0]
input_b = NumToBinRegisters(0, wordsize=1, label="IN")[0]


# Define circuit in pythonic way (Gates can also be obscured and combined inside of python functions)
or_result = OR_GATE(input_a, input_b).execute()
and_result = AND_GATE(input_a, input_b).execute()
not_result = NOT_GATE(and_result).execute()

# Define the final output of the circuit. OUT gate is not needed, though is useful for debugging purposes
final_output = OUT_GATE(or_result).execute()

# ----- Step 2: Generate the JSON Configuration of circuit -----
# Create a configuration object that captures all the stages and gates.
config = CircuitConfig()
config_json = config.createJSONConfig()

# Write the configuration to a file.
with open("config.json", "w") as config_file:
    config_file.write(config_json)

print("Configuration file 'config.json' has been created.")

# ----- Step 3: Compile the Configuration into ATOMIC Imply Logic -----
# Make sure the output directory exists.
if not os.path.exists("out"):
    os.makedirs("out")

# Run the compiler which converts the JSON config into imply logic.
num_memristors = compile_circuit(configPath="config.json", outfile="out/atomic_config.txt")
print("Compilation complete.")
print(f"Total number of memristors used: {num_memristors}")

# ----- Step 4: Inform the User Which Memristor to Measure -----
# The final output register holds the result.
result_label = final_output.getLabel()

result_memristor = getOutputIndices([result_label])
print(f"To read the circuit's output, measure the memristor corresponding to register '{result_memristor}'.")

