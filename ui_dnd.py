import customtkinter as ctk
from tkinterdnd2 import DND_FILES

class DragDropWindow(ctk.CTkFrame):
    def __init__(self, master, on_files_dropped_callback):
        super().__init__(master)
        self.on_files_dropped = on_files_dropped_callback

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.label_frame = ctk.CTkFrame(self, border_width=2, border_color="gray")
        self.label_frame.grid(row=0, column=0, padx=50, pady=50, sticky="nsew")

        self.lbl_instruction = ctk.CTkLabel(
            self.label_frame, 
            text="請將檔案拖曳至此處\n(Drag & Drop Files Here)",
            font=("Arial", 24)
        )
        self.lbl_instruction.place(relx=0.5, rely=0.5, anchor="center")

        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        if event.data:
            files = self.parse_dnd_files(event.data)
            self.on_files_dropped(files)

    def parse_dnd_files(self, data_str):
        files = []
        buf = ""
        in_curly = False
        for char in data_str:
            if char == '{': in_curly = True
            elif char == '}': in_curly = False
            elif char == ' ' and not in_curly:
                if buf: files.append(buf); buf = ""
            else: buf += char
        if buf: files.append(buf)
        return files