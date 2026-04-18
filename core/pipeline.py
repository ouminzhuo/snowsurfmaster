"""
snowsurfmaster 主处理 Pipeline

整合所有模块：视频 → 骨骼提取 → 指标计算 → 动作对比 → 反馈生成
"""

import json
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
import yaml

from core.extraction import SkeletonExtractor
from core.metrics import AngleCalculator
from core.comparison import ActionComparator
from core.feedback import FeedbackGenerator


class SkiAnalysisPipeline:
    """滑雪动作分析完整流程"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化 Pipeline
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        
        if Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}
        
        logger.info("Initializing SkiAnalysisPipeline")
        
        # 初始化各模块
        self.extractor = SkeletonExtractor(self.config.get('mediapipe', {}))
        self.calculator = AngleCalculator(self.config.get('analysis', {}))
        self.comparator = ActionComparator(self.config.get('comparison', {}))
        self.feedback_gen = FeedbackGenerator(self.config.get('llm', {}))
        
        logger.info("Pipeline initialized")
    
    def analyze_video(self, video_path: str, 
                     template_path: Optional[str] = None,
                     output_dir: Optional[str] = None,
                     use_llm: bool = True) -> Dict:
        """
        分析滑雪视频
        
        Args:
            video_path: 输入视频路径
            template_path: 标准动作模板路径（可选）
            output_dir: 输出目录（可选）
            use_llm: 是否使用大模型生成反馈
            
        Returns:
            完整分析结果
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        logger.info(f"Starting analysis pipeline for {video_path.name}")
        
        # 1. 骨骼提取
        logger.info("Step 1/4: Extracting skeleton...")
        skeleton_data = self.extractor.extract_from_video(
            str(video_path),
            output_path=str(Path(output_dir or 'data/processed') / f"{video_path.stem}_skeleton.json") if output_dir else None,
            output_format='json'
        )
        
        # 2. 指标计算
        logger.info("Step 2/4: Calculating metrics...")
        metrics = self.calculator.calculate_all_metrics(skeleton_data)
        metrics = self.calculator.smooth_metrics(metrics)
        
        if output_dir:
            output_path = Path(output_dir) / f"{video_path.stem}_metrics.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        # 3. 动作对比
        logger.info("Step 3/4: Comparing with template...")
        if template_path is None:
            # 使用默认模板
            template_path = Path(__file__).parent.parent / "data/templates/parallel_turn_pro.json"
        
        if Path(template_path).exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            comparison_result = self.comparator.compare_with_template(metrics, template)
        else:
            logger.warning(f"Template not found: {template_path}")
            comparison_result = None
        
        # 4. 反馈生成
        logger.info("Step 4/4: Generating feedback...")
        if comparison_result:
            feedback_text = self.feedback_gen.generate_feedback(
                comparison_result, 
                use_llm=use_llm
            )
            
            if output_dir:
                report_path = self.feedback_gen.generate_report(
                    comparison_result,
                    output_path=str(Path(output_dir) / f"{video_path.stem}_report.html"),
                    format='html'
                )
            else:
                report_path = None
        else:
            feedback_text = "无法生成反馈：缺少标准动作模板"
            report_path = None
        
        # 组装结果
        result = {
            'video_info': skeleton_data['video_info'],
            'skeleton_data': skeleton_data,
            'metrics': metrics,
            'comparison': comparison_result,
            'feedback': feedback_text,
            'report_path': report_path
        }
        
        logger.info("Analysis pipeline complete")
        
        return result
    
    def analyze_batch(self, video_paths: list, 
                     template_path: Optional[str] = None,
                     output_dir: Optional[str] = None) -> list:
        """
        批量分析视频
        
        Args:
            video_paths: 视频路径列表
            template_path: 模板路径
            output_dir: 输出目录
            
        Returns:
            结果列表
        """
        results = []
        
        for i, video_path in enumerate(video_paths, 1):
            logger.info(f"Processing video {i}/{len(video_paths)}: {video_path}")
            
            try:
                result = self.analyze_video(
                    video_path,
                    template_path=template_path,
                    output_dir=output_dir
                )
                results.append({
                    'video': video_path,
                    'status': 'success',
                    'result': result
                })
            except Exception as e:
                logger.error(f"Failed to analyze {video_path}: {e}")
                results.append({
                    'video': video_path,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results


# 便捷函数
def analyze_skiing_video(video_path: str, config_path: Optional[str] = None) -> Dict:
    """
    便捷函数：分析滑雪视频
    
    Args:
        video_path: 视频路径
        config_path: 配置文件路径
        
    Returns:
        分析结果
    """
    pipeline = SkiAnalysisPipeline(config_path)
    return pipeline.analyze_video(video_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        pipeline = SkiAnalysisPipeline()
        result = pipeline.analyze_video(video_path, output_dir='output')
        
        print(f"\n{'='*50}")
        print(f"Analysis complete for: {video_path}")
        print(f"Similarity score: {result['comparison']['overall']['similarity_score']:.1f}/100")
        print(f"\nFeedback:\n{result['feedback']}")
    else:
        print("Usage: python pipeline.py <video_path>")
        print("Example: python pipeline.py data/demo/demo_beginner.mp4")
