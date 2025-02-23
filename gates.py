import numpy as np
from itertools import product
import json

labelLists = {
    # label format like OR0, OR1, ...
    "OR": [],
    "AND": [],
    "XOR": [],
    "NOT": [],
    "IN": [], # used to label input registers
    "OUT": [], # used to label output registers
}

maxGatesPerStage = 1

# Define custom datastructures for dependency and flow tracing

class Register():
    freeRegistersAfter = {}
    inputRegisters = []

    def reset():
        Register.freeRegistersAfter = {}
        Register.inputRegisters = []

    def __init__(self, value, gateLabel:str, stage=0):
        self.value = value
        self.label = Register.determineNextRegisterLabel(gateLabel)
        self.stage = stage                              # stage where this value was created, valid after this stage
        self.lastUsed = stage                           # stage where this value is used for the last time, can be freed afterwards
        if self.stage == 0:
            Register.inputRegisters.append(self)
        self.register_for_freeing()

    def setStage(self, stage):
        self.stage = stage

    def register_for_freeing(self):
        try:
            Register.freeRegistersAfter[self.lastUsed].append(self)
        except Exception:
            Register.freeRegistersAfter[self.lastUsed] = [self]

    def remove_from_freeing(self):
        try:
            # remove old stage when register could be freed
            Register.freeRegistersAfter[self.lastUsed].remove(self)
        except Exception:
            pass

    def usedAt(self, stage: int):
        if stage <= self.lastUsed:
            return
        self.remove_from_freeing()
        self.lastUsed = stage
        # update when this register could be freed
        self.register_for_freeing()

    def setValue(self, value):
        self.value = value

    def setLabel(self, gateLabel):
        self.label = Register.determineNextRegisterLabel(gateLabel)

    # def setLabel(self, label):
    #     self.label = label

    def __str__(self):
        return f"[value: {self.value} | label: {self.label} | stage: {self.stage} | lastUsed: {self.lastUsed}]"

    def getValue(self):
        return self.value
    
    def getLabel(self):
        return self.label
    
    def getStage(self):
        return self.stage
    
    def determineNextRegisterLabel(gateLabel: str):
        try:
            number = int(labelLists[gateLabel][-1].split(gateLabel)[-1])
            # print(number+1)
            label = f"{gateLabel}{number+1}"
            labelLists[gateLabel].append(label)
            # print(labelLists[gateLabel])
        except Exception:
            label = f"{gateLabel}0"
            labelLists[gateLabel] = [label]
            # print(labelLists[gateLabel])
        return label

class Gate():
    outGatesID = 9999999
    usedGates = {
        outGatesID: []
    }

    def reset():
        Gate.usedGates = {
            Gate.outGatesID: []
        }

    def __init__(self, gateLabel: str, inputs: list):
        self.gateLabel = gateLabel
        self.inputs = inputs
        self.stage = self.determineStage()

        self.name = None
        self.output = None

    def to_json_dict(self):
        return {"type": self.gateLabel,
                "name": self.name,
                "inputs": [inp.getLabel() for inp in self.inputs]}

    def __str__(self):
        return f"[stage: {self.stage} | type: {self.gateLabel} | inputs: ({', '.join([r.getLabel() for r in self.inputs])}) | name: {self.name} | output: {self.output}]"

    def determineStage(self) -> int:
        if self.gateLabel == "OUT":
            return Gate.outGatesID
        # this gate can earlies be executed after its last executed input
        maxInputStage = max([input.getStage() for input in self.inputs]) + 1

        # search for lowest stage >= maxInputStage that doesnt have maxGatesPerStage gates yet
        try:
            while len(Gate.usedGates[maxInputStage]) >= maxGatesPerStage:
                maxInputStage = maxInputStage + 1
        except KeyError:
            return maxInputStage

        return maxInputStage
    
    def registerGate(self) -> None:
        try:
            Gate.usedGates[self.stage].append(self)
        except Exception:
            Gate.usedGates[self.stage] = [self]
            sortedKeys = sorted(list(Gate.usedGates.keys()))
            Gate.usedGates = {key:Gate.usedGates[key] for key in sortedKeys}

    def getStage(self) -> int:
        return self.stage
    
    def getGateLabel(self) -> str:
        return self.gateLabel
    
    def getInputs(self) -> list[Register]:
        return self.inputs
    
    def setOutput(self, outputRegister: Register) -> None:
        self.output = outputRegister
        self.name = self.output.label

    def getOutput(self) -> Register:
        return self.output
    

