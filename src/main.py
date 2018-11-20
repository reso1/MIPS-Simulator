import os
import src.utils as utils
import src.instruction as ist

"""
Main program class
"""
class program():
################################### Public Function ###################################
    # Initiatation and read input
    def __init__(self, input_path):
        self.START_PC = 64                  # pc starts at #64
        self.START_DATA = self.START_PC     # data start address
        self.REGISTER_NUM = 32              # set register number to 32

        data_dir = os.path.dirname(input_path) + '/'
        self.DISASSEMBLY_FILENAME = data_dir +'disassembly.txt'
        self.SIMULATION_FILENAME = data_dir +'simulation.txt'

        self.circle = 0 
        self.pc = [self.START_PC]    
        self.regs = [0] * self.REGISTER_NUM
        self.mems = {}
        self.ists = []
        self.branches = {}
        self.raw_data = utils.read(input_path)

        print('! Input Read Finished...\n')
        
    # Disasembly sample
    def disassembly(self):
        b = 1
        pc = self.START_PC
        disassembly_str = ''

        for idx in range(len(self.raw_data)):
            word = self.raw_data[idx].strip()
            # Record disassembly string
            bitarray = [word[0:6], word[6:11], word[11:16], word[16:21], word[21:26], word[26:32]]
            disassembly_str += ' '.join(bitarray) + '\t' + str(pc) + '\t'
            # Decode instruction word
            decoded = self.decode_ist(word)
            disassembly_str += decoded.get_MIPS() + '\n' 
            self.ists.append(decoded)
            pc += 4
            # End of instructions if meets [BREAK]
            if decoded.name == 'BREAK':
                b = idx
                self.START_DATA = pc
                break
        print('# Instruction Word Decode Finished...')
        
        for idx in range(b+1, len(self.raw_data)):
            word = self.raw_data[idx].strip()
            # Decode memory word
            decoded = utils.signed_b2i(self.raw_data[idx].strip())
            # Record disassembly string
            disassembly_str += word + '\t' + str(pc) + '\t' +str(decoded) + '\n'
            self.set_mem_val(pc, decoded)
            pc += 4
        print('# Memory Word Decode Finished...')
        print('! Disassembly Finished...\n')
        return disassembly_str

    # Simulate Disassembly MIPS code
    def simulate(self):
        # Disassembly First
        disassembly_str = self.disassembly()
        # Simulate Then
        simulation_str = ''
        while self.get_pc() != -1:
            # Fetch for a instruction
            b_data_addr = self.START_DATA
            instruction, o_str = self.fetch()
            # Execute instruction
            instruction.execute()
            # Record simulation string
            simulation_str += '--------------------\n' + o_str + '\t'
            simulation_str += instruction.get_MIPS() + '\n\n'+ 'Registers\n' + 'R00:'
            for i in range(16):
                simulation_str += '\t' + str(self.get_reg_val(i))
            simulation_str += '\nR16:'
            for i in range(16, 32):
                simulation_str += '\t' + str(self.get_reg_val(i))
            simulation_str += '\n\nData'
            for i in range(len(self.mems)):
                if i%8 == 0:
                    simulation_str += '\n' + str(b_data_addr + 4*i) + ':'
                simulation_str += '\t' + str(self.get_mem_val(b_data_addr + 4*i))
            simulation_str += '\n\n'

        print('! Simulation Finished...\n')
        return disassembly_str, simulation_str

################################### Private Function ###################################
    # set pc value
    def set_pc(self, val):
        self.pc = [val]
    # get pc value
    def get_pc(self):
        return self.pc[0]
    # get register value by index 
    def get_reg_val(self, reg_idx):
        return self.regs[reg_idx]
    # set register value by index 
    def set_reg_val(self, reg_idx, val):
        self.regs[reg_idx] = val
    # get register value by address 
    def get_mem_val(self, mem_addr):
        return self.mems[mem_addr]
    # set register value by address 
    def set_mem_val(self, mem_addr, val):
        self.mems[mem_addr] = val

    # Decode instructions stored in a word 
    def decode_ist(self, word):
        assert(len(word) == 32)
        op = ist.OPCODE_TYPES[word[0:6]] if word[0:6] in ist.OPCODE_TYPES.keys() else 'SPECIAL'
        fst = utils.b2i(word[6:11])
        sec = utils.b2i(word[11:16])
        imm_off = utils.signed_b2i(word[16:32])     # signed int  
        
        # Non-Special type
        if op == 'J':
            return ist.J(utils.b2i(word[6:32]), self)
        elif op == 'BEQ':
            return ist.BEQ(fst, sec, imm_off, self)
        elif op == 'BGTZ':
            return ist.BGTZ(fst, imm_off, self)
        elif op == 'SW':
            return ist.SW(fst, sec, imm_off, self)
        elif op == 'LW':
            return ist.LW(fst, sec, imm_off, self)
        elif op == 'REGIMM':
            return ist.BLTZ(fst, imm_off, self)
        # Special type
        else:
            is_immidiate = (word[0] == '1')
            fur = utils.b2i(word[21:26])
            
            if is_immidiate:
                func = ist.SPECIAL_TYPES[word[0:6]] 
                trd = imm_off
            else:
                func = ist.SPECIAL_TYPES[word[26:32]] 
                trd = utils.b2i(word[16:21])

            # Special 2 type
            if op == 'SPECIAL2':
                return ist.MUL(is_immidiate, fst, sec, trd, self)

            if func == 'ADD' or func == 'ADDI':
                return ist.ADD(is_immidiate, fst, sec, trd, self)
            elif func == 'SUB' or func == 'SUBI':
                return ist.SUB(is_immidiate, fst, sec, trd, self)
            elif func == 'AND' or func == 'ANDI':
                return ist.AND(is_immidiate, fst, sec, trd, self)
            elif func == 'NOR' or func == 'NORI':
                return ist.NOR(is_immidiate, fst, sec, trd, self)
            elif func == 'SLT' or func =='SLTI':
                return ist.SLT(is_immidiate, fst, sec, trd, self)
            elif func == 'JR':
                return ist.JR(fst, fur, self)
            elif func == 'BREAK':
                return ist.BREAK(utils.b2i(word[6:26]), self)
            elif func == 'SLL':
                return ist.NOP(self) if word[6:26] == '00000000000000000000' else ist.SLL(sec, trd, fur, self)
            elif func == 'SRL':
                return ist.SRL(sec, trd, fur, self)
            elif func == 'SRA':
                return ist.SRA(sec, trd, fur, self)
            else:
                print('No such instrucion opcode found !')
                return None
    
    # Fetch next instruction
    def fetch(self):
        self.circle += 1
        addr = self.get_pc()
        idx = int((addr - self.START_PC) / 4)
        return self.ists[idx], 'Cycle:%d\t%d'%(self.circle, addr) 

    # pc + 4
    def next(self):
        self.set_pc(self.get_pc() + 4)