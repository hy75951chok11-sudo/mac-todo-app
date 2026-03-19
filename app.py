import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QDialog,
    QLineEdit, QTextEdit, QMessageBox, QFrame,
    QSystemTrayIcon, QStyle, QMenu, QSpinBox, 
    QListWidget, QListWidgetItem, QAbstractItemView, QComboBox,
    QDateEdit, QTimeEdit, QGraphicsDropShadowEffect, QStackedWidget,
    QGraphicsOpacityEffect
)
from PyQt6.QtGui import QIcon, QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QDateTime, QTimer, QDate, QTime, QSize, QVariantAnimation

from todo_manager import TodoManager

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# ==========================================
# 2. PyQt6 Application
# ==========================================
class TaskDialog(QDialog):
    def __init__(self, parent=None, title="添加任务", todo=None, callback=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 500)
        self.todo = todo
        self.callback = callback
        
        self.setStyleSheet("""
            QDialog { background-color: #F8F9FA; }
            QLabel { font-size: 13px; color: #555555; font-weight: bold; }
            QLineEdit, QDateEdit, QTimeEdit, QSpinBox, QTextEdit {
                background-color: white; border: 1px solid #E0E0E0; border-radius: 8px; padding: 6px; font-size: 13px;
            }
            QPushButton {
                background-color: white; border-radius: 8px; border: 1px solid #E0E0E0; padding: 8px; font-size: 13px; font-weight: bold; color: #333;
            }
            QPushButton:hover { background-color: #F2F2F7; }
        """)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("任务标题："))
        self.title_entry = QLineEdit()
        layout.addWidget(self.title_entry)
        
        layout.addWidget(QLabel("截止日期与时间："))
        date_time_layout = QHBoxLayout()
        self.date_entry = QDateEdit()
        self.date_entry.setCalendarPopup(True)
        self.date_entry.setDisplayFormat("yyyy-MM-dd")
        self.date_entry.setDate(QDate.currentDate())
        
        self.time_entry = QTimeEdit()
        self.time_entry.setDisplayFormat("HH:mm")
        self.time_entry.setTime(QTime.currentTime())
        
        self.now_btn = QPushButton("现在")
        self.now_btn.setStyleSheet("padding: 6px 12px; border-radius: 8px; font-size: 13px; font-weight: bold; background-color: #EBF5FF; color: #007AFF; border: none;")
        self.now_btn.clicked.connect(self.set_to_now)
        
        date_time_layout.addWidget(self.date_entry)
        date_time_layout.addWidget(self.time_entry)
        date_time_layout.addWidget(self.now_btn)
        layout.addLayout(date_time_layout)
        
        layout.addWidget(QLabel("优先级 (0为最高，可输入任意非负数)："))
        self.priority_spin = QSpinBox()
        self.priority_spin.setMinimum(0)
        self.priority_spin.setMaximum(99999)
        layout.addWidget(self.priority_spin)
        
        layout.addWidget(QLabel("任务描述："))
        self.desc_box = QTextEdit()
        layout.addWidget(self.desc_box)
        
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.setStyleSheet("background-color: #007AFF; color: white; border: none;")
        self.save_btn.clicked.connect(self.save)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)
        
        if self.todo:
            self.title_entry.setText(self.todo.get("title", ""))
            due_str = self.todo.get("due_date", "")
            if due_str:
                dt = QDateTime.fromString(due_str, "yyyy-MM-dd HH:mm:ss")
                if dt.isValid():
                    self.date_entry.setDate(dt.date())
                    self.time_entry.setTime(dt.time())
            if "priority" in self.todo:
                self.priority_spin.setValue(int(self.todo["priority"]))
            self.desc_box.setText(self.todo.get("description", ""))

    def set_to_now(self):
        self.date_entry.setDate(QDate.currentDate())
        self.time_entry.setTime(QTime.currentTime())

    def save(self):
        title = self.title_entry.text().strip()
        if not title:
            QMessageBox.critical(self, "错误", "任务标题不能为空")
            return
            
        selected_dt = QDateTime(self.date_entry.date(), self.time_entry.time())
        due_date = selected_dt.toString("yyyy-MM-dd HH:mm:ss")
        
        is_changed = True
        if self.todo and self.todo.get("due_date") == due_date:
            is_changed = False
            
        if is_changed and selected_dt < QDateTime.currentDateTime():
            QMessageBox.warning(self, "时间错误", "截止时间不可早于当前所在时间！")
            return
            
        priority = self.priority_spin.value()
        description = self.desc_box.toPlainText().strip()
        
        if self.callback:
            self.callback(title, description, due_date, priority, self.todo.get('id') if self.todo else None)
        self.accept()


