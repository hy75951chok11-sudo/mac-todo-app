import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from todo_manager import TodoManager

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class TaskDialog(ctk.CTkToplevel):
    def __init__(self, master, title="Add Task", todo=None, callback=None):
        super().__init__(master)
        self.title(title)
        self.geometry("400x500")
        self.callback = callback
        self.todo = todo
        
        # Make it modal
        self.transient(master)
        self.grab_set()
        
        # Focus handling
        self.after(100, self.focus_force)

        # Main frame
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Title
        self.title_label = ctk.CTkLabel(self.frame, text="Task Title:", anchor="w")
        self.title_label.pack(fill="x", pady=(0, 5))
        self.title_entry = ctk.CTkEntry(self.frame, placeholder_text="Enter task title")
        self.title_entry.pack(fill="x", pady=(0, 15))

        # Due Date
        self.due_date_label = ctk.CTkLabel(self.frame, text="Due Date (e.g. 2024-12-31):", anchor="w")
        self.due_date_label.pack(fill="x", pady=(0, 5))
        self.due_date_entry = ctk.CTkEntry(self.frame, placeholder_text="YYYY-MM-DD or empty")
        self.due_date_entry.pack(fill="x", pady=(0, 15))

        # Priority
        self.priority_label = ctk.CTkLabel(self.frame, text="Priority:", anchor="w")
        self.priority_label.pack(fill="x", pady=(0, 5))
        self.priority_var = ctk.StringVar(value="Medium")
        self.priority_menu = ctk.CTkOptionMenu(self.frame, values=["High", "Medium", "Low"], variable=self.priority_var)
        self.priority_menu.pack(fill="x", pady=(0, 15))

        # Description
        self.desc_label = ctk.CTkLabel(self.frame, text="Description:", anchor="w")
        self.desc_label.pack(fill="x", pady=(0, 5))
        self.desc_box = ctk.CTkTextbox(self.frame, height=100)
        self.desc_box.pack(fill="both", expand=True, pady=(0, 15))

        # Buttons
        self.btn_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.btn_frame.pack(fill="x")
        
        self.cancel_btn = ctk.CTkButton(self.btn_frame, text="Cancel", fg_color="gray", command=self.destroy, width=100)
        self.cancel_btn.pack(side="left", padx=(0, 10))
        
        self.save_btn = ctk.CTkButton(self.btn_frame, text="Save", command=self.save, width=100)
        self.save_btn.pack(side="right")

        # Pre-fill if editing
        if self.todo:
            self.title_entry.insert(0, self.todo.get("title", ""))
            self.due_date_entry.insert(0, self.todo.get("due_date", ""))
            self.priority_var.set(self.todo.get("priority", "Medium"))
            self.desc_box.insert("0.0", self.todo.get("description", ""))

    def save(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Error", "Title cannot be empty")
            return
            
        due_date = self.due_date_entry.get().strip()
        priority = self.priority_var.get()
        description = self.desc_box.get("0.0", "end").strip()
        
        if self.callback:
            self.callback(title, description, due_date, priority, self.todo.get('id') if self.todo else None)
        self.destroy()

class TodoApp(ctk.CTk):
    def __init__(self, manager: TodoManager):
        super().__init__()

        self.manager = manager
        self.title("Mac Todo")
        self.geometry("450x600")
        
        # Header Frame
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=15, pady=15)
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="My Tasks", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(side="left")
        
        self.add_btn = ctk.CTkButton(self.header_frame, text="+ Add Task", width=100, command=self.show_add_dialog)
        self.add_btn.pack(side="right")

        # Scrollable Task List
        self.task_list_frame = ctk.CTkScrollableFrame(self)
        self.task_list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Footer Frame
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.clear_btn = ctk.CTkButton(self.footer_frame, text="Clear Completed", fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), command=self.clear_completed)
        self.clear_btn.pack(side="right")

        self.refresh_list()

    def show_add_dialog(self):
        TaskDialog(self, title="New Task", callback=self.save_task)

    def show_edit_dialog(self, todo):
        TaskDialog(self, title="Edit Task", todo=todo, callback=self.save_task)

    def save_task(self, title, description, due_date, priority, todo_id=None):
        if todo_id is None:
            self.manager.add_todo(title, description, due_date, priority)
        else:
            self.manager.update_todo(todo_id, title, description, due_date, priority)
        self.refresh_list()

    def toggle_task(self, todo_id):
        self.manager.toggle_todo(todo_id)
        self.refresh_list()
        
    def delete_task(self, todo_id):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this task?"):
            self.manager.delete_todo(todo_id)
            self.refresh_list()

    def clear_completed(self):
        count = self.manager.clear_completed()
        if count > 0:
            self.refresh_list()

    def refresh_list(self):
        # Clear existing widgets
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()

        # Get all todos, prioritize active ones
        active_todos = self.manager.get_active_todos()
        completed_todos = self.manager.get_completed_todos()
        
        all_todos = active_todos + completed_todos
        
        if not all_todos:
            empty_label = ctk.CTkLabel(self.task_list_frame, text="No tasks found. Click '+ Add Task' to start.", text_color="gray")
            empty_label.pack(pady=40)
            return

        for todo in all_todos:
            self.create_task_row(todo)

    def create_task_row(self, todo):
        is_completed = todo.get("completed", False)
        
        # Row Frame
        row = ctk.CTkFrame(self.task_list_frame)
        row.pack(fill="x", pady=5)
        
        # Left side: Checkbox + Title + Meta
        left_frame = ctk.CTkFrame(row, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Checkbox
        chk_var = ctk.BooleanVar(value=is_completed)
        chk = ctk.CTkCheckBox(left_frame, text="", variable=chk_var, width=24, command=lambda t=todo['id']: self.toggle_task(t))
        chk.pack(side="left")
        
        # Title & Meta
        text_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        # Strikethrough effect if completed
        title_font = ctk.CTkFont(overstrike=is_completed, size=14)
        title_color = "gray" if is_completed else ("black", "white")
        
        title_label = ctk.CTkLabel(text_frame, text=todo['title'], font=title_font, text_color=title_color, anchor="w")
        title_label.pack(fill="x")
        
        # Meta row (Priority & Due Date)
        meta_parts = []
        if todo.get("priority"):
            meta_parts.append(f"Pri: {todo['priority']}")
        if todo.get("due_date"):
            meta_parts.append(f"Due: {todo['due_date']}")
            
        if meta_parts:
            meta_text = " • ".join(meta_parts)
            meta_label = ctk.CTkLabel(text_frame, text=meta_text, font=ctk.CTkFont(size=11), text_color="gray", anchor="w")
            meta_label.pack(fill="x")
            
        # Right side: Edit & Delete buttons
        right_frame = ctk.CTkFrame(row, fg_color="transparent")
        right_frame.pack(side="right", padx=10, pady=10)
        
        edit_btn = ctk.CTkButton(right_frame, text="Edit", width=50, fg_color="transparent", border_width=1, command=lambda t=todo: self.show_edit_dialog(t))
        edit_btn.pack(side="left", padx=2)
        
        del_btn = ctk.CTkButton(right_frame, text="X", width=30, fg_color="#ff5555", hover_color="#cc0000", command=lambda t=todo['id']: self.delete_task(t))
        del_btn.pack(side="left", padx=2)

if __name__ == "__main__":
    manager = TodoManager()
    app = TodoApp(manager)
    app.mainloop()
