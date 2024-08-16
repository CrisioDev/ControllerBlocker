import tkinter as tk
from tkinter import messagebox, Listbox, MULTIPLE, Entry
import psutil
import pygame
import threading
import time

# Initialize pygame for controller detection
pygame.init()
pygame.joystick.init()


class ControllerBlockerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Controller Blocker")

        # Data structures
        self.controllers = {}
        self.blocked_programs = {}
        self.all_programs = []  # Stores all programs to filter with search
        self.blocking_active = True  # Controls the blocking logic

        # GUI Layout
        self.setup_gui()

        # Start blocking logic in a separate thread
        self.blocking_thread = threading.Thread(target=self.start_blocking_logic, daemon=True)
        self.blocking_thread.start()

        # Update loop to monitor running programs and controllers
        self.update_controller_list()
        self.update_program_list()

    def setup_gui(self):
        # Frame for controller selection
        self.controller_frame = tk.Frame(self.root)
        self.controller_frame.pack(side=tk.LEFT, padx=10, pady=10)

        tk.Label(self.controller_frame, text="Connected Controllers").pack()
        self.controller_listbox = Listbox(self.controller_frame, selectmode=tk.SINGLE)
        self.controller_listbox.pack()
        self.controller_listbox.bind('<<ListboxSelect>>', self.on_controller_select)

        # Frame for program list with search functionality
        self.program_frame = tk.Frame(self.root)
        self.program_frame.pack(side=tk.LEFT, padx=10, pady=10)

        tk.Label(self.program_frame, text="Running Programs").pack()

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_search)  # Update search results on every keystroke
        self.search_entry = Entry(self.program_frame, textvariable=self.search_var)
        self.search_entry.pack(pady=5)

        self.program_listbox = Listbox(self.program_frame, selectmode=MULTIPLE)
        self.program_listbox.pack()

        # Frame for blocked programs
        self.blocked_programs_frame = tk.Frame(self.root)
        self.blocked_programs_frame.pack(side=tk.LEFT, padx=10, pady=10)

        tk.Label(self.blocked_programs_frame, text="Blocked Programs for Selected Controller").pack()
        self.blocked_programs_listbox = Listbox(self.blocked_programs_frame)
        self.blocked_programs_listbox.pack()

        # Buttons
        self.add_button = tk.Button(self.blocked_programs_frame, text="Block", command=self.block_programs)
        self.add_button.pack(pady=5)

        self.remove_button = tk.Button(self.blocked_programs_frame, text="Unblock", command=self.unblock_programs)
        self.remove_button.pack(pady=5)

    def update_controller_list(self):
        # Update the list of connected controllers
        self.controller_listbox.delete(0, tk.END)
        self.controllers = {}

        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            controller_name = joystick.get_name()
            self.controllers[controller_name] = joystick
            self.controller_listbox.insert(tk.END, controller_name)

        # Call this function again every 2 seconds
        self.root.after(2000, self.update_controller_list)

    def update_program_list(self):
        # Update the list of running programs
        self.all_programs = [p.info['name'] for p in psutil.process_iter(['name'])]  # Store all programs
        self.update_search()  # Update the list based on current search

        # Call this function again every 2 seconds
        self.root.after(2000, self.update_program_list)

    def update_search(self, *args):
        search_term = self.search_var.get().lower()
        self.program_listbox.delete(0, tk.END)
        filtered_programs = [p for p in self.all_programs if search_term in p.lower()]

        for program in filtered_programs:
            self.program_listbox.insert(tk.END, program)

    def on_controller_select(self, event):
        # When a controller is selected, show the blocked programs
        selected_controller = self.controller_listbox.get(tk.ACTIVE)
        self.blocked_programs_listbox.delete(0, tk.END)

        if selected_controller in self.blocked_programs:
            for program in self.blocked_programs[selected_controller]:
                self.blocked_programs_listbox.insert(tk.END, program)

    def block_programs(self):
        selected_controller = self.controller_listbox.get(tk.ACTIVE)
        selected_programs = [self.program_listbox.get(i) for i in self.program_listbox.curselection()]

        if selected_controller not in self.blocked_programs:
            self.blocked_programs[selected_controller] = []

        for program in selected_programs:
            if program not in self.blocked_programs[selected_controller]:
                self.blocked_programs[selected_controller].append(program)

        self.on_controller_select(None)

    def unblock_programs(self):
        selected_controller = self.controller_listbox.get(tk.ACTIVE)
        selected_programs = [self.blocked_programs_listbox.get(i) for i in self.blocked_programs_listbox.curselection()]

        if selected_controller in self.blocked_programs:
            for program in selected_programs:
                if program in self.blocked_programs[selected_controller]:
                    self.blocked_programs[selected_controller].remove(program)

        self.on_controller_select(None)

    def is_program_running(self, program_name):
        """Checks if a specific program is currently running."""
        return any(program_name.lower() in (p.info['name'] or '').lower() for p in psutil.process_iter(['name']))

    def start_blocking_logic(self):
        while self.blocking_active:
            for controller_name, joystick in self.controllers.items():
                if controller_name in self.blocked_programs:
                    for program in self.blocked_programs[controller_name]:
                        if self.is_program_running(program):
                            # Block controller inputs for the program
                            for event in pygame.event.get():
                                if event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION):
                                    print(f"Input blocked for {controller_name} while {program} is running.")
                                    # Ignore the input
                                    continue
            time.sleep(0.1)  # Short delay to reduce CPU usage


def run_app():
    root = tk.Tk()
    app = ControllerBlockerApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()