# Define gates here:
class OR_GATE(Gate):
    def __init__(self, *args):
        self.gateLabel = "OR"
        if len(args) == 1 and isinstance(args[0], list):
            self.inputs = args[0]
        else:
            self.inputs = list(args)
            
        self.stage = self.determineStage()
        self.registerGate()
        self.name = None
        self.output = None
        if(len(self.inputs) != 2):
            raise Exception(f"ERROR: OR-Gate Expects 2 inputs, given {len(self.inputs)}!")
        

    def execute(self) -> Register:
        a = self.inputs[0]
        b = self.inputs[1]
        a.usedAt(self.getStage())
        b.usedAt(self.getStage())
        
        val = a.getValue() or b.getValue()
        outRegister = Register(value=val, gateLabel=self.gateLabel, stage=self.stage)
        self.setOutput(outputRegister=outRegister)

        # self.registerGate()
        return outRegister
    
class AND_GATE(Gate):
    def __init__(self, *args):
        self.gateLabel = "AND"
        if len(args) == 1 and isinstance(args[0], list):
            self.inputs = args[0]
        else:
            self.inputs = list(args)
            
        self.stage = self.determineStage()
        self.registerGate()

        self.name = None
        self.output = None
        if(len(self.inputs) != 2):
            raise Exception(f"ERROR: OR-Gate Expects 2 inputs, given {len(self.inputs)}!")

    def execute(self) -> Register:
        a = self.inputs[0]
        b = self.inputs[1]
        a.usedAt(self.getStage())
        b.usedAt(self.getStage())

        val = a.getValue() and b.getValue()
        outRegister = Register(value=val, gateLabel=self.gateLabel, stage=self.stage)
        self.setOutput(outputRegister=outRegister)

        # self.registerGate()
        return outRegister
    
class XOR_GATE(Gate):
    def __init__(self, *args):
        self.gateLabel = "XOR"
        if len(args) == 1 and isinstance(args[0], list):
            self.inputs = args[0]
        else:
            self.inputs = list(args)
            
        self.stage = self.determineStage()
        self.registerGate()

        self.name = None
        self.output = None
        if(len(self.inputs) != 2):
            raise Exception(f"ERROR: OR-Gate Expects 2 inputs, given {len(self.inputs)}!")

    def execute(self) -> Register:
        a = self.inputs[0]
        b = self.inputs[1]
        a.usedAt(self.getStage())
        b.usedAt(self.getStage())

        val = a.getValue() ^ b.getValue()
        outRegister = Register(value=val, gateLabel=self.gateLabel, stage=self.stage)
        self.setOutput(outputRegister=outRegister)

        # self.registerGate()
        return outRegister
    
class OUT_GATE(Gate):
    def __init__(self, *args):
        self.gateLabel = "OUT"
        if len(args) == 1 and isinstance(args[0], list):
            self.inputs = [args[0]]
        else:
            self.inputs = list(args)

        self.stage = self.determineStage()
        self.registerGate()

        self.name = None
        self.output = None
        if(len(self.inputs) != 1):
            raise Exception(f"ERROR: OUT-Gate Expects 1 inputs, given {len(self.inputs)}!")
        
    def execute(self) -> Register:
        a = self.inputs[0]
        a.usedAt(self.getStage())

        # a.setLabel(self.gateLabel)
        out = Register(value=a.getValue(), gateLabel=self.gateLabel, stage=self.stage)
        self.setOutput(outputRegister=out)

        return out


