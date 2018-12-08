"""
The instruction class file
"""
import src.utils as utils

OPCODE_TYPES = {'000000':'SPECIAL', '011100':'SPECIAL2', 
                '000010':'J', '000100':'BEQ', '000111':'BGTZ', '000001':'REGIMM', '101011':'SW', '100011':'LW'}

SPECIAL_TYPES = {'001000':'JR', '001101':'BREAK', '000000':'SLL', '000010':'SRL', '000011':'SRA',
                '100000':'ADD', '100010':'SUB', '100100':'AND', '100110':'NOR', '101010':'SLT', 
                '110000':'ADDI', '110001':'SUBI', '110010':'ANDI', '110011':'NORI', '110101':'SLTI'}

ALU_ISTS = ['ADD', 'SUB', 'AND', 'NOR', 'SLT']    
ALUB_ISTS = ['SLL', 'SRL', 'SRA', 'MUL'] 
MEM_ISTS = ['SW', 'LW']           

################################### BASE INSTRUCION CLASS ###################################
class ist_obj():
    # virtual funcitons for override
    def execute(self):
        raise NotImplementedError
    def get_MIPS(self):
        raise NotImplementedError

################################### CATEGORY 1 INSTRUCIONS ###################################
"""  
Name   : J
Format : J #target
Usage  : Jump to an Instruction Index
"""
class J(ist_obj):
    def __init__(self, _target, _program):
        self.name = 'J'
        self.target = _target
        self.PG = _program
        # used for data-hazard detection
        self.sregs = []
        self.dregs = []

    # pc must be a list
    def execute(self):
        _p = self.PG
        _p.set_pc(self.target<<2)
    
    def get_MIPS(self):
        return 'J #%d'%(self.target<<2)

"""  
Name   : JR
Format : JR rs
Usage  : Jump to an Instruction Index stored in [rs]
"""
class JR(ist_obj):
    def __init__(self, _rs, _hint, _program):
        self.name = 'JR'
        self.rs = _rs
        self.hint = _hint
        self.PG = _program
        # used for data-hazard detection
        self.sregs = [self.rs]
        self.dregs = []


    # pc must be a list
    def execute(self):
        _p = self.PG
        _p.set_pc(_p.get_reg_val(self.rs))
    
    def get_MIPS(self):
        return 'JR R%d'%(self.rs)

"""  
Name   : BEQ
Format : BEQ rs, rt, offset
Usage  : If rs = rt then branch
"""
class BEQ(ist_obj):
    def __init__(self, _rs, _rt, _offset, _program):
        self.name = 'BEQ'
        self.rs = _rs
        self.rt = _rt
        self.offset = _offset
        self.PG = _program
        # used for data-hazard detection
        self.sregs = [self.rs, self.rt]
        self.dregs = []

    # pc must be a list
    def execute(self):
        _p = self.PG
        if _p.get_reg_val(self.rs) == _p.get_reg_val(self.rt):
            _p.set_pc((self.offset<<2) + _p.get_pc())
        _p.next()
    
    def get_MIPS(self):
        return 'BEQ R%d, R%d, #%d'%(self.rs, self.rt, self.offset<<2)

"""  
Name   : BLTZ
Format : BLTZ rs, offset
Usage  : If rs < 0 then branch
"""
class BLTZ(ist_obj):
    def __init__(self, _rs, _offset, _program):
        self.name = 'BLTZ'
        self.rs = _rs
        self.offset = _offset
        self.PG = _program
        # used for data-hazard detection
        self.sregs = [self.rs]
        self.dregs = []

    # pc must be a list
    def execute(self):
        _p = self.PG
        if _p.get_reg_val(self.rs) < 0:
            _p.set_pc((self.offset<<2) + _p.get_pc())
        _p.next()
    
    def get_MIPS(self):
        return 'BLTZ R%d, #%d'%(self.rs, self.offset<<2)

"""  
Name   : BGTZ
Format : BGTZ rs, offset
Usage  : If rs > 0 then branch
"""
class BGTZ(ist_obj):
    def __init__(self, _rs, _offset, _program):
        self.name = 'BGTZ'
        self.rs = _rs
        self.offset = _offset
        self.PG = _program
        # used for data-hazard detection
        self.sregs = [self.rs]
        self.dregs = []

    # pc must be a list
    def execute(self):
        _p = self.PG
        if _p.get_reg_val(self.rs) > 0:
            _p.set_pc((self.offset<<2) + _p.get_pc())
        _p.next()
    
    def get_MIPS(self):
        return 'BGTZ R%d, #%d'%(self.rs, self.offset<<2)

