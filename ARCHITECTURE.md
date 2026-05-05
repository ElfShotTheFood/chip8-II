# CHIP-8 II Emulator Architecture Documentation

## Overview
This repository contains a CHIP-8 language emulator and editor implemented in Python. The system consists of four main modules that work together to emulate the CHIP-8 virtual machine, provide a graphical display, manage memory, and offer a GUI-based control interface.

## Architecture Components

### 1. **vm.py** - CHIP-8 Virtual Machine Core
**Purpose**: Implements the CHIP-8 instruction set and virtual machine state.

**Key Features**:
- 16 general-purpose 8-bit registers (V0-VF)
- 16-bit index register (I)
- 16-bit program counter (PC) starting at 0x200
- Stack for subroutine calls (max 16 levels)
- Delay timer (DT) and sound timer (ST)
- Full CHIP-8 instruction set implementation

**External Dependencies**:
- `memory` module for memory read/write operations
- `display` module for graphics operations

**Main Methods**:
- `reset()`: Resets VM to initial state (preserves loaded programs)
- `execute_instruction()`: Fetches, decodes, and executes a single CHIP-8 instruction

**Instruction Coverage**:
- 0x0NNN: Machine code routine (ignored)
- 0x00E0: Clear display
- 0x00EE: Return from subroutine
- 0x1NNN: Jump to address
- 0x2NNN: Call subroutine
- 0x3XNN, 0x4XNN: Skip instructions based on register comparison
- 0x5XY0, 0x9XY0: Skip based on register equality/inequality
- 0x6XNN, 0x7XNN: Set/add to registers
- 0x8XYx: Register arithmetic/logic (15 operations)
- 0xANNN: Set index register
- 0xBNNN: Jump with offset
- 0xCXNN: Random number generation
- 0xDXYN: Draw sprite (with collision detection)
- 0xEXxx: Key operations (partially implemented)
- 0xFXxx: Timer, BCD, register store/load operations

### 2. **memory.py** - Memory Management
**Purpose**: Manages the CHIP-8 4KB memory space.

**Memory Map**:
- 0x000-0x1FF: Interpreter area (font sprites)
- 0x200-0xFFF: Program ROM and RAM

**Key Features**:
- 4096-byte memory array
- Built-in font sprites (0-9, A-F) at addresses 0x000-0x04F
- ROM loading capability
- Memory dump functionality

**API Methods**:
- `init()`: Initialize memory and load font sprites
- `read(address)`: Read byte from memory
- `write(address, value)`: Write byte to memory
- `load_rom(rom_data, start_address)`: Load ROM data
- `get_memory_dump(start, end)`: Get memory range as list

### 3. **display.py** - Graphics Display
**Purpose**: Renders the CHIP-8 display using Pygame.

**Display Specifications**:
- Configurable size in CHIP-8 pixels (default: 64x32)
- Each CHIP-8 pixel rendered as 10x10 device pixels
- Black background with white pixels

**Key Features**:
- Pixel coordinate wrapping (CHIP-8 behavior)
- XOR-based pixel toggling for sprite drawing
- Collision detection (pixel was on before toggle)

**API Methods**:
- `init(x, y)`: Initialize display with specified dimensions
- `clear()`: Clear all pixels
- `set_pixel(x, y)`: Set pixel to on (white)
- `clear_pixel(x, y)`: Set pixel to off (black)
- `xor_pixel(x, y)`: Toggle pixel, return previous state

### 4. **chip-8.py** - GUI Control Interface
**Purpose**: Provides a tkinter-based GUI for controlling the CHIP-8 VM.

**Main Features**:

**Control Section**:
- RUN/STOP buttons for execution control
- SINGLE STEP button for instruction-by-instruction execution
- RESET button to reset VM state
- TEST button to load a demonstration program
- Configurable delay between instructions (default: 500ms)

**Registers Display**:
- V0-VF general-purpose registers (4x4 grid layout)
- I (index register)
- PC (program counter)
- SP (stack pointer)
- DT (delay timer)
- ST (sound timer)
- Changed values highlighted in red

**Memory Editor**:
- Scrollable display of even addresses from 0x200 to 0xFFE
- 4-digit hex value display for each 2-byte word
- Editable memory entries
- PC address highlighted in pale green
- Real-time memory updates during execution

**Additional Features**:
- Pygame event pumping to keep display responsive
- Graceful shutdown with pygame cleanup
- Keyboard navigation in memory editor (Tab, Enter, Escape)

## Component Interaction Flow

1. **Initialization**:
   - `chip-8.py` creates `CHIP8VM` instance
   - VM constructor calls `memory.init()` (loads font sprites)
   - VM calls `display.init()` (creates Pygame window)
   - GUI creates memory display and register views

2. **Program Execution**:
   - User clicks RUN or SINGLE STEP
   - GUI calls `vm.execute_instruction()`
   - VM fetches opcode from memory via `memory.read()`
   - VM decodes and executes instruction
   - For graphics ops, VM calls `display.xor_pixel()` etc.
   - GUI updates register display and memory view
   - Process repeats with configurable delay

3. **Memory Editing**:
   - User modifies memory entry in GUI
   - Value validated as 4-digit hex
   - Written to memory via `memory.write()` (high/low bytes)
   - Display updates to show new value

## Technical Details

### CHIP-8 Specifications Implemented:
- **Memory**: 4KB (4096 bytes)
- **Registers**: 16 8-bit general purpose (V0-VF)
- **Index Register**: 16-bit (I)
- **Program Counter**: 16-bit (starts at 0x200)
- **Stack**: 16 levels maximum
- **Timers**: 8-bit delay and sound timers
- **Display**: 64x32 monochrome pixels
- **Input**: 16-key hex keypad (0-F) - partially implemented
- **Opcode Size**: 2 bytes (big-endian)

### Font Sprites:
Each digit 0-F represented as 5-byte sprite (5x8 pixels):
- Stored at addresses 0x000-0x04F
- Accessed via FX29 instruction (I = VX * 5)

### Graphics:
- XOR-based drawing (DXYN instruction)
- Sprite height: 1-15 bytes
- Each byte represents 8 horizontal pixels
- Collision flag (VF) set when pixel turned from on to off
- Coordinate wrapping at screen edges

## Known Limitations

1. **Keyboard Input**: EX9E/EXA1 (skip on key press) and FX0A (wait for key) are not fully implemented
2. **Timers**: DT and ST decrement not implemented (would need separate thread/timer)
3. **Sound**: No actual sound output (ST timer exists but no audio)
4. **Performance**: Instruction delay is GUI-based, not cycle-accurate

## Testing

The repository includes a test program (TEST button) that:
1. Loads a simple sprite drawing program into memory
2. Sets up registers for drawing
3. Executes draw instruction (D011)
4. Loops to demonstrate program flow

Test program bytes (at 0x200):
```
A2 0A 60 00 61 00 D0 11 12 08 80
```

This demonstrates:
- Register loading (6XNN)
- Index register setting (ANNN)
- Sprite drawing (DXYN)
- Program flow control (1NNN jump)

## Dependencies

- Python 3.x
- tkinter (built-in)
- pygame (`pip install pygame`)

## Usage

```bash
python chip-8.py
```

The GUI window provides:
- Visual VM state monitoring
- Interactive memory editing
- Step-through debugging capability
- Real-time register updates
- Visual PC tracking in memory display