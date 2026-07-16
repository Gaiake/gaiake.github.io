# HW2 Answer

## (1) Necessary ports and signals

### Data memory

The data memory is used by `lw` and `sw`.

| Port / signal | Direction | Meaning |
| --- | --- | --- |
| `Addr` | input | Data memory address. For `lw` and `sw`, this comes from `imm`. |
| `WriteData` | input | Data written to memory. For `sw`, this comes from `Reg[ri]`. |
| `ReadData` | output | Data read from memory. For `lw`, this is written back to `Reg[ri]`. |
| `MemRead` | input control | Enabled for `lw`. |
| `MemWrite` | input control | Enabled for `sw`. |
| `clk` | input | Used for memory write on `sw`. |

Control values:

| Instruction | `MemRead` | `MemWrite` |
| --- | --- | --- |
| `lw ri, imm` | 1 | 0 |
| `sw ri, imm` | 0 | 1 |
| `add ri, imm` | 0 | 0 |

### Register file

The register file must read `Reg[ri]` for `sw` and `add`, and write `Reg[ri]` for `lw` and `add`.

| Port / signal | Direction | Meaning |
| --- | --- | --- |
| `ReadReg` | input | Register index `ri`. |
| `ReadData` | output | Value of `Reg[ri]`. |
| `WriteReg` | input | Register index `ri`. |
| `WriteData` | input | Value written back to `Reg[ri]`. |
| `RegWrite` | input control | Enabled for `lw` and `add`. |
| `clk` | input | Used for register write. |

Control values:

| Instruction | `RegWrite` | Register write data |
| --- | --- | --- |
| `lw ri, imm` | 1 | `Mem[imm]` |
| `sw ri, imm` | 0 | Don't care |
| `add ri, imm` | 1 | `Reg[ri] + imm` |

The write-back mux needs the control signal `MemToReg` / `WBSel`:

| Instruction | `WBSel` |
| --- | --- |
| `lw ri, imm` | select data memory `ReadData` |
| `add ri, imm` | select adder result `Reg[ri] + imm` |
| `sw ri, imm` | don't care |

## (2) Datapath

See also: `HW2_datapath.svg`.

```mermaid
flowchart LR
    PC[PC] -->|Instruction address| IMEM[Instruction memory]
    PC --> PCADD[Adder: PC + 4]
    PCADD -->|next PC| PC

    IMEM -->|opcode| CTRL[Control unit]
    IMEM -->|ri| RF[Register file]
    IMEM -->|imm field| IMM[Imm gen]

    IMM -->|imm| DMEM[Data memory]
    IMM -->|imm| ADDI[Adder: Reg[ri] + imm]

    RF -->|ReadData = Reg[ri]| DMEM
    RF -->|ReadData = Reg[ri]| ADDI

    DMEM -->|ReadData| WB[Mux]
    ADDI -->|Sum| WB
    WB -->|WriteData| RF

    CTRL -->|RegWrite| RF
    CTRL -->|MemRead| DMEM
    CTRL -->|MemWrite| DMEM
    CTRL -->|WBSel| WB
```

Equivalent signal-level description:

1. `PC` supplies the instruction address to instruction memory.
2. Instruction memory outputs `opcode`, `ri`, and `imm`.
3. `ri` is connected to both `ReadReg` and `WriteReg` of the register file.
4. The immediate generator produces the sign-extended / formatted `imm`.
5. For `lw`, data memory reads `Mem[imm]`, and the mux writes that value to `Reg[ri]`.
6. For `sw`, the register file reads `Reg[ri]`, and data memory writes it to `Mem[imm]`.
7. For `add`, the adder computes `Reg[ri] + imm`, and the mux writes the result to `Reg[ri]`.
8. For all three instructions, the next PC is `PC + 4`.

Control table:

| Instruction | `RegWrite` | `MemRead` | `MemWrite` | `WBSel` |
| --- | ---: | ---: | ---: | --- |
| `lw ri, imm` | 1 | 1 | 0 | memory data |
| `sw ri, imm` | 0 | 0 | 1 | don't care |
| `add ri, imm` | 1 | 0 | 0 | add result |