"""  
Name   : BREAK
Format : BREAK
Usage  : Causet a breakpoint exception
"""
class BREAK(ist_obj):
    def __init__(self, _code, _program):
        self.name = 'BREAK'
        self.code = _code
        self.PG = _program

    # pc must be a list
    def execute(self):
        _p = self.PG
        _p.set_pc(-1)   # set pc = -1 as stop signal 
    
    def get_MIPS(self):
        return 'BREAK'

"""  
Name   : SW
Format : SW rt, offset(base)
Usage  : Store a word from register to memory
"""
class SW(ist_obj):
    def __init__(self, _base, _rt, _offset, _program):
        self.name = 'SW'
        self.base = _base
        self.rt = _rt
        self.offset = _offset
        self.PG = _program
        # used for data-hazard detection
        self.sregs = [self.rt, self.base]
        self.dregs = []

    def WB(self):
        _p = self.PG
        _p.set_mem_val(_p.get_reg_val(self.base) + self.offset, _p.get_reg_val(self.rt))
    
    def execute(self):
        self.WB()
        self.PG.next()
    
    def get_MIPS(self):
        return 'SW R%d, %d(R%d)'%(self.rt, self.offset, self.base)

"""  
Name   : LW
Format : LW rt, offset(base)
Usage  : Load a word from memory to register
"""
class LW(ist_obj):
    def __init__(self, _base, _rt, _offset, _program):
        self.name = 'LW'
        self.base = _base
        self.rt = _rt
        self.offset = _offset
        self.PG = _program
        # used for data-hazard detection
        self.sregs = [self.base]
        self.dregs = [self.rt]
    
    def WB(self):
        self.PG.set_reg_val(self.rt, self.PG.get_mem_val(self.PG.get_reg_val(self.base) + self.offset))

    def execute(self):
        self.WB()
        self.PG.next()
    
    def get_MIPS(self):
        return 'LW R%d, %d(R%d)'%(self.rt, self.offset, self.base)

"""  
Name   : SLL
Format : SLL rd, rt, sa
Usage  : Left-Shift a word by a fixed number of bits (Logical)
"""
class SLL(ist_obj):
    def __init__(self, _rt, _rd, _sa, _program):
        self.name = 'SLL'
        self.rt = _rt
        self.rd = _rd
        self.sa = _sa
        self.PG = _program
        # used for data-hazard detection
        self.sregs = [self.rt]
        self.dregs = [self.rd]

    def WB(self):
        self.PG.set_reg_val(self.rd, utils.shiftLogic(self.PG.get_reg_val(self.rt), -self.sa))

    def execute(self):
        self.WB()
        self.PG.next()
    
    def get_MIPS(self):
        return 'SLL R%d, R%d, #%d'%(self.rd, self.rt, self.sa)

"""  
Name   : SRL
Format : SRL rd, rt, sa
Usage  : Right-Shift a word by a fixed number of bits (Logical)
"""
class SRL(ist_obj):
    def __init__(self, _rt, _rd, _sa, _program):
        self.name = 'SRL'
        self.rt = _rt
        self.rd = _rd
        self.sa = _sa
        self.PG = _program
        # used for data-hazard detection
        self.sregs = [self.rt]
        self.dregs = [self.rd]

    def WB(self):
        self.PG.set_reg_val(self.rd, utils.shiftLogic(self.PG.get_reg_val(self.rt), self.sa))

    def execute(self):
        self.WB()
        self.PG.next()
    
    def get_MIPS(self):
        return 'SRL R%d, R%d, #%d'%(self.rd, self.rt, self.sa)

"""  
Name   : SRA
Format : SRA rd, rt, sa
Usage  : Right-Shift a word by a fixed number of bits (Arithmetic)
"""
class SRA(ist_obj):
    def __init__(self, _rt, _rd, _sa, _program):
        self.name = 'SRA'
        self.rt = _rt
        self.rd = _rd
        self.sa = _sa
        self.PG = _program
        # used for data-hazard detection
        self.sregs = [self.rt]
        self.dregs = [self.rd]

    def WB(self):
        self.PG.set_reg_val(self.rd, utils.shiftArith(self.PG.get_reg_val(self.rt), self.sa))

    def execute(self):
        self.WB()
        self.PG.next()
    
    def get_MIPS(self):
        return 'SRA R%d, R%d, #%d'%(self.rd, self.rt, self.sa)

