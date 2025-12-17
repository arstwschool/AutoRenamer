import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import threading
import os
import sys

from ai_service import AIService 
from ui_config import APIConfigDialog

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class RenamerWindow(ctk.CTkFrame):
    def __init__(self, master, manager, on_back_callback):
        super().__init__(master)
        self.manager = manager
        self.on_back_callback = on_back_callback
        
        try:
            self.img_file = ctk.CTkImage(
                light_image=Image.open(resource_path("img/file.png")), 
                dark_image=Image.open(resource_path("img/file.png")), 
                size=(20, 20)
            )
            self.img_folder = ctk.CTkImage(
                light_image=Image.open(resource_path("img/folder.png")), 
                dark_image=Image.open(resource_path("img/folder.png")), 
                size=(20, 20)
            )
        except Exception as e:
            print(f"Warning: 無法載入圖標 ({e})")
            self.img_file = None
            self.img_folder = None

        self.setup_ui()
        
        _, removed = self.manager.validate_files()
        if removed > 0:
            messagebox.showinfo("檔案變更", f"有 {removed} 個檔案已不存在，已從列表中移除。")

        self.update_preview() 
        
        self.entry_pattern.focus_set()

    def setup_ui(self):
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", padx=10, pady=10)

        # RegEx Pattern
        ctk.CTkLabel(input_frame, text="RegEx 查找:").grid(row=0, column=0, padx=5, sticky="w")
        self.entry_pattern = ctk.CTkEntry(input_frame, width=300)
        self.entry_pattern.grid(row=0, column=1, padx=5, pady=5)
        self.entry_pattern.bind("<KeyRelease>", self.update_preview)

        # Replacement
        ctk.CTkLabel(input_frame, text="替換為:").grid(row=0, column=2, padx=5, sticky="w")
        self.entry_repl = ctk.CTkEntry(input_frame, width=300)
        self.entry_repl.grid(row=0, column=3, padx=5, pady=5)
        self.entry_repl.bind("<KeyRelease>", self.update_preview)

        hint_label = ctk.CTkLabel(
            input_frame, 
            text="提示: 使用 (...) 捕獲群組，使用 $1, $2 來引用。", 
            text_color="gray", 
            font=("Arial", 10)
        )
        hint_label.grid(row=1, column=0, columnspan=4, sticky="w", padx=5)

        self.lbl_status = ctk.CTkLabel(input_frame, text="準備就緒", text_color="gray")
        self.lbl_status.grid(row=2, column=0, columnspan=4, sticky="w", padx=5)

        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=30)
        header_frame.pack(fill="x", padx=10)
        
        header_frame.grid_columnconfigure(0, weight=0) # Icon
        header_frame.grid_columnconfigure(1, weight=4) # 原檔名
        header_frame.grid_columnconfigure(2, weight=0) # 箭頭
        header_frame.grid_columnconfigure(3, weight=4) # 新檔名
        header_frame.grid_columnconfigure(4, weight=0) # AI 按鈕
        header_frame.grid_columnconfigure(5, weight=0) # 刪除按鈕

        ctk.CTkLabel(header_frame, text="", width=30).grid(row=0, column=0)
        ctk.CTkLabel(header_frame, text="原檔名", anchor="w", font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="ew", padx=5)
        ctk.CTkLabel(header_frame, text="➜").grid(row=0, column=2)
        ctk.CTkLabel(header_frame, text="新檔名", anchor="w", font=("Arial", 12, "bold")).grid(row=0, column=3, sticky="ew", padx=5)
        ctk.CTkLabel(header_frame, text="AI", width=30, font=("Arial", 12, "bold")).grid(row=0, column=4, padx=5)
        ctk.CTkLabel(header_frame, text="刪除", width=40, font=("Arial", 12, "bold")).grid(row=0, column=5, padx=5)

        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.preview_items_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.preview_items_frame.pack(fill="both", expand=True)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)

        self.btn_add = ctk.CTkButton(btn_frame, text="+ 加入更多檔案", command=self.on_back_callback, fg_color="#555")
        self.btn_add.pack(side="left", padx=5)

        self.btn_undo = ctk.CTkButton(btn_frame, text="⟲ Undo", command=self.do_undo, state="disabled", fg_color="gray")
        self.btn_undo.pack(side="left", padx=5)

        self.btn_redo = ctk.CTkButton(btn_frame, text="⟳ Redo", command=self.do_redo, state="disabled", fg_color="gray")
        self.btn_redo.pack(side="left", padx=5)

        self.btn_confirm = ctk.CTkButton(btn_frame, text="確認並批量重命名", command=self.do_rename, fg_color="green")
        self.btn_confirm.pack(side="right", padx=5)

    def update_preview(self, event=None):
        pattern = self.entry_pattern.get()
        repl = self.entry_repl.get()

        for widget in self.preview_items_frame.winfo_children():
            widget.destroy()

        self.current_previews, error, has_conflict = self.manager.get_preview(pattern, repl)

        if error:
            self.lbl_status.configure(text=error, text_color="red")
            self.btn_confirm.configure(state="disabled", fg_color="gray")
        elif has_conflict:
            self.lbl_status.configure(text="警告：檢測到檔名衝突！", text_color="orange")
            self.btn_confirm.configure(state="normal", fg_color="#D97706") # Dark Orange
        else:
            self.lbl_status.configure(text=f"列表共 {len(self.current_previews)} 個項目", text_color="green")
            self.btn_confirm.configure(state="normal", fg_color="green")

        self.preview_items_frame.grid_columnconfigure(0, weight=0)
        self.preview_items_frame.grid_columnconfigure(1, weight=4)
        self.preview_items_frame.grid_columnconfigure(2, weight=0)
        self.preview_items_frame.grid_columnconfigure(3, weight=4)
        self.preview_items_frame.grid_columnconfigure(4, weight=0)
        self.preview_items_frame.grid_columnconfigure(5, weight=0)

        for i, item in enumerate(self.current_previews):
            row_color = "transparent" if i % 2 == 0 else ("#2b2b2b" if ctk.get_appearance_mode()=="Dark" else "#e0e0e0")
            
            row_frame = ctk.CTkFrame(self.preview_items_frame, fg_color=row_color, height=35)
            row_frame.pack(fill="x", pady=1)
            
            row_frame.grid_columnconfigure(0, weight=0)
            row_frame.grid_columnconfigure(1, weight=4)
            row_frame.grid_columnconfigure(2, weight=0)
            row_frame.grid_columnconfigure(3, weight=4)
            row_frame.grid_columnconfigure(4, weight=0)
            row_frame.grid_columnconfigure(5, weight=0)

            icon_img = self.img_folder if item['is_dir'] else self.img_file
            if icon_img:
                ctk.CTkLabel(row_frame, text="", image=icon_img, width=30).grid(row=0, column=0, padx=5)
            else:
                ctk.CTkLabel(row_frame, text="[F]" if item['is_dir'] else "[D]", width=30).grid(row=0, column=0, padx=5)

            ctk.CTkLabel(row_frame, text=item['original'], anchor="w").grid(row=0, column=1, sticky="ew", padx=5)
            
            ctk.CTkLabel(row_frame, text="➜", text_color="gray").grid(row=0, column=2)

            new_text = item['new']
            status_text = ""
            label_text_color = "text_color"
            
            if item.get('is_overridden'):
                # status_text = " [AI]"
                status_text = ""
                label_text_color = "#3498DB"
            elif item['status'] != 'ok':
                status_text = f" [{item['status']}]"
                if item['status'] == 'conflict': label_text_color = "orange"
                if item['status'] == 'duplicate': label_text_color = "red"
                
            ctk.CTkLabel(
                row_frame, 
                text=new_text + status_text, 
                anchor="w", 
                text_color=label_text_color if label_text_color != "text_color" else None
            ).grid(row=0, column=3, sticky="ew", padx=5)
            
            if not item['is_dir']:
                btn_ai = ctk.CTkButton(
                    row_frame, 
                    text="✨", 
                    width=30, 
                    height=24, 
                    fg_color="#8E44AD", 
                    hover_color="#9B59B6",
                    command=lambda p=item['full_old'], uid=item['id']: self.run_ai_analysis(uid, p)
                )
                btn_ai.grid(row=0, column=4, padx=2, pady=2)
            
            btn_del = ctk.CTkButton(
                row_frame, 
                text="X", 
                width=30, 
                height=24, 
                fg_color="#C0392B", 
                hover_color="#E74C3C",
                command=lambda uid=item['id']: self.remove_item(uid)
            )
            btn_del.grid(row=0, column=5, padx=5, pady=2)

    def run_ai_analysis(self, uid, file_path):        
        if not AIService.is_configured():
            APIConfigDialog(self, lambda ep, key: self.on_api_configured(ep, key, uid, file_path))
            return

        self.execute_ai_thread(uid, file_path)

    def on_api_configured(self, endpoint, key, uid, file_path):
        AIService.configure(key, endpoint)
        self.execute_ai_thread(uid, file_path)

    def execute_ai_thread(self, uid, file_path):
        def task():
            self.lbl_status.configure(text="AI 分析中 (上傳與運算)...", text_color="blue")
            
            new_name, msg = AIService.analyze_and_rename(file_path)
            
            self.after(0, lambda: self.handle_ai_result(uid, new_name, msg))

        threading.Thread(target=task, daemon=True).start()

    def handle_ai_result(self, uid, new_name, msg):
        if new_name:
            self.manager.set_file_override(uid, new_name)
            self.lbl_status.configure(text=msg, text_color="green")
            self.update_preview()
        else:
            messagebox.showerror("AI 分析失敗", msg)
            self.lbl_status.configure(text=f"AI 錯誤: {msg}", text_color="red")

    def remove_item(self, uid):
        self.manager.remove_file_by_id(uid)
        self.update_buttons_state()
        self.update_preview()

    def do_rename(self):
        _, _, has_conflict = self.manager.get_preview(self.entry_pattern.get(), self.entry_repl.get())
        if has_conflict:
            if not messagebox.askyesno("衝突警告", "檢測到檔名衝突。\n確定要繼續嗎？"):
                return

        success, msg = self.manager.execute_rename(self.current_previews)
        if success:
            self.lbl_status.configure(text=msg, text_color="green")
            self.entry_pattern.delete(0, 'end')
            self.entry_repl.delete(0, 'end')
            self.update_buttons_state()
            self.update_preview()
        else:
            messagebox.showerror("錯誤", msg)

    def do_undo(self):
        success, msg = self.manager.undo()
        self.handle_history_op(success, msg)

    def do_redo(self):
        success, msg = self.manager.redo()
        self.handle_history_op(success, msg)

    def handle_history_op(self, success, msg):
        if success:
            self.lbl_status.configure(text=msg, text_color="blue")
            self.update_buttons_state()
            self.update_preview()
        else:
            messagebox.showerror("錯誤", msg)
            self.update_preview() # 刷新列表以移除可能已遺失的檔案

    def update_buttons_state(self):
        """更新 Undo/Redo 按鈕的可用狀態"""
        self.btn_undo.configure(
            state="normal" if self.manager.history else "disabled", 
            fg_color="#3B8ED0" if self.manager.history else "gray"
        )
        self.btn_redo.configure(
            state="normal" if self.manager.redo_stack else "disabled", 
            fg_color="#3B8ED0" if self.manager.redo_stack else "gray"
        )