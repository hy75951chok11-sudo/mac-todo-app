# MacTodo

一个 macOS 本地待办事项应用，当前主线使用 PyQt6 构建桌面 UI，数据保存在本地 JSON 文件中。

## 当前状态

- 主入口: `app.py`
- 数据层: `todo_manager.py`
- 图标生成: `create_assets.py`
- App 打包: `build_mac.sh`
- DMG 打包: `build_dmg.sh`
- PyInstaller 配置: `MacTodo.spec`

## 已实现功能

- 任务增删改查
- 本地 JSON 存储
- 按优先级排序
- 按截止日期排序
- 拖拽重排优先级
- 系统托盘显示/隐藏
- 全局热键 `Cmd+Option+T`
- 窗口置顶
- glassmorphism 风格任务卡片

## 历史文件

以下文件是旧版 Tk/customtkinter 实现，目前不是主线入口：

- `main.py`
- `gui.py`

保留它们是为了参考旧实现；后续开发应优先修改 `app.py` 和 `todo_manager.py`。

## 本地开发

安装依赖：

```bash
./venv/bin/pip install -r requirements.txt
```

启动应用：

```bash
./venv/bin/python app.py
```

如果只做语法检查，建议把 Python 字节码缓存定向到项目目录，避免 macOS 缓存权限问题：

```bash
PYTHONPYCACHEPREFIX=.pycache ./venv/bin/python -m py_compile app.py todo_manager.py gui.py main.py create_assets.py
```

## 打包

构建 `.app`：

```bash
./build_mac.sh
```

构建 `.dmg`：

```bash
./build_dmg.sh
```

## 数据文件

默认数据文件位置：

```text
~/.mac_todo_data.json
```

## 后续建议

- 逐步移除或归档旧版 Tk 文件，避免依赖混淆
- 为 `TodoManager` 增加单元测试
- 为 PyQt6 UI 增加基本的回归测试或冒烟测试
- 补充打包后的签名、公证与发布流程