class NOT_GATE(Gate):
    def __init__(self, *args):
        self.gateLabel = "NOT"
        if len(args) == 1 and isinstance(args[0], list):
            self.inputs = [args[0]]
        else:
            self.inputs = list(args)
            
        self.stage = self.determineStage()
        self.registerGate()

        self.name = None
        self.output = None
        if(len(self.inputs) != 1):
            raise Exception(f"ERROR: OR-Gate Expects 2 inputs, given {len(self.inputs)}!")

    def execute(self) -> Register:
        a = self.inputs[0]
        a.usedAt(self.getStage())

        val = 1 - a.getValue()
        outRegister = Register(value=val, gateLabel=self.gateLabel, stage=self.stage)
        self.setOutput(outputRegister=outRegister)

        # self.registerGate()
        return outRegister
    


# Define more abstract logic blocks

def NumToBinRegisters(num, wordsize, label="IN"):
    if num < 0:
        num = 2**wordsize+num
    base = bin(num)[2:]
    padding_size = wordsize - len(base)
    binString = '0' * padding_size + base
    return [Register(int(val), gateLabel=label) for val in binString]

def BinRegistersToNum(bin):
    bin = [str(r.getValue()) for r in bin]
    integer = 0
    for i, bit in enumerate(bin[::-1]):
        integer = integer + int(bit)* (2**i)
    return integer

def traceable_half_adder(a: Register, b: Register) -> tuple[Register, Register]:
    """
    Gibt (sum, carry) zurück.
    sum = a XOR b
    carry = a AND b
    """
    sum_ = XOR_GATE([a, b]).execute()
    carry = AND_GATE([a, b]).execute()
    return sum_, carry

def traceable_full_adder(a: Register, b: Register, cin: Register) -> tuple[Register, Register]:
    """
    Gibt (sum, carry) zurück.
    Realisiert mit 2 Half-Addern + OR-Gatter:
       s1, c1 = half_adder(a, b)
       s2, c2 = half_adder(s1, cin)
       sum = s2
       carry_out = c1 OR c2
    """
    s1, c1 = traceable_half_adder(a, b)
    s2, c2 = traceable_half_adder(s1, cin)
    carry_out = OR_GATE([c1, c2]).execute()
    return s2, carry_out

def traceable_approx_compressor_4to2(x1, x2, x3, x4): # passt
    """
    Gibt das approximierte Sum- und Carry-Bit zurück,
    gemäß:
        Carry  = (x1 AND x2) OR (x3 AND x4)
        Sum    = x1 OR x2 OR x3 OR x4
    Alle x_i sind 0 oder 1 (bzw. False/True).
    """
    # Approx. Sum = OR aller Eingänge
    sum_12 = OR_GATE([x1, x2]).execute()
    sum_34 = OR_GATE([x3, x4]).execute()
    sum_approx = OR_GATE([sum_12, sum_34]).execute()  # = x1 OR x2 OR x3 OR x4
    
    # Approx. Carry = OR der AND-Paare
    carry_12 = AND_GATE([x1, x2]).execute()
    carry_34 = AND_GATE([x3, x4]).execute()
    carry_approx = OR_GATE([carry_12, carry_34]).execute()
    
    # Als 0/1 zurückgeben
    return sum_approx, carry_approx


def traceable_approx_compressor_4to2_stage2(x1: Register, x2: Register, x3: Register, x4: Register) -> tuple[Register, Register]: # passt
    """
    Gibt das approximierte Sum- und Carry-Bit zurück,
    gemäß:
        Carry  = (x1 AND x2) OR (x3 AND x4)
        Sum    = x1 OR x2 OR x3 OR x4
    Alle x_i sind 0 oder 1 (bzw. False/True).
    """
    # Approx. Sum = OR(x1,x3)
    sum_approx = OR_GATE([x1, x3]).execute()  # = x1 OR x2 OR x3 OR x4
    
    # Approx. Carry = OR(x2,x4)
    carry_approx = OR_GATE([x2, x4]).execute()
    
    # Als 0/1 zurückgeben
    return sum_approx, carry_approx

