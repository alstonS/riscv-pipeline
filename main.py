import os
import argparse

MemSize = 1000 # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.

class InsMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        
        with open(ioDir + "/imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]

    def instrSize(self):
        return len(self.IMem)//4
    
    def readInstr(self, ReadAddress):
        #read instruction memory
        #return 32 bit hex val
        index = ReadAddress
        instr = ''.join(self.IMem[index:index+4])
        return instr
          
class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        self.DMem = ['00000000' for _ in range(1000)]
        #with open(ioDir + "/dmem.txt") as dm:
            #self.DMem = [data.replace("\n", "") for data in dm.readlines()]
        with open(ioDir + "/dmem.txt") as dm:
            for i, data in enumerate(dm.readlines()):
                if i < 1000:  # Ensure not to exceed the allocated 1000 bytes.
                    self.DMem[i] = data.strip()


    def readInstr(self, ReadAddress):
        #read data memory
        #return 32 bit hex val
        index = ReadAddress
        instr = ''.join(self.DMem[index:index+4])
        return instr
    
    def writeDataMem(self, Address, WriteData):
        parsedWriteData = [WriteData[i:i+8] for i in range(0, 32, 8)]
        #print(parsedWriteData)
        for i, split in enumerate(parsedWriteData):
            if Address+i >= len(self.DMem):
                raise IndexError(f"Attempt to write out of bounds. Address {Address+i} exceeds data memory size.")
            self.DMem[Address+i] = split
                     
    def outputDataMem(self):
        #resPath = self.ioDir + "\\" + self.id + "_DMEMResult.txt"
        resPath = os.path.join(self.ioDir, self.id + "_DMEMResult.txt")
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])

class RegisterFile(object):
    def __init__(self, ioDir):
        self.outputFile = ioDir + "RFResult.txt"
        #self.outputFile = os.path.join(ioDir, "RFResult.txt")
        self.Registers = ["00000000000000000000000000000000" for i in range(32)]
    
    def readRF(self, Reg_addr):
        # Fill in
        if 0 <= Reg_addr < len(self.Registers):
            return self.Registers[Reg_addr]
        else:
            print("Address cannot be negative or invalid register address: ", Reg_addr)
            return None
            
    def writeRF(self, Reg_addr, Wrt_reg_data):
        # Fill in

        # checking write data
        #binary_data = format(Wrt_reg_data, '032b')

        if 0 < Reg_addr < len(self.Registers):
            self.Registers[Reg_addr] = Wrt_reg_data
            #print("Register file:", self.Registers[Reg_addr])
        elif Reg_addr == 0:
            print("Cannot use register 0")
        else:
            print("Invalid register address: ", Reg_addr)
         
    def outputRF(self, cycle):
        op = ["-"*70 + "\n", "State of RF after executing cycle:" + str(cycle) + "\n"]
        for val in self.Registers:
            if isinstance(val, int):
                # Convert integer to a 32-bit binary string
                val_str = format(val, '032b')
            elif isinstance(val, str):
                val_str = val 
                assert len(val_str) == 32, "String value in Registers is not 32 bits."
            else:
                raise TypeError(f"Unsupported type in Registers: {type(val)}")
            op.append(val_str + "\n")
        
        if cycle == 0: perm = "w"
        else: perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)
            file.flush

