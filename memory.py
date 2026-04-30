"""
CHIP-8 Memory Module

Implements the CHIP-8 memory space (4KB = 4096 bytes).

API Methods:
1. read(address): Read a byte from memory at the specified address.
2. write(address, value): Write a byte to memory at the specified address.

The CHIP-8 memory map:
- 0x000-0x1FF: Interpreter area (font sprites typically stored here)
- 0x200-0xFFF: Program ROM and RAM
"""

# CHIP-8 has 4KB of memory
MEMORY_SIZE = 4096
_memory = [0] * MEMORY_SIZE

# Standard CHIP-8 font sprites (each digit is 5 bytes)
_FONT_SPRITES = [
    0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
    0x20, 0x60, 0x20, 0x20, 0x70,  # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
    0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
    0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
    0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
    0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
    0xF0, 0x80, 0xF0, 0x80, 0x80,  # F
]


def init():
    """Initialize memory and load font sprites into the interpreter area (0x000-0x04F)."""
    global _memory
    # Clear memory
    _memory = [0] * MEMORY_SIZE
    # Load font sprites at the start of memory (0x000)
    for i, byte in enumerate(_FONT_SPRITES):
        _memory[i] = byte


def read(address):
    """Read a byte from memory at the specified address.

    Args:
        address (int): Memory address (0x000-0xFFF).

    Returns:
        int: The byte value at the specified address (0-255).

    Raises:
        ValueError: If address is out of range.
    """
    if address < 0 or address >= MEMORY_SIZE:
        raise ValueError(f"Memory read out of range: 0x{address:03X}")
    return _memory[address]


def write(address, value):
    """Write a byte to memory at the specified address.

    Args:
        address (int): Memory address (0x000-0xFFF).
        value (int): Byte value to write (0-255).

    Raises:
        ValueError: If address is out of range or value is not a valid byte.
    """
    if address < 0 or address >= MEMORY_SIZE:
        raise ValueError(f"Memory write out of range: 0x{address:03X}")
    if value < 0 or value > 255:
        raise ValueError(f"Invalid byte value: {value}")
    _memory[address] = value


def load_rom(rom_data, start_address=0x200):
    """Load ROM data into memory starting at the specified address.

    Args:
        rom_data (bytes or list): The ROM data to load.
        start_address (int): Starting address (default 0x200 for CHIP-8).

    Raises:
        ValueError: If ROM data exceeds available memory.
    """
    rom_size = len(rom_data)
    if start_address + rom_size > MEMORY_SIZE:
        raise ValueError(
            f"ROM too large: {rom_size} bytes at 0x{start_address:03X} "
            f"exceeds memory size of {MEMORY_SIZE}"
        )
    for i, byte in enumerate(rom_data):
        _memory[start_address + i] = byte & 0xFF


def get_memory_dump(start=0, end=None):
    """Get a dump of memory as a list of bytes.

    Args:
        start (int): Starting address (default 0).
        end (int): Ending address (exclusive, default MEMORY_SIZE).

    Returns:
        list: List of byte values in the specified range.
    """
    if end is None:
        end = MEMORY_SIZE
    return _memory[start:end]