import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class TodoManager:
    def __init__(self, storage_file=None):
        if storage_file is None:
            self.storage_file = os.path.expanduser("~/.mac_todo_data.json")
        else:
            self.storage_file = os.path.expanduser(storage_file)
        self.todos = self.load_todos()

    def load_todos(self) -> List[Dict]:
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    todos = json.load(f)
                    for todo in todos:
                        if 'due_date' not in todo: todo['due_date'] = ""
                        
                        # Data Migration: Parse string priorities to Ints (0 is highest)
                        if 'priority' not in todo: 
                            todo['priority'] = 0
                        else:
                            if isinstance(todo['priority'], str):
                                p = str(todo['priority']).lower()
                                if p == 'high': todo['priority'] = 0
                                elif p == 'medium': todo['priority'] = 1
                                elif p == 'low': todo['priority'] = 2
                                else: todo['priority'] = 0
                            else:
                                try:
                                    todo['priority'] = int(todo['priority'])
                                except ValueError:
                                    todo['priority'] = 0
                                    
                        if 'description' not in todo: todo['description'] = ""
                    return todos
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_todos(self):
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.todos, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"保存待办数据时发生错误: {e}")

    def _shift_priorities(self, new_priority: int, exclude_id: int, old_priority: Optional[int] = None):
        active_todos = [t for t in self.todos if not t.get("completed", False) and t["id"] != exclude_id]
        if old_priority is not None:
            if new_priority < old_priority:
                for t in active_todos:
                    p = t.get("priority", 99999)
                    if new_priority <= p < old_priority:
                        t["priority"] = p + 1
            elif new_priority > old_priority:
                for t in active_todos:
                    p = t.get("priority", 99999)
                    if old_priority < p <= new_priority:
                        t["priority"] = p - 1
        else:
            for t in active_todos:
                p = t.get("priority", 99999)
                if p >= new_priority:
                    t["priority"] = p + 1

    def add_todo(self, title: str, description: str = "", due_date: str = "", priority: int = 0) -> Dict:
        new_id = 1
        if self.todos:
            new_id = max(todo["id"] for todo in self.todos) + 1
            
        self._shift_priorities(priority, new_id)
        
        todo = {
            "id": new_id,
            "title": title,
            "description": description,
            "due_date": due_date,
            "priority": priority,
            "completed": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self.todos.append(todo)
        self.save_todos()
        return todo

    def get_active_todos(self) -> List[Dict]:
        return [todo for todo in self.todos if not todo.get("completed", False)]
        
    def get_completed_todos(self) -> List[Dict]:
        return [todo for todo in self.todos if todo.get("completed", False)]

    def toggle_todo(self, todo_id: int) -> Optional[Dict]:
        for todo in self.todos:
            if todo["id"] == todo_id:
                todo["completed"] = not todo.get("completed", False)
                todo["updated_at"] = datetime.now().isoformat()
                self.save_todos()
                return todo
        return None

    def delete_todo(self, todo_id: int) -> bool:
        for i, todo in enumerate(self.todos):
            if todo["id"] == todo_id:
                del self.todos[i]
                self.save_todos()
                return True
        return False
        
    def clear_completed(self) -> int:
        initial_count = len(self.todos)
        self.todos = [todo for todo in self.todos if not todo.get("completed", False)]
        cleared_count = initial_count - len(self.todos)
        self.save_todos()
        return cleared_count

    def update_todo(self, todo_id: int, title: str, description: str, due_date: str, priority: int) -> Optional[Dict]:
        for todo in self.todos:
            if todo["id"] == todo_id:
                old_priority = todo.get("priority", 99999)
                if old_priority != priority:
                    self._shift_priorities(priority, todo_id, old_priority)
                todo["title"] = title
                todo["description"] = description
                todo["due_date"] = due_date
                todo["priority"] = priority
                todo["updated_at"] = datetime.now().isoformat()
                self.save_todos()
                return todo
        return None

    def reorder_priorities(self, ordered_ids: List[int]):
        """Update priorities sequentially based on the new visual list index."""
        id_to_priority = {todo_id: index for index, todo_id in enumerate(ordered_ids)}
        for todo in self.todos:
            if todo["id"] in id_to_priority:
                todo["priority"] = id_to_priority[todo["id"]]
        self.save_todos()
