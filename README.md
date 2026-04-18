# snowsurfmaster 🎿

**滑雪动作智能分析系统** - 基于计算机视觉与大语言模型的滑雪动作分析与反馈平台

---

## 📖 项目概述

snowsurfmaster 是一个面向雪场商用的滑雪动作分析系统，通过计算机视觉技术提取用户滑雪视频中的骨骼关键点，与标准动作模板对比，结合大语言模型生成专业的自然语言反馈报告。

### 核心价值

- **对雪场**：提升客户体验，增加二次消费，打造差异化服务
- **对用户**：获得专业级动作分析，快速提升滑雪技能
- **对教练**：量化评估工具，辅助教学决策

---

## 🎯 投标 Demo 版本 (v0.1-Tender)

当前开发阶段：**投标导向 Demo**，聚焦核心展示功能

### Demo 功能清单

| 功能模块 | 状态 | 说明 |
|---------|------|------|
| 视频上传 | 🟢 已实现 | 支持 MP4/MOV 上传并触发分析 |
| MediaPipe 骨骼提取 | 🟢 已实现 | 33 个关键点 BlazePose |
| 关节角度计算 | 🟢 已实现 | 膝、髋、肩、前倾、对称性指标 |
| DTW 动作对比 | 🟢 已实现 | 与标准模板进行相似度评分 |
| 大模型反馈生成 | 🟢 已实现 | 本地模型 + OpenAI 兼容 API + 模板兜底 |
| 可视化报告 | 🟡 部分实现 | HTML 文本报告已实现；骨骼叠加视频/热力图待补齐 |
| Web 演示界面 | 🟢 已实现 | Streamlit 上传与结果展示 |

### 投标展示重点

1. **视觉冲击**：骨骼线叠加视频（用户 vs 标准动作）
2. **专业报告**：量化数据 + 自然语言反馈
3. **商业方案**：硬件部署图 + 价格方案

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                     snowsurfmaster 架构                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  用户视频 → MediaPipe → 骨骼序列 → DTW 对比 → 偏差指标      │
│              (33 关键点)    (JSON)     (相似度)    (角度差)  │
│                                    ↓                        │
│                            Qwen-7B + RAG                    │
│                            (大模型反馈)                      │
│                                    ↓                        │
│                      可视化报告 (视频 + 文字)                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

| 模块 | 技术选型 | 理由 |
|------|---------|------|
| **骨骼提取** | MediaPipe BlazePose | 轻量、实时、33 个关键点 |
| **量化分析** | PyBodyTrack + 自研 | 开箱即用的运动指标 |
| **动作对比** | Dynamic Time Warping (DTW) | 标准序列相似度算法 |
| **大模型反馈** | Qwen-7B-Chat (4bit 量化) | 本地部署、可控、低成本 |
| **Web 界面** | Streamlit | 快速原型、适合 Demo |
| **后端服务** | FastAPI (Phase 2) | 异步任务队列支持 |

---

## 📁 项目结构

```
snowsurfmaster/
├── README.md                 # 本文件
├── requirements.txt          # Python 依赖
├── config.yaml              # 配置文件
│
├── core/                    # 核心算法模块
│   ├── __init__.py
│   ├── extraction.py        # MediaPipe 骨骼提取
│   ├── metrics.py           # 关节角度计算
│   ├── comparison.py        # DTW 动作对比
│   └── feedback.py          # 大模型反馈生成
│
├── models/                  # 模型文件
│   └── (qwen-7b 量化模型)
│
├── data/                    # 数据目录
│   ├── raw/                 # 原始视频
│   ├── processed/           # 处理后数据 (骨骼 JSON)
│   ├── templates/           # 标准动作模板
│   └── demo/                # Demo 预设视频
│
├── vis/                     # 可视化模块
│   ├── __init__.py
│   ├── overlay.py           # 骨骼线叠加视频
│   └── heatmap.py           # 偏差热力图
│
├── web/                     # Web 界面
│   ├── app.py               # Streamlit 主程序
│   └── components/          # UI 组件
│
├── output/                  # 输出报告
│   ├── reports/             # PDF/HTML 报告
│   └── videos/              # 叠加视频
│
├── pitch/                   # 投标材料
│   ├── hardware_plan.pdf    # 硬件部署方案
│   ├── pricing.pdf          # 价格方案
│   └── demo_script.md       # 演示脚本
│
└── tests/                   # 测试用例
    ├── test_extraction.py
    ├── test_metrics.py
    └── test_comparison.py
```

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- GPU (可选，加速 MediaPipe 和大模型推理)
- 8GB+ 内存

