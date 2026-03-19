#!/bin/bash
# Mac Todo App 自动打包脚本 (PyInstaller)
# 请在执行此脚本前，确保已经通过终端安装了相关依赖：
# pip install pyqt6 pyinstaller pynput

echo "清理历史构建缓存..."
rm -rf build dist

echo "正在执行 PyInstaller 进行应用打包..."
# 统一走 spec 文件，避免脚本参数和 MacTodo.spec 漂移。
./venv/bin/python -m PyInstaller MacTodo.spec

echo ""
echo "=========== 打包完成！==========="
echo "应用存放位置: ./dist/MacTodo.app"
echo "你可以直接双击运行以上 .app 文件，也可以将其拖至「应用程序」文件夹！"