def traceable_approx_compressor_4to2_stage3(x1: Register, x2: Register, x3: Register, x4: Register) -> tuple[Register, Register]: # passt
    """
    Gibt das approximierte Sum- und Carry-Bit zurück,
    gemäß:
        Carry  = (x1 AND x2) OR (x3 AND x4)
        Sum    = x1 OR x2 OR x3 OR x4
    Alle x_i sind 0 oder 1 (bzw. False/True).
    """
    # Approx. Sum = OR(x1,x3,x4)
    sum_13 = OR_GATE([x1, x3]).execute()
    sum_approx = OR_GATE([sum_13, x4]).execute()
    
    # Approx. Carry = OR(AND(x1,x2), AND(x3,x4))
    carry_12 = AND_GATE([x1, x2]).execute()
    carry_34 = AND_GATE([x3, x4]).execute()
    carry_approx = OR_GATE([carry_12, carry_34]).execute()
    
    # Als 0/1 zurückgeben
    return sum_approx, carry_approx

def traceable_approx_compressor_4to2_stage4(x1: Register, x2: Register, x3: Register, x4: Register, get_carry: bool) -> tuple[Register, Register]: # passt
    """
    Gibt das approximierte Sum- und Carry-Bit zurück,
    gemäß:
        Carry  = (x1 AND x2) OR (x3 AND x4)
        Sum    = x1 OR x2 OR x3 OR x4
    Alle x_i sind 0 oder 1 (bzw. False/True).
    """
    # Approx. Sum = OR(x1,x2,x3)
    sum_12 = OR_GATE([x1, x2]).execute()
    sum_approx = OR_GATE([sum_12, x3]).execute()
    
    # Approx. Carry = OR(x2, AND(x3,x4))
    if get_carry:
        carry_34 = AND_GATE([x3, x4]).execute()
        carry_approx = OR_GATE([x2, carry_34]).execute()
    else:
        carry_approx = "0"
    # Als 0/1 zurückgeben
    return sum_approx, carry_approx

def traceable_exact_compressor_4to2(x1: Register,x2: Register,x3: Register,x4: Register,cin: Register, combine_carries: bool=False) -> tuple[Register, Register, Register]:
    '''
        Gibt das exakte sum, cout und carry bit zurück.
        cout und carry sind gleich gewichtet, also stufe höher als das sum/input bits
    '''

    tmp_sum, cout = traceable_full_adder(x1,x2,x3)
    sum, carry = traceable_full_adder(tmp_sum, x4, cin)

    # carry = (x1 ^ x2 ^ x3 ^ x4) & cin | (1-(x1 ^ x2 ^ x3 ^ x4)) & x4
    if combine_carries:
        return sum, carry ^ cout, None
    
    return sum, carry, cout

def traceable_exact_compressor_5to2(x1: Register,x2: Register,x3: Register,x4: Register,x5: Register,cin1: Register, cin2: Register) -> tuple[Register, Register, Register, Register]:
    tmp_sum, cout1 = traceable_full_adder(x1, x2, x3)
    tmp_sum, cout2 = traceable_full_adder(tmp_sum, x4, cin1)
    sum, carry = traceable_full_adder(tmp_sum, x5, cin2)
    return sum, carry, cout1, cout2

