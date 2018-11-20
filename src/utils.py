"""
File read and bit manipulation file
"""
import os
import math

################################### File I/O ###################################
def read(path):
    f = open(path, 'r')
    ret = f.readlines() 
    f.close()
    return ret

def write(path, in_str, avoid_rewriting = False):
    new_path = path
    # Avoid file overwriting
    if avoid_rewriting == True:
        idx = 0
        while os.path.exists(new_path):
            prefix, ftype = os.path.splitext(path)
            new_path = prefix + '_' + str(idx) + ftype

    f = open(new_path, 'w')
    f.write(in_str)
    f.close()

################################### Bit Manipulation ###################################
"""
Shift bits arithmetically, left shift if bits<0 else right shift
(invalid) overflow sets to 0 
"""
def shiftArith(origin, bits):
    # if abs(bits) >= 32:
    #     return 0
    return origin<<-bits if bits<0 else origin>>bits

"""
Shift bits logically, left shift if bits<0 else right shift
(invalid) overflow sets to -1 if negtive number right shift overflow else 0
"""
def shiftLogic(origin, bits):
    if bits == 0 or origin >= 0:
        return shiftArith(origin, bits)
    
    # if abs(bits) >= 32:
    #     return -1 if bits >= 32 else 0

    return abs(origin)<<-bits if bits < 0 else (math.pow(2, 31)+abs(origin)) >> bits

# Decode unsigned bits to integers 
def b2i(word):
    return int(word, 2)

# Decode signed bits(32) to integers 
def signed_b2i(word):
    if word[0] == '0':
        return b2i(word)
    else:
        tmp = ''
        for c in word[1:]:
            tmp += str(1-int(c))
        return -b2i(tmp)-1

# get first non-zero index of a word.
def get_first_NZ_idx(word):
    for idx, b in enumerate(word):
        if b == '1':
            return idx+1
    return 0
