"""
大模型反馈生成模块

基于对比结果，使用 Qwen-7B 生成自然语言滑雪动作反馈
"""

import json
from typing import Dict, List, Optional
from pathlib import Path
from loguru import logger


class FeedbackGenerator:
    """滑雪动作反馈生成器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化反馈生成器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.model_name = self.config.get('model_name', 'Qwen/Qwen-7B-Chat')
        self.quantization = self.config.get('quantization', '4bit')
        self.temperature = self.config.get('temperature', 0.7)
        
        self.model = None
        self.tokenizer = None
        
        logger.info("FeedbackGenerator initialized (lazy loading)")
    
    def load_model(self):
        """延迟加载模型"""
        if self.model is not None:
            return
        
        logger.info("Loading Qwen-7B model...")
        
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            # 加载 tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # 根据量化配置加载模型
            if self.quantization == '4bit':
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True
                )
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    quantization_config=quantization_config,
                    device_map="auto",
                    trust_remote_code=True
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    device_map="auto",
                    trust_remote_code=True
                )
            
            self.model.eval()
            logger.info("Model loaded successfully")
            
        except ImportError as e:
            logger.warning(f"Failed to load model: {e}")
            logger.warning("Feedback will use template-based generation")
            self.model = None
    
    def build_prompt(self, comparison_result: Dict, 
                    knowledge_context: Optional[str] = None) -> str:
        """
        构建 prompt
        
        Args:
            comparison_result: 对比结果
            knowledge_context: 滑雪知识库上下文（RAG）
            
        Returns:
            prompt 字符串
        """
        overall = comparison_result['overall']
        metrics = comparison_result['metric_analysis']
        
        # 基础信息
        prompt = f"""你是一位专业的滑雪教练。请根据以下动作分析数据，为学员生成一份专业的滑雪动作反馈报告。

## 整体评分
- 动作相似度：{overall['similarity_score']:.1f}/100
- DTW 距离：{overall['dtw_distance']:.2f}
- 对比模板：{overall['template_name']}

## 详细指标分析
"""
        
        # 添加各指标分析
        for metric_name, analysis in metrics.items():
            status_emoji = {
                'excellent': '✅',
                'good': '🟡',
                'needs_improvement': '❌'
            }.get(analysis['status'], '⚪')
            
            metric_name_cn = self._translate_metric_name(metric_name)
            prompt += f"""
### {status_emoji} {metric_name_cn}
- 你的数值：{analysis['user_mean']:.1f}
- 标准数值：{analysis['template_mean']:.1f}
- 差异：{analysis['difference']:+.1f}
- 评价：{self._translate_status(analysis['status'])}
"""
        
        # 添加知识库上下文（如果有）
        if knowledge_context:
            prompt += f"""
## 专业建议参考
{knowledge_context}
"""
        
        # 生成要求
        prompt += """
## 报告要求
请生成一份 300-500 字的反馈报告，包含：

1. **总体评价**（1-2 句话总结）
2. **做得好的地方**（2-3 点）
3. **需要改进的地方**（2-3 点，按优先级排序）
4. **具体训练建议**（2-3 个可执行的练习）

语气要求：
- 专业但友好
- 多鼓励，少批评
- 建议具体可执行
- 避免过于技术化的术语

请用中文回复。
"""
        
        return prompt
    
    def _translate_metric_name(self, metric_name: str) -> str:
        """翻译指标名称"""
        translations = {
            'left_knee_angle': '左膝角度',
            'right_knee_angle': '右膝角度',
            'left_hip_angle': '左髋角度',
            'right_hip_angle': '右髋角度',
            'left_shoulder_angle': '左肩角度',
            'right_shoulder_angle': '右肩角度',
            'forward_lean': '身体前倾',
            'symmetry_score': '左右对称性'
        }
        return translations.get(metric_name, metric_name)
    
    def _translate_status(self, status: str) -> str:
        """翻译状态"""
        translations = {
            'excellent': '优秀',
            'good': '良好',
            'needs_improvement': '需要改进'
        }
        return translations.get(status, status)
    
    def generate_feedback(self, comparison_result: Dict, 
                         use_llm: bool = True) -> str:
        """
        生成反馈
        
        Args:
            comparison_result: 对比结果
            use_llm: 是否使用大模型（否则用模板）
            
        Returns:
            反馈文本
        """
        if use_llm and self.model is not None:
            return self._generate_with_llm(comparison_result)
        else:
            return self._generate_with_template(comparison_result)
    
    def _generate_with_llm(self, comparison_result: Dict) -> str:
        """使用大模型生成反馈"""
        import torch
        
        prompt = self.build_prompt(comparison_result)
        
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = inputs.to(self.model.device)
        
        # 生成
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=self.temperature,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # 提取生成的文本（跳过 prompt 部分）
        generated_text = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:], 
            skip_special_tokens=True
        )
        
        return generated_text.strip()
    
    def _generate_with_template(self, comparison_result: Dict) -> str:
        """使用模板生成反馈（备用方案）"""
        overall = comparison_result['overall']
        metrics = comparison_result['metric_analysis']
        
        # 总体评价
        if overall['similarity_score'] >= 80:
            overall_comment = "非常出色的动作！你的技术已经接近专业水平。"
        elif overall['similarity_score'] >= 60:
            overall_comment = "不错的动作！基础扎实，还有一些细节可以优化。"
        else:
            overall_comment = "继续加油！掌握了一些基础，但还有较大提升空间。"
        
        # 找出优点和需改进点
        strengths = []
        improvements = []
        
        for metric_name, analysis in metrics.items():
            metric_cn = self._translate_metric_name(metric_name)
            if analysis['status'] == 'excellent':
                strengths.append(f"{metric_cn}控制得很好")
            elif analysis['status'] == 'needs_improvement':
                diff = analysis['difference']
                if diff > 0:
                    improvements.append(f"{metric_cn}偏大（+{diff:.1f}°），建议适当减小")
                else:
                    improvements.append(f"{metric_cn}偏小（{diff:.1f}°），建议适当增大")
        
        # 组装报告
        report = f"""🎿 滑雪动作分析报告