def traceable_multiply4x4_M1(a: list[Register],b: list[Register]):
    result = []

    # stage 0
    result.append(AND_GATE(a[-1], b[-1]).execute())

    # stage 1
    sum, carry = traceable_half_adder(AND_GATE([a[-1], b[-2]]).execute(), AND_GATE([a[-2], b[-1]]).execute())
    result.append(sum)

    # stage 2
    p20 = OR_GATE([AND_GATE([a[-3], b[-1]]).execute(), AND_GATE([a[-1], b[-3]]).execute()]).execute() # pp20 OR pp02
    g10 = AND_GATE(AND_GATE(a[-2], b[-1]).execute(), AND_GATE(a[-1], b[-2]).execute()).execute() ## pp10 AND pp01
    sum, carry = traceable_approx_compressor_4to2_stage2(p20, g10, AND_GATE(a[-2], b[-2]).execute(), carry)
    result.append(sum)

    # stage 3
    g30 = AND_GATE(AND_GATE(a[-4], b[-1]).execute(), AND_GATE(a[-1], b[-4]).execute()).execute() # pp30 AND pp03
    g21 = AND_GATE(AND_GATE(a[-3], b[-2]).execute(), AND_GATE(a[-2], b[-3]).execute()).execute() # pp21 AND pp12
    p21 = OR_GATE(AND_GATE(a[-3], b[-2]).execute(), AND_GATE(a[-2], b[-3]).execute()).execute() # pp21 OR pp12
    p30 = OR_GATE(AND_GATE(a[-4], b[-1]).execute(), AND_GATE(a[-1], b[-4]).execute()).execute() # pp30 OR pp03
    sum, carry = traceable_approx_compressor_4to2_stage3(carry, OR_GATE(g30,g21).execute(), p21, p30)
    result.append(sum)

    # stage 4
    p31 = OR_GATE(AND_GATE(a[-4], b[-2]).execute(), AND_GATE(a[-2], b[-4]).execute()).execute() # pp31 OR pp13
    g31 = AND_GATE(AND_GATE(a[-4], b[-2]).execute(), AND_GATE(a[-2], b[-4]).execute()).execute() # pp31 AND pp13
    p22 = OR_GATE(AND_GATE(a[-3], b[-3]).execute(), AND_GATE(a[-3], b[-3]).execute()).execute() # pp22 OR pp22
    sum, carry = traceable_approx_compressor_4to2_stage4(p31, g31, p22, carry, get_carry=True)
    result.append(sum)

    # stage 5
    sum, carry = traceable_full_adder(AND_GATE(a[-4], b[-3]).execute(), AND_GATE(a[-4], b[-3]).execute(), carry)
    result.append(sum)

    # stage 6
    sum, carry = traceable_half_adder(AND_GATE(a[-4], b[-4]).execute(), carry)
    result.append(sum)

    # stage 7
    result.append(carry)

    result.reverse()

    return result

