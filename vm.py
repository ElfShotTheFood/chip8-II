"""
CHIP-8 Virtual Machine Emulator Module

This module implements a CHIP-8 virtual machine with the following external API:
- reset(): Resets the VM to initial state
- execute_instruction(): Fetches and executes a single CHIP-8 instruction

The VM uses the following modules for external functionality:
- memory module: Provides read(address) and write(address, value) for memory operations.
- display module: Provides set_pixel(x, y), clear_pixel(x, y), xor_pixel(x, y) for display operations.
"""

import random
import memory
import display


class CHIP8VM:
    """CHIP-8 Virtual Machine implementation."""

    def __init__(self):
        """Initialize the VM and reset to initial state."""
        self.reset()

    def reset(self):
        """Reset the VM to its initial state."""
        # 16 8-bit general purpose registers (V0-VF)
        self.V = [0] * 16
        # 16-bit index register
        self.I = 0
        # 16-bit program counter (starts at standard CHIP-8 entry point 0x200)
        self.PC = 0x200
        # Stack for subroutine calls (max 16 levels)
        self.stack = []
        # 8-bit delay timer
        self.delay_timer = 0
        # 8-bit sound timer
        self.sound_timer = 0
        # Initialize memory (load font sprites)
        memory.init()

    def execute_instruction(self):
        """
        Fetch and execute a single CHIP-8 instruction.

        Raises:
            RuntimeError: If stack underflow/overflow occurs, or external methods are missing.
        """
        # Fetch 2-byte opcode from memory at current PC
        high_byte = memory.read(self.PC)
        low_byte = memory.read(self.PC + 1)

        opcode = (high_byte << 8) | low_byte
        # Increment PC by 2 (all CHIP-8 instructions are 2 bytes)
        self.PC += 2

        # Decode opcode nibbles
        n1 = (opcode >> 12) & 0xF  # Opcode group
        n2 = (opcode >> 8) & 0xF   # X register index
        n3 = (opcode >> 4) & 0xF   # Y register index
        n4 = opcode & 0xF          # Low nibble (varies by opcode)

        # Execute opcode based on group
        if n1 == 0x0:
            if opcode == 0x00E0:
                # Clear the display
                display.clear()
            elif opcode == 0x00EE:
                # Return from subroutine
                if not self.stack:
                    raise RuntimeError("Stack underflow on RET instruction")
                self.PC = self.stack.pop()
            # 0x0NNN: Machine code routine call (ignored in modern CHIP-8)

        elif n1 == 0x1:
            # 1NNN: Jump to address NNN
            self.PC = opcode & 0xFFF

        elif n1 == 0x2:
            # 2NNN: Call subroutine at NNN
            self.stack.append(self.PC)
            if len(self.stack) > 16:
                raise RuntimeError("Stack overflow (max 16 levels)")
            self.PC = opcode & 0xFFF

        elif n1 == 0x3:
            # 3XNN: Skip next instruction if VX == NN
            x = n2
            nn = opcode & 0xFF
            if self.V[x] == nn:
                self.PC += 2

        elif n1 == 0x4:
            # 4XNN: Skip next instruction if VX != NN
            x = n2
            nn = opcode & 0xFF
            if self.V[x] != nn:
                self.PC += 2

        elif n1 == 0x5:
            # 5XY0: Skip next instruction if VX == VY
            if n4 != 0x0:
                return  # Invalid opcode
            x = n2
            y = n3
            if self.V[x] == self.V[y]:
                self.PC += 2

        elif n1 == 0x6:
            # 6XNN: Set VX to NN
            x = n2
            self.V[x] = opcode & 0xFF

        elif n1 == 0x7:
            # 7XNN: Add NN to VX
            x = n2
            self.V[x] = (self.V[x] + (opcode & 0xFF)) & 0xFF

        elif n1 == 0x8:
            # 8XYx: Register arithmetic/logic operations
            x = n2
            y = n3
            sub_op = n4
            if sub_op == 0x0:
                # 8XY0: VX = VY
                self.V[x] = self.V[y]
            elif sub_op == 0x1:
                # 8XY1: VX = VX | VY
                self.V[x] = (self.V[x] | self.V[y]) & 0xFF
            elif sub_op == 0x2:
                # 8XY2: VX = VX & VY
                self.V[x] = (self.V[x] & self.V[y]) & 0xFF
            elif sub_op == 0x3:
                # 8XY3: VX = VX ^ VY
                self.V[x] = (self.V[x] ^ self.V[y]) & 0xFF
            elif sub_op == 0x4:
                # 8XY4: VX = VX + VY, VF = carry
                sum_val = self.V[x] + self.V[y]
                self.V[x] = sum_val & 0xFF
                self.V[0xF] = 1 if sum_val > 0xFF else 0
            elif sub_op == 0x5:
                # 8XY5: VX = VX - VY, VF = not borrow
                self.V[0xF] = 1 if self.V[x] > self.V[y] else 0
                self.V[x] = (self.V[x] - self.V[y]) & 0xFF
            elif sub_op == 0x6:
                # 8XY6: VX = VY >> 1, VF = LSB of VY
                self.V[0xF] = self.V[y] & 0x1
                self.V[x] = (self.V[y] >> 1) & 0xFF
            elif sub_op == 0x7:
                # 8XY7: VX = VY - VX, VF = not borrow
                self.V[0xF] = 1 if self.V[y] > self.V[x] else 0
                self.V[x] = (self.V[y] - self.V[x]) & 0xFF
            elif sub_op == 0xE:
                # 8XYE: VX = VY << 1, VF = MSB of VY
                self.V[0xF] = (self.V[y] >> 7) & 0x1
                self.V[x] = (self.V[y] << 1) & 0xFF

        elif n1 == 0x9:
            # 9XY0: Skip next instruction if VX != VY
            if n4 != 0x0:
                return  # Invalid opcode
            x = n2
            y = n3
            if self.V[x] != self.V[y]:
                self.PC += 2

        elif n1 == 0xA:
            # ANNN: Set I to NNN
            self.I = opcode & 0xFFF

        elif n1 == 0xB:
            # BNNN: Jump to NNN + V0
            self.PC = ((opcode & 0xFFF) + self.V[0]) & 0xFFF

        elif n1 == 0xC:
            # CXNN: VX = random byte & NN
            x = n2
            nn = opcode & 0xFF
            self.V[x] = (random.randint(0, 255) & nn) & 0xFF

        elif n1 == 0xD:
            # DXYN: Draw sprite at (VX, VY) with height N
            x = n2
            y = n3
            n = n4
            vx = self.V[x]
            vy = self.V[y]
            collision = False

            for row in range(n):
                sprite_byte = memory.read(self.I + row)

                for bit in range(8):
                    if (sprite_byte >> (7 - bit)) & 1:
                        pixel_x = vx + bit
                        pixel_y = vy + row
                        if display.xor_pixel(pixel_x, pixel_y):
                            collision = True
            # Set collision flag (VF) if any pixel was turned from on to off
            self.V[0xF] = 1 if collision else 0

        elif n1 == 0xE:
            # EX9E: Skip if key VX pressed
            # EXA1: Skip if key VX not pressed
            # TODO: Implement when key state external method is added
            pass

        elif n1 == 0xF:
            # FXxx: Miscellaneous operations
            x = n2
            sub_op = opcode & 0xFF
            if sub_op == 0x07:
                # FX07: VX = delay timer
                self.V[x] = self.delay_timer
            elif sub_op == 0x0A:
                # FX0A: Wait for key press, store in VX
                # TODO: Implement when key wait method is added
                pass
            elif sub_op == 0x15:
                # FX15: Delay timer = VX
                self.delay_timer = self.V[x] & 0xFF
            elif sub_op == 0x18:
                # FX18: Sound timer = VX
                self.sound_timer = self.V[x] & 0xFF
            elif sub_op == 0x1E:
                # FX1E: I += VX, VF = overflow
                old_I = self.I
                self.I = (self.I + self.V[x]) & 0xFFF
                self.V[0xF] = 1 if (old_I + self.V[x]) > 0xFFF else 0
            elif sub_op == 0x29:
                # FX29: I = font sprite location for digit VX
                # Assumes 5-byte font sprites starting at 0x000
                self.I = (self.V[x] * 5) & 0xFFF
            elif sub_op == 0x33:
                # FX33: Store BCD of VX at I, I+1, I+2
                value = self.V[x]
                memory.write(self.I, value // 100)
                memory.write(self.I + 1, (value // 10) % 10)
                memory.write(self.I + 2, value % 10)
            elif sub_op == 0x55:
                # FX55: Store V0 to VX in memory starting at I
                for i in range(x + 1):
                    memory.write(self.I + i, self.V[i])
            elif sub_op == 0x65:
                # FX65: Read V0 to VX from memory starting at I
                for i in range(x + 1):
                    self.V[i] = memory.read(self.I + i) & 0xFF
