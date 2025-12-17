import customtkinter as ctk

class APIConfigDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_confirm_callback):
        super().__init__(parent)
        self.on_confirm = on_confirm_callback
        
        self.title("OpenAI API 設定")
        self.geometry("400x250")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()

        self.setup_ui()
        
        self.center_window(parent)

    def center_window(self, parent):
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        ctk.CTkLabel(self, text="請輸入 API 資訊", font=("Arial", 16, "bold")).pack(pady=15)

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=20)

        ctk.CTkLabel(input_frame, text="API Endpoint:").pack(anchor="w")
        self.entry_endpoint = ctk.CTkEntry(input_frame, placeholder_text="預設: https://api.openai.com/v1")
        self.entry_endpoint.pack(fill="x", pady=(0, 10))

        self.entry_endpoint.insert(0, "https://api.openai.com/v1")

        ctk.CTkLabel(input_frame, text="API Key:").pack(anchor="w")
        self.entry_key = ctk.CTkEntry(input_frame, show="*", placeholder_text="sk-...")
        self.entry_key.pack(fill="x", pady=(0, 10))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(btn_frame, text="取消", fg_color="gray", command=self.destroy).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="確認", fg_color="green", command=self.on_submit).pack(side="right", expand=True, padx=5)

    def on_submit(self):
        endpoint = self.entry_endpoint.get().strip()
        key = self.entry_key.get().strip()

        if not endpoint:
            endpoint = "https://api.openai.com/v1"
        
        if not key:
            self.entry_key.configure(placeholder_text="請務必輸入 API Key !", border_color="red")
            return

        self.on_confirm(endpoint, key)
        self.destroy()