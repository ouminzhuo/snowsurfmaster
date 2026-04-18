"""
snowsurfmaster Web 演示界面

基于 Streamlit 快速搭建的滑雪动作分析 Demo
"""

import streamlit as st
import json
from pathlib import Path
import tempfile
import os

# 设置页面配置
st.set_page_config(
    page_title="snowsurfmaster - 滑雪动作分析",
    page_icon="🎿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
    }
    .score-display {
        font-size: 72px;
        font-weight: bold;
        text-align: center;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .status-excellent { color: #28a745; font-weight: bold; }
    .status-good { color: #ffc107; font-weight: bold; }
    .status-needs_improvement { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


def main():
    """主应用"""
    
    # 标题
    st.markdown("""
    <div class="main-header">
        <h1>🎿 snowsurfmaster</h1>
        <h2>滑雪动作智能分析系统</h2>
        <p>基于计算机视觉与大语言模型的专业动作分析</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 设置")
        
        # 模板选择
        template_options = {
            "专业选手 - 平行式转弯": "data/templates/parallel_turn_pro.json",
            "初学者 - 平行式转弯": "data/templates/parallel_turn_beginner.json"
        }
        
        selected_template = st.selectbox(
            "选择标准动作模板",
            options=list(template_options.keys()),
            index=0
        )
        
        template_path = template_options[selected_template]
        
        # 是否使用大模型
        use_llm = st.checkbox("使用大模型生成反馈", value=True)
        
        st.divider()
        
        st.info("""
        **Demo 说明**
        
        1. 上传滑雪视频（MP4/MOV）
        2. 系统自动分析动作
        3. 生成专业反馈报告
        
        当前为投标演示版本
        """)
    
    # 主内容区
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📹 上传视频")
        
        uploaded_file = st.file_uploader(
            "选择滑雪视频文件",
            type=['mp4', 'mov'],
            help="支持 MP4 或 MOV 格式，建议时长 10-60 秒"
        )
        
        if uploaded_file is not None:
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                video_path = tmp_file.name
            
            # 显示视频
            st.video(uploaded_file)
            
            # 分析按钮
            if st.button("🚀 开始分析", type="primary", use_container_width=True):
                with st.spinner("正在分析您的动作... 这可能需要几分钟"):
                    try:
                        # 导入 pipeline
                        from core.pipeline import SkiAnalysisPipeline
                        
                        # 创建输出目录
                        output_dir = Path("output/demo")
                        output_dir.mkdir(parents=True, exist_ok=True)
                        
                        # 运行分析
                        pipeline = SkiAnalysisPipeline()
                        result = pipeline.analyze_video(
                            video_path,
                            template_path=template_path,
                            output_dir=str(output_dir),
                            use_llm=use_llm
                        )
                        
                        # 显示结果
                        st.success("✅ 分析完成！")
                        
                        # 保存结果到 session state
                        st.session_state['analysis_result'] = result
                        
                    except Exception as e:
                        st.error(f"❌ 分析失败：{str(e)}")
                    finally:
                        # 清理临时文件
                        if os.path.exists(video_path):
                            os.unlink(video_path)
        
        # 使用预设 Demo 视频
        st.divider()
        st.subheader("或使用预设 Demo 视频")
        
        demo_videos = {
            "初学者示例": "data/demo/demo_beginner.mp4",
            "中级示例": "data/demo/demo_intermediate.mp4",
            "专业示例": "data/demo/demo_pro.mp4"
        }
        
        selected_demo = st.selectbox(
            "选择 Demo 视频",
            options=list(demo_videos.keys()),
            index=1
        )
        
        if st.button("加载 Demo 视频"):
            demo_path = demo_videos[selected_demo]
            if Path(demo_path).exists():
                st.session_state['demo_video'] = demo_path
                st.video(demo_path)
                st.info(f"已加载：{demo_path}")
            else:
                st.warning(f"Demo 视频不存在：{demo_path}\n\n请先将测试视频放入 data/demo/ 目录")
    
    # 结果显示区
    with col2:
        st.header("📊 分析结果")
        
        if 'analysis_result' in st.session_state:
            result = st.session_state['analysis_result']
            
            # 整体评分
            if result['comparison']:
                similarity_score = result['comparison']['overall']['similarity_score']
                
                # 颜色根据分数变化
                if similarity_score >= 80:
                    score_color = "#28a745"
                elif similarity_score >= 60:
                    score_color = "#ffc107"
                else:
                    score_color = "#dc3545"
                
                st.markdown(f"""
                <div class="score-display" style="color: {score_color}">
                    {similarity_score:.0f}
                </div>
                <div style="text-align: center; margin-bottom: 20px;">
                    <span style="font-size: 18px;">动作相似度</span><br>
                    <span style="color: #666;">/100</span>
                </div>
                """, unsafe_allow_html=True)
                
                # 详细指标
                st.subheader("📈 详细指标")
                
                for metric_name, analysis in result['comparison']['metric_analysis'].items():
                    status_class = f"status-{analysis['status']}"
                    status_text = analysis['status'].replace('_', ' ').title()
                    
                    # 翻译指标名
                    metric_translations = {
                        'left_knee_angle': '左膝角度',
                        'right_knee_angle': '右膝角度',
                        'left_hip_angle': '左髋角度',
                        'right_hip_angle': '右髋角度',
                        'forward_lean': '身体前倾',
                        'symmetry_score': '左右对称性'
                    }
                    metric_cn = metric_translations.get(metric_name, metric_name)
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="display: flex; justify-content: space-between;">
                            <span>{metric_cn}</span>
                            <span class="{status_class}">{status_text}</span>
                        </div>
                        <div style="font-size: 12px; color: #666; margin-top: 5px;">
                            你的数值：{analysis['user_mean']:.1f} | 标准：{analysis['template_mean']:.1f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 反馈文本
                st.divider()
                st.subheader("📝 专业反馈")
                
                with st.expander("查看详细反馈", expanded=True):
                    st.markdown(result['feedback'])
                
                # 下载按钮
                if result['report_path']:
                    with open(result['report_path'], 'r', encoding='utf-8') as f:
                        report_html = f.read()
                    
                    st.download_button(
                        label="📥 下载 HTML 报告",
                        data=report_html,
                        file_name=f"snowsurfmaster_report.html",
                        mime="text/html"
                    )
            
            else:
                st.warning("未生成对比结果")
                st.markdown(result['feedback'])
        
        else:
            st.info("👆 请先上传视频或选择 Demo，然后点击「开始分析」")
    
    # 底部信息
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: 40px;">
        <p><strong>snowsurfmaster</strong> v0.1-Tender | 投标演示版本</p>
        <p>Powered by MediaPipe + Qwen-7B + DTW</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