"""  
Name   : NOP
Format : NOP
Usage  : Perform no operation as placeholder
"""
class NOP(ist_obj):
    def __init__(self, _program):
        self.name = 'SRA'
        self.PG = _program

    def execute(self):
        self.PG.next()
    
    def get_MIPS(self):
        return 'NOP'

################################### CATEGORY 2 INSTRUCIONS ###################################
### 0 if is register, 1 if is immidiate

"""  
Name   : ADD
Format : ADD rd, rs, rt / ADD rt, rs, #[imm]
Usage  : To add 32-bit integers 
"""
class ADD(ist_obj):
    def __init__(self, _is_IMMIDIATE, _rs, _rt, _rd_imm, _program):
        self.name = 'ADD'
        self.is_imm = _is_IMMIDIATE
        self.rs = _rs
        self.rt = _rt
        self.rd_imm = _rd_imm
        self.PG = _program
        # used for data-hazard detection
        if self.is_imm:
            self.sregs = [self.rs]
            self.dregs = [self.rt]
        else:
            self.sregs = [self.rs, self.rt]
            self.dregs = [self.rd_imm]

    def WB(self):
        _p = self.PG
        if self.is_imm:
            _p.set_reg_val(self.rt, _p.get_reg_val(self.rs) + self.rd_imm)
        else:
            _p.set_reg_val(self.rd_imm, _p.get_reg_val(self.rs) + _p.get_reg_val(self.rt))

    def execute(self):
        self.WB()
        self.PG.next()
    
    def get_MIPS(self):
        if self.is_imm:
            return 'ADD R%d, R%d, #%d'%(self.rt, self.rs, self.rd_imm)
        return 'ADD R%d, R%d, R%d'%(self.rd_imm, self.rs, self.rt)

"""  
Name   : SUB
Format : SUB rd, rs, rt / SUB rt, rs, #[imm]
Usage  : To subtract 32-bit integers
"""
class SUB(ist_obj):
    def __init__(self, _is_IMMIDIATE, _rs, _rt, _rd_imm, _program):
        self.name = 'SUB'
        self.is_imm = _is_IMMIDIATE
        self.rs = _rs
        self.rt = _rt
        self.rd_imm = _rd_imm
        self.PG = _program
        # used for data-hazard detection
        if self.is_imm:
            self.sregs = [self.rs]
            self.dregs = [self.rt]
        else:
            self.sregs = [self.rs, self.rt]
            self.dregs = [self.rd_imm]

    def WB(self):
        _p = self.PG
        if self.is_imm:
            _p.set_reg_val(self.rt, _p.get_reg_val(self.rs) - self.rd_imm)
        else:
            _p.set_reg_val(self.rd_imm, _p.get_reg_val(self.rs) - _p.get_reg_val(self.rt))

    def execute(self):
        self.WB()
        self.PG.next()
    
    def get_MIPS(self):
        if self.is_imm:
            return 'SUB R%d, R%d, #%d'%(self.rt, self.rs, self.rd_imm)
        return 'SUB R%d, R%d, R%d'%(self.rd_imm, self.rs, self.rt)

"""  
Name   : MUL
Format : MUL rd, rs, rt / MUL rt, rs, #[imm]
Usage  : To multiply 32-bit integers
"""
class MUL(ist_obj):
    def __init__(self, _is_IMMIDIATE, _rs, _rt, _rd_imm, _program):
        self.name = 'MUL'
        self.is_imm = _is_IMMIDIATE
        self.rs = _rs
        self.rt = _rt
        self.rd_imm = _rd_imm
        self.PG = _program
        # used for data-hazard detection
        if self.is_imm:
            self.sregs = [self.rs]
            self.dregs = [self.rt]
        else:
            self.sregs = [self.rs, self.rt]
            self.dregs = [self.rd_imm]

    def WB(self):
        _p = self.PG
        if self.is_imm:
            _p.set_reg_val(self.rt, _p.get_reg_val(self.rs) * self.rd_imm)
        else:
            _p.set_reg_val(self.rd_imm, _p.get_reg_val(self.rs) * _p.get_reg_val(self.rt))

    def execute(self):
        self.WB()
        self.PG.next()
    
    def get_MIPS(self):
        if self.is_imm:
            return 'MUL R%d, R%d, #%d'%(self.rt, self.rs, self.rd_imm)
        return 'MUL R%d, R%d, R%d'%(self.rd_imm, self.rs, self.rt)

