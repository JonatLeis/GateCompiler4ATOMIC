# Imply Logic Compiler for LTspice/ATOMIC

This project provides a pythonic way to define digital circuits using imply logic. It is designed to be compatible with the ATOMIC tool—and ultimately LTspice—and leverages Python’s variable dependencies to automatically track data flow through your circuit. In addition, it optimizes the number of memristors used, calculates the memristors consumed (both per output and in total), and manages the allocation of memristors required for the defined operations.

## Overview

- **Pythonic Circuit Definition:** Define circuits in Python by simply expressing the desired logic, while internal dependencies automatically determine the data flow.
- **Automatic Memristor Optimization:** Automatically calculates, optimizes, and outputs the memristor count used by your circuit.
- **JSON Configuration Export:** Exports a JSON configuration file (`config.json`) that details your circuit. This configuration is then used by the compiler.
- **Imply Logic Generation:** The compiler (in `compiler.py`) reads the JSON configuration and translates it into imply logic strings that are saved (by default in `out/atomic_config.txt`).
- **Extensibility:** Easily extend the system with new gates or higher-level subcircuits (e.g., full adders or multipliers).
- **Truth Comparison:** Includes a convenient, pythonic way of comparing circuit outputs to a definable truth value.

## Project Structure

- **gates.py:**  
  Contains definitions for basic logic gates (OR, AND, XOR, NOT, OUT) as well as more complex blocks such as half adders, full adders, compressors, and multipliers. Custom data structures are implemented here to trace dependencies and manage circuit stages.

- **compiler.py:**  
  Reads the JSON configuration file generated by `gates.py` and converts the circuit into imply logic strings, managing memristor allocation along the way. The output is written to a file (default: `out/atomic_config.txt`), and the total memristor count is printed.

- **./dev_src:**  
  Contains no additional logic! Contains jupyter notebooks with the same logic as `gates,py` and `compiler.py` that are useful for further development or debugging

- **./about:**  
  Contains no additional logic! Contains documentation of the imply logic used to implement the most important logic gates.

- **./examples:**  
  Contains example scripts for usage of this framework and test of constructed circuits.

- **./examples/example.py:**  
  Example on how to define custom circuits with this framework and compile them into ATOMIC interpretable imply logic

## Setup & Installation

### Prerequisites

- Python 3.6 or higher
- [NumPy](https://numpy.org/) (Install via `pip install numpy`)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/JonatLeis/GateCompiler4ATOMIC
   cd GateCompiler4ATOMIC

# Extensibility & Parallelization

- **Adding New Gates/Subcircuits:**
    The system is designed to be modular. You can easily add new logic gate classes by extending the Gate class in gates.py or implement higher-level subcircuits such as full adders and multipliers for reuse in larger designs.

- **Parallelized Circuit Development:**
    The compiler supports the idea of executing multiple gates in parallel within a stage. Future extensions can focus on further enhancing parallelization support, making it even easier to design and optimize circuits for concurrent processing.

# License & Contact
This project is provided for use in our group project for EMCA during WS24/25 at University Heidelberg only. If you wish to use it for commercial purposes or outside the scope of this project, please contact me directly.

For any questions, suggestions, or licensing inquiries, please open an Issue or email the developer of this framework at jonathan.leis@outlook.de