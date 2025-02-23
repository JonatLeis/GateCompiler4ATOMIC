import json
import os

circuit = json.load(open('config.json'))

parallelism = 1 # number of gates that can maximally be executed in parallel

registers_translation = {label:index for index, label in enumerate(circuit["input_registers"])}
reservable_registers = {label:False for label in circuit["input_registers"]} # label of register : is register free to use

num_registers = len(registers_translation)
num_free_registers = 0

imply_logic_strings_parallel = []
AND_count = 0
OR_count = 0
NOT_count = 0
XOR_count = 0

# Helper functions to administer registers

def allocate_registers(num_alloc):
    global num_registers, num_free_registers, reservable_registers
    # allocate new registers if needed
    startRegisterLabel = len(registers_translation)-len(circuit["input_registers"])
    for i in range(num_alloc):
        new_register_label = f"w{startRegisterLabel+i}"
        new_register_idx = num_registers

        registers_translation.update({new_register_label:new_register_idx})
        reservable_registers.update({new_register_label:True})

        num_registers = num_registers + 1
        num_free_registers = num_free_registers + 1

def reserve_registers(num_req_registers):
    global num_registers, num_free_registers, reservable_registers
    # check if enough free registers are available
    if num_req_registers > num_free_registers:
        allocate_registers(num_req_registers - num_free_registers)

    reserved_registers = []
    for _ in range(num_req_registers):
        # look for a free register
        for register, status in reservable_registers.items():
            if status == False:
                continue
            
            reserved_registers.append(register)
            reservable_registers[register] = False
            num_free_registers = num_free_registers - 1
            break

    return reserved_registers

def free_registers(registers):
    global reservable_registers, num_free_registers
    for register in registers:
        reservable_registers[register] = True
        num_free_registers = num_free_registers + 1

def rename_register(old, new):
    global registers_translation, reservable_registers

    tmp = registers_translation[old]
    del registers_translation[old]
    registers_translation.update({new:tmp})

    tmp = reservable_registers[old]
    del reservable_registers[old]
    reservable_registers.update({new:tmp})



# Defining Imply logic for Gates

def OR(inputs):
    '''
        creates imply logic for implementing a OR gate

        expects:
            inputs: labels of both input registers

        returns:
            result: label of register in which result is saved
            imply_logic_strings: resulting imply logic in format usable by the ATOMIC tool
    '''
    global OR_count
    OR_count = OR_count + 1
    inp1, inp2 = inputs
    imply_logic_strings = []
    work1, work2 = reserve_registers(2)
    imply_logic_strings.append(f"F{registers_translation[work1]},{registers_translation[work2]}    # OR{OR_count}")
    imply_logic_strings.append(f"I{registers_translation[inp1]},{registers_translation[work1]}")
    imply_logic_strings.append(f"I{registers_translation[work1]},{registers_translation[work2]}")
    imply_logic_strings.append(f"F{registers_translation[work1]}")
    imply_logic_strings.append(f"I{registers_translation[inp2]},{registers_translation[work1]}")
    imply_logic_strings.append(f"I{registers_translation[work1]},{registers_translation[work2]}    # ENDE OR{OR_count}")
    result = work2
    to_be_freed = [work1]

    return result, imply_logic_strings, to_be_freed


def AND(inputs):
    '''
        creates imply logic for implementing a AND gate

        expects:
            inputs: labels of both input registers

        returns:
            result: label of register in which result is saved
            imply_logic_strings: resulting imply logic in format usable by the ATOMIC tool
    '''
    global AND_count
    AND_count = AND_count + 1
    inp1, inp2 = inputs
    imply_logic_strings = []
    work1, work2 = reserve_registers(2)
    imply_logic_strings.append(f"F{registers_translation[work1]},{registers_translation[work2]}    # AND{AND_count}")
    imply_logic_strings.append(f"I{registers_translation[inp1]},{registers_translation[work1]}")
    imply_logic_strings.append(f"I{registers_translation[inp2]},{registers_translation[work1]}")
    imply_logic_strings.append(f"I{registers_translation[work1]},{registers_translation[work2]}    # ENDE AND{AND_count}")
    result = work2
    to_be_freed = [work1]

    return result, imply_logic_strings, to_be_freed

def XOR(inputs):
    global XOR_count
    XOR_count = XOR_count + 1
    inp1, inp2 = inputs
    imply_logic_strings = []
    work1, work2, work3 = reserve_registers(3)

    imply_logic_strings.append(f"F{registers_translation[work1]},{registers_translation[work2]}    # XOR{XOR_count}")
    imply_logic_strings.append(f"F{registers_translation[work1]},{registers_translation[work2]}")
    imply_logic_strings.append(f"I{registers_translation[inp1]},{registers_translation[work1]}")
    imply_logic_strings.append(f"I{registers_translation[inp2]},{registers_translation[work1]}")
    imply_logic_strings.append(f"I{registers_translation[work1]},{registers_translation[work2]}")
    imply_logic_strings.append(f"F{registers_translation[work1]},{registers_translation[work3]}")
    imply_logic_strings.append(f"I{registers_translation[inp1]},{registers_translation[work1]}")
    imply_logic_strings.append(f"I{registers_translation[work1]},{registers_translation[work3]}")
    imply_logic_strings.append(f"F{registers_translation[work1]}")
    imply_logic_strings.append(f"I{registers_translation[inp2]},{registers_translation[work1]}")
    imply_logic_strings.append(f"I{registers_translation[work1]},{registers_translation[work3]}")
    imply_logic_strings.append(f"I{registers_translation[work3]},{registers_translation[work2]}")
    imply_logic_strings.append(f"F{registers_translation[work1]}")
    imply_logic_strings.append(f"I{registers_translation[work2]},{registers_translation[work1]}     # ENDE XOR{XOR_count}")

    result = work1
    to_be_freed = [work2, work3]
    return result, imply_logic_strings, to_be_freed