def traceable_multiply4x4_M2(a: list[Register],b: list[Register]):
    result = []

    # stage 0
    result.append(AND_GATE(a[-1], b[-1]).execute())

    # stage 1
    sum, carry = traceable_half_adder(AND_GATE([a[-1], b[-2]]).execute(), AND_GATE([a[-2], b[-1]]).execute())
    result.append(sum)

    # stage 2
    p20 = OR_GATE([AND_GATE([a[-3], b[-1]]).execute(), AND_GATE([a[-1], b[-3]]).execute()]).execute() # pp20 OR pp02
    g10 = AND_GATE(AND_GATE(a[-2], b[-1]).execute(), AND_GATE(a[-1], b[-2]).execute()).execute() ## pp10 AND pp01
    sum, carry = traceable_approx_compressor_4to2_stage2(p20, g10, AND_GATE(a[-2], b[-2]).execute(), carry)
    result.append(sum)

    # stage 3
    g30 = AND_GATE(AND_GATE(a[-4], b[-1]).execute(), AND_GATE(a[-1], b[-4]).execute()).execute() # pp30 AND pp03
    g21 = AND_GATE(AND_GATE(a[-3], b[-2]).execute(), AND_GATE(a[-2], b[-3]).execute()).execute() # pp21 AND pp12
    p21 = OR_GATE(AND_GATE(a[-3], b[-2]).execute(), AND_GATE(a[-2], b[-3]).execute()).execute() # pp21 OR pp12
    p30 = OR_GATE(AND_GATE(a[-4], b[-1]).execute(), AND_GATE(a[-1], b[-4]).execute()).execute() # pp30 OR pp03
    sum, carry = traceable_approx_compressor_4to2_stage3(carry, OR_GATE(g30,g21).execute(), p21, p30)
    result.append(sum)

    # stage 4
    p31 = OR_GATE(AND_GATE(a[-4], b[-2]).execute(), AND_GATE(a[-2], b[-4]).execute()).execute() # pp31 OR pp13
    g31 = AND_GATE(AND_GATE(a[-4], b[-2]).execute(), AND_GATE(a[-2], b[-4]).execute()).execute() # pp31 AND pp13
    p22 = OR_GATE(AND_GATE(a[-3], b[-3]).execute(), AND_GATE(a[-3], b[-3]).execute()).execute() # pp22 OR pp22
    sum, carry = traceable_approx_compressor_4to2_stage4(p31, g31, p22, carry, get_carry=True)
    result.append(sum)

    # stage 5
    sum, carry = traceable_half_adder(AND_GATE(a[-4], b[-3]).execute(), AND_GATE(a[-4], b[-3]).execute())
    result.append(sum)

    # stage 6
    sum, carry = traceable_half_adder(AND_GATE(a[-4], b[-4]).execute(), carry)
    result.append(sum)

    # stage 7
    result.append(carry)

    result.reverse()

    return result

def traceable_multiply4x4_exact(a: list[Register],b: list[Register]) -> list[Register]:
    result = []

    # stage 0
    sum = AND_GATE(a[-1], b[-1]).execute()
    result.append(sum)

    # stage 1
    sum, carry = traceable_half_adder(AND_GATE(a[-1], b[-2]).execute(), AND_GATE(a[-2], b[-1]).execute())
    result.append(sum)
    # stage 2
    pp20 = AND_GATE(a[-3], b[-1]).execute()
    pp11 = AND_GATE(a[-2], b[-2]).execute()
    pp02 = AND_GATE(a[-1], b[-3]).execute()
    sum, cout, carry = traceable_exact_compressor_4to2(pp20, pp11, pp02, Register(0,"IN"), carry, combine_carries=False)
    result.append(sum)

    # stage 3
    pp30 = AND_GATE(a[-4], b[-1]).execute()
    pp21 = AND_GATE(a[-3], b[-2]).execute()
    pp12 = AND_GATE(a[-2], b[-3]).execute()
    pp03 = AND_GATE(a[-1], b[-4]).execute()
    sum, carry, cout1, cout2 = traceable_exact_compressor_5to2(pp30, pp21, pp12, pp03, Register(0, "IN"), cout, carry)
    result.append(sum)

    # stage 4
    pp31 = AND_GATE(a[-4], b[-2]).execute()
    pp22 = AND_GATE(a[-3], b[-3]).execute()
    pp13 = AND_GATE(a[-2], b[-4]).execute()
    sum, carry, cout1, cout2 = traceable_exact_compressor_5to2(pp31, pp22, pp13, Register(0, "IN"), carry, cout1, cout2)
    result.append(sum)

    # stage 5
    pp32 = AND_GATE(a[-4], b[-3]).execute()
    pp23 = AND_GATE(a[-3], b[-4]).execute()
    sum, cout, carry = traceable_exact_compressor_4to2(pp32, pp23, carry, cout1, cout2)
    result.append(sum)

    # stage 6
    pp33 = AND_GATE(a[-4], b[-4]).execute()
    sum, carry = traceable_full_adder(pp33, carry, cout)
    result.append(sum)

    # stage 7
    result.append(carry)

    result.reverse()

    return result