【总体评价】
{overall_comment}
动作相似度：{overall['similarity_score']:.1f}/100

【做得好的地方】
"""
        
        for i, strength in enumerate(strengths, 1):
            report += f"{i}. ✅ {strength}\n"
        
        if not strengths:
            report += "继续保持，整体表现稳定！\n"
        
        report += "\n【需要改进的地方】\n"
        
        for i, improvement in enumerate(improvements[:3], 1):  # 最多 3 个
            report += f"{i}. 🔧 {improvement}\n"
        
        if not improvements:
            report += "动作已经很标准，可以继续挑战更高难度！\n"
        
        report += "\n【训练建议】\n"
        report += "1. 对着镜子练习基本站姿，感受正确的角度\n"
        report += "2. 录制自己的动作视频，与标准动作对比\n"
        report += "3. 请教练现场指导，及时纠正错误动作\n"
        
        return report
    
    def generate_report(self, comparison_result: Dict, 
                       output_path: str, format: str = 'html') -> str:
        """
        生成完整报告（HTML 或 PDF）
        
        Args:
            comparison_result: 对比结果
            output_path: 输出路径
            format: 格式（'html' 或 'pdf'）
            
        Returns:
            报告文件路径
        """
        feedback_text = self.generate_feedback(comparison_result)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'html':
            html_content = self._build_html_report(comparison_result, feedback_text)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML report saved to {output_path}")
        
        elif format == 'pdf':
            # TODO: 使用 pdfkit 或 reportlab 生成 PDF
            logger.warning("PDF generation not implemented yet, using HTML")
            html_path = output_path.with_suffix('.html')
            html_content = self._build_html_report(comparison_result, feedback_text)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return str(html_path)
        
        return str(output_path)
    
    def _build_html_report(self, comparison_result: Dict, feedback_text: str) -> str:
        """构建 HTML 报告"""
        overall = comparison_result['overall']
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>snowsurfmaster - 滑雪动作分析报告</title>
    <style>
        body {{ font-family: 'Arial', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; }}
        .score {{ font-size: 48px; font-weight: bold; }}
        .section {{ margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
        .metric {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e0e0e0; }}
        .excellent {{ color: #28a745; }}
        .good {{ color: #ffc107; }}
        .needs_improvement {{ color: #dc3545; }}
        .feedback {{ white-space: pre-wrap; line-height: 1.8; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎿 snowsurfmaster</h1>
        <h2>滑雪动作分析报告</h2>
        <div class="score">{overall['similarity_score']:.0f}<span style="font-size: 24px;">/100</span></div>
        <p>动作相似度</p>
    </div>
    
    <div class="section">
        <h3>📊 详细指标</h3>
"""
        
        for metric_name, analysis in comparison_result['metric_analysis'].items():
            status_class = analysis['status']
            metric_cn = self._translate_metric_name(metric_name)
            html += f"""
        <div class="metric">
            <span>{metric_cn}</span>
            <span class="{status_class}">{analysis['status'].replace('_', ' ').title()}</span>
        </div>
"""
        
        html += f"""
    </div>
    
    <div class="section">
        <h3>📝 专业反馈</h3>
        <div class="feedback">{feedback_text}</div>
    </div>
    
    <div style="text-align: center; margin-top: 40px; color: #666;">
        <p>Generated by snowsurfmaster | {overall['template_name']}</p>
    </div>
</body>
</html>
"""
        
        return html


# 便捷函数
def generate_feedback(comparison_result: Dict, config: Optional[Dict] = None) -> str:
    """
    便捷函数：生成反馈
    
    Args:
        comparison_result: 对比结果
        config: 配置字典
        
    Returns:
        反馈文本
    """
    generator = FeedbackGenerator(config)
    generator.load_model()
    return generator.generate_feedback(comparison_result)


if __name__ == "__main__":
    # 测试
    test_comparison = {
        'overall': {
            'similarity_score': 72.5,
            'dtw_distance': 15.3,
            'template_name': 'parallel_turn_pro'
        },
        'metric_analysis': {
            'left_knee_angle': {
                'user_mean': 125.0,
                'template_mean': 130.0,
                'difference': -5.0,
                'status': 'good'
            },
            'symmetry_score': {
                'user_mean': 75.0,
                'template_mean': 85.0,
                'difference': -10.0,
                'status': 'needs_improvement'
            }
        }
    }
    
    generator = FeedbackGenerator()
    feedback = generator.generate_feedback(test_comparison, use_llm=False)
    print(feedback)
