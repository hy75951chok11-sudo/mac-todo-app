#!/bin/bash
# 生成可安装的 DMG 包脚本

echo "准备制作 MacTodo.dmg..."

STAGING_DIR="build/dmg_staging"
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

if [ ! -d "dist/MacTodo.app" ]; then
    echo "错误：未找到 dist/MacTodo.app，请先运行 build_mac.sh 打包！"
    exit 1
fi

echo "复制 .app 应用程序包..."
cp -R "dist/MacTodo.app" "$STAGING_DIR/"

echo "创建 /Applications 快捷方式 (方便用户直接拖拽安装)..."
ln -s /Applications "$STAGING_DIR/Applications"

echo "开始生成 DMG (可能需要几秒钟)..."
rm -f dist/MacTodo.dmg
hdiutil create -volname "MacTodo Installation" -srcfolder "$STAGING_DIR" -ov -format UDZO "dist/MacTodo.dmg"

echo "清理临时文件..."
rm -rf "$STAGING_DIR"

echo "================================="
echo "打包成功！"
echo "您现在可以将 dist/MacTodo.dmg 发送给其他人了。"
echo "别人双击打开后，只需将 MacTodo 拖入旁边的 Applications 文件夹即可完成安装。"
echo "================================="
