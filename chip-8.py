"""
CHIP-8 VM Control Module

Implements a tkinter-based dialog window to control the CHIP-8 VM, with:
1. Control Section: RUN, STOP, SINGLE STEP, RESET buttons and delay configuration
2. Registers Section: Display of V0-VF, I, PC, SP, DT, ST registers
3. Memory Section: Scrollable display of even CHIP-8 memory addresses (starting at 0x200) with edit capability

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


class Chip8Gui:
    """Main GUI class for the CHIP-8 VM controller."""

    def __init__(self, root):
        self.root = root
        self.root.title("CHIP-8 VM Controller")
        self.root.geometry("900x750")  # Increased width for new register layout

        print("\nDEBUG: Chip8Gui.__init__() called")
        print("DEBUG: About to create VM instance (this will call memory.init())")

        # Initialize CHIP-8 display (64x32 chip-8 pixels, 10x10 device pixels each)
        display.init(64, 32)

        # Initialize VM (calls memory.init() once in __init__)
        self.vm = vm.CHIP8VM()
        print("DEBUG: VM instance created")

        # State variables
        self.is_running = False
        self.memory_entries = {}  # Maps address -> Entry widget
        self.addr_labels = {}  # Maps address -> (addr_canvas, addr_text_id, rect_id, addr_frame)
        self.current_original_value = None  # For ESC key revert
        self.current_entry_addr = None
        self.highlighted_pc = None  # Track which address is currently highlighted
        
        # Previous register values for change detection
        self.prev_V = [0] * 16
        self.prev_I = 0
        self.prev_PC = 0x200
        self.prev_SP = 0  # Stack pointer (len of stack)
        self.prev_DT = 0
        self.prev_ST = 0

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

        # --- Registers Frame ---
        self.reg_frame = tk.LabelFrame(self.root, text="Registers", padx=10, pady=10)
        self.reg_frame.pack(fill=tk.X, padx=10, pady=5)

        # Create a horizontal container for the three sections
        reg_container = tk.Frame(self.reg_frame)
        reg_container.pack(fill=tk.X, padx=5, pady=5)

        # Left column: PC, SP, I (vertical stack)
        left_col = tk.Frame(reg_container)
        left_col.pack(side=tk.LEFT, padx=(0, 15), anchor="n")

        # PC register
        pc_frame = tk.Frame(left_col)
        pc_frame.pack(fill=tk.X, pady=2)
        tk.Label(pc_frame, text="PC:", width=3, anchor="w", fg="lightblue").pack(side=tk.LEFT)
        self.PC_label = tk.Label(pc_frame, text="0200", width=6, font=("Consolas", 10))
        self.PC_label.pack(side=tk.LEFT)

        # SP register (4-digit hex, aligned with PC and I)
        sp_frame = tk.Frame(left_col)
        sp_frame.pack(fill=tk.X, pady=2)
        tk.Label(sp_frame, text="SP:", width=3, anchor="w", fg="lightblue").pack(side=tk.LEFT)
        self.SP_label = tk.Label(sp_frame, text="0000", width=6, font=("Consolas", 10))
        self.SP_label.pack(side=tk.LEFT)

        # I register
        i_frame = tk.Frame(left_col)
        i_frame.pack(fill=tk.X, pady=2)
        tk.Label(i_frame, text="I:", width=3, anchor="w", fg="lightblue").pack(side=tk.LEFT)
        self.I_label = tk.Label(i_frame, text="0000", width=6, font=("Consolas", 10))
        self.I_label.pack(side=tk.LEFT)

        # Middle column: DT, ST (vertical stack)
        mid_col = tk.Frame(reg_container)
        mid_col.pack(side=tk.LEFT, padx=(0, 15), anchor="n")

        # DT register
        dt_frame = tk.Frame(mid_col)
        dt_frame.pack(fill=tk.X, pady=2)
        tk.Label(dt_frame, text="DT:", width=3, anchor="w", fg="lightblue").pack(side=tk.LEFT)
        self.DT_label = tk.Label(dt_frame, text="00", width=4, font=("Consolas", 10))
        self.DT_label.pack(side=tk.LEFT)

        # ST register
        st_frame = tk.Frame(mid_col)
        st_frame.pack(fill=tk.X, pady=2)
        tk.Label(st_frame, text="ST:", width=3, anchor="w", fg="lightblue").pack(side=tk.LEFT)
        self.ST_label = tk.Label(st_frame, text="00", width=4, font=("Consolas", 10))
        self.ST_label.pack(side=tk.LEFT)

        # Right section: V0-VF in 4x4 grid (column-major order)
        right_section = tk.Frame(reg_container)
        right_section.pack(side=tk.LEFT, padx=(0, 0), anchor="n")

        self.reg_labels = {}  # Maps register name -> value_label

        # V0-VF registers in 4x4 grid, column-major order
        # Column 0: V0, V1, V2, V3 (top-down)
        # Column 1: V4, V5, V6, V7
        # Column 2: V8, V9, VA, VB
        # Column 3: VC, VD, VE, VF
        for i in range(16):
            col = i // 4  # Column number (0-3)
            row = i % 4   # Row number (0-3)
            reg_name = f"V{i:X}"  # V0, V1, ..., VF
            
            # Create frame for each register
            reg_frame = tk.Frame(right_section)
            reg_frame.grid(row=row, column=col, padx=10, pady=2, sticky="w")
            
            # Register name label (light blue)
            name_label = tk.Label(reg_frame, text=f"{reg_name}:", width=3, anchor="w", fg="lightblue")
            name_label.pack(side=tk.LEFT)
            
            # Register value label (hex format)
            value_label = tk.Label(reg_frame, text="00", width=4, font=("Consolas", 10))
            value_label.pack(side=tk.LEFT)
            
            self.reg_labels[reg_name] = value_label

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
        
        # Initial register display
        self.update_registers()
        
        # Highlight initial PC address
        if self.vm.PC in self.addr_labels:
            self.highlight_address(self.vm.PC, highlight=True)
            self.highlighted_pc = self.vm.PC

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_rounded_rect(self, canvas, x1, y1, x2, y2, radius=8, **kwargs):
        """Draw a rounded rectangle on a canvas.
        
        Args:
            canvas: The tkinter Canvas to draw on
            x1, y1: Top-left corner coordinates
            x2, y2: Bottom-right corner coordinates
            radius: Corner radius
            **kwargs: Additional arguments for create_polygon (fill, outline, etc.)
        
        Returns:
            The canvas item ID of the rounded rectangle
        """
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1, x2, y1+radius,
            x2, y2-radius,
            x2, y2, x2-radius, y2,
            x1+radius, y2,
            x1, y2, x1, y2-radius,
            x1, y1+radius, x1, y1
        ]
        return canvas.create_polygon(points, **kwargs, smooth=True)

    def highlight_address(self, addr, highlight=True):
        """Highlight or unhighlight an address label in the memory display.
        
        Args:
            addr: The memory address to highlight/unhighlight
            highlight: True to add highlight, False to remove
        """
        if addr not in self.addr_labels:
            return
        
        canvas, text_id, rect_id, _ = self.addr_labels[addr]
        
        if highlight:
            # Update text to bold black
            canvas.itemconfig(text_id, fill="black", font=("Consolas", 10, "bold"))
            # Update rectangle to very light green with rounded corners
            canvas.itemconfig(rect_id, fill="palegreen", outline="palegreen")
        else:
            # Remove highlight - restore normal text
            canvas.itemconfig(text_id, fill="black", font=("Consolas", 10))
            # Restore rectangle to no fill
            canvas.itemconfig(rect_id, fill="SystemButtonFace", outline="SystemButtonFace")

    def update_registers(self):
        """Update the register display, showing changed values in red."""
        # Update V0-VF
        for i in range(16):
            reg_name = f"V{i:X}"
            new_val = self.vm.V[i]
            value_label = self.reg_labels[reg_name]
            
            # Check if value changed
            if new_val != self.prev_V[i]:
                value_label.config(text=f"{new_val:02X}", fg="red")
                self.prev_V[i] = new_val
            else:
                value_label.config(text=f"{new_val:02X}", fg="black")
        
        # Update I register
        if self.vm.I != self.prev_I:
            self.I_label.config(text=f"{self.vm.I:04X}", fg="red")
            self.prev_I = self.vm.I
        else:
            self.I_label.config(text=f"{self.vm.I:04X}", fg="black")
        
        # Update PC and highlight in memory display
        if self.vm.PC != self.prev_PC:
            self.PC_label.config(text=f"{self.vm.PC:04X}", fg="red")
            # Remove highlight from old PC
            if self.highlighted_pc is not None and self.highlighted_pc in self.addr_labels:
                self.highlight_address(self.highlighted_pc, highlight=False)
            # Add highlight to new PC
            if self.vm.PC in self.addr_labels:
                self.highlight_address(self.vm.PC, highlight=True)
                self.highlighted_pc = self.vm.PC
            self.prev_PC = self.vm.PC
        else:
            self.PC_label.config(text=f"{self.vm.PC:04X}", fg="black")
        
        # Update SP (stack pointer = length of stack) - show as 4-digit hex
        sp = len(self.vm.stack)
        sp_hex = f"{sp:04X}"
        if sp != self.prev_SP:
            self.SP_label.config(text=sp_hex, fg="red")
            self.prev_SP = sp
        else:
            self.SP_label.config(text=sp_hex, fg="black")
        
        # Update DT (Delay Timer)
        if self.vm.delay_timer != self.prev_DT:
            self.DT_label.config(text=f"{self.vm.delay_timer:02X}", fg="red")
            self.prev_DT = self.vm.delay_timer
        else:
            self.DT_label.config(text=f"{self.vm.delay_timer:02X}", fg="black")
        
        # Update ST (Sound Timer)
        if self.vm.sound_timer != self.prev_ST:
            self.ST_label.config(text=f"{self.vm.sound_timer:02X}", fg="red")
            self.prev_ST = self.vm.sound_timer
        else:
            self.ST_label.config(text=f"{self.vm.sound_timer:02X}", fg="black")

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

            # Address label with green rounded rectangle highlight capability
            # Use a Canvas to draw rounded rectangle with text
            addr_frame = tk.Frame(row, bg="SystemButtonFace")
            addr_frame.pack(side=tk.LEFT, padx=(0, 10))
            
            # Create a small canvas for the address label with rounded rectangle
            addr_canvas = tk.Canvas(addr_frame, width=70, height=24, bg="SystemButtonFace", 
                                     highlightthickness=0)
            addr_canvas.pack()
            
            # Draw rounded rectangle (green when highlighted)
            rect_id = self.create_rounded_rect(addr_canvas, 2, 2, 68, 22, radius=8,
                                                  fill="SystemButtonFace", outline="SystemButtonFace", width=0)
            
            # Create text on top of rectangle
            text_id = addr_canvas.create_text(35, 12, text=f"0x{addr:04X}", 
                                              font=("Consolas", 10), fill="black")
            
            # Store reference: (canvas, text_id, rect_id, addr_frame)
            self.addr_labels[addr] = (addr_canvas, text_id, rect_id, addr_frame)

            # Value entry (4-digit hex) - using Consolas font
            entry = tk.Entry(row, width=6, font=("Consolas", 10))
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
                self.update_registers()
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
            self.update_registers()
        except Exception as e:
            messagebox.showerror("VM Execution Error", str(e))

    def reset_vm(self):
        """Stop execution, reset VM registers, and refresh memory display."""
        self.is_running = False
        self.vm.reset()  # Resets registers, PC, stack, and re-initializes memory
        display.clear()  # Clear the CHIP-8 display
        self.set_memory_editable(True)
        self.refresh_memory()
        self.update_registers()
        self.status_value.config(text="STOPPED", fg="red")

    def load_test_program(self):
        """Load a test program into memory starting at 0x200 (temporary test button)."""
        # Test program bytes: A20A 6000 6100 D011 1208 80
        test_bytes = [
            0xA2, 0x0A,  # A20A: Set I to 0x20A
            0x60, 0x00,  # 6000: Set V0 to 0x00
            0x61, 0x00,  # 6100: Set V1 to 0x00
            0xD0, 0x11,  # D011: Draw sprite at (V0, V1) height 1 from I
            0x12, 0x08,  # 1208: Jump to 0x208
            0x80,        # 80: Single byte (pads to even address)
        ]

        # Stop VM if running
        self.is_running = False
        self.status_value.config(text="STOPPED", fg="red")

        print(f"\nDEBUG: load_test_program() called")
        print(f"DEBUG: Before writing test bytes:")
        print(f"  memory[0x200] = 0x{memory.read(0x200):02X}")
        print(f"  memory[0x201] = 0x{memory.read(0x201):02X}")

        # Write bytes to memory starting at 0x200
        print(f"DEBUG: Writing test bytes to memory...")
        for i, byte in enumerate(test_bytes):
            addr = 0x200 + i
            memory.write(addr, byte)
            print(f"  memory.write(0x{addr:04X}, 0x{byte:02X})")

        # Debug: Verify memory was written correctly
        print(f"DEBUG: load_test_program: After writing test bytes:")
        print(f"  memory[0x200] = 0x{memory.read(0x200):02X} (expected 0xA2)")
        print(f"  memory[0x201] = 0x{memory.read(0x201):02X} (expected 0x0A)")

        # Refresh the memory display
        self.refresh_memory()

        # Reset VM to ensure PC is at 0x200
        print(f"DEBUG: About to call vm.reset()")
        self.vm.reset()
        print(f"DEBUG: After vm.reset(), PC = 0x{self.vm.PC:04X}")
        
        # Update register display
        self.update_registers()

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
    app = Chip8Gui(root)
    root.mainloop()