def mult8x8_from4x4(a: list[Register],b: list[Register], mult4x4_low=traceable_multiply4x4_exact, mult4x4_mid=traceable_multiply4x4_exact, mult4x4_high=traceable_multiply4x4_exact):

    # create two "bit-nibbles", high/low for each number
    a_low = a[4:]
    b_low = b[4:]

    a_high = a[:4]
    b_high = b[:4]

    low_low_partial = mult4x4_low(a_low, b_low)
    low_high_partial = mult4x4_mid(a_low, b_high)
    high_low_partial = mult4x4_mid(a_high, b_low)
    high_high_partial = mult4x4_high(a_high, b_high)

    # combine partials
    # result will be filled least significant -> highest significant
    # before returning, reverse result to get correct bit order
    result = []

    # reverse all partials to make control flow easier
    low_low_partial.reverse()
    low_high_partial.reverse()
    high_low_partial.reverse()
    high_high_partial.reverse()

    # use lowest 4 bits as output
    result.extend(low_low_partial[:4])

    # ignore lowest 4 bits, combine ll_p and hh_p
    ll_hh_partial = low_low_partial[4:]
    ll_hh_partial.extend(high_high_partial)

    # loop through and combine the next 8 bits
    carry = Register(0, "IN")
    cout = Register(0, "IN")
    for b1, b2, b3 in zip(ll_hh_partial[:8], low_high_partial, high_low_partial):
        sum, carry, cout = traceable_exact_compressor_4to2(b1, b2, b3, carry, cout)
        result.append(sum)

    partial = ll_hh_partial[-4:]

    # next bit full adder with carries
    sum, carry = traceable_full_adder(partial[0], carry, cout)

    result.append(sum)

    # next two bits with half adder
    sum, carry = traceable_half_adder(partial[1], carry)
    result.append(sum)

    sum, carry = traceable_half_adder(partial[2], carry)
    result.append(sum)

    # last bit only XOR because carry no longer relevant
    sum = XOR_GATE(partial[3], carry).execute()
    result.append(sum)

    # bring result back into correct order
    result.reverse()

    return result

def traceable_full_adder_nimar(x1: Register, x2: Register, carry: Register) -> tuple[Register, Register]:
    or1 = OR_GATE(x1,x2).execute()
    nor1 = OR_GATE(NOT_GATE(x1).execute(), NOT_GATE(x2).execute()).execute()
    or2 = OR_GATE(NOT_GATE(nor1).execute(), carry).execute()
    or3 = OR_GATE(NOT_GATE(or1).execute(), or2).execute()
    cout = NOT_GATE(OR_GATE(NOT_GATE(or1).execute(), NOT_GATE(or2).execute()).execute()).execute()

    xor1 = XOR_GATE(x1, x2).execute()
    or4 = OR_GATE(NOT_GATE(carry).execute(), xor1).execute()
    sum = OR_GATE(NOT_GATE(or3).execute(), NOT_GATE(or4).execute()).execute()

    return sum, cout

def traceable16x16_adder(a: list[Register],b: list[Register], approximate=True):
    
    # reverse a and b to make control flow easier, i.e low -> high significant bits
    a.reverse()
    b.reverse()

    result = []

    if approximate:
        approximated_adds = 8
    else:
        approximated_adds = 0

    for i in range(approximated_adds):
        sum = XOR_GATE(a[i], b[i]).execute()
        result.append(sum)

    sum, carry = traceable_half_adder(a[approximated_adds], b[approximated_adds])
    result.append(sum)

    approximated_adds = approximated_adds + 1

    for i in range(approximated_adds, 16):
        sum, carry = traceable_full_adder_nimar(a[i], b[i], carry)
        result.append(sum)
    
    result.reverse()
    return result