class State(object):
    def __init__(self):
        self.IF = {"nop": False, "PC": 0, "instr_ctr": 0}
        self.ID = {"nop": False, "Instr": 0, "Branching": 0}
        self.EX = {"nop": False, "instr": 0, "Read_data1": "00000000000000000000000000000000", "Read_data2": "00000000000000000000000000000000",
                    "Imm": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "is_I_type": False, "rd_mem": 0, "wrt_mem": 0, "alu_op": 0, "wrt_enable": 0}
        self.MEM = {"nop": False, "ALUresult": 0, "Store_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "rd_mem": 0, 
                   "wrt_mem": 0, "wrt_enable": 0}
        self.WB = {"nop": False, "Wrt_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0}

class Core(object):
    def __init__(self, ioDir, imem, dmem):
        self.myRF = RegisterFile(ioDir)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem

class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        #super(SingleStageCore, self).__init__(ioDir + "\\SS_", imem, dmem)
        #self.opFilePath = ioDir + "\\StateResult_SS.txt"
        # Note the change here: not modifying ioDir anymore to append a directory
        super(SingleStageCore, self).__init__(ioDir + "/SS_", imem, dmem)
        # Directly appending "SS_" prefix to the filename instead of altering ioDir
        self.opFilePath = os.path.join(ioDir, "StateResult_SS.txt")

    def step(self):
        # Your implementation
        if self.state.IF["nop"]:
            # If in post-halt cycle, set halted to True and skip processing any instructions
            self.state.IF['instr_ctr'] += 1
            self.halted = True
        else:
            current_pc = self.state.IF['PC']
            instr = self.ext_imem.readInstr(current_pc)
            ins_decoded = self.decode(instr)
            incrementPC = True
            #print("PC: ",self.state.IF['PC'])
            #print("instruction: ", instr)
            if ins_decoded['type'] == "R":
                self.ALU(ins_decoded['funct3'], ins_decoded['funct7'], ins_decoded['rs2'], ins_decoded['rs1'], ins_decoded['rd'])
            elif ins_decoded['type'] == "I":
                self.immALU(ins_decoded['imm'], ins_decoded['funct3'], ins_decoded['rs1'], ins_decoded['rd'])
            elif ins_decoded['type'] == "L":
                self.loadWord(ins_decoded['imm'], ins_decoded['funct3'], ins_decoded['rs1'], ins_decoded['rd'])
            elif ins_decoded['type'] == "S":
                self.saveWord(ins_decoded['imm'], ins_decoded['funct3'], ins_decoded['rs2'], ins_decoded['rs1'])
            elif ins_decoded['type'] == "B":
                taken = self.branching(ins_decoded['imm'], ins_decoded['funct3'], ins_decoded['rs2'], ins_decoded['rs1'])
                if taken:
                    incrementPC = False
            elif ins_decoded['type'] == "J":
                self.jumpTo(ins_decoded['imm'], ins_decoded['rd'])
                incrementPC = False
            elif ins_decoded['type'] == "H":
                self.state.IF["nop"] = True
                incrementPC = False
            self.state.IF['instr_ctr'] += 1

            #print("Finished decode with opcode type: ", ins_decoded['type'])
            #print("Register file:", self.myRF.Registers[self.cycle])
            # increment PC

            if incrementPC:
                self.nextState.IF['PC'] = self.state.IF['PC'] + 4

        # if statements to pass to another function called ALU 
        # self.halted = True
        #if self.state.IF["nop"]:
            #self.halted = True

        
        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
        self.myRF.outputRF(self.cycle) # dump RF
        
        if not self.halted:
            self.state = self.nextState
        self.cycle += 1

        if self.halted:
            self.report_performance_metrics()

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")
        
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

    def decode(self, instruction):
        # instruction is 32 bit
        opcode = instruction[25:32]

        # R Type instruction
        if opcode == '0110011':
            funct3 = instruction[17:20]
            funct7 = instruction[0:7]
            rs2 = int(instruction[7:12], 2)
            rs1 = int(instruction[12:17], 2)
            rd = int(instruction[20:25], 2)
            return {'type': 'R', 
                    'funct3': funct3, 
                    'funct7': funct7, 
                    'rs2': rs2, 
                    'rs1': rs1,
                    'rd': rd}
        # I Type instructions and LW, uses same structure
        elif opcode == '0010011':
            imm = self.sign_extends(int(instruction[0:12], 2), 12)
            #imm = int(instruction[0:12], 2)
            rs1 = int(instruction[12:17], 2)
            rd = int(instruction[20:25], 2)
            funct3 = instruction[17:20]
            return {'type': 'I', 
                    'imm': imm, 
                    'rs1': rs1,
                    'rd': rd, 
                    'funct3': funct3}
        # Load word instruction
        elif opcode == '0000011':
            imm = self.sign_extends(int(instruction[0:12], 2), 12)
            #imm = int(instruction[0:12], 2)
            rs1 = int(instruction[12:17], 2)
            rd = int(instruction[20:25], 2)
            funct3 = instruction[17:20]
            return {'type': 'L', 
                    'imm': imm, 
                    'rs1': rs1,
                    'rd': rd, 
                    'funct3': funct3} 
        # SW instruction
        elif opcode == '0100011':  # S-type
            imm = self.sign_extends(int(instruction[0:7] + instruction[20:25], 2), 12)
            #imm = int(instruction[0:7] + instruction[20:25], 2)
            rs2 = int(instruction[7:12], 2)
            rs1 = int(instruction[12:17], 2)
            funct3 = instruction[17:20]
            return {'type': 'S',
                    'imm': imm,
                    'rs2': rs2, 
                    'rs1': rs1, 
                    'funct3': funct3}
        # Branch instructions 
        elif opcode == '1100011': 
            imm = self.sign_extends(int(instruction[0] + instruction[24] + instruction[1:7] + instruction[20:24] + "0", 2), 13)
            #imm = int(instruction[0] + instruction[24] + instruction[1:7] + instruction[20:24], 2)
            rs2 = int(instruction[7:12], 2)
            rs1 = int(instruction[12:17], 2)
            funct3 = instruction[17:20]
            return {'type': 'B', 
                    'imm': imm, 
                    'rs2': rs2, 
                    'rs1': rs1, 
                    'funct3': funct3}
        # Jump instruction
        elif opcode == '1101111':  # J-type (JAL)
            imm = self.sign_extends(int(instruction[0] + instruction[12:20] + instruction[11] + instruction[1:11] + "0", 2), 20)
            #imm = int(instruction[0] + instruction[12:20] + instruction[11] + instruction[1:11], 2)
            rd = int(instruction[20:25], 2)
            return {'type': 'J', 
                    'imm': imm, 
                    'rd': rd}
        # HALT all 1's
        elif opcode == '1111111':
            return {'type': 'H'}
        else:
            return {'type': 'unknown'}
        
    def sign_extends(self, value, bits):
        sign_bit = 1 << (bits - 1)
        # returns integer
        return (value & (sign_bit - 1)) - (value & sign_bit)
    
    def ALU(self, funct3, funct7, rs2, rs1, rd):
        #rs1_value = self.myRF.readRF(rs1)
        #s2_value = self.myRF.readRF(rs2)
       
        rs1_value = int(self.myRF.readRF(rs1), 2)  
        rs2_value = int(self.myRF.readRF(rs2), 2)
        if (funct3 == '000' and rs1_value & (1 << 31)):
            rs1_value -= (1 << 32)
        if (funct3 == '000' and rs2_value & (1 << 31)):
            rs2_value -= (1 << 32)
        result = 0
        # check funct3 for operation
        if funct3 == '000':
            # ADD
            if funct7 == '0000000':
                result = rs1_value + rs2_value
            elif funct7 == '0100000': # SUBTRACT
                result = rs1_value - rs2_value
        elif funct3 == '100': # XOR
            result = rs1_value ^ rs2_value
        elif funct3 == '110': # OR
            result = rs1_value | rs2_value
        elif funct3 == '111': # AND
            result = rs1_value & rs2_value

        result = result & 0xFFFFFFFF

        result_binary = format(result, '032b')

        self.myRF.writeRF(rd, result_binary)

    def immALU(self, imm, funct3, rs1, rd):
        rs1_value = int(self.myRF.readRF(rs1), 2)

        # Perform the operation.
        if funct3 == '000':  # ADDI, consider sign adjustments if necessary.
            # Adjust rs1_value if it's negative.
            if rs1_value & (1 << 31):
                rs1_value -= (1 << 32)
            result = rs1_value + imm
        elif funct3 == '100':  # XORI
            result = rs1_value ^ imm
        elif funct3 == '110':  # ORI
            result = rs1_value | imm
        elif funct3 == '111':  # ANDI
            result = rs1_value & imm

        if result < 0:
            result_binary = format(2**32 + result, '032b')
        else:
            result_binary = format(result, '032b')

        self.myRF.writeRF(rd, result_binary)

    def loadWord(self, imm, funct3, rs1, rd):
        base_address = int(self.myRF.readRF(rs1),2)

        #base_address = int(self.myRF.readRF(rs1), 2)
        effective_address = base_address + imm
        #print("the current effeective address: ", effective_address)
        data = self.ext_dmem.readInstr(effective_address)
        self.myRF.writeRF(rd, data)

    def saveWord(self, imm, funct3, rs2, rs1):
        base_address =int(self.myRF.readRF(rs1),2)
        effective_address = base_address + imm
        # Retrieve the data from rs2 register to store in memory
        data_to_store = self.myRF.readRF(rs2) 
        # Store the data memory addressm
        #print(data_to_store)
        self.ext_dmem.writeDataMem(effective_address, data_to_store)

    def branching(self, imm, funct3, rs2, rs1):
        #rs1_value = self.myRF.readRF(rs1) 
        #rs2_value = self.myRF.readRF(rs2)
        rs1_value = int(self.myRF.readRF(rs1), 2)  
        rs2_value = int(self.myRF.readRF(rs2), 2)
        branch_taken = False

        if funct3 == '001':  # BNE
            if rs1_value != rs2_value:
                branch_taken = True
        elif funct3 == '000':
            if rs1_value == rs2_value:
                branch_taken = True
        
        if branch_taken:
            self.state.IF['PC'] += imm
            return True

    def jumpTo(self, imm, rd):
        next_pc = self.state.IF['PC'] + 4  # Address of the next instruction
        target_address = self.state.IF['PC'] + imm  # Calculate target address
        #print(imm)
        #print(self.state.IF['PC'])
        # Store the address of the next instruction in the specified register
        self.myRF.writeRF(rd, next_pc)
        
        # Update PC to the target address
        self.nextState.IF['PC'] = target_address

    def report_performance_metrics(self):
        # Calculate performance metrics
        total_cycles = self.cycle
        #total_instructions = self.ext_imem.instrSize()
        total_instructions = self.state.IF['instr_ctr']
        #print(total_instructions)
        cpi = total_cycles / total_instructions if total_instructions else 0
        ipc = total_instructions / total_cycles if total_cycles else 0

        performance_data = (f"Performance of Single Stage:\n"
                            f"#Cycles -> {total_cycles}\n"
                            f"#Instructions -> {total_instructions}\n"
                            f"CPI -> {cpi}\n"
                            f"IPC -> {ipc}\n")

        # Write performance data to file
        performance_file_path = os.path.join(ioDir + "/" + "PerformanceMetrics.txt")
        with open(performance_file_path, "a") as perf_file:
            perf_file.write(performance_data)
        
        print(performance_data)

class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        #super(FiveStageCore, self).__init__(ioDir + "\\FS_", imem, dmem)
        #self.opFilePath = ioDir + "\\StateResult_FS.txt"
        super(FiveStageCore, self).__init__(ioDir + "/FS_", imem, dmem)
        self.opFilePath = os.path.join(ioDir, "StateResult_FS.txt")
        self.state.ID['nop'] = True
        self.state.EX['nop'] = True
        self.state.MEM['nop'] = True
        self.state.WB['nop'] = True

    def step(self):
        # Your implementation
        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
            self.halted = True
            #self.state.IF['instr_ctr'] += 1
            #self.report_performance_metrics()
        else:
            # --------------------- WB stage ---------------------
            # self.WB = {"nop": False, "Wrt_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0}
            if self.state.WB['nop'] == False:
                if self.state.WB['wrt_enable'] == 1:
                    data = self.state.WB['Wrt_data']
                    rd = int(self.state.WB['Wrt_reg_addr'],2)
                    self.myRF.writeRF(rd, data)
                    #print("data into RF " ,data)
                    #print("RF1", self.myRF.readRF(1))
                    #print("RF2", self.myRF.readRF(2))
            elif self.state.WB['nop'] != False:
                if self.state.MEM['nop'] != True:
                    self.state.WB['nop'] = False 

            
            # --------------------- MEM stage --------------------
            if self.state.MEM['nop'] == False:
                if self.state.MEM['wrt_mem'] == 1: # typically only save word
                    effective_address= self.state.MEM['ALUresult']
                    data_to_store = self.state.MEM['Store_data']
                    #print(effective_address)
                    #print(data_to_store)
                    self.ext_dmem.writeDataMem(effective_address, data_to_store)
                    self.nextState.WB['Wrt_data'] = self.state.MEM['ALUresult']
                    self.nextState.WB['Rs'] = self.state.MEM['Rs']
                    self.nextState.WB['Rt'] = self.state.MEM['Rt']
                    self.nextState.WB['Wrt_reg_addr'] = "00000"
                    self.nextState.WB['wrt_enable'] = 0
                    self.state.WB['nop'] == False
                else: 
                    self.nextState.WB['Wrt_data'] = self.state.MEM['ALUresult']
                    self.nextState.WB['Rs'] = self.state.MEM['Rs']
                    self.nextState.WB['Rt'] = self.state.MEM['Rt']
                    self.nextState.WB['Wrt_reg_addr'] = self.state.MEM['Wrt_reg_addr']
                    self.nextState.WB['wrt_enable'] = self.state.MEM['wrt_enable']
                    self.state.WB['nop'] == False
                    pass
            elif self.state.MEM['nop'] != False:
                self.state.WB['nop'] = True
                if self.state.IF['nop'] != True:
                    self.state.MEM['nop'] = False
                pass
            
            
            # --------------------- EX stage ---------------------
            if self.state.EX['nop'] == False:
                instruction = self.state.EX['instr']
                opcode = instruction[25:32]
                #print("here is the instruction in R type:", instruction)
                
                # R - Type instructions 
                if opcode == "0110011":
                    funct3 = instruction[17:20]
                    funct7 = instruction[0:7]
                    #print("inside the ADD in EX", int(self.state.EX['Read_data1'],2))
                    rs1_value = int(self.state.EX['Read_data1'],2)
                    rs2_value = int(self.state.EX['Read_data2'],2)
                    if funct3 == "000": # add / subtract
                        if (rs1_value & (1 << 31)):
                            rs1_value -= (1 << 32)
                        if (rs2_value & (1 << 31)):
                            rs2_value -= (1 << 32)
                        result = 0
                        if funct7 == '0000000': # add
                            result = rs1_value + rs2_value
                        elif funct7 == '0100000': #substract
                            result = rs1_value - rs2_value
                    elif funct3 == "100": #XOR
                        result = rs1_value ^ rs2_value
                    elif funct3 == "110": #OR
                        result = rs1_value | rs2_value
                    elif funct3 == "111": #AND
                        result = rs1_value & rs2_value
                    result_binary = format(result & 0xFFFFFFFF, '032b')
                    self.nextState.MEM['ALUresult'] = result_binary
                    self.nextState.MEM['Store_data'] = '00000000000000000000000000000000'
                    self.nextState.MEM['Rs'] = self.state.EX['Rs']
                    self.nextState.MEM['Rt'] = self.state.EX['Rt']
                    self.nextState.MEM['rd_mem'] = self.state.EX['rd_mem']
                    self.nextState.MEM['wrt_mem'] = self.state.EX['wrt_mem']
                    self.nextState.MEM['wrt_enable'] = self.state.EX['wrt_enable']
                    self.nextState.MEM['Wrt_reg_addr'] = self.state.EX['Wrt_reg_addr']
                    self.nextState.MEM['nop'] = False

                elif opcode == "0010011": # IMM instructions
                    rs1_value = int(self.state.EX['Read_data1'], 2)
                    # self.state.EX['Imm'] is a 12 bit binary 
                    # sign_extends return an integer
                    funct3 = instruction[17:20]
                    imm = self.sign_extends(int(self.state.EX['Imm'], 2), 12)
                    if funct3 == "000":  # ADDI
                        if rs1_value & (1 << 31):
                            rs1_value -= (1 << 32)
                        result = rs1_value + imm
                    elif funct3 == "100":  # XORI
                        result = rs1_value ^ imm
                    elif funct3 == "110":  # ORI
                        result = rs1_value | imm
                    elif funct3 == "111":  # ANDI
                        result = rs1_value & imm
                    result_binary = format(result & 0xFFFFFFFF, '032b')
                    self.nextState.MEM['ALUresult'] = result_binary
                    self.nextState.MEM['Store_data'] = '00000000000000000000000000000000'
                    self.nextState.MEM['Rs'] = self.state.MEM['Rs']
                    self.nextState.MEM['Rt'] = self.state.MEM['Rt'] # not used
                    self.nextState.MEM['rd_mem'] = self.state.EX['rd_mem']
                    self.nextState.MEM['wrt_mem'] = self.state.EX['wrt_mem']
                    self.nextState.MEM['wrt_enable'] = self.state.EX['wrt_enable']
                    self.nextState.MEM['Wrt_reg_addr'] = self.state.EX['Wrt_reg_addr']
                    self.nextState.MEM['nop'] = False
                elif opcode == "1101111": # JAL
                    int_value = self.sign_extends(int(self.state.EX['Imm'] , 2), 21)
                    result = self.state.IF['PC'] - int_value
                    result_binary = format(result & 0xFFFFFFFF, '032b')

                    self.nextState.MEM['ALUresult'] = result_binary
                    self.nextState.MEM['Store_data'] = '00000000000000000000000000000000'
                    self.nextState.MEM['Rs'] = self.state.MEM['Rs']
                    self.nextState.MEM['Rt'] = self.state.MEM['Rt'] # Not used
                    self.nextState.MEM['rd_mem'] = self.state.EX['rd_mem']
                    self.nextState.MEM['wrt_mem'] = self.state.EX['wrt_mem']
                    self.nextState.MEM['wrt_enable'] = self.state.EX['wrt_enable']
                    self.nextState.MEM['Wrt_reg_addr'] = self.state.EX['Wrt_reg_addr']
                    self.nextState.MEM['nop'] = False
                elif opcode == "1100011": # BNE / BEQ
                    funct3 = instruction[17:20]
                    # the branching is done in ID stage
                    self.nextState.MEM['ALUresult'] = '00000000000000000000000000000000'
                    self.nextState.MEM['Store_data'] = '00000000000000000000000000000000'
                    self.nextState.MEM['Rs'] = self.state.EX['Rs'] # not used
                    self.nextState.MEM['Rt'] = self.state.EX['Rt'] # not used
                    self.nextState.MEM['rd_mem'] = self.state.EX['rd_mem']
                    self.nextState.MEM['wrt_mem'] = self.state.EX['wrt_mem']
                    self.nextState.MEM['wrt_enable'] = self.state.EX['wrt_enable']
                    self.nextState.MEM['Wrt_reg_addr'] = '00000'
                    self.nextState.MEM['nop'] = False
                    if funct3 == "000": #BEQ
                        pass
                    elif funct3 == "001": #BNE
                        pass
                elif opcode == "0000011": #LW
                    base_address = int(self.state.EX['Read_data1'],2)
                    immd = self.sign_extends(int(self.state.EX['Imm'], 2), 12)
                    result = base_address + immd
                    data = self.ext_dmem.readInstr(result)
                    self.nextState.MEM['ALUresult'] = data
                    self.nextState.MEM['Store_data'] = '00000000000000000000000000000000'
                    self.nextState.MEM['Rs'] = self.state.EX['Rs'] 
                    # LW only has rs1 or Rs and the RD
                    self.nextState.MEM['Rt'] = self.state.MEM['Rt'] # not used
                    self.nextState.MEM['rd_mem'] = self.state.EX['rd_mem']
                    self.nextState.MEM['wrt_mem'] = self.state.EX['wrt_mem']
                    self.nextState.MEM['wrt_enable'] = self.state.EX['wrt_enable']
                    self.nextState.MEM['Wrt_reg_addr'] = self.state.EX['Wrt_reg_addr']
                    self.nextState.MEM['nop'] = False
                elif opcode == "0100011": #SW
                    rs1_value = int(self.state.EX['Read_data1'],2)
                    rs2_value = int(self.state.EX['Read_data2'],2)
                    base_address = int(self.state.EX['Read_data1'],2)
                    immd = self.sign_extends(int(self.state.EX['Imm'], 2), 12)
                    effective_address = base_address + immd
                    # Retrieve the data from rs2 register to store in memory
                    data_to_store = self.state.EX['Read_data2']
                    #print(data_to_store)
                    #result_binary = format(data_to_store & 0xFFFFFFFF, '032b')
                    # Store the data memory addressm
                    # print(data_to_store)
                    # self.ext_dmem.writeDataMem(effective_address, data_to_store)
                    #print(data_to_store)
                    self.nextState.MEM['ALUresult'] = effective_address
                    self.nextState.MEM['Store_data'] = data_to_store
                    self.nextState.MEM['Rs'] = self.state.EX['Rs'] 
                    # LW only has rs1 or rs2 and not the RD
                    self.nextState.MEM['Rt'] = self.state.EX['Rt']
                    self.nextState.MEM['rd_mem'] = self.state.EX['rd_mem']
                    self.nextState.MEM['wrt_mem'] = self.state.EX['wrt_mem']
                    self.nextState.MEM['wrt_enable'] = self.state.EX['wrt_enable']
                    self.nextState.MEM['Wrt_reg_addr'] = self.state.MEM['Wrt_reg_addr'] # not used
                    self.nextState.MEM['nop'] = False
            else:
                # If there is a nop we want to pass it on to next stage and skip whatever is in the if 
                self.nextState.MEM['nop'] = True
                if self.state.IF['nop'] != True:
                    self.nextState.EX['nop'] = False        
            
            # --------------------- ID stage ---------------------
            if self.state.ID['nop'] == False:
                # Since this ID stage is executed after MEM and EX we can check if the resulting 
                # values are used in this new ID stage, so we can use fowarding.
                # 
                # We need to also check for a load use hazard, other than that we can directly foward
                # To check for a load use hazard, we need to identify if the previous instruction is a LW 
                # if it is and we find that the results are used in the next, we need to NOP the EX stage once
                # Once we nop the instruction, we will skip the EX stage, so next time when we come to ID again 
                # we will remove the NOP so that next cycle we will have an EX stage. 
                # In the EX stage where we NOPPED, we need to NOP the next MEM in the next cycle since there wont
                # be any values because of the EX Nop.
                #
                # instruction decode
                # check for forwarding by looking at rs and rt and inside EX/MEM and MEM/WB stage for register
                #self.IF = {"nop": False, "PC": 0, "instr_ctr": 0}
                #self.ID = {"nop": False, "Instr": 0}
                #self.EX = {"nop": False, "Read_data1": 0, "Read_data2": 0, "Imm": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "is_I_type": False, "rd_mem": 0, 
                #       "wrt_mem": 0, "alu_op": 0, "wrt_enable": 0}
                #self.MEM = {"nop": False, "ALUresult": 0, "Store_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "rd_mem": 0, 
                #       "wrt_mem": 0, "wrt_enable": 0}
                #self.WB = {"nop": False, "Wrt_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0}

                # check if rs and rt equals the write destination of previous 

                instr = self.state.ID['Instr'] 
                decoded = self.decode(instr)
                opcode = decoded['opcode']
                #print(opcode)
                hazard_flag = False
                fowarding_flag = False
                fowarding_flag2 = False
                # Here is checking for load use hazards
                if self.nextState.EX['rd_mem'] == 1: # when there is a read to mem we need to check for hazard

                    if (opcode == '0110011' or opcode == '1100011' or opcode == '0100011'):
                        if (self.nextState.EX['Wrt_reg_addr'] == decoded['rs1']) or  (self.nextState.EX['Wrt_reg_addr'] == decoded['rs2']):
                            self.nextState.EX['nop'] = True
                            self.state.IF['PC'] =  self.state.IF['PC'] - 4
                            hazard_flag = True
                    elif opcode == '0010011' or opcode == '0000011':
                        if (self.nextState.EX['Wrt_reg_addr'] == decoded['rs1']):
                            self.nextState.EX['nop'] = True
                            self.state.IF['PC'] =  self.state.IF['PC'] - 4
                            hazard_flag = True
                # not imm or jal or lw, check if the RT of mem or wb 
                # if opcode is add, branch instr, or save word
                if (opcode == '0110011' or opcode == '1100011' or opcode == '0100011'):
                    # seperate the two if statements for rs1 and rs2 only one will transfers
                    # We check the next state's MEM and WB since we already computed those right above
                    # Compare it to current ID to determine what NEXT EX values are
                    #print("MEM stage wtr_reg" ,self.nextState.MEM['Wrt_reg_addr'])
                    #print("WB stage wtr_reg" ,self.nextState.WB['Wrt_reg_addr'])
                    #print("rs1", decoded['rs1'])
                    #print("rs2", decoded['rs2'])
                    if self.nextState.MEM['Wrt_reg_addr'] == decoded['rs1']:
                        fowarding_flag = True
                        self.nextState.EX['Read_data1'] = self.state.MEM['ALUresult']
                        if opcode == "1100011":
                            pass
                        #print("Accessed the Fowarding EXR1", self.nextState.EX['Read_data1'] )
                    if self.nextState.MEM['Wrt_reg_addr'] == decoded['rs2']:
                        fowarding_flag2 = True
                        self.nextState.EX['Read_data2'] = self.state.MEM['ALUresult']
                        if opcode == "1100011":
                            pass
                        #print("Accessed the Fowarding EXR2", self.nextState.EX['Read_data2'] )
                    if self.nextState.WB['Wrt_reg_addr'] == decoded['rs1']:
                        fowarding_flag = True
                        self.nextState.EX['Read_data1'] = self.state.WB['Wrt_data']
                        if opcode == "1100011":
                            pass
                        #print("Accessed the Fowarding WBR1", self.nextState.EX['Read_data1'] )
                    if self.nextState.WB['Wrt_reg_addr'] == decoded['rs2']:
                        fowarding_flag2 = True
                        self.nextState.EX['Read_data2'] = self.state.WB['Wrt_data']
                        if opcode == "1100011":
                            pass
                        #print("Accessed the Fowarding WBR2", self.nextState.EX['Read_data2'] )
                elif opcode == '0010011' or opcode == '0000011': # imm  or lw instrs that uses rs1
                    if self.nextState.MEM['Wrt_reg_addr'] == decoded['rs1']:
                        fowarding_flag = True
                        self.nextState.EX['Read_data1'] = self.state.MEM['ALUresult']
                        if opcode == "1100011":
                            pass
                        #print("Accessed the Fowarding ", self.nextState.EX['Read_data1'] )
                    elif self.nextState.WB['Wrt_reg_addr'] == decoded['rs1']:
                        fowarding_flag = True
                        self.nextState.EX['Read_data1'] = self.state.WB['Wrt_data']
                        if opcode == "1100011":
                            pass
                        #print("Accessed the Fowarding ", self.nextState.EX['Read_data1'] )
                # Features:
                # We have the forwarding complete to my knowledge
                # We need to figure out if Load Use Hazard to NOP
                # Then we need to figure out branching NOPS
                # 
                # R type instructions rd/wrt mem are both off, not i type
                if opcode == '0110011': # add/sub/xor/or/and check funct3
                    self.nextState.EX['instr'] = self.state.ID['Instr']
                    self.nextState.EX['Rs'] = decoded['rs1']
                    self.nextState.EX['Rt'] = decoded['rs2']
                    self.nextState.EX['Wrt_reg_addr'] = decoded['rd']
                    self.nextState.EX['is_I_type'] = 0
                    self.nextState.EX['rd_mem'] = 0
                    self.nextState.EX['wrt_mem'] = 0 
                    self.nextState.EX['wrt_enable'] = 1
                    self.nextState.EX['alu_op'] = 10
                    self.nextState.EX['Imm'] = self.sign_extendsBin(int(decoded['funct7'],2),12)
                    #print("inside R", self.nextState.EX['Read_data1'])
                    #print("inside R", self.nextState.EX['Read_data2'])
                    if fowarding_flag == False:
                        self.nextState.EX['Read_data1'] = self.myRF.readRF(int(decoded['rs1'],2))
                    if fowarding_flag2 == False:
                        self.nextState.EX['Read_data2'] = self.myRF.readRF(int(decoded['rs2'],2))
                    if hazard_flag == False:
                        self.nextState.EX['nop'] = False
                    #print("printed out readdata1" ,self.nextState.EX['Read_data1'])
                    #print("printed out readdata2" , self.nextState.EX['Read_data2'])
                    
                elif opcode == '0010011': # immediate adds
                    self.nextState.EX['instr'] = self.state.ID['Instr']
                    self.nextState.EX['Rs'] = decoded['rs1']
                    self.nextState.EX['Rt'] = self.state.EX['Rt'] # not used
                    self.nextState.EX['Wrt_reg_addr'] = decoded['rd']
                    self.nextState.EX['is_I_type'] = 1
                    self.nextState.EX['rd_mem'] = 0
                    self.nextState.EX['wrt_mem'] = 0 
                    self.nextState.EX['wrt_enable'] = 1
                    self.nextState.EX['alu_op'] = 00
                    self.nextState.EX['Imm'] = decoded['imm']
                    if fowarding_flag == False:
                        self.nextState.EX['Read_data1'] = self.myRF.readRF(int(decoded['rs1'],2))
                        # No read_data2
                    if hazard_flag == False:
                        self.nextState.EX['nop'] = False

                elif opcode == '1101111': #Jump and Link, store the PC + 4, current PC, did not reach IF yet
                    self.nextState.EX['instr'] = self.state.ID['Instr']
                    self.nextState.EX['Rs'] = self.state.EX['Rs'] # not used 
                    self.nextState.EX['Rt'] = self.state.EX['Rt'] # not used
                    self.nextState.EX['Wrt_reg_addr'] = decoded['rd']
                    self.nextState.EX['is_I_type'] = 1
                    self.nextState.EX['rd_mem'] = 0
                    self.nextState.EX['wrt_mem'] = 0 
                    self.nextState.EX['wrt_enable'] = 1
                    self.nextState.EX['alu_op'] = 00
                    self.nextState.EX['Imm'] = decoded['imm'] # 21 bits
                    int_value = self.sign_extends(int(decoded['imm'] , 2), 21)
                    self.state.IF['PC'] = self.state.IF['PC'] - 4 + int_value
                    if hazard_flag == False:
                        self.nextState.EX['nop'] = False

                elif opcode == '1100011': #Branching
                    # need to implement branch prediction 
                    # Will complete all opcode are done + load use solution
                    # Need to look at funct3 for BEQ or BNE
                    # first we need to compare then branch or stay same.
                    #rs1 is rs2??? 
                    #print(decoded['rs1'])
                    #print(decoded['rs2'])
                    self.nextState.EX['instr'] = self.state.ID['Instr']
                    self.nextState.EX['Rs'] = decoded['rs1'] # not used 
                    self.nextState.EX['Rt'] = decoded['rs2'] # not used
                    self.nextState.EX['Wrt_reg_addr'] = self.state.EX['Wrt_reg_addr']
                    self.nextState.EX['is_I_type'] = 0
                    self.nextState.EX['rd_mem'] = 0
                    self.nextState.EX['wrt_mem'] = 0 
                    self.nextState.EX['wrt_enable'] = 0
                    self.nextState.EX['alu_op'] = 00
                    self.nextState.EX['Imm'] = decoded['immBin'] # Binary
                    ImmBinary = decoded['imm'] # deicmal used for branching
                    funct3 = decoded['funct3']
                    #print(fowarding_flag)
                    #print(fowarding_flag2)
                    if fowarding_flag == False:
                        self.nextState.EX['Read_data1'] = self.myRF.readRF(int(decoded['rs2'],2))
                    if fowarding_flag2 == False:
                        self.nextState.EX['Read_data2'] = self.myRF.readRF(int(decoded['rs1'],2))
                    #print(self.myRF.readRF(int(decoded['rs1'],2)))
                    #print(self.myRF.readRF(int(decoded['rs2'],2)))

                    # Now we need to perform branch prediction and set the correct PC & nops
                    # This point we have the binary values of rs1 and rs2, compare them
                    # then jump or not depending on opcode 
                    rs1_value = int(self.state.EX['Read_data1'],2)
                    rs2_value = int(self.state.EX['Read_data2'],2)
                    #print(rs1_value)
                    #print(rs2_value)
                    # 000 is BEQ and 001 is BNE 
                    # This if statement will be true then it will branch covering both BEQ and BNE
                    if (rs1_value == rs2_value and funct3 == '000') or (rs1_value != rs2_value and funct3 == '001'):
                        # set nop on ID and EX, and update IF to imm + pc
                        self.state.ID['Branching'] = 1
                        self.nextState.ID['nop'] = True
                        self.nextState.EX['nop'] = True
                        self.nextState.IF['PC'] = self.state.IF['PC'] - 4 + ImmBinary
                        self.state.IF['instr_ctr'] += 1
                        #print(self.nextState.IF['PC'])
                    else: 
                        # setting PC to PC + 4 which is do nothing because program flows normally
                        if hazard_flag == False and self.state.ID['Branching'] == 0:
                            self.nextState.EX['nop'] = True
                elif opcode == '0000011': #load word
                    self.nextState.EX['instr'] = self.state.ID['Instr']
                    self.nextState.EX['Rs'] = decoded['rs1']
                    self.nextState.EX['Rt'] = self.state.EX['Rt'] # not used
                    self.nextState.EX['Wrt_reg_addr'] = decoded['rd']
                    self.nextState.EX['is_I_type'] = 1
                    self.nextState.EX['rd_mem'] = 1
                    self.nextState.EX['wrt_mem'] = 0 
                    self.nextState.EX['wrt_enable'] = 1
                    self.nextState.EX['alu_op'] = 00
                    self.nextState.EX['Imm'] = decoded['imm'] # 12 bit binary
                    if fowarding_flag == False:
                        self.nextState.EX['Read_data1'] = self.myRF.readRF(int(decoded['rs1'],2))
                        # No read_data2
                    if hazard_flag == False:
                        self.nextState.EX['nop'] = False
                elif opcode == '0100011': #store word
                    self.nextState.EX['instr'] = self.state.ID['Instr']
                    #print(decoded['rs1'])
                    #print(decoded['rs2'])
                    self.nextState.EX['Rs'] = decoded['rs1']
                    self.nextState.EX['Rt'] = decoded['rs2']
                    self.nextState.EX['Wrt_reg_addr'] = "00000"
                    self.nextState.EX['is_I_type'] = 1
                    self.nextState.EX['rd_mem'] = 0
                    self.nextState.EX['wrt_mem'] = 1
                    self.nextState.EX['wrt_enable'] = 0 # does not write to register 
                    self.nextState.EX['alu_op'] = 00
                    self.nextState.EX['Imm'] = self.sign_extendsBin(int(decoded['imm'],2),12)

                    #print(self.nextState.EX['Read_data2'])
                    #print(int(decoded['rs1'],2))
                    if fowarding_flag == False:
                        self.nextState.EX['Read_data1'] = self.myRF.readRF(int(decoded['rs1'],2))
                    if fowarding_flag2 == False:
                        self.nextState.EX['Read_data2'] = self.myRF.readRF(int(decoded['rs2'],2))
                    if hazard_flag == False:
                        self.nextState.EX['nop'] = False
                    #print(self.nextState.EX['Read_data1'])
                    #print(self.nextState.EX['Read_data2'])
                elif opcode == '1111111': #halt
                    self.nextState.ID['nop'] = True
                    self.nextState.IF['nop'] = True
            else:
                self.nextState.EX['nop'] = True
                self.state.ID['Branching'] = 0
                if self.state.IF['nop'] == False:
                    self.nextState.ID['nop'] == False
            
            # --------------------- IF stage ---------------------
            if self.state.IF['nop'] == False and self.state.ID['Branching'] == 0:
                program_counter = self.state.IF['PC']
                self.state.IF['instr_ctr'] += 1
                instr = self.ext_imem.readInstr(program_counter)
                if instr == "11111111111111111111111111111111":
                    self.nextState.ID['nop'] = True
                    self.nextState.IF['nop'] = True
                else:
                    self.nextState.ID['Instr'] = instr
                    self.nextState.IF['PC'] = self.state.IF['PC'] + 4
                    self.nextState.ID['nop'] = False
            # self.halted = True
            # if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
                #3self.halted = True            
        #self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
        self.myRF.outputRF(self.cycle)

        self.state = self.nextState #The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1
        if self.halted:
            pass
            self.report_performance_metrics()

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.extend(["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()])
        printstate.extend(["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()])
        printstate.extend(["EX." + key + ": " + str(val) + "\n" for key, val in state.EX.items()])
        printstate.extend(["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()])
        printstate.extend(["WB." + key + ": " + str(val) + "\n" for key, val in state.WB.items()])

        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

    def decode(self, instruction):
        # instruction is 32 bit
        opcode = instruction[25:32]

        # R Type instruction
        if opcode == '0110011':
            funct3 = instruction[17:20]
            funct7 = instruction[0:7]
            rs2 = instruction[7:12]
            rs1 = instruction[12:17]
            rd = instruction[20:25]
            return {'opcode': opcode, 
                    'funct3': funct3, 
                    'funct7': funct7, 
                    'rs2': rs2, 
                    'rs1': rs1,
                    'rd': rd}
        # I Type instructions and LW, uses same structure
        elif opcode == '0010011':
            imm_bin = instruction[0:12]
            imm = self.sign_extends(int(instruction[0:12], 2), 12)
            #imm = int(instruction[0:12], 2)
            rs1 = instruction[12:17]
            rd = instruction[20:25]
            funct3 = instruction[17:20]
            return {'opcode': opcode, 
                    'imm': imm_bin, 
                    'rs1': rs1,
                    'rd': rd, 
                    'funct3': funct3}
        # Load word instruction
        elif opcode == '0000011':
            imm_bin = instruction[0:12]
            imm = self.sign_extends(int(instruction[0:12], 2), 12)
            #imm = int(instruction[0:12], 2)
            rs1 = instruction[12:17]
            rd = instruction[20:25]
            funct3 = instruction[17:20]
            return {'opcode': opcode, 
                    'imm': imm_bin, 
                    'rs1': rs1,
                    'rd': rd, 
                    'funct3': funct3} 
        # SW instruction
        elif opcode == '0100011':  # S-type
            imm_bin = instruction[0:7] + instruction[20:25]
            imm = self.sign_extends(int(instruction[0:7] + instruction[20:25], 2), 12)
            #imm = int(instruction[0:7] + instruction[20:25], 2)
            rs2 = instruction[7:12]
            rs1 = instruction[12:17]
            funct3 = instruction[17:20]
            return {'opcode': opcode,
                    'imm': imm_bin,
                    'rs2': rs2, 
                    'rs1': rs1, 
                    'funct3': funct3}
        # Branch instructions 
        elif opcode == '1100011': 
            imm_bin = instruction[0] + instruction[24] + instruction[1:7] + instruction[20:24] + "0"
            imm = self.sign_extends(int(instruction[0] + instruction[24] + instruction[1:7] + instruction[20:24] + "0", 2), 13)
            #imm = int(instruction[0] + instruction[24] + instruction[1:7] + instruction[20:24], 2)
            rs2 = instruction[7:12]
            rs1 = instruction[12:17]
            funct3 = instruction[17:20]
            return {'opcode': opcode, 
                    'imm': imm,
                    'immBin': imm_bin, 
                    'rs2': rs2, 
                    'rs1': rs1, 
                    'funct3': funct3}
        # Jump instruction
        elif opcode == '1101111':  # J-type (JAL)
            imm_bin = instruction[0] + instruction[12:20] + instruction[11] + instruction[1:11] + "0"
            imm = self.sign_extends(int(instruction[0] + instruction[12:20] + instruction[11] + instruction[1:11] + "0", 2), 21)
            #imm = int(instruction[0] + instruction[12:20] + instruction[11] + instruction[1:11], 2)
            rd = instruction[20:25]
            return {'opcode': opcode, 
                    'imm': imm_bin, 
                    'rd': rd}
        # HALT all 1's
        elif opcode == '1111111':
            return {'opcode': opcode}
        else:
            return {'opcode': 'unknown'}
        
    def sign_extends(self, value, bits):
        sign_bit = 1 << (bits - 1)
        # returns integer
        return (value & (sign_bit - 1)) - (value & sign_bit)

    def sign_extendsBin(self, value, bits):
        sign_bit = 1 << (bits - 1)
        extended_value = (value & (sign_bit - 1)) - (value & sign_bit)
        # Convert to binary with 'bits' length, removing the '0b' prefix
        binary_string = format(extended_value & ((1 << bits) - 1), '0{}b'.format(bits))
        return binary_string
    
    def report_performance_metrics(self):
        # Calculate performance metrics
        total_cycles = self.cycle
        #total_instructions = self.ext_imem.instrSize()
        total_instructions = self.state.IF['instr_ctr']
        #print(total_instructions)
        cpi = total_cycles / total_instructions if total_instructions else 0
        ipc = total_instructions / total_cycles if total_cycles else 0

        performance_data = (f"\nPerformance of Five Stage:\n"
                            f"#Cycles -> {total_cycles}\n"
                            f"#Instructions -> {total_instructions}\n"
                            f"CPI -> {cpi}\n"
                            f"IPC -> {ipc}")

        # Write performance data to file
        performance_file_path = os.path.join(ioDir + "/" + "PerformanceMetrics.txt")
        #with open(performance_file_path, "w") as perf_file:
            #perf_file.write(performance_data)
        with open(performance_file_path, "a") as perf_file:
            perf_file.write(performance_data)
        
        print(performance_data)
   

if __name__ == "__main__":
     
    #parse arguments for input file location
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="", type=str, help='Directory containing the input files.')
    args = parser.parse_args()

    ioDir = os.path.abspath(args.iodir)
    print("IO Directory:", ioDir)
 
    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir)
    dmem_fs = DataMem("FS", ioDir)
    
    ssCore = SingleStageCore(ioDir, imem, dmem_ss)
    fsCore = FiveStageCore(ioDir, imem, dmem_fs)
    #ssCore.myRF.outputRF(0)
    while(True):
        if not ssCore.halted:
            ssCore.step()
        
        if not fsCore.halted:
            fsCore.step()

        if ssCore.halted and fsCore.halted:
            break
    
    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()