class HotkeySignalManager(QObject):
    toggle_signal = pyqtSignal()


class MacAppFilter(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.ApplicationActivate:
            self.window.showNormal()
            self.window.raise_()
            self.window.activateWindow()
            self.window.is_visible = True
        return False


def get_shadow(radius=15, alpha=20, y_offset=4):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(radius)
    shadow.setColor(QColor(0, 0, 0, alpha))
    shadow.setOffset(0, y_offset)
    return shadow

class TaskItemWidget(QFrame):
    def __init__(self, item: QListWidgetItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.title_lbl = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        lbl = self.title_lbl
        if lbl is not None:
            # Layout geometry: Frame width - margins(32) - checkbox(~24) - gap(16) - gap(16) - tools(~85) = ~173
            avail_w = max(50, self.width() - 175)
            t_h = lbl.heightForWidth(avail_w)
            
            # Vertical margin padding and meta height approximation
            needed_h = max(self.minimumHeight(), t_h + 52)
            if self.item.sizeHint().height() != needed_h:
                self.item.setSizeHint(QSize(self.item.sizeHint().width(), needed_h))

class TodoApp(QMainWindow):
    def __init__(self, manager: TodoManager):
        super().__init__()
        self.manager = manager
        self.setWindowTitle("Mac Todo — 日常待办清单")
        self.resize(550, 700)
        self.is_visible = True
        
        arrow_url = resource_path('assets/chevron-down.svg').replace(os.sep, '/')
        self.setStyleSheet(f"""
            QMainWindow {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #EAF0FF, stop:1 #F3E5F5); 
            }}
            QListWidget {{ background-color: transparent; border: none; outline: none; }}
            QListWidget::item {{ background-color: transparent; border: none; margin-bottom: 12px; }}
            QListWidget::item:selected {{ background-color: transparent; border: none; }}
            
            QComboBox {{ 
                background-color: white; 
                border-radius: 10px; 
                border: 1px solid #E0E0E0; 
                padding: 6px 36px 6px 14px; 
                font-size: 13px; 
                color: #555555; 
                font-weight: 600;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: none; 
            }}
            QComboBox::down-arrow {{
                image: url("{arrow_url}");
                width: 14px;
                height: 14px;
            }}
            
            QPushButton {{ 
                background-color: white; 
                border-radius: 10px; 
                border: 1px solid #E0E0E0; 
                padding: 6px 14px; 
                font-size: 13px; 
                color: #555555; 
                font-weight: 600;
            }}
            
            QLabel {{ background-color: transparent; }}
            
            QPushButton:hover, QComboBox:hover {{ background-color: #F8F9FA; }}
            QPushButton:pressed {{ background-color: #E5E5EA; }}
            #IconBtn {{ padding: 6px; }}
            #AddBtn {{ padding-left: 10px; padding-right: 14px; }}
        """)
        
        self.signal_manager = HotkeySignalManager()
        self.signal_manager.toggle_signal.connect(self.toggle_window_visibility)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        title_label = QLabel("我的待办")
        title_label.setStyleSheet("font-size: 26px; font-weight: 800; color: #2C3E50; letter-spacing: -0.5px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["按优先级排序 (可拖拽)", "按截止日期排序"])
        self.sort_combo.currentIndexChanged.connect(self.refresh_list)
        self.sort_combo.setGraphicsEffect(get_shadow(10, 15, 2))
        header_layout.addWidget(self.sort_combo)

        self.pin_btn = QPushButton()
        self.pin_btn.setIcon(QIcon(resource_path("assets/pin.svg")))
        self.pin_btn.setIconSize(QSize(18, 18))
        self.pin_btn.setObjectName("IconBtn")
        self.pin_btn.setToolTip("置顶窗口")
        self.pin_btn.setCheckable(True)
        self.pin_btn.clicked.connect(self.toggle_pin)
        self.pin_btn.setGraphicsEffect(get_shadow(10, 15, 2))
        header_layout.addWidget(self.pin_btn)
        
        self.add_btn = QPushButton(" 新建任务")
        self.add_btn.setIcon(QIcon(resource_path("assets/plus.svg")))
        self.add_btn.setIconSize(QSize(18, 18))
        self.add_btn.setObjectName("AddBtn")
        self.add_btn.clicked.connect(self.show_add_dialog)
        self.add_btn.setGraphicsEffect(get_shadow(10, 15, 2))
        header_layout.addWidget(self.add_btn)

        self.main_layout.addLayout(header_layout)
        self.main_layout.addSpacing(10)
        
        self.stack = QStackedWidget()
        self.task_list = QListWidget()
        self.task_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.stack.addWidget(self.task_list)
        
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_icon = QLabel()
        empty_icon.setPixmap(QIcon(resource_path("assets/empty-box.svg")).pixmap(80, 80))
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_text = QLabel("今天想做点什么？\n点击右上角 新建 吧 🚀")
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_text.setStyleSheet("color: #999999; font-size: 15px; font-weight: 500;")
        
        empty_layout.addWidget(empty_icon)
        empty_layout.addSpacing(16)
        empty_layout.addWidget(empty_text)
        self.stack.addWidget(self.empty_widget)
        
        self.main_layout.addWidget(self.stack)
        
        self.task_list.model().rowsMoved.connect(self.on_rows_moved)
        
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        clear_btn = QPushButton(" 清理已完成")
        clear_btn.setIcon(QIcon(resource_path("assets/clear.svg")))
        clear_btn.setIconSize(QSize(16, 16))
        clear_btn.setStyleSheet("color: #FF3B30; border: none; background-color: transparent;")
        clear_btn.clicked.connect(self.clear_completed)
        footer_layout.addWidget(clear_btn)
        self.main_layout.addLayout(footer_layout)
        
        self.tray_icon = QSystemTrayIcon(self)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        self.tray_menu = QMenu()
        show_action = self.tray_menu.addAction("显示/隐藏 MacTodo")
        show_action.triggered.connect(self.toggle_window_visibility)
        self.tray_menu.addSeparator()
        quit_action = self.tray_menu.addAction("退出程序")
        quit_action.triggered.connect(QApplication.instance().quit)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.tray_clicked)
        self.tray_icon.show()
        
        self.refresh_list()

    def tray_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_window_visibility()

    def toggle_pin(self):
        if self.pin_btn.isChecked():
            self.pin_btn.setIcon(QIcon(resource_path("assets/pin-filled.svg")))
            self.pin_btn.setStyleSheet("background-color: #EBF5FF;")
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        else:
            self.pin_btn.setIcon(QIcon(resource_path("assets/pin.svg")))
            self.pin_btn.setStyleSheet("")
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self.show()

    def toggle_window_visibility(self):
        if self.is_visible:
            self.hide()
            self.is_visible = False
        else:
            self.showNormal()
            self.raise_()
            self.activateWindow()
            self.is_visible = True

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.is_visible = False

    def show_add_dialog(self):
        dlg = TaskDialog(self, title="新建待办", callback=self.save_task)
        dlg.exec()

    def show_edit_dialog(self, todo):
        dlg = TaskDialog(self, title="编辑任务", todo=todo, callback=self.save_task)
        dlg.exec()

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
        confirm = QMessageBox.question(self, "确认删除", "确定永久移除此记录吗？", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.manager.delete_todo(todo_id)
            
            target_item = None
            for i in range(self.task_list.count()):
                it = self.task_list.item(i)
                if it.data(Qt.ItemDataRole.UserRole) == todo_id:
                    target_item = it
                    break
                    
            if target_item:
                target_widget = self.task_list.itemWidget(target_item)
                if target_widget:
                    anim = QVariantAnimation(self)
                    start_h = target_item.sizeHint().height()
                    anim.setStartValue(start_h)
                    anim.setEndValue(0)
                    anim.setDuration(300)
                    
                    effect = QGraphicsOpacityEffect(target_widget)
                    target_widget.setGraphicsEffect(effect)
                    
                    def update_anim(val):
                        target_item.setSizeHint(QSize(target_item.sizeHint().width(), val))
                        if start_h > 0:
                            effect.setOpacity(max(0.0, float(val) / start_h))
                            
                    anim.valueChanged.connect(update_anim)
                    
                    def on_finished():
                        row = self.task_list.row(target_item)
                        if row >= 0:
                            self.task_list.takeItem(row)
                        if not self.manager.get_active_todos() and not self.manager.get_completed_todos():
                            self.stack.setCurrentWidget(self.empty_widget)
                    
                    anim.finished.connect(on_finished)
                    
                    if not hasattr(self, '_anims'):
                        self._anims = []
                    self._anims.append(anim)
                    anim.finished.connect(lambda: self._anims.remove(anim) if anim in self._anims else None)
                    
                    anim.start()
                else:
                    self.refresh_list()
            else:
                self.refresh_list()

    def clear_completed(self):
        count = self.manager.clear_completed()
        if count > 0:
            self.refresh_list()

    def on_rows_moved(self, parent, start, end, destination, row):
        if self.sort_combo.currentIndex() != 0:
            return
        ordered_ids = []
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            todo_id = item.data(Qt.ItemDataRole.UserRole)
            if todo_id is not None:
                ordered_ids.append(todo_id)
                
        self.manager.reorder_priorities(ordered_ids)
        QTimer.singleShot(0, self.refresh_list)

    def format_relative_time(self, date_str):
        if not date_str:
            return ""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            target_day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            
            days_diff = (target_day - today).days
            time_str = dt.strftime("%H:%M")
            
            if days_diff == 0:
                return f"今天 {time_str}"
            elif days_diff == 1:
                return f"明天 {time_str}"
            elif days_diff == -1:
                return f"昨天 {time_str}"
            elif dt.year == now.year:
                return f"{dt.month}月{dt.day}日 {time_str}"
            else:
                return f"{dt.year}年{dt.month}月{dt.day}日 {time_str}"
        except Exception:
            return date_str

    def refresh_list(self):
        self.task_list.clear()

        active_todos = self.manager.get_active_todos()
        completed_todos = self.manager.get_completed_todos()
        
        sort_mode = self.sort_combo.currentIndex()
        if sort_mode == 0:
            active_todos.sort(key=lambda t: t.get("priority", 99999))
            self.task_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
            self.task_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        else:
            active_todos.sort(key=lambda t: t.get("due_date") or "9999-12-31 23:59:59")
            self.task_list.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
            
        all_todos = active_todos + completed_todos
        
        if not all_todos:
            self.stack.setCurrentWidget(self.empty_widget)
            return

        self.stack.setCurrentWidget(self.task_list)

        for todo in all_todos:
            self.create_task_row(todo)

    def create_task_row(self, todo):
        is_completed = todo.get("completed", False)
        
        item = QListWidgetItem(self.task_list)
        item.setData(Qt.ItemDataRole.UserRole, todo['id'])
        
        if is_completed:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled & ~Qt.ItemFlag.ItemIsDropEnabled)
        
        row_widget = TaskItemWidget(item)
        row_widget.setObjectName("taskRow")
        row_widget.setMinimumHeight(64)
        
        glass_qss = """
            #taskRow {
                background-color: rgba(255, 255, 255, 0.75);
                border: 1px solid rgba(255, 255, 255, 1.0);
                border-radius: 16px;
            }
        """
        if is_completed:
            glass_qss = """
                #taskRow {
                    background-color: rgba(255, 255, 255, 0.4);
                    border: 1px solid rgba(255, 255, 255, 0.5);
                    border-radius: 16px;
                }
            """
        
        row_widget.setStyleSheet(glass_qss)

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(16, 12, 16, 12)
        row_layout.setSpacing(0)
        row_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        chk_style = """
            QCheckBox { spacing: 0px; }
            QCheckBox::indicator { 
                width: 20px; 
                height: 20px; 
                border-radius: 6px; 
                border: 2px solid #C7C7CC; 
                background: white; 
            }
            QCheckBox::indicator:hover { border: 2px solid #A0A0A5; }
            QCheckBox::indicator:checked { 
                background: #007AFF; 
                border: 2px solid #007AFF; 
                image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'><polyline points='20 6 9 17 4 12'/></svg>");
            }
        """
        chk = QCheckBox()
        chk.setStyleSheet(chk_style)
        chk.setChecked(is_completed)
        chk.clicked.connect(lambda checked, t=todo['id']: self.toggle_task(t))
        row_layout.addWidget(chk)
        
        row_layout.addSpacing(16)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        title_lbl = QLabel(todo['title'])
        title_lbl.setWordWrap(True)
        
        font = title_lbl.font()
        font.setPixelSize(16)
        font.setWeight(QFont.Weight.DemiBold)
        title_lbl.setFont(font)
        
        if is_completed:
            title_lbl.setStyleSheet("background-color: transparent; text-decoration: line-through; color: #999999;")
        else:
            title_lbl.setStyleSheet("background-color: transparent; color: #222222;")
            
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        text_layout.addWidget(title_lbl)
        row_widget.title_lbl = title_lbl
        
        meta_parts = []
        fmt_date = self.format_relative_time(todo.get("due_date"))
        if fmt_date: meta_parts.append(f"截止: {fmt_date}")
        meta_parts.append(f"优先级 {todo.get('priority', 0)}")
            
        meta_lbl = QLabel(" • ".join(meta_parts))
        meta_font = meta_lbl.font()
        meta_font.setPixelSize(12)
        meta_font.setWeight(QFont.Weight.Normal)
        meta_lbl.setFont(meta_font)
        meta_lbl.setStyleSheet("background-color: transparent; color: #9A9A9A;")
        text_layout.addWidget(meta_lbl)
            
        row_layout.addLayout(text_layout, stretch=1)
        
        row_layout.addSpacing(16)
        
        tools_layout = QHBoxLayout()
        tools_layout.setSpacing(8)
        
        if not is_completed and self.sort_combo.currentIndex() == 0:
            drag_lbl = QLabel()
            drag_lbl.setPixmap(QIcon(resource_path("assets/drag.svg")).pixmap(16, 16))
            drag_lbl.setToolTip("长按拖拽")
            tools_layout.addWidget(drag_lbl)
        
        btn_style = "QPushButton { border: none; background: transparent; padding: 4px; border-radius: 6px; } QPushButton:hover:!disabled { background-color: rgba(0,0,0,0.05); }"
        danger_btn_style = "QPushButton { border: none; background: transparent; padding: 4px; border-radius: 6px; } QPushButton:hover:!disabled { background-color: #FFE5E5; }"
        
        edit_btn = QPushButton()
        edit_btn.setIcon(QIcon(resource_path("assets/edit.svg")))
        edit_btn.setIconSize(QSize(16, 16))
        edit_btn.setToolTip("编辑任务")
        edit_btn.setFixedWidth(26)
        edit_btn.setFixedHeight(26)
        edit_btn.setStyleSheet(btn_style)
        if is_completed: edit_btn.setEnabled(False)
        edit_btn.clicked.connect(lambda checked, t=todo: self.show_edit_dialog(t))
        tools_layout.addWidget(edit_btn)
        
        del_btn = QPushButton()
        del_btn.setIcon(QIcon(resource_path("assets/trash.svg")))
        del_btn.setIconSize(QSize(16, 16))
        del_btn.setToolTip("移除任务")
        del_btn.setFixedWidth(26)
        del_btn.setFixedHeight(26)
        del_btn.setStyleSheet(danger_btn_style)
        del_btn.clicked.connect(lambda checked, t=todo['id']: self.delete_task(t))
        tools_layout.addWidget(del_btn)
        
        row_layout.addLayout(tools_layout)
        
        row_widget.setLayout(row_layout)
        item.setSizeHint(row_widget.sizeHint())
        self.task_list.setItemWidget(item, row_widget)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Mac Todo")
    
    manager = TodoManager()
    main_window = TodoApp(manager)
    main_window.show()

    mac_filter = MacAppFilter(main_window)
    app.installEventFilter(mac_filter)
    
    try:
        from pynput import keyboard
        def on_activate_h():
            main_window.signal_manager.toggle_signal.emit()
        hotkey = keyboard.GlobalHotKeys({'<cmd>+<alt>+t': on_activate_h})
        hotkey.start()
    except Exception as e:
        hotkey = None
        print(f"全局热键注册跳过: {e}")
    
    try:
        sys.exit(app.exec())
    finally:
        if 'hotkey' in locals() and hotkey:
            hotkey.stop()

if __name__ == "__main__":
    main()
