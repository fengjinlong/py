#!/bin/bash

# 定义 Chrome 路径和基础目录
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE_ROOT="$HOME/ChromeProfiles/"

# 创建基础目录
mkdir -p "$PROFILE_ROOT"
chmod 700 "$PROFILE_ROOT"

# 清理超过 7 天的缓存文件
find "$PROFILE_ROOT" -type d -name 'Profile*' -mtime +7 -exec rm -rf {}/Cache {}/Code\ Cache {}/GPUCache {}/Media\ Cache \;

# 打开 3 个独立的 Chrome 窗口
for i in {1..3}; do
    USER_DATA_DIR="$PROFILE_ROOT/Profile$i"
    
    # 创建用户数据目录（如果不存在）
    mkdir -p "$USER_DATA_DIR"
    chmod 700 "$USER_DATA_DIR"
    
    # 启动 Chrome
    "$CHROME" --user-data-dir="$USER_DATA_DIR" --no-first-run --new-window &
done
