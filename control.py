"""
CHIP-8 VM Control Module

Implements a tkinter-based dialog window to control the CHIP-8 VM, with:
1. Control Section: RUN, STOP, SINGLE STEP, RESET buttons and delay configuration
2. Memory Section: Scrollable display of even CHIP-8 memory addresses (starting at 0x200) with edit capability

Requires:
- tkinter (built-in)
- pygame (for display, already used by display.py)
"""

import tkinter as tk
from tkinter import messagebox
import pygame
import vm
import memory
import display


class ControlGUI:
    """Main GUI class for the CHIP-8 VM controller."""

    def __init__(self, root):
        self.root = root
        self.root.title("CHIP-8 VM Controller")
        self.root.geometry("800x600")

        # Initialize CHIP-8 display (64x32 chip-8 pixels, 10x10 device pixels each)
        display.init(64, 32)

        # Initialize VM (calls reset() which initializes memory with font sprites)
        self.vm = vm.CHIP8VM()

        # State variables
        self.is_running = False
        self.memory_entries = {}  # Maps address -> Entry widget
        self.current_original_value = None  # For ESC key revert
        self.current_entry_addr = None

        # --- Control Frame ---
        self.control_frame = tk.LabelFrame(self.root, text="Control", padx=10, pady=10)
        self.control_frame.pack(fill=tk.X, padx=10, pady=5)

        # RUN button
        self.run_btn = tk.Button(
            self.control_frame, text="RUN", command=self.start_run, width=10
        )
        self.run_btn.pack(side=tk.LEFT, padx=5)

        # STOP button
        self.stop_btn = tk.Button(
            self.control_frame, text="STOP", command=self.stop_run, width=10
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # SINGLE STEP button
        self.step_btn = tk.Button(
            self.control_frame, text="SINGLE STEP", command=self.single_step, width=15
        )
        self.step_btn.pack(side=tk.LEFT, padx=5)

        # RESET button
        self.reset_btn = tk.Button(
            self.control_frame, text="RESET", command=self.reset_vm, width=10
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        # TEST button (temporary)
        self.test_btn = tk.Button(
            self.control_frame, text="TEST", command=self.load_test_program, width=10
        )
        self.test_btn.pack(side=tk.LEFT, padx=5)

        # Delay configuration
        self.delay_label = tk.Label(self.control_frame, text="Delay (ms):")
        self.delay_label.pack(side=tk.LEFT, padx=20)
        self.delay_entry = tk.Entry(self.control_frame, width=10)
        self.delay_entry.insert(0, "500")  # Default 500ms
        self.delay_entry.pack(side=tk.LEFT, padx=5)

        # Status indicator
        self.status_label = tk.Label(self.control_frame, text="Status:")
        self.status_label.pack(side=tk.LEFT, padx=20)
        self.status_value = tk.Label(
            self.control_frame, text="STOPPED", fg="red", font=("Arial", 10, "bold")
        )
        self.status_value.pack(side=tk.LEFT, padx=5)

        # --- Memory Frame ---
        self.mem_frame = tk.LabelFrame(
            self.root, text="Memory (Even Addresses from 0x0200)", padx=10, pady=10
        )
        self.mem_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollable canvas for memory rows
        self.mem_canvas = tk.Canvas(self.mem_frame)
        self.vscroll = tk.Scrollbar(
            self.mem_frame, orient=tk.VERTICAL, command=self.mem_canvas.yview
        )
        self.mem_canvas.configure(yscrollcommand=self.vscroll.set)

        self.vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.mem_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Inner frame to hold memory address rows
        self.mem_inner_frame = tk.Frame(self.mem_canvas)
        self.mem_canvas.create_window(
            (0, 0), window=self.mem_inner_frame, anchor=tk.NW
        )

        # Populate memory rows
        self.populate_memory()

        # Update scroll region after population
        self.mem_inner_frame.update_idletasks()
        self.mem_canvas.configure(scrollregion=self.mem_canvas.bbox("all"))

        # Start pygame event pumping to keep display responsive
        self.pump_pygame_events()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def populate_memory(self):
        """Populate the memory frame with rows for each even address starting at 0x200."""
        # Even addresses from 0x200 to 0xFFE (inclusive)
        for addr in range(0x200, 0x1000, 2):
            # Read 2-byte value from memory (high byte at addr, low byte at addr+1)
            high_byte = memory.read(addr)
            low_byte = memory.read(addr + 1)
            value = (high_byte << 8) | low_byte
            value_hex = f"{value:04X}"  # 4-digit hex string

            # Create row frame
            row = tk.Frame(self.mem_inner_frame)
            row.pack(fill=tk.X, pady=2)

            # Address label (hex format)
            addr_label = tk.Label(
                row, text=f"0x{addr:04X}", width=8, anchor=tk.W
            )
            addr_label.pack(side=tk.LEFT, padx=(0, 10))

            # Value entry (4-digit hex)
            entry = tk.Entry(row, width=6)
            entry.insert(0, value_hex)
            entry.pack(side=tk.LEFT)

            # Bind events for editing
            entry.bind(
                "<FocusIn>",
                lambda e, a=addr, ent=entry: self.on_entry_focus_in(e, a, ent),
            )
            entry.bind(
                "<Return>",
                lambda e, a=addr, ent=entry: self.on_entry_save(e, a, ent),
            )
            entry.bind(
                "<Tab>",
                lambda e, a=addr, ent=entry: self.on_entry_save(e, a, ent),
            )
            entry.bind(
                "<Escape>",
                lambda e, a=addr, ent=entry: self.on_entry_escape(e, a, ent),
            )

            # Store entry reference
            self.memory_entries[addr] = entry

    def on_entry_focus_in(self, event, addr, entry):
        """Save original value when entry gains focus (for ESC revert)."""
        self.current_original_value = entry.get()
        self.current_entry_addr = addr

    def on_entry_save(self, event, addr, entry):
        """Save entry value to memory and move focus to next address."""
        text = entry.get().strip().upper()
        if not text:
            text = "0000"

        # Validate hex input
        try:
            value = int(text, 16)
        except ValueError:
            messagebox.showerror("Invalid Input", f"'{text}' is not a valid hex value.")
            entry.delete(0, tk.END)
            entry.insert(0, self.current_original_value)
            return "break"

        # Mask to 16 bits (2 bytes)
        value &= 0xFFFF
        high_byte = (value >> 8) & 0xFF
        low_byte = value & 0xFF

        # Write to memory
        memory.write(addr, high_byte)
        memory.write(addr + 1, low_byte)

        # Update entry to formatted value
        entry.delete(0, tk.END)
        entry.insert(0, f"{value:04X}")

        # Move focus to next even address
        next_addr = addr + 2
        if next_addr <= 0xFFE:
            if next_addr in self.memory_entries:
                self.memory_entries[next_addr].focus_set()
        else:
            # Wrap to first address if at end
            if 0x200 in self.memory_entries:
                self.memory_entries[0x200].focus_set()

        return "break"  # Prevent default Tab behavior

    def on_entry_escape(self, event, addr, entry):
        """Revert entry to original value and preserve focus."""
        if self.current_original_value is not None:
            entry.delete(0, tk.END)
            entry.insert(0, self.current_original_value)
        return "break"

    def start_run(self):
        """Start the VM execution loop with configurable delay."""
        if not self.is_running:
            self.is_running = True
            self.set_memory_editable(False)
            self.status_value.config(text="RUNNING", fg="green")
            self.run_step()

    def run_step(self):
        """Execute a single instruction and schedule the next if still running."""
        if self.is_running:
            try:
                self.vm.execute_instruction()
            except Exception as e:
                messagebox.showerror("VM Execution Error", str(e))
                self.stop_run()
                return

            # Get delay from entry (default to 500ms if invalid)
            try:
                delay = int(self.delay_entry.get())
                delay = max(0, delay)  # Ensure non-negative
            except ValueError:
                delay = 500

            # Schedule next instruction
            self.root.after(delay, self.run_step)

    def stop_run(self):
        """Stop the VM execution loop."""
        self.is_running = False
        self.set_memory_editable(True)
        self.status_value.config(text="STOPPED", fg="red")

    def single_step(self):
        """Execute a single CHIP-8 instruction without delay."""
        try:
            self.vm.execute_instruction()
        except Exception as e:
            messagebox.showerror("VM Execution Error", str(e))

    def reset_vm(self):
        """Stop execution, reset VM registers, and refresh memory display."""
        self.is_running = False
        self.vm.reset()  # Resets registers, PC, stack, and re-initializes memory
        display.clear()  # Clear the CHIP-8 display
        self.set_memory_editable(True)
        self.refresh_memory()
        self.status_value.config(text="STOPPED", fg="red")

    def load_test_program(self):
        """Load a test program into memory starting at 0x200 (temporary test button)."""
        # Test program bytes: A206 6000 6100 D011 1208 80
        test_bytes = [
            0xA2, 0x06,  # A206: Set I to 0x206
            0x60, 0x00,  # 6000: Set V0 to 0x00
            0x61, 0x00,  # 6100: Set V1 to 0x00
            0xD0, 0x11,  # D011: Draw sprite at (V0, V1) height 1 from I
            0x12, 0x08,  # 1208: Jump to 0x208
            0x80,        # 80: Single byte (pads to even address)
        ]

        # Stop VM if running
        self.is_running = False
        self.status_value.config(text="STOPPED", fg="red")

        # Write bytes to memory starting at 0x200
        for i, byte in enumerate(test_bytes):
            memory.write(0x200 + i, byte)

        # Refresh the memory display
        self.refresh_memory()

        # Reset VM to ensure PC is at 0x200
        self.vm.reset()

    def set_memory_editable(self, editable):
        """Enable/disable memory entries based on VM running state."""
        state = tk.NORMAL if editable else tk.DISABLED
        for entry in self.memory_entries.values():
            entry.config(state=state)

    def refresh_memory(self):
        """Refresh all memory entries to reflect current memory contents."""
        for addr, entry in self.memory_entries.items():
            high_byte = memory.read(addr)
            low_byte = memory.read(addr + 1)
            value = (high_byte << 8) | low_byte
            entry.delete(0, tk.END)
            entry.insert(0, f"{value:04X}")

    def pump_pygame_events(self):
        """Periodically pump pygame events to keep the display responsive."""
        pygame.event.pump()
        self.root.after(100, self.pump_pygame_events)

    def on_close(self):
        """Cleanup pygame and close the application."""
        pygame.quit()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ControlGUI(root)
    root.mainloop()