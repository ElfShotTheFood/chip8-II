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
from tkinter import filedialog, messagebox
import pygame
import vm
import memory
import display


class Chip8Gui:
    """Main GUI class for the CHIP-8 VM controller."""

    def __init__(self, root):
        self.root = root
        self.root.title("CHIP-8 VM Controller")
        self.root.geometry("900x750")

        print("\nDEBUG: Chip8Gui.__init__() called")
        print("DEBUG: About to create VM instance (this will call memory.init())")

        # Initialize CHIP-8 display
        display.init(64, 32)

        # Initialize VM
        self.vm = vm.CHIP8VM()
        print("DEBUG: VM instance created")

        # State variables
        self.is_running = False
        self.memory_entries = {}
        self.addr_labels = {}
        self.current_original_value = None
        self.current_entry_addr = None
        self.highlighted_pc = None
        
        # Previous register values for change detection
        self.prev_V = [0] * 16
        self.prev_I = 0
        self.prev_PC = 0x200
        self.prev_SP = 0
        self.prev_DT = 0
        self.prev_ST = 0

        # --- Control Frame ---
        self.control_frame = tk.LabelFrame(self.root, text="Control", padx=10, pady=10)
        self.control_frame.pack(fill=tk.X, padx=10, pady=5)

        # RUN button
        self.run_btn = tk.Button(
            self.control_frame, text="RUN", command=lambda: self.blur_edit_then_run(), width=10
        )
        self.run_btn.pack(side=tk.LEFT, padx=5)

        # STOP button
        self.stop_btn = tk.Button(
            self.control_frame, text="STOP", command=lambda: self.blur_edit_then_stop(), width=10
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # SINGLE STEP button
        self.step_btn = tk.Button(
            self.control_frame, text="SINGLE STEP", command=lambda: self.blur_edit_then_step(), width=15
        )
        self.step_btn.pack(side=tk.LEFT, padx=5)

        # RESET button
        self.reset_btn = tk.Button(
            self.control_frame, text="RESET", command=lambda: self.blur_edit_then_reset(), width=10
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        # Delay configuration
        self.delay_label = tk.Label(self.control_frame, text="Delay (ms):")
        self.delay_label.pack(side=tk.LEFT, padx=20)
        self.delay_entry = tk.Entry(self.control_frame, width=10)
        self.delay_entry.insert(0, "500")
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

        reg_container = tk.Frame(self.reg_frame)
        reg_container.pack(fill=tk.X, padx=5, pady=5)

        # Left column: PC, SP, I
        left_col = tk.Frame(reg_container)
        left_col.pack(side=tk.LEFT, padx=(0, 15), anchor="n")

        # PC register
        pc_frame = tk.Frame(left_col)
        pc_frame.pack(fill=tk.X, pady=2)
        self._create_reg_name_canvas(pc_frame, "PC", width=3)
        self.PC_label = tk.Label(pc_frame, text="0200", width=6, font=("Consolas", 10))
        self.PC_label.pack(side=tk.LEFT)

        # SP register
        sp_frame = tk.Frame(left_col)
        sp_frame.pack(fill=tk.X, pady=2)
        self._create_reg_name_canvas(sp_frame, "SP", width=3)
        self.SP_label = tk.Label(sp_frame, text="0000", width=6, font=("Consolas", 10))
        self.SP_label.pack(side=tk.LEFT)

        # I register
        i_frame = tk.Frame(left_col)
        i_frame.pack(fill=tk.X, pady=2)
        self._create_reg_name_canvas(i_frame, "I", width=3)
        self.I_label = tk.Label(i_frame, text="0000", width=6, font=("Consolas", 10))
        self.I_label.pack(side=tk.LEFT)

        # Middle column: DT, ST
        mid_col = tk.Frame(reg_container)
        mid_col.pack(side=tk.LEFT, padx=(0, 15), anchor="n")

        # DT register
        dt_frame = tk.Frame(mid_col)
        dt_frame.pack(fill=tk.X, pady=2)
        self._create_reg_name_canvas(dt_frame, "DT", width=3)
        self.DT_label = tk.Label(dt_frame, text="00", width=4, font=("Consolas", 10))
        self.DT_label.pack(side=tk.LEFT)

        # ST register
        st_frame = tk.Frame(mid_col)
        st_frame.pack(fill=tk.X, pady=2)
        self._create_reg_name_canvas(st_frame, "ST", width=3)
        self.ST_label = tk.Label(st_frame, text="00", width=4, font=("Consolas", 10))
        self.ST_label.pack(side=tk.LEFT)

        # Right section: V0-VF in 4x4 grid
        right_section = tk.Frame(reg_container)
        right_section.pack(side=tk.LEFT, padx=(0, 0), anchor="n")

        self.reg_labels = {}

        for i in range(16):
            col = i // 4
            row = i % 4
            reg_name = f"V{i:X}"
            
            reg_frame = tk.Frame(right_section)
            reg_frame.grid(row=row, column=col, padx=10, pady=2, sticky="w")
            
            self._create_reg_name_canvas(reg_frame, reg_name, width=3)
            
            value_label = tk.Label(reg_frame, text="00", width=4, font=("Consolas", 10))
            value_label.pack(side=tk.LEFT)
            
            self.reg_labels[reg_name] = value_label

        # --- Memory Frame ---
        self.mem_frame = tk.LabelFrame(
            self.root, text="Memory", padx=10, pady=10,
            takefocus=0, highlightthickness=0
        )
        self.mem_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Button row frame
        self.mem_button_frame = tk.Frame(self.mem_frame, highlightthickness=0, bd=0)
        self.mem_button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

        # LOAD button - renamed from LOAD ROM
        self.load_rom_btn = tk.Button(
            self.mem_button_frame, text="LOAD", command=self.load_rom_from_file, width=10
        )
        self.load_rom_btn.pack(side=tk.LEFT, padx=5)

        # SAVE button - new
        self.save_rom_btn = tk.Button(
            self.mem_button_frame, text="SAVE", command=self.save_memory_to_file, width=10
        )
        self.save_rom_btn.pack(side=tk.LEFT, padx=5)

        # Scrollable canvas for memory rows
        self.mem_canvas = tk.Canvas(self.mem_frame, highlightthickness=0)
        self.vscroll = tk.Scrollbar(
            self.mem_frame, orient=tk.VERTICAL, command=self.mem_canvas.yview,
            takefocus=0
        )
        self.mem_canvas.configure(yscrollcommand=self.vscroll.set)

        self.vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.mem_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Inner frame to hold memory address rows
        self.mem_inner_frame = tk.Frame(self.mem_canvas, highlightthickness=0, bd=0)
        # Padding to reserve space for button at top
        self.mem_inner_frame.pack_configure(pady=(25, 0))
        self.mem_canvas.create_window(
            (0, 0), window=self.mem_inner_frame, anchor=tk.NW
        )

        # Populate memory rows
        self.populate_memory()

        # Update scroll region after population
        self.mem_inner_frame.update_idletasks()
        self.mem_canvas.configure(scrollregion=self.mem_canvas.bbox("all"))

        # Start pygame event pumping
        self.pump_pygame_events()
        
        # Initial register display
        self.update_registers()
        
        # Highlight initial PC address
        if self.vm.PC in self.addr_labels:
            self.highlight_address(self.vm.PC, highlight=True)
            self.highlighted_pc = self.vm.PC

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _create_reg_name_canvas(self, parent, text, width=3):
        """Create a canvas with text on light blue rounded rectangle background."""
        canvas_width = width * 12 + 10
        canvas_height = 24
        
        canvas = tk.Canvas(parent, width=canvas_width, height=canvas_height, 
                          bg="SystemButtonFace", highlightthickness=0)
        canvas.pack(side=tk.LEFT)
        
        rect_id = self.create_rounded_rect(canvas, 2, 2, canvas_width-2, canvas_height-2, 
                                            radius=6, fill="lightblue", outline="lightblue", width=0)
        
        text_id = canvas.create_text(canvas_width//2, canvas_height//2, 
                                    text=text, font=("Consolas", 10), fill="black")

    def create_rounded_rect(self, canvas, x1, y1, x2, y2, radius=8, **kwargs):
        """Draw a rounded rectangle on a canvas."""
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
        """Highlight or unhighlight an address label in the memory display."""
        if addr not in self.addr_labels:
            return
        
        canvas, text_id, rect_id, _ = self.addr_labels[addr]
        
        if highlight:
            canvas.itemconfig(text_id, fill="black", font=("Consolas", 10, "bold"))
            canvas.itemconfig(rect_id, fill="palegreen", outline="palegreen")
        else:
            canvas.itemconfig(text_id, fill="black", font=("Consolas", 10))
            canvas.itemconfig(rect_id, fill="SystemButtonFace", outline="SystemButtonFace")

    def update_registers(self):
        """Update the register display, showing changed values in red."""
        # Update V0-VF
        for i in range(16):
            reg_name = f"V{i:X}"
            new_val = self.vm.V[i]
            value_label = self.reg_labels[reg_name]
            
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
        
        # Update PC and highlight
        if self.vm.PC != self.prev_PC:
            self.PC_label.config(text=f"{self.vm.PC:04X}", fg="red")
            if self.highlighted_pc is not None and self.highlighted_pc in self.addr_labels:
                self.highlight_address(self.highlighted_pc, highlight=False)
            if self.vm.PC in self.addr_labels:
                self.highlight_address(self.vm.PC, highlight=True)
                self.highlighted_pc = self.vm.PC
            self.prev_PC = self.vm.PC
        else:
            self.PC_label.config(text=f"{self.vm.PC:04X}", fg="black")
        
        # Update SP
        sp = len(self.vm.stack)
        sp_hex = f"{sp:04X}"
        if sp != self.prev_SP:
            self.SP_label.config(text=sp_hex, fg="red")
            self.prev_SP = sp
        else:
            self.SP_label.config(text=sp_hex, fg="black")
        
        # Update DT
        if self.vm.delay_timer != self.prev_DT:
            self.DT_label.config(text=f"{self.vm.delay_timer:02X}", fg="red")
            self.prev_DT = self.vm.delay_timer
        else:
            self.DT_label.config(text=f"{self.vm.delay_timer:02X}", fg="black")
        
        # Update ST
        if self.vm.sound_timer != self.prev_ST:
            self.ST_label.config(text=f"{self.vm.sound_timer:02X}", fg="red")
            self.prev_ST = self.vm.sound_timer
        else:
            self.ST_label.config(text=f"{self.vm.sound_timer:02X}", fg="black")

    def populate_memory(self):
        """Populate the memory frame with rows for each even address starting at 0x200."""
        for addr in range(0x200, 0x1000, 2):
            high_byte = memory.read(addr)
            low_byte = memory.read(addr + 1)
            value = (high_byte << 8) | low_byte
            value_hex = f"{value:04X}"

            row = tk.Frame(self.mem_inner_frame, takefocus=0, highlightthickness=0, bd=0)
            row.pack(fill=tk.X, pady=2)

            addr_frame = tk.Frame(row, bg="SystemButtonFace", highlightthickness=0, bd=0)
            addr_frame.pack(side=tk.LEFT, padx=(0, 10))
            
            addr_canvas = tk.Canvas(addr_frame, width=70, height=24, bg="SystemButtonFace", 
                                     highlightthickness=0)
            addr_canvas.pack()
            
            rect_id = self.create_rounded_rect(addr_canvas, 2, 2, 68, 22, radius=8,
                                                  fill="SystemButtonFace", outline="SystemButtonFace", width=0)
            
            text_id = addr_canvas.create_text(35, 12, text=f"0x{addr:04X}", 
                                              font=("Consolas", 10), fill="black")
            
            self.addr_labels[addr] = (addr_canvas, text_id, rect_id, addr_frame)

            value_display = tk.Label(row, text=value_hex, width=6, font=("Consolas", 10),
                                    bg="white", relief="sunken", anchor="w")
            value_display.pack(side=tk.LEFT)

            entry = tk.Entry(row, width=6, font=("Consolas", 10),
                           highlightthickness=0, bd=1, takefocus=0,
                           insertofftime=0, insertwidth=2, exportselection=0,
                           bg="white", relief="sunken")
            entry.insert(0, value_hex)

            def on_key_press(event, ent=entry):
                if len(event.char) == 1 and event.char.isprintable():
                    cursor_pos = ent.index(tk.INSERT)
                    current_text = ent.get()
                    if cursor_pos < len(current_text):
                        new_text = current_text[:cursor_pos] + event.char + current_text[cursor_pos+1:]
                        ent.delete(0, tk.END)
                        ent.insert(0, new_text)
                        ent.icursor(cursor_pos + 1)
                        return "break"

            def start_edit(event, lbl=value_display, ent=entry, a=addr):
                lbl.pack_forget()
                ent.pack(side=tk.LEFT)
                ent.focus_set()
                ent.select_range(0, tk.END)
                ent.icursor(0)

            def finish_edit_with_nav(event, lbl=value_display, ent=entry, a=addr, direction=1):
                text = ent.get().strip().upper()
                if not text:
                    text = "0000"

                try:
                    value = int(text, 16)
                except ValueError:
                    messagebox.showerror("Invalid Input", f"'{text}' is not a valid hex value.")
                    ent.delete(0, tk.END)
                    ent.insert(0, lbl.cget("text"))
                    return "break"

                value &= 0xFFFF
                high_byte = (value >> 8) & 0xFF
                low_byte = value & 0xFF

                memory.write(a, high_byte)
                memory.write(a + 1, low_byte)

                formatted = f"{value:04X}"
                lbl.config(text=formatted)
                ent.delete(0, tk.END)
                ent.insert(0, formatted)

                ent.pack_forget()
                lbl.pack(side=tk.LEFT)

                self.refresh_memory()

                next_addr = a + (2 * direction)
                if 0x200 <= next_addr <= 0xFFE:
                    if next_addr in self.memory_entries:
                        next_widgets = self.memory_entries[next_addr]
                        next_widgets["label"].pack_forget()
                        next_widgets["entry"].pack(side=tk.LEFT)
                        next_widgets["entry"].focus_set()
                        next_widgets["entry"].select_range(0, tk.END)
                        next_widgets["entry"].icursor(0)

                return "break"

            def cancel_edit(event, lbl=value_display, ent=entry, a=addr):
                original = lbl.cget("text")
                ent.delete(0, tk.END)
                ent.insert(0, original)
                ent.pack_forget()
                lbl.pack(side=tk.LEFT)
                return "break"

            value_display.bind("<Button-1>", start_edit)
            entry.bind("<Return>", lambda e, lbl=value_display, ent=entry, a=addr: finish_edit_with_nav(e, lbl, ent, a, 1))
            entry.bind("<Tab>", lambda e, lbl=value_display, ent=entry, a=addr: finish_edit_with_nav(e, lbl, ent, a, 1))
            entry.bind("<Shift-Tab>", lambda e, lbl=value_display, ent=entry, a=addr: finish_edit_with_nav(e, lbl, ent, a, -1))
            entry.bind("<Escape>", cancel_edit)
            entry.bind("<KeyPress>", on_key_press)
            entry.bind("<FocusOut>", lambda e, lbl=value_display, ent=entry: (
                ent.pack_forget(), lbl.pack(side=tk.LEFT)))

            self.memory_entries[addr] = {"entry": entry, "label": value_display}

    def load_rom_from_file(self):
        """Open file dialog to select a ROM file and load it into memory at 0x200."""
        if self.is_running:
            self.stop_run()

        file_path = filedialog.askopenfilename(
            title="Select CHIP-8 ROM File",
            filetypes=[("Binary files", "*.bin *.rom *.ch8"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'rb') as f:
                rom_data = f.read()

            memory.load_rom(rom_data, start_address=0x200)

            print(f"\nDEBUG: load_rom_from_file(): Loaded {len(rom_data)} bytes from {file_path}")
            print(f"DEBUG: First bytes: {' '.join(f'{b:02X}' for b in rom_data[:10])}")

            self.vm.reset()
            
            self.refresh_memory()
            self.update_registers()

            messagebox.showinfo("ROM Loaded", f"Loaded {len(rom_data)} bytes from {file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load ROM: {str(e)}")

    def save_memory_to_file(self):
        """Open file dialog to save current emulator memory to a binary file."""
        if self.is_running:
            self.stop_run()

        file_path = filedialog.asksaveasfilename(
            title="Save Memory to Binary File",
            filetypes=[("Binary files", "*.bin *.rom *.ch8"), ("All files", "*.*")],
            defaultextension=".bin"
        )

        if not file_path:
            return

        try:
            # Collect memory bytes from 0x200 to the end of loaded program
            # We'll save from 0x200 to 0xFFF (all user ROM area)
            memory_bytes = []
            for addr in range(0x200, 0x1000):
                memory_bytes.append(memory.read(addr))

            with open(file_path, 'wb') as f:
                f.write(bytes(memory_bytes))

            print(f"\nDEBUG: save_memory_to_file(): Saved {len(memory_bytes)} bytes to {file_path}")
            print(f"DEBUG: First bytes: {' '.join(f'{b:02X}' for b in memory_bytes[:10])}")

            messagebox.showinfo("Memory Saved", f"Saved {len(memory_bytes)} bytes to {file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save memory: {str(e)}")

    def set_memory_editable(self, editable):
        """Enable/disable memory entries based on VM running state."""
        for addr, widgets in self.memory_entries.items():
            if editable:
                widgets["label"].bind("<Button-1>", 
                    lambda e, a=addr, lbl=widgets["label"], ent=widgets["entry"]: (
                        lbl.pack_forget(),
                        ent.pack(side=tk.LEFT),
                        ent.focus_set(),
                        ent.icursor(0)
                    ))
            else:
                widgets["label"].unbind("<Button-1>")

    def refresh_memory(self):
        """Refresh all memory entries to reflect current memory contents."""
        for addr, widgets in self.memory_entries.items():
            high_byte = memory.read(addr)
            low_byte = memory.read(addr + 1)
            value = (high_byte << 8) | low_byte
            formatted = f"{value:04X}"
            widgets["label"].config(text=formatted)
            widgets["entry"].delete(0, tk.END)
            widgets["entry"].insert(0, formatted)

    def pump_pygame_events(self):
        """Periodically pump pygame events to keep the display responsive."""
        pygame.event.pump()
        self.root.after(100, self.pump_pygame_events)

    def on_close(self):
        """Cleanup pygame and close the application."""
        pygame.quit()
        self.root.destroy()

    # Control button handlers
    def blur_edit_then_run(self):
        self.root.focus_set()
        self.start_run()

    def blur_edit_then_stop(self):
        self.root.focus_set()
        self.stop_run()

    def blur_edit_then_step(self):
        self.root.focus_set()
        self.single_step()

    def blur_edit_then_reset(self):
        self.root.focus_set()
        self.reset_vm()

    def start_run(self):
        if not self.is_running:
            self.is_running = True
            self.set_memory_editable(False)
            self.status_value.config(text="RUNNING", fg="green")
            self.run_step()

    def run_step(self):
        if self.is_running:
            try:
                self.vm.execute_instruction()
                self.update_registers()
            except Exception as e:
                messagebox.showerror("VM Execution Error", str(e))
                self.stop_run()
                return

            try:
                delay = int(self.delay_entry.get())
                delay = max(0, delay)
            except ValueError:
                delay = 500

            self.root.after(delay, self.run_step)

    def stop_run(self):
        self.is_running = False
        self.set_memory_editable(True)
        self.status_value.config(text="STOPPED", fg="red")

    def single_step(self):
        try:
            self.vm.execute_instruction()
            self.update_registers()
        except Exception as e:
            messagebox.showerror("VM Execution Error", str(e))

    def reset_vm(self):
        self.is_running = False
        self.vm.reset()
        display.clear()
        self.set_memory_editable(True)
        self.refresh_memory()
        self.update_registers()
        self.status_value.config(text="STOPPED", fg="red")


if __name__ == "__main__":
    root = tk.Tk()
    app = Chip8Gui(root)
    root.mainloop()