def MAC_unit(a:list[Register],b:list[Register],c:list[Register], mult4x4_low=traceable_multiply4x4_exact, mult4x4_mid=traceable_multiply4x4_exact, mult4x4_high=traceable_multiply4x4_exact, ApproximateAdder=True):
    product = mult8x8_from4x4(a,b,mult4x4_low=mult4x4_low, mult4x4_mid=mult4x4_mid, mult4x4_high=mult4x4_high)

    mac_result = traceable16x16_adder(product, c, approximate=ApproximateAdder)

    return mac_result

def add_OUT_layer(results):
    for i in range(len(results)):
        results[i] = OUT_GATE(results[i]).execute()
    return results

# Wrapper class for the four different approximate levels of our circuit
def MAC_Wrap(a:int, b:int, c:int, mult4x4_low=traceable_multiply4x4_exact, mult4x4_mid=traceable_multiply4x4_exact, mult4x4_high=traceable_multiply4x4_exact, ApproximateAdder=True):
    Gate.reset()
    Register.reset()
    labelLists = {
        "OR": [],
        "AND": [],
        "XOR": [],
        "NOT": [],
        "IN": [],
        "OUT": []
    }
    a = NumToBinRegisters(a, 8)
    b = NumToBinRegisters(b, 8)
    c = NumToBinRegisters(c, 16)
    result = MAC_unit(a,b,c,mult4x4_low=mult4x4_low,mult4x4_mid=mult4x4_mid,mult4x4_high=mult4x4_high,ApproximateAdder=ApproximateAdder)
    Gate.reset()
    Register.reset()
    return BinRegistersToNum(result)

# Helper class for exporting circuit as a config readable by the compiler


class CircuitConfig():

    def __init__(self):
        self.input_registers = [reg.getLabel() for reg in Register.inputRegisters]
        try:
            useless_inputs = [reg.getLabel() for reg in Register.freeRegistersAfter[0]]
        except Exception:
            useless_inputs = []
        print(f"Removing useless Input: {useless_inputs}")
        if len(useless_inputs) > 0:
            for useless_input in useless_inputs:
                self.input_registers.remove(useless_input)
        self.stages = []
        for stage in Gate.usedGates.keys():
            try:
                freeRegisters = [register for register in Register.freeRegistersAfter[stage] if not (register.getLabel() in output_labels)]
            except Exception:
                freeRegisters = []

            self.stages.append({"gates": [gate.to_json_dict() for gate in Gate.usedGates[stage]],
                                "free_registers_after_stage": [reg.getLabel() for reg in freeRegisters]})
            
    def createJSONConfig(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)
    
    def writeToFile(path="config.json"):
        json_string = CircuitConfig().createJSONConfig()
        try:
            with open('path', 'x') as f:
                f.write(json_string)
        except Exception:
            with open('path', 'w') as f:
                f.write(json_string)

# Circuits
exactAdder_exactMultiplier = lambda a,b,c: MAC_Wrap(a,b,c, mult4x4_low=traceable_multiply4x4_exact, mult4x4_mid=traceable_multiply4x4_exact, mult4x4_high=traceable_multiply4x4_exact, ApproximateAdder=False)
exactAdder_approxMultiplier = lambda a,b,c: MAC_Wrap(a,b,c, mult4x4_low=traceable_multiply4x4_M2, mult4x4_mid=traceable_multiply4x4_M1, mult4x4_high=traceable_multiply4x4_exact, ApproximateAdder=False)
approxAdder_exactMultiplier = lambda a,b,c: MAC_Wrap(a,b,c, mult4x4_low=traceable_multiply4x4_exact, mult4x4_mid=traceable_multiply4x4_exact, mult4x4_high=traceable_multiply4x4_exact, ApproximateAdder=True)
approxAdder_approxMultiplier = lambda a,b,c: MAC_Wrap(a,b,c, mult4x4_low=traceable_multiply4x4_M2, mult4x4_mid=traceable_multiply4x4_M1, mult4x4_high=traceable_multiply4x4_exact, ApproximateAdder=True)