### 安装步骤

```bash
# 1. 克隆项目
git clone <repo-url>
cd snowsurfmaster

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 下载标准动作模板 (待实现)
python scripts/download_templates.py

# 5. 运行 Demo
streamlit run web/app.py
```

### 大模型反馈方式（本地 / OpenAI 兼容 API）

项目支持两种反馈生成方式（见 `config.yaml -> llm`）：

1. `provider: local`  
   使用本地模型（默认 Qwen-7B）。
2. `provider: openai_compatible`  
   使用 OpenAI 格式接口（`/chat/completions`），可对接 OpenAI 或兼容网关（如 vLLM/OneAPI）。

示例配置：

```yaml
llm:
  provider: openai_compatible
  api_base_url: "https://api.openai.com/v1"
  api_path: /chat/completions
  api_key: "YOUR_API_KEY"
  api_model: "gpt-4o-mini"
  temperature: 0.7
  max_tokens: 512
```

### 使用示例

```python
from core.extraction import extract_skeleton
from core.metrics import calculate_angles
from core.comparison import compare_with_template
from core.feedback import generate_feedback

# 1. 提取骨骼
video_path = "data/raw/my_skiing.mp4"
skeleton_data = extract_skeleton(video_path)

# 2. 计算角度
angles = calculate_angles(skeleton_data)

# 3. 对比标准动作
template = load_template("parallel_turn_pro")
score, dtw_distance = compare_with_template(angles, template)

# 4. 生成反馈
report = generate_feedback(angles, score, dtw_distance)
print(report)
```

---

## 📊 Demo 数据说明

### 标准动作模板

当前支持的动作类型（Phase 1）：

| 动作名称 | 难度 | 模板来源 |
|---------|------|---------|
| 平行式转弯 (Parallel Turn) | 中级 | YouTube 专业教学视频提取 |
| 犁式制动 (Snowplow) | 初级 | 待标注 |
| 大回转 (Giant Slalom) | 高级 | 待标注 |

### 预设 Demo 视频

为投标演示准备，提前处理好的视频样本：

| 文件名 | 时长 | 说明 |
|--------|------|------|
| `demo_beginner.mp4` | 30s | 初学者典型错误动作 |
| `demo_intermediate.mp4` | 45s | 中级爱好者标准动作 |
| `demo_pro.mp4` | 60s | 专业教练示范动作 |

---

## 🎯 开发路线图

### Phase 1: 投标 Demo (当前阶段)
- **时间**: 2-3 周
- **目标**: 完成可演示的核心功能
- **交付**: Web Demo + 投标材料

### Phase 2: 滑后分析增强
- **时间**: 8-10 周
- **目标**: 用户系统、多动作支持、云端部署
- **交付**: 可商用的滑后分析 SaaS

### Phase 3: 实时分析原型
- **时间**: 12-16 周
- **目标**: UWB+ 视觉融合、边缘计算部署
- **交付**: 雪场实时分析系统

---

## 📋 投标信息

### 硬件部署方案 (预览)

| 雪场规模 | 设备配置 | 估算成本 |
|---------|---------|---------|
| 中小型雪场 | 1 台工控机 + 2 摄像头 | ¥30,000-50,000 |
| 大型度假村 | 3 台工控机 + 6 摄像头 + 服务器 | ¥150,000-200,000 |

### 价格方案 (预览)

| 版本 | 功能 | 价格模式 |
|------|------|---------|
| 基础版 | 单次分析、基础报告 | ¥29/次 |
| 专业版 | 详细报告、历史对比 | ¥99/次 |
| 企业版 | 雪场定制、后台管理 | ¥50,000/年 |

---

## 🤝 团队与协作


### 待招募
- 计算机视觉工程师 (MediaPipe 优化)
- 前端工程师 (Web UI 美化)
- 滑雪教练顾问 (动作标准制定)

---

## 📝 开发日志

- **2026-04-18**: 项目创建，完成技术架构设计
- **2026-04-18**: 编写 README，搭建项目结构

---

## 📄 许可证

MIT License (投标阶段暂不公开源码)


---

*Last updated: 2026-04-18*  
*Version: v0.1-Tender*