"""  
Name   : AND
Format : AND rd, rs, rt / AND rt, rs, #[imm]
Usage  : To do bitwise logical AND
"""
class AND(ist_obj):
    def __init__(self, _is_IMMIDIATE, _rs, _rt, _rd_imm, _program):
        self.name = 'AND'
        self.is_imm = _is_IMMIDIATE
        self.rs = _rs
        self.rt = _rt
        self.rd_imm = _rd_imm
        self.PG = _program
        # used for data-hazard detection
        if self.is_imm:
            self.sregs = [self.rs]
            self.dregs = [self.rt]
        else:
            self.sregs = [self.rs, self.rt]
            self.dregs = [self.rd_imm]

    def WB(self):
        _p = self.PG
        if self.is_imm:
            _p.set_reg_val(self.rt, _p.get_reg_val(self.rs) and self.rd_imm)
        else:
            _p.set_reg_val(self.rd_imm, _p.get_reg_val(self.rs) and _p.get_reg_val(self.rt))

    def execute(self):
        self.WB()
        self.PG.next()
    
    def get_MIPS(self):
        if self.is_imm:
            return 'AND R%d, R%d, #%d'%(self.rt, self.rs, self.rd_imm)
        return 'AND R%d, R%d, R%d'%(self.rd_imm, self.rs, self.rt)

"""  
Name   : NOR
Format : NOR rd, rs, rt / NOR rt, rs, #[imm]
Usage  : To do bitwise logical NOT OR
"""
class NOR(ist_obj):
    def __init__(self, _is_IMMIDIATE, _rs, _rt, _rd_imm, _program):
        self.name = 'NOR'
        self.is_imm = _is_IMMIDIATE
        self.rs = _rs
        self.rt = _rt
        self.rd_imm = _rd_imm
        self.PG = _program
        # used for data-hazard detection
        if self.is_imm:
            self.sregs = [self.rs]
            self.dregs = [self.rt]
        else:
            self.sregs = [self.rs, self.rt]
            self.dregs = [self.rd_imm]

    def WB(self):
        _p = self.PG
        if self.is_imm:
            _p.set_reg_val(self.rt, _p.get_reg_val(self.rs) or not self.rd_imm)
        else:
            _p.set_reg_val(self.rd_imm, _p.get_reg_val(self.rs) or not _p.get_reg_val(self.rt))

    def execute(self):
        self.WB()
        self.PG.next()
    
    def get_MIPS(self):
        if self.is_imm:
            return 'NOR R%d, R%d, #%d'%(self.rt, self.rs, self.rd_imm)
        return 'NOR R%d, R%d, R%d'%(self.rd_imm, self.rs, self.rt)

"""  
Name   : SLT
Format : SLT rd, rs, rt / SLT rt, rs, #[imm]
Usage  : To record the result of a less-than comparsion
"""
class SLT(ist_obj):
    def __init__(self, _is_IMMIDIATE, _rs, _rt, _rd_imm, _program):
        self.name = 'SLT'
        self.is_imm = _is_IMMIDIATE
        self.rs = _rs
        self.rt = _rt
        self.rd_imm = _rd_imm
        self.PG = _program
        # used for data-hazard detection
        if self.is_imm:
            self.sregs = [self.rs]
            self.dregs = [self.rt]
        else:
            self.sregs = [self.rs, self.rt]
            self.dregs = [self.rd_imm]

    def WB(self):
        _p = self.PG
        if self.is_imm:
            _p.set_reg_val(self.rt, _p.get_reg_val(self.rs) < self.rd_imm)
        else:
            _p.set_reg_val(self.rd_imm, _p.get_reg_val(self.rs) < _p.get_reg_val(self.rt))

    def execute(self):
        self.WB()
        self.PG.next()
    
    def get_MIPS(self):
        if self.is_imm:
            return 'SLT R%d, R%d, #%d'%(self.rt, self.rs, self.rd_imm)
        return 'SLT R%d, R%d, R%d'%(self.rd_imm, self.rs, self.rt)