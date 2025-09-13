#!/bin/bash

echo "期权分析工具 - 优化版"
echo "========================"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查必要的Python包
echo "检查Python依赖包..."
python3 -c "import pandas, matplotlib, numpy, openpyxl" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "错误: 缺少必要的Python包，请运行以下命令安装："
    echo "pip3 install pandas matplotlib numpy openpyxl"
    exit 1
fi

echo "依赖包检查完成！"
echo ""

# 运行分析程序
echo "开始运行期权分析..."
python3 yqcallxjb.py

echo ""
echo "分析完成！请查看 export 文件夹中的结果文件。"
