# 项目可用性检视报告

- 检视日期：2026-04-18
- 检视结论：**当前仓库可以作为“方案 Demo 骨架”阅读，但还不满足“开箱即用”的可运行状态**。

## 已验证项

1. 代码基础结构存在：`core/` 与 `web/` 主模块文件齐全。
2. Python 语法层面可编译：`python -m compileall core web` 通过。

## 关键阻塞项

1. 文档与仓库现状不一致（README 中列出的若干路径/脚本在仓库中不存在）：
   - `scripts/download_templates.py`
   - `vis/overlay.py`
   - `vis/heatmap.py`
   - `web/components/`
   - `tests/test_extraction.py`
   - `data/raw/`、`data/demo/`
   - `output/reports/`、`output/videos/`

2. 在当前环境中导入主流程失败：
   - `import core.pipeline` 报错 `ImportError: libGL.so.1`（由 OpenCV/MediaPipe 依赖触发）。
   - 说明：即便 Python 语法无误，运行时依赖仍未满足。

## 可执行修复建议（最小闭环）

1. 补齐目录与占位文件，至少保证 README 的路径可落地。
2. 提供一键环境脚本安装系统依赖（例如 Ubuntu 上的 `libgl1` 等）。
3. 增加“无视频输入”的 smoke test：
   - 模拟最小 skeleton JSON → metrics → comparison → feedback。
4. 在 README 增加“环境依赖排障”章节，明确系统库依赖（不仅是 pip 包）。

## 建议判断标准

满足以下三条后，可标记为“可用 Demo”：

- `streamlit run web/app.py` 可启动并打开页面。
- 预置 demo 视频可跑通一次分析并生成 `output/demo/*.html`。
- `pytest` 至少有 1-3 个核心模块单测通过。
