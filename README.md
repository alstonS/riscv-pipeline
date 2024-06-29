# RISC-V Multistage Pipeline Project

## Overview

This project simulates a RISC-V multistage pipeline processor that executes 32-bit RISC-V instructions. The processor reads instructions from an instruction memory file (`imem`) and data from a data memory file (`dmem`), both in binary format. It performs arithmetic and memory operations as specified by the instructions, and outputs cycle-by-cycle state results, register file contents, and the final state of the data memory.

## Features

- **Multistage Pipeline**: Implements Fetch, Decode, Execute, Memory Access, and Write-back stages.
- **Instruction Memory (`imem`)**: Reads instructions in binary format.
- **Data Memory (`dmem`)**: Reads initial data and stores results post-execution.
- **Cycle-by-Cycle Output**: Provides state results and register file updates per cycle.
- **Final Memory State**: Outputs the final state of `dmem` after instruction execution.

