import gates as g
import random

# Example to test the exact MAC_Unit for 1000 random inputs

samplesize = 1000       # how many random inputs will be tested



error = 0
for _ in range(samplesize):
    i = random.randint(0, 2**8-1)
    j = random.randint(0, 2**8-1)
    k = random.randint(0, 2**10) # To mitigate overflows with the MAC unit
    g.Gate.reset()
    g.Register.reset()
    labelLists = {
        # label format like OR0, OR1, ...
        "OR": [],
        "AND": [],
        "XOR": [],
        "NOT": [],
        "IN": [],
        "OUT": []
    }

    mac_product = g.exactAdder_exactMultiplier(i, j, k)
    if mac_product != i*j+k:
        print(f"Result differs at ({i} * {j} + {k}) = {mac_product} | truth: {i*j+k}")
        error = error + 1
    
        
print(f"Error rate: {(error/samplesize)*100}%")