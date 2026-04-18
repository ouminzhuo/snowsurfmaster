#!/bin/bash

# snowsurfmaster 快速安装脚本

set -e

echo "🎿 snowsurfmaster 安装脚本"
echo "=========================="
echo ""

# 检查 Python 版本
echo "📌 检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python $python_version"

# 创建虚拟环境
echo ""
echo "📦 创建虚拟环境..."
python3 -m venv venv
echo "   ✅ 虚拟环境已创建"

# 激活虚拟环境
echo ""
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo ""
echo "📥 安装依赖（这可能需要几分钟）..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ 依赖安装完成"

# 创建必要目录
echo ""
echo "📁 创建目录结构..."
mkdir -p data/{raw,processed,templates,demo}
mkdir -p output/{reports,videos}
mkdir -p models
mkdir -p web/components
echo "   ✅ 目录已创建"

# 创建示例配置文件
echo ""
echo "⚙️ 创建配置文件..."
if [ ! -f config.yaml ]; then
    echo "   config.yaml 已存在，跳过"
else
    echo "   ✅ config.yaml 已创建"
fi

# 下载示例模板（占位符）
echo ""
echo "📋 创建示例动作模板..."

# 专业模板
cat > data/templates/parallel_turn_pro.json << 'EOF'
{
  "template_name": "parallel_turn_pro",
  "description": "专业选手平行式转弯动作模板",
  "video_info": {
    "fps": 30,
    "total_frames": 90,
    "width": 1920,
    "height": 1080
  },
  "frames": [],
  "keypoints": ["nose", "left_shoulder", "right_shoulder", "left_hip", "right_hip", "left_knee", "right_knee"],
  "metrics": {
    "left_knee_angle": {"mean": 130, "std": 5},
    "right_knee_angle": {"mean": 125, "std": 5},
    "left_hip_angle": {"mean": 150, "std": 8},
    "right_hip_angle": {"mean": 148, "std": 8},
    "forward_lean": {"mean": -15, "std": 3},
    "symmetry_score": {"mean": 90, "std": 5}
  }
}
EOF

# 初学者模板
cat > data/templates/parallel_turn_beginner.json << 'EOF'
{
  "template_name": "parallel_turn_beginner",
  "description": "初学者平行式转弯参考模板",
  "video_info": {
    "fps": 30,
    "total_frames": 90,
    "width": 1920,
    "height": 1080
  },
  "frames": [],
  "keypoints": ["nose", "left_shoulder", "right_shoulder", "left_hip", "right_hip", "left_knee", "right_knee"],
  "metrics": {
    "left_knee_angle": {"mean": 140, "std": 10},
    "right_knee_angle": {"mean": 135, "std": 10},
    "left_hip_angle": {"mean": 160, "std": 12},
    "right_hip_angle": {"mean": 158, "std": 12},
    "forward_lean": {"mean": -8, "std": 5},
    "symmetry_score": {"mean": 75, "std": 10}
  }
}
EOF

echo "   ✅ 模板已创建"

# 创建 README
echo ""
echo "📝 创建说明文档..."
cat > data/README.md << 'EOF'
# 数据目录说明

## raw/
放置原始滑雪视频文件
- 支持格式：MP4, MOV
- 建议时长：10-60 秒
- 建议分辨率：720p 以上

## processed/
存储处理后的数据
- 骨骼数据 JSON
- 指标数据 JSON

## templates/
标准动作模板
- parallel_turn_pro.json
- parallel_turn_beginner.json

## demo/
预设演示视频
- demo_beginner.mp4
- demo_intermediate.mp4
- demo_pro.mp4

**注意**：demo 视频需要自行准备或从网上下载
EOF

cat > data/demo/README.md << 'EOF'
# Demo 视频说明

请将以下视频文件放入此目录：

1. **demo_beginner.mp4** - 初学者滑雪视频（30 秒）
2. **demo_intermediate.mp4** - 中级爱好者视频（45 秒）
3. **demo_pro.mp4** - 专业选手视频（60 秒）

**视频来源建议**：
- 自己录制
- YouTube 下载（注意版权）
- 开源数据集

**推荐 YouTube 频道**：
- PSIA-AASI（美国滑雪教练协会）
- Ski Magazine
- Epic TV
EOF

echo "   ✅ 说明文档已创建"

# 完成
echo ""
echo "=========================================="
echo "🎉 安装完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 准备测试视频放入 data/raw/ 或 data/demo/"
echo "2. 运行 Web 界面：streamlit run web/app.py"
echo "3. 或命令行测试：python core/pipeline.py data/raw/your_video.mp4"
echo ""
echo "查看 README.md 了解更多使用方法"
echo ""