def NOT(input):
    '''
        creates imply logic for implementing a NOT gate

        expects:
            inputs: label of input register

        returns:
            result: label of register in which result is saved
            imply_logic_strings: resulting imply logic in format usable by the ATOMIC tool
    '''
    global NOT_count
    NOT_count = NOT_count + 1
    inp = input[0]
    imply_logic_strings = []
    work = reserve_registers(1)[0]
    # print(f"work: {work}")
    imply_logic_strings.append(f"F{registers_translation[work]}    # NOT{NOT_count}")
    imply_logic_strings.append(f"I{registers_translation[inp]},{registers_translation[work]}    # ENDE NOT{NOT_count}")
    result = work
    to_be_freed = []
    return result, imply_logic_strings, to_be_freed

def OUT(input):
    return input[0], [], []
    
# Maps gate labels to Gate functions
gate_mapping = {"OR": OR, "AND": AND, "NOT": NOT, "XOR": XOR, "OUT": OUT}


# Functions important for circuit flow

def pad_list(lst, length):
    while len(lst) < length:
        lst.append("nop")
    return lst

def combine_logic_chunks(chunk):
    '''
        combines operations that can be run in parallel
    '''

    while len(chunk) < parallelism:
        chunk.append([])

    # if only one gate is present - only unpack and return
    if len(chunk) == 1:
        # print("only one gate present")
        return chunk[0]

    output = []

    # pad gatelogics to length of largest (first) gate
    length = len(chunk[0])
    for i in range(len(chunk[1:])):
        chunk[i+1] = pad_list(chunk[i+1], length)

    for parallel_logics in zip(*chunk):
        output.append(" | ".join(parallel_logics))

    return output



def process_stage(stage):
    current_stage = circuit["stages"][stage]
    generated_imply_logics = []
    maxSteps = 0

    to_be_freed = []

    # process gates in current stage
    for gate in current_stage["gates"]:
        func = gate_mapping[gate["type"]]
        outputName = gate['name']
        inputs = gate["inputs"]

        out, imply_logic, free_regs = func(inputs)
        generated_imply_logics.append(imply_logic)
        to_be_freed.extend(free_regs)
        if len(imply_logic) > maxSteps:
            maxSteps = len(imply_logic)

        rename_register(out, outputName)
    
    free_registers(to_be_freed)

    generated_imply_logics = sorted(generated_imply_logics, key=lambda x: len(x), reverse=True)
    

    # combine into chunks that will be processed in parallel
    generated_imply_logics = [generated_imply_logics[i: i+parallelism] for i in range(0, len(generated_imply_logics), parallelism)]
    # combine chunks into parallelized imply logic statements
    imply_logic = []
    for chunk in generated_imply_logics:
        imply_logic.extend(combine_logic_chunks(chunk))

    free_registers(current_stage['free_registers_after_stage'])
    
    return imply_logic


# function to compile the circuit defined in configPath, outputs imply logic into outfile
# returns amount of memristors used for this circuit
def compile_circuit(configPath:str="config.json", outfile:str="out/atomic_config.txt"):
    global registers_translation, reservable_registers, num_registers, num_free_registers, imply_logic_strings_parallel, logic_result
    global AND_count, OR_count, NOT_count, XOR_count
    circuit = json.load(open(configPath))
    parallelism = 1 # number of gates that can maximally be executed in parallel (compiler support works iff config.json is correctly parallelized!)

    registers_translation = {label:index for index, label in enumerate(circuit["input_registers"])}
    reservable_registers = {label:False for label in circuit["input_registers"]} # label of register : is register free to use

    num_registers = len(registers_translation)
    num_free_registers = 0

    imply_logic_strings_parallel = []

    logic_result = []
    AND_count = -1
    OR_count = -1
    NOT_count = -1
    XOR_count = -1


    for stage in range(len(circuit["stages"])):
        logic_result.extend(process_stage(stage))


    try:
        with open(outfile, 'x') as f:
            f.write('\n'.join(logic_result))
    except Exception:
        with open(outfile, "w") as f:
            f.write('\n'.join(logic_result))

    print(f"Number of Memristors: {len(reservable_registers)}")
    return len(reservable_registers)
    
def getOutputIndices(output_labels:list[str]):
    # outputs ids 
    output_ids = {f"OUT {index}" : registers_translation[label] for index, label in enumerate(output_labels)}
    return output_ids