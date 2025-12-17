import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
from logic import RenameManager
from ui_dnd import DragDropWindow
from ui_renamer import RenamerWindow

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class MainApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        
        self.title("AI 智慧批量重命名工具")
        self.geometry("900x600")
        
        self.manager = RenameManager()
        
        self.frame_dnd = DragDropWindow(self, self.on_files_dropped)
        self.frame_renamer = None 
        
        self.frame_dnd.pack(fill="both", expand=True)

    def on_files_dropped(self, files):
        if not self.manager.files:
            self.manager.set_files(files)
        else:
            self.manager.add_files(files)
            
        self.switch_to_renamer()

    def switch_to_renamer(self):
        self.frame_dnd.pack_forget()
        
        if self.frame_renamer:
            self.frame_renamer.destroy()
            
        self.frame_renamer = RenamerWindow(self, self.manager, self.switch_to_dnd)
        self.frame_renamer.pack(fill="both", expand=True)

    def switch_to_dnd(self):
        if self.frame_renamer:
            self.frame_renamer.pack_forget()
        self.frame_dnd.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()