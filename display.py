"""
CHIP-8 Display Module

Implements the CHIP-8 screen with chip-8 pixels, where each chip-8 pixel is rendered as 10x10 device pixels.
The screen size is specified in chip-8 pixels via the init() method.

API Methods:
1. init(x, y): Initialize the chip-8 screen with width x and height y (in chip-8 pixels). Creates a display window.
2. clear(): Clear all chip-8 pixels (set to off).
3. set_pixel(x, y): Set the chip-8 pixel at (x, y) to on (white).
4. clear_pixel(x, y): Set the chip-8 pixel at (x, y) to off (black).
5. xor_pixel(x, y): Toggle the chip-8 pixel at (x, y). Returns True if the pixel was on before toggling (collision flag).

Requires pygame: Install with `pip install pygame`.
"""

import pygame

# Global display state
_screen = None
_pixel_array = None  # 2D array: _pixel_array[y][x] = 0 (off) or 1 (on)
_chip8_width = 0
_chip8_height = 0
_PIXEL_SCALE = 10  # Number of device pixels per chip-8 pixel (10x10)


def init(x, y):
    """Initialize the CHIP-8 screen with specified size in chip-8 pixels.

    Args:
        x (int): Width of the screen in chip-8 pixels.
        y (int): Height of the screen in chip-8 pixels.
    """
    global _screen, _pixel_array, _chip8_width, _chip8_height

    _chip8_width = x
    _chip8_height = y

    # Initialize pygame
    pygame.init()

    # Calculate actual window size (chip-8 pixels * scale factor)
    window_width = x * _PIXEL_SCALE
    window_height = y * _PIXEL_SCALE

    # Create display window
    _screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("CHIP-8 Display")

    # Initialize pixel state array (all pixels off by default)
    _pixel_array = [[0 for _ in range(x)] for _ in range(y)]

    # Fill screen with black (off state)
    _screen.fill((0, 0, 0))
    pygame.display.flip()

    # Pump event queue to prevent window freeze
    pygame.event.pump()


def clear():
    """Clear all chip-8 pixels (set to off state)."""
    global _pixel_array, _screen

    if _screen is None:
        raise RuntimeError("Display not initialized. Call init() first.")

    # Reset all pixel states to off
    for y in range(_chip8_height):
        for x in range(_chip8_width):
            _pixel_array[y][x] = 0

    # Clear screen to black
    _screen.fill((0, 0, 0))
    pygame.display.flip()
    pygame.event.pump()


def set_pixel(x, y):
    """Set the chip-8 pixel at (x, y) to on (white).

    Args:
        x (int): X coordinate of the chip-8 pixel (wraps around screen width).
        y (int): Y coordinate of the chip-8 pixel (wraps around screen height).
    """
    global _pixel_array, _screen

    if _screen is None:
        raise RuntimeError("Display not initialized. Call init() first.")

    # Wrap coordinates to match CHIP-8 behavior
    x = x % _chip8_width
    y = y % _chip8_height

    # Only update if pixel is currently off
    if _pixel_array[y][x] == 0:
        _pixel_array[y][x] = 1
        # Draw 10x10 rectangle for this chip-8 pixel
        rect = pygame.Rect(
            x * _PIXEL_SCALE,
            y * _PIXEL_SCALE,
            _PIXEL_SCALE,
            _PIXEL_SCALE
        )
        pygame.draw.rect(_screen, (255, 255, 255), rect)
        pygame.display.flip()

    pygame.event.pump()


def clear_pixel(x, y):
    """Set the chip-8 pixel at (x, y) to off (black).

    Args:
        x (int): X coordinate of the chip-8 pixel (wraps around screen width).
        y (int): Y coordinate of the chip-8 pixel (wraps around screen height).
    """
    global _pixel_array, _screen

    if _screen is None:
        raise RuntimeError("Display not initialized. Call init() first.")

    # Wrap coordinates to match CHIP-8 behavior
    x = x % _chip8_width
    y = y % _chip8_height

    # Only update if pixel is currently on
    if _pixel_array[y][x] == 1:
        _pixel_array[y][x] = 0
        # Draw black 10x10 rectangle for this chip-8 pixel
        rect = pygame.Rect(
            x * _PIXEL_SCALE,
            y * _PIXEL_SCALE,
            _PIXEL_SCALE,
            _PIXEL_SCALE
        )
        pygame.draw.rect(_screen, (0, 0, 0), rect)
        pygame.display.flip()

    pygame.event.pump()


def xor_pixel(x, y):
    """Toggle the chip-8 pixel at (x, y).

    Args:
        x (int): X coordinate of the chip-8 pixel (wraps around screen width).
        y (int): Y coordinate of the chip-8 pixel (wraps around screen height).

    Returns:
        bool: True if the pixel was on before toggling (indicates collision for CHIP-8 DXYN instruction),
              False otherwise.
    """
    global _pixel_array, _screen

    if _screen is None:
        raise RuntimeError("Display not initialized. Call init() first.")

    # Wrap coordinates to match CHIP-8 behavior
    x = x % _chip8_width
    y = y % _chip8_height

    prev_state = _pixel_array[y][x]

    if prev_state == 1:
        # Pixel was on, turn it off
        _pixel_array[y][x] = 0
        rect = pygame.Rect(
            x * _PIXEL_SCALE,
            y * _PIXEL_SCALE,
            _PIXEL_SCALE,
            _PIXEL_SCALE
        )
        pygame.draw.rect(_screen, (0, 0, 0), rect)
    else:
        # Pixel was off, turn it on
        _pixel_array[y][x] = 1
        rect = pygame.Rect(
            x * _PIXEL_SCALE,
            y * _PIXEL_SCALE,
            _PIXEL_SCALE,
            _PIXEL_SCALE
        )
        pygame.draw.rect(_screen, (255, 255, 255), rect)

    pygame.display.flip()
    pygame.event.pump()

    return prev_state == 1