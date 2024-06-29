# RISC-V Multistage Pipeline Project

## Overview

This project simulates a RISC-V multistage pipeline processor that executes 32-bit RISC-V instructions. The processor reads instructions from an instruction memory file (`imem`) and data from a data memory file (`dmem`), both in binary format. It performs arithmetic and memory operations as specified by the instructions, and outputs cycle-by-cycle state results, register file contents, and the final state of the data memory.

## Features

- **Multistage Pipeline**: Implements Fetch, Decode, Execute, Memory Access, and Write-back stages.
- **Instruction Memory (`imem`)**: Reads instructions in binary format.
- **Data Memory (`dmem`)**: Reads initial data and stores results post-execution.
- **Cycle-by-Cycle Output**: Provides state results and register file updates per cycle.
- **Final Memory State**: Outputs the final state of `dmem` after instruction execution.

## Usage

The imem.txt file is used to initialize the instruction memory and the dmem.txt file is used to initialize the
data memory of the processor. Each line in the files contain a byte of data on the instruction or the data
memory and both the instruction and data memory are byte addressable. This means that for a 32 bit
processor, 4 lines in the imem.txt file makes one instruction. Both instruction and data memory are in
“Big-Endian” format (the most significant byte is stored in the smallest address).

## RISC-V Stages

The simulator should have the following five stages in its pipeline:
- **Instruction Fetch**: Fetches instruction from the instruction memory using PC value as address.
- **Instruction Decode/ Register Read**: Decodes the instruction using the format in the table above
and generates control signals and data signals after reading from the register file.
- **Execute**: Perform operations on the data as directed by the control signals.
- **Load/ Store**: Perform memory related operations.
- **Writeback**: Write the result back into the destination register.

## Run the Simulation:
python main.py -iodir <path_to_input_output_directory>
