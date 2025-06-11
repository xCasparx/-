import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, font, ttk
import os
from datetime import datetime

class Notepad:
    def __init__(self, root):
        self.root = root
        self.root.title("進階記事本")
        self.root.geometry("800x600")
        self.filename = None
        self.saved_filepath = None
        self.auto_save_enabled = True
        self.auto_save_interval = 1000
        self.current_font_size = 14
        self.is_modified = False

        # 創建工具列
        self.toolbar = tk.Frame(root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # 工具列按鈕
        self.create_toolbar_buttons()
        
        # 創建狀態欄
        self.status_bar = tk.Label(root, text="就緒", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 設置文字編輯區域
        self.text_frame = tk.Frame(root)
        self.text_frame.pack(expand='yes', fill='both')
        
        self.text = tk.Text(self.text_frame, wrap='word', font=("Arial", self.current_font_size), 
                           undo=True, bg="#f4f4f4", fg="#333")
        self.text.pack(side=tk.LEFT, expand='yes', fill='both', padx=10, pady=10)
        
        # 添加垂直滾動條
        self.scrollbar = ttk.Scrollbar(self.text_frame, orient="vertical", command=self.text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.configure(yscrollcommand=self.scrollbar.set)

        # 綁定事件
        self.text.bind('<<Modified>>', self.on_text_modified)
        self.text.bind('<Key>', self.update_status)
        
        # 設置選單
        self.create_menu()
        
        # 自動儲存設置
        self.auto_save_folder = "autosave"
        if not os.path.exists(self.auto_save_folder):
            os.makedirs(self.auto_save_folder)

        self.prompt_for_filename()
        self.auto_save_task = self.root.after(self.auto_save_interval, self.auto_save)

    def create_toolbar_buttons(self):
        # 新建按鈕
        new_btn = ttk.Button(self.toolbar, text="新建", command=self.new_file)
        new_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 開啟按鈕
        open_btn = ttk.Button(self.toolbar, text="開啟", command=self.open_file)
        open_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 儲存按鈕
        save_btn = ttk.Button(self.toolbar, text="儲存", command=self.save_file)
        save_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 搜尋按鈕
        search_btn = ttk.Button(self.toolbar, text="搜尋", command=self.search_text)
        search_btn.pack(side=tk.LEFT, padx=2, pady=2)

    def create_menu(self):
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        
        # 檔案選單
        self.file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="檔案", menu=self.file_menu)
        self.file_menu.add_command(label="新建", command=self.new_file)
        self.file_menu.add_command(label="開啟", command=self.open_file)
        self.file_menu.add_command(label="儲存", command=self.save_file)
        self.file_menu.add_command(label="另存新檔", command=self.save_file_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="關閉", command=self.root.quit)

        # 編輯選單
        self.edit_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="編輯", menu=self.edit_menu)
        self.edit_menu.add_command(label="復原", command=self.text.edit_undo)
        self.edit_menu.add_command(label="重做", command=self.text.edit_redo)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="剪下", command=lambda: self.text.event_generate("<<Cut>>"))
        self.edit_menu.add_command(label="複製", command=lambda: self.text.event_generate("<<Copy>>"))
        self.edit_menu.add_command(label="貼上", command=lambda: self.text.event_generate("<<Paste>>"))
        self.edit_menu.add_command(label="刪除", command=lambda: self.text.delete("sel.first", "sel.last"))
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="全選", command=lambda: self.text.tag_add("sel", "1.0", "end"))

        # 自動儲存選單
        self.auto_save_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="自動儲存", menu=self.auto_save_menu)
        self.auto_save_menu.add_command(label="開啟/關閉自動儲存", command=self.toggle_auto_save)
        self.auto_save_menu.add_command(label="設定自動儲存間隔", command=self.set_auto_save_interval)
        self.auto_save_menu.add_command(label="打開自動儲存文件", command=self.open_autosave_file)

        # 字型大小選單
        self.font_size_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="字型大小", menu=self.font_size_menu)
        for size in [10, 12, 14, 16, 18, 20, 24, 28, 32]:
            self.font_size_menu.add_command(label=str(size), command=lambda size=size: self.change_font_size(size))

    def new_file(self):
        if self.is_modified:
            if not messagebox.askyesno("確認", "是否要儲存當前文件？"):
                return
            self.save_file()
        self.text.delete(1.0, tk.END)
        self.filename = None
        self.saved_filepath = None
        self.is_modified = False
        self.update_status()

    def on_text_modified(self, event=None):
        self.is_modified = True
        self.update_status()
        self.text.edit_modified(False)

    def update_status(self, event=None):
        if self.filename:
            status = f"檔案: {self.filename} | "
        else:
            status = "未命名 | "
        
        # 獲取當前游標位置
        try:
            line, col = self.text.index(tk.INSERT).split('.')
            status += f"行: {line} 列: {col} | "
        except:
            pass
        
        # 獲取字數統計
        content = self.text.get(1.0, tk.END)
        char_count = len(content)
        word_count = len(content.split())
        status += f"字數: {char_count} 詞數: {word_count}"
        
        self.status_bar.config(text=status)

    def search_text(self):
        search_window = tk.Toplevel(self.root)
        search_window.title("搜尋")
        search_window.geometry("300x100")
        
        search_frame = tk.Frame(search_window)
        search_frame.pack(padx=10, pady=10)
        
        search_label = tk.Label(search_frame, text="搜尋:")
        search_label.pack(side=tk.LEFT)
        
        search_entry = tk.Entry(search_frame)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.focus_set()
        
        def do_search():
            search_term = search_entry.get()
            if search_term:
                self.text.tag_remove('search', '1.0', tk.END)
                start_pos = '1.0'
                while True:
                    start_pos = self.text.search(search_term, start_pos, tk.END, nocase=True)
                    if not start_pos:
                        break
                    end_pos = f"{start_pos}+{len(search_term)}c"
                    self.text.tag_add('search', start_pos, end_pos)
                    start_pos = end_pos
                self.text.tag_config('search', background='yellow')
        
        search_button = ttk.Button(search_frame, text="搜尋", command=do_search)
        search_button.pack(side=tk.LEFT, padx=5)

    def prompt_for_filename(self):
        self.filename = simpledialog.askstring("命名檔案", "請輸入文件名稱：")
        if self.filename is None or not self.filename.strip():
            result = messagebox.askyesno("自動命名", "文件名不能為空！是否使用自動命名？")
            if result:
                self.auto_name()
            else:
                self.prompt_for_filename()
        else:
            self.filename = self.filename.strip()
            if len(self.filename) > 50:
                messagebox.showwarning("名稱過長", "文件名過長，請重新輸入。")
                self.prompt_for_filename()
            else:
                self.saved_filepath = os.path.join(self.auto_save_folder, f"{self.filename}.txt")

    def open_file(self):
        filepath = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if filepath:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
                self.text.delete(1.0, tk.END)
                self.text.insert(tk.END, content)
            self.filename = os.path.basename(filepath).split('.')[0]
            self.saved_filepath = filepath

    def save_file(self):
        if not self.filename:
            self.prompt_for_filename()
        filepath = filedialog.asksaveasfilename(initialfile=self.filename, defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if filepath:
            with open(filepath, "w", encoding="utf-8") as file:
                content = self.text.get(1.0, tk.END)
                file.write(content)
            self.filename = os.path.basename(filepath).split('.')[0]
            self.saved_filepath = filepath

    def save_file_as(self):
        filepath = filedialog.asksaveasfilename(initialfile=self.filename, defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if filepath:
            with open(filepath, "w", encoding="utf-8") as file:
                content = self.text.get(1.0, tk.END)
                file.write(content)
            self.filename = os.path.basename(filepath).split('.')[0]
            self.saved_filepath = filepath

    def auto_save(self):
        if self.auto_save_enabled and self.filename:
            autosave_path = os.path.join(self.auto_save_folder, f"{self.filename}.txt")
            with open(autosave_path, "w", encoding="utf-8") as file:
                content = self.text.get(1.0, tk.END)
                file.write(content)
        self.auto_save_task = self.root.after(self.auto_save_interval, self.auto_save)

    def toggle_auto_save(self):
        self.auto_save_enabled = not self.auto_save_enabled
        status = "開啟" if self.auto_save_enabled else "關閉"
        messagebox.showinfo("自動儲存", f"自動儲存已{status}。")

    def set_auto_save_interval(self):
        interval_str = simpledialog.askstring("設定自動儲存間隔", "請輸入自動儲存間隔（毫秒）：")
        if interval_str is None or not interval_str.strip():
            return
        try:
            interval = int(interval_str)
            if interval > 0:
                self.auto_save_interval = interval
                messagebox.showinfo("設定成功", f"自動儲存間隔已設定為 {interval} 毫秒。")
                self.root.after_cancel(self.auto_save_task)
                self.auto_save_task = self.root.after(self.auto_save_interval, self.auto_save)
            else:
                messagebox.showwarning("設定錯誤", "請輸入正確的間隔時間（毫秒）。")
        except ValueError:
            messagebox.showwarning("設定錯誤", "請輸入有效的數字。")

    def open_autosave_file(self):
        files = os.listdir(self.auto_save_folder)
        if not files:
            messagebox.showinfo("提示", "沒有自動儲存的文件。")
            return

        top = tk.Toplevel(self.root)
        top.title("選擇自動儲存文件")
        top.geometry("300x300")
        frame = tk.Frame(top)
        frame.pack(fill='both', expand=True)

        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)

        file_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=file_frame, anchor="nw")

        for file in files:
            button_frame = tk.Frame(file_frame)
            button_frame.pack(fill='x', padx=10, pady=5)

            # 查看文件按鈕
            view_btn = tk.Button(button_frame, text=file, font=("Arial", 12), bg="#e0e0e0", command=lambda f=file: self.load_file(f, top))
            view_btn.pack(side='left', fill='x', expand=True)

            # 刪除文件按鈕
            delete_btn = tk.Button(button_frame, text="刪除", font=("Arial", 12), bg="#f8d7da", command=lambda f=file: self.delete_autosave_file(f, top))
            delete_btn.pack(side='right', padx=5)

        file_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        top.bind_all("<MouseWheel>", self.on_mouse_wheel)

    def load_file(self, filename, window):
        """載入自動儲存的文件"""
        filepath = os.path.join(self.auto_save_folder, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
                self.text.delete(1.0, tk.END)
                self.text.insert(tk.END, content)
            self.filename = os.path.splitext(filename)[0]
            self.saved_filepath = filepath
            window.destroy()
        else:
            messagebox.showwarning("錯誤", f"文件 '{filename}' 不存在。")

    def delete_autosave_file(self, filename, window):
        """刪除自動儲存的文件"""
        result = messagebox.askyesno("確認刪除", f"你確定要刪除文件 '{filename}' 嗎？")
        if result:
            filepath = os.path.join(self.auto_save_folder, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                messagebox.showinfo("刪除成功", f"文件 '{filename}' 已刪除。")
                window.destroy()
            else:
                messagebox.showwarning("刪除失敗", f"文件 '{filename}' 不存在。")

    def auto_name(self):
        base_name = "紀錄"
        counter = 1
        while os.path.exists(os.path.join(self.auto_save_folder, f"{base_name}{counter}.txt")):
            counter += 1
        self.filename = f"{base_name}{counter}"
        self.saved_filepath = os.path.join(self.auto_save_folder, f"{self.filename}.txt")
        messagebox.showinfo("自動命名", f"文件已命名為: {self.filename}")

    def change_font_size(self, size):
        """更改文字區域的字型大小"""
        self.current_font_size = size
        self.text.configure(font=("Arial", self.current_font_size))

    def on_mouse_wheel(self, event):
        """處理滾輪事件。"""
        if event.widget.winfo_class() == 'Canvas':
            event.widget.yview_scroll(int(-1*(event.delta/120)), "units")

if __name__ == "__main__":
    root = tk.Tk()
    app = Notepad(root)
    root.mainloop()
