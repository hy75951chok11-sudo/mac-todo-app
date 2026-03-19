#!/bin/bash

echo "Building MacTodo App using PyInstaller..."

rm -rf build dist
./venv/bin/python -m PyInstaller MacTodo.spec

echo "Build complete!"
