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
        """ Program Configs """
        data_dir = os.path.dirname(input_path) + '/'
        self.DISASSEMBLY_FILENAME = data_dir +'disassembly.txt'
        self.SIMULATION_FILENAME = data_dir +'simulation.txt'
        self.PIPELINE_FILENAME = data_dir +'pipeline.txt'

        # read raw sample input 
        self.raw_data = utils.read(input_path)  

        self.START_PC = 64                  # pc starts at #64
        self.START_DATA = self.START_PC     # data start address
        self.REGISTER_NUM = 32              # set register number to 32
        
        """ Regular Field """
        self.cycle = 0 
        self.pc = [self.START_PC]    
        self.regs = [0] * self.REGISTER_NUM
        self.mems = {}
        self.ists = []

        """ Pipeline Field """
        # buffers for pipelining, each has only 1 entry except 4 for PRE_ISSUE 
        self.buffer_PRE_ISSUE = []          # 4 entries
        self.buffer_POST_ALU  = None          
        self.buffer_POST_ALUB = None          
        self.buffer_POST_MEM  = None          

        # queues for pipelining, each has 2 entries
        self.queue_PRE_MEM  = []
        self.queue_PRE_ALU  = []
        self.queue_PRE_ALUB = []

        # IF stalling due to branches
        self.waiting_ist_IF = None
        
        """ ALUB cycle state
        | 0  |  occupied |
        | 1  | available | """
        self.ALUB_state = 1

        # stop signal
        self.is_break_fetched = False

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

    # Simulate Pipeline of MIPS code
    def pipeline(self):
        # disassembly first
        disassembly_str = self.disassembly()
        # pipeline then
        pipeline_str = ''
        while not self.is_break_fetched:
            # cycle infos
            self.cycle += 1
            pipeline_str += '--------------------\nCycle:%d\n\n'%(self.cycle)
            # pipeline infos
            fetched_ists, IF_str = self.IF()
            issued_ists_idx = self.Issue()
            executed = self.EXE()
            written_back = self.WB()
            self.update(fetched_ists, issued_ists_idx, executed, written_back)
            pipeline_str += IF_str + self.get_pre_issue_infos() + self.get_buffer_queue_infos()
            # register infos
            pipeline_str += '\nRegisters\nR00:%s\nR08:%s\nR16:%s\nR24:%s\n\n' \
                %(self.get_reg_infos(0,8), self.get_reg_infos(8,16), self.get_reg_infos(16,24), self.get_reg_infos(24,32)) 
            # memory infos
            b_data_addr = self.START_DATA
            pipeline_str += 'Data'
            for i in range(len(self.mems)):
                if i%8 == 0:
                    pipeline_str += '\n' + str(b_data_addr + 4*i) + ':'
                pipeline_str += '\t' + str(self.get_mem_val(b_data_addr + 4*i))
            pipeline_str += '\n'
        return disassembly_str, pipeline_str

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
    # pc + 4
    def next(self):
        self.set_pc(self.get_pc() + 4)

    """ Used for Proj1 ONLY"""
    # Fetch next instruction
    def fetch(self):
        self.cycle += 1
        addr = self.get_pc()
        idx = int((addr - self.START_PC) / 4)
        return self.ists[idx], 'Cycle:%d\t%d'%(self.cycle, addr) 

    """ Used for pipeline of Proj2 """ 
    # stage 1 of Instruction Fetch
    def IF(self):
        # cycle += 1
        ret_str = 'IF Unit:\n\tWaiting Instruction: \n\tExecuted Instruction: \n'
        fetched_ists = []

        """ check branch waiting stalling of IF """
        if self.is_branch_waiting():
            tmp = self.waiting_ist_IF.get_MIPS()
            # check branch is ready to execute
            if self.is_branch_ready(self.waiting_ist_IF):
                self.waiting_ist_IF.execute()
                self.waiting_ist_IF = None
                ret_str = 'IF Unit:\n\tWaiting Instruction: \n\tExecuted Instruction: %s\n'%tmp
            else: 
                ret_str = 'IF Unit:\n\tWaiting Instruction: %s\n\tExecuted Instruction: \n'%tmp

        else:        
            """ check structural hazards """
            buffer_empty = 4 - len(self.buffer_PRE_ISSUE)
            assert(buffer_empty >= 0 and buffer_empty <= 4)
            # no empty slot in pre-issue buffer
            if buffer_empty != 0:
                """ IF operation """
                iterations = 1 if buffer_empty == 1 else 2
                for i in range(iterations):
                    I = self.fetch_v2()
                    if I.name == 'NOP' or I.name == 'BREAK':
                        I.execute()
                        ret_str = 'IF Unit:\n\tWaiting Instruction: \n\tExecuted Instruction: %s\n'%(I.name)
                        if I.name == 'BREAK':
                            self.is_break_fetched = True
                    elif I.name == 'J' or I.name == 'JR' or I.name == 'BEQ' or I.name == 'BLTZ' or I.name == 'BGTZ':
                        ret_str = self.exec_branch_IF(I)
                    else:
                        # write non-Branch/NOP/BREAK instruction to pre-issue buffer
                        fetched_ists.append(I)
                        self.next()

        return fetched_ists, ret_str
          
    # stage 2 of Instruction Issue
    def Issue(self):
        issue_list = []
        """ decide which entries to issue """
        if len(self.buffer_PRE_ISSUE) != 0:            
            earlier_not_issued_ists_sregs = []
            earlier_not_issued_ists_dregs = []
            has_earlier_not_issued_sw = False

            PRE_ALU_size = len(self.queue_PRE_ALU)
            PRE_ALUB_size = len(self.queue_PRE_ALUB)
            PRE_MEM_size = len(self.queue_PRE_MEM)
            for idx, I in enumerate(self.buffer_PRE_ISSUE):
                # cannot issue more than two instruction per cycle
                if len(issue_list) > 2:
                    break
                # structural hazards
                PRE_ALU_not_empty = I.name in ist.ALU_ISTS and PRE_ALU_size == 2        # PRE-ALU not empty
                PRE_ALUB_not_empty = I.name in ist.ALUB_ISTS and PRE_ALUB_size == 2     # PRE-ALUB not empty
                PRE_MEM_not_empty = I.name in ist.MEM_ISTS and PRE_MEM_size == 2        # PRE-MEM not empty
                #print(PRE_ALU_not_empty, PRE_ALUB_not_empty, PRE_MEM_not_empty)
                # data hazards
                WAR = utils.list_intersection(I.dregs, earlier_not_issued_ists_sregs)   # WAR hazards
                RAW = utils.list_intersection(I.sregs,                                  # RAW hazards
                    utils.list_union(self.get_unready_regs(), earlier_not_issued_ists_dregs))                                         
                WAW = utils.list_intersection(I.dregs,                                  # WAW hazards   
                    utils.list_union(self.get_unready_regs(), earlier_not_issued_ists_dregs))                                              
                #print(WAR, RAW, WAW)
    
                # mem hazards, stores must in order and load should issued after stores
                mem_not_in_order = I.name in ist.MEM_ISTS and has_earlier_not_issued_sw
                #print(mem_not_in_order)
                if I.name != 'SW':
                    earlier_not_issued_ists_sregs = utils.list_union(earlier_not_issued_ists_sregs, I.sregs)
                earlier_not_issued_ists_dregs = utils.list_union(earlier_not_issued_ists_dregs, I.dregs)
                # cannot issue cases
                if PRE_ALU_not_empty or PRE_ALUB_not_empty or PRE_MEM_not_empty \
                    or RAW != [] or WAR != [] or WAW != [] or mem_not_in_order:
                    if I.name == 'SW':
                        has_earlier_not_issued_sw = True
                # can issue
                else:
                    issue_list.append(idx)
                    if I.name in ist.ALU_ISTS:
                        PRE_ALU_size += 1
                    elif I.name in ist.ALUB_ISTS:
                        PRE_ALUB_size += 1
                    else:
                        PRE_MEM_size += 1
        return issue_list
    
    # stage 3 of Execution of ALU / ALUB / MEM
    def EXE(self):
        return self.ALU(), self.ALUB(), self.MEM()
    
    def ALU(self):
        """ ALU operation """
        return self.queue_PRE_ALU != []

    def ALUB(self):
        """ ALUB operation """
        assert(self.ALUB_state == -1 or self.ALUB_state == 0 or self.ALUB_state == 1)
        if self.ALUB_state == 1:
            if self.queue_PRE_ALUB != []:
                self.ALUB_state = 0
            return False
        else:
            self.ALUB_state = 1
            return True

    def MEM(self):
        return self.queue_PRE_MEM != []
    
    # stage 4 of Write Back
    def WB(self):    
        return self.buffer_POST_ALU is not None, self.buffer_POST_ALUB is not None, self.buffer_POST_MEM is not None

    def update(self, fetched_ists, issued_ists_idx, executed, written_back):
        # issue
        for i in range(len(issued_ists_idx)):
            idx = issued_ists_idx[i] - i
            I = self.buffer_PRE_ISSUE[idx]
            # enqueue pre-ALU / pre-ALUB / pre-MEM
            if I.name in ist.ALU_ISTS:
                self.queue_PRE_ALU.append(I)
            elif I.name in ist.ALUB_ISTS:
                self.queue_PRE_ALUB.append(I)
            else:
                self.queue_PRE_MEM.append(I)
            # dequeue pre-issue 
            self.buffer_PRE_ISSUE.pop(idx)
        # IF
        for i in fetched_ists:
            # add pre-issue
            self.buffer_PRE_ISSUE.append(i) 
        # WB
        if written_back[0]:
            self.buffer_POST_ALU.WB()
            self.buffer_POST_ALU = None
        if written_back[1]:
            self.buffer_POST_ALUB.WB()
            self.buffer_POST_ALUB = None
        if written_back[2]:
            self.buffer_POST_MEM.WB()
            self.buffer_POST_MEM = None  
        # execute
        if executed[0]:
            self.buffer_POST_ALU = self.queue_PRE_ALU.pop(0)
        if executed[1]:
            self.buffer_POST_ALUB = self.queue_PRE_ALUB.pop(0)
        if executed[2]:
            I = self.queue_PRE_MEM.pop(0)
            if I.name == 'SW':
                I.WB()
                self.buffer_POST_MEM = None  
            else:
                self.buffer_POST_MEM = I
        
    def fetch_v2(self):
        addr = self.get_pc()
        idx = int((addr - self.START_PC) / 4) % len(self.ists)
        return self.ists[idx]

    def is_branch_waiting(self):
        return self.waiting_ist_IF is not None

    def is_branch_ready(self, I):
        if I.name == 'J': 
            return True
        tmp = self.get_unready_regs()
        for i in range(len(self.buffer_PRE_ISSUE)):
            tmp = utils.list_union(self.buffer_PRE_ISSUE[i].dregs, tmp)

        return utils.list_intersection(I.sregs, tmp) == []

    def exec_branch_IF(self, I):
        tmp = I.get_MIPS()
        # check branch is ready to execute
        if self.is_branch_ready(I):
            I.execute()
            return 'IF Unit:\n\tWaiting Instruction: \n\tExecuted Instruction: %s\n'%tmp
        else:
            self.waiting_ist_IF = I
            return 'IF Unit:\n\tWaiting Instruction: %s\n\tExecuted Instruction: \n'%tmp

    def get_unready_regs(self):
        ret = set()
        if self.buffer_POST_ALU:
            ret |= set(self.buffer_POST_ALU.dregs)
        if self.buffer_POST_ALUB:
            ret |= set(self.buffer_POST_ALUB.dregs) 
        if self.buffer_POST_MEM:
            ret |= set(self.buffer_POST_MEM.dregs) 
        
        for i in self.queue_PRE_ALU:
            ret = ret | set(i.dregs)
        for i in self.queue_PRE_ALUB:
            ret = ret | set(i.dregs)
        for i in self.queue_PRE_MEM:
            ret = ret | set(i.dregs)

        return list(ret)

    def get_queue_buffer_info(self, obj, obj_max_size):
        ret_str = ''  
        assert(obj != [])
        for idx, I in enumerate(obj):
            ret_str += '\tEntry %d:[%s]\n'%(idx, I.get_MIPS())
        for i in range(obj_max_size - len(obj)):
            ret_str += '\tEntry %d:\n'%(i+len(obj))
        return ret_str

    def get_reg_infos(self, begin, end):
        ret = ''
        for i in range(begin, end):
            ret += '\t' + str(self.get_reg_val(i))
        return ret

    def get_pre_issue_infos(self):
        ret_str = '\tEntry 0:\n\tEntry 1:\n\tEntry 2:\n\tEntry 3:\n' \
            if len(self.buffer_PRE_ISSUE) == 0 else self.get_queue_buffer_info(self.buffer_PRE_ISSUE, 4)
        return 'Pre-Issue Buffer:\n' + ret_str
            
    def get_buffer_queue_infos(self):  
        # pre-ALU 
        tmp = '\tEntry 0:\n\tEntry 1:\n' if len(self.queue_PRE_ALU) == 0 \
            else self.get_queue_buffer_info(self.queue_PRE_ALU, 2)
        ret_str = 'pre-ALU Queue:\n' + tmp
        # Post-ALU 
        ret_str += 'Post-ALU Buffer:%s\n'%('['+self.buffer_POST_ALU.get_MIPS()+']' \
            if self.buffer_POST_ALU is not None else '')
        # pre-ALUB
        tmp = '\tEntry 0:\n\tEntry 1:\n' if len(self.queue_PRE_ALUB) == 0 \
            else self.get_queue_buffer_info(self.queue_PRE_ALUB, 2)
        ret_str += 'pre-ALUB Queue:\n' + tmp
        # Post-ALUB 
        ret_str += 'Post-ALUB Buffer:%s\n'%('['+self.buffer_POST_ALUB.get_MIPS()+']' \
            if self.buffer_POST_ALUB is not None else '')
        # pre-MEM 
        tmp = '\tEntry 0:\n\tEntry 1:\n' if len(self.queue_PRE_MEM) == 0 \
            else self.get_queue_buffer_info(self.queue_PRE_MEM, 2)
        ret_str += 'pre-MEM Queue:\n' + tmp
        # Post-MEM 
        ret_str += 'Post-MEM Buffer:%s\n'%('['+self.buffer_POST_MEM.get_MIPS()+']' \
            if self.buffer_POST_MEM is not None else '')
        
        return ret_str