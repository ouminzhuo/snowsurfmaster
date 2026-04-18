"""
DTW 动作对比模块

使用 Dynamic Time Warping 算法对比用户动作与标准模板
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
from loguru import logger


class ActionComparator:
    """滑雪动作对比器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化对比器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.radius = self.config.get('radius', 3)
        self.normalize = self.config.get('normalize', True)
        logger.info("ActionComparator initialized with DTW")
    
    def load_template(self, template_path: str) -> Dict:
        """
        加载标准动作模板
        
        Args:
            template_path: 模板文件路径
            
        Returns:
            模板数据字典
        """
        import json
        from pathlib import Path
        
        template_path = Path(template_path)
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = json.load(f)
        
        logger.info(f"Loaded template: {template_path.name}")
        return template
    
    def extract_metric_sequence(self, metrics: Dict, metric_names: List[str]) -> np.ndarray:
        """
        从指标数据中提取时间序列
        
        Args:
            metrics: 指标字典
            metric_names: 要提取的指标名称列表
            
        Returns:
            numpy 数组 (frames x metrics)
        """
        sequences = []
        
        for frame_data in metrics['frames']:
            frame_values = []
            for metric_name in metric_names:
                value = frame_data['metrics'].get(metric_name)
                if value is None or np.isnan(value):
                    value = 0.0  # 用 0 填充缺失值
                frame_values.append(value)
            sequences.append(frame_values)
        
        return np.array(sequences)
    
    def calculate_dtw_distance(self, sequence1: np.ndarray, 
                               sequence2: np.ndarray) -> Tuple[float, List]:
        """
        计算两个序列的 DTW 距离
        
        Args:
            sequence1: 序列 1 (n x m)
            sequence2: 序列 2 (p x m)
            
        Returns:
            (dtw_distance, path)
        """
        distance, path = fastdtw(sequence1, sequence2, radius=self.radius, dist=euclidean)
        
        return float(distance), path
    
    def normalize_sequence(self, sequence: np.ndarray) -> np.ndarray:
        """
        归一化序列（min-max 归一化到 0-1）
        
        Args:
            sequence: 输入序列
            
        Returns:
            归一化序列
        """
        min_val = np.nanmin(sequence, axis=0)
        max_val = np.nanmax(sequence, axis=0)
        
        # 避免除零
        range_val = max_val - min_val
        range_val[range_val == 0] = 1
        
        normalized = (sequence - min_val) / range_val
        
        return normalized
    
    def compare_with_template(self, user_metrics: Dict, template: Dict,
                             metric_names: Optional[List[str]] = None) -> Dict:
        """
        对比用户动作与标准模板
        
        Args:
            user_metrics: 用户动作指标
            template: 标准动作模板
            metric_names: 要对比的指标列表
            
        Returns:
            对比结果字典
        """
        if metric_names is None:
            # 默认对比关键指标
            metric_names = [
                'left_knee_angle', 'right_knee_angle',
                'left_hip_angle', 'right_hip_angle',
                'forward_lean', 'symmetry_score'
            ]
        
        logger.info(f"Comparing action with template using metrics: {metric_names}")
        
        # 提取序列
        user_sequence = self.extract_metric_sequence(user_metrics, metric_names)
        template_sequence = self.extract_metric_sequence(template, metric_names)
        
        # 归一化
        if self.normalize:
            user_sequence = self.normalize_sequence(user_sequence)
            template_sequence = self.normalize_sequence(template_sequence)
        
        # 计算 DTW 距离
        dtw_distance, path = self.calculate_dtw_distance(user_sequence, template_sequence)
        
        # 计算相似度评分（0-100）
        # DTW 距离越小，相似度越高
        max_distance = len(user_sequence) * len(metric_names) * 2  # 理论最大距离
        similarity_score = max(0, 100 * (1 - dtw_distance / max_distance))
        
        # 逐指标分析
        metric_analysis = {}
        for i, metric_name in enumerate(metric_names):
            user_metric = user_sequence[:, i]
            template_metric = template_sequence[:, i]
            
            # 计算该指标的 DTW 距离
            metric_dtw, _ = fastdtw(user_metric.reshape(-1, 1), 
                                   template_metric.reshape(-1, 1), 
                                   radius=self.radius, dist=euclidean)
            
            # 计算均值差异
            user_mean = np.nanmean(user_metric)
            template_mean = np.nanmean(template_metric)
            mean_diff = user_mean - template_mean
            
            metric_analysis[metric_name] = {
                'dtw_distance': float(metric_dtw),
                'user_mean': float(user_mean),
                'template_mean': float(template_mean),
                'difference': float(mean_diff),
                'status': self._get_status(mean_diff, metric_name)
            }
        
        result = {
            'overall': {
                'dtw_distance': float(dtw_distance),
                'similarity_score': float(similarity_score),
                'template_name': template.get('template_name', 'unknown')
            },
            'metric_analysis': metric_analysis,
            'path': path
        }
        
        logger.info(f"Comparison complete: similarity={similarity_score:.1f}%")
        
        return result
    
    def _get_status(self, diff: float, metric_name: str) -> str:
        """
        根据差异判断状态
        
        Args:
            diff: 差异值
            metric_name: 指标名称
            
        Returns:
            状态字符串
        """
        # 不同指标的合理差异范围不同
        thresholds = {
            'left_knee_angle': 10,
            'right_knee_angle': 10,
            'left_hip_angle': 15,
            'right_hip_angle': 15,
            'forward_lean': 5,
            'symmetry_score': -10  # 对称性越高越好
        }
        
        threshold = thresholds.get(metric_name, 10)
        
        if metric_name == 'symmetry_score':
            # 对称性：负差异表示比模板差
            if diff >= 0:
                return "excellent"
            elif diff >= threshold:
                return "good"
            else:
                return "needs_improvement"
        else:
            # 角度：绝对值越小越好
            abs_diff = abs(diff)
            if abs_diff <= threshold * 0.5:
                return "excellent"
            elif abs_diff <= threshold:
                return "good"
            else:
                return "needs_improvement"
    
    def compare_multiple_templates(self, user_metrics: Dict, 
                                   template_paths: List[str]) -> Dict:
        """
        对比多个模板，返回最佳匹配
        
        Args:
            user_metrics: 用户动作指标
            template_paths: 模板文件路径列表
            
        Returns:
            对比结果字典
        """
        results = []
        
        for template_path in template_paths:
            try:
                template = self.load_template(template_path)
                result = self.compare_with_template(user_metrics, template)
                result['template_path'] = template_path
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to load template {template_path}: {e}")
        
        # 按相似度排序
        results.sort(key=lambda x: x['overall']['similarity_score'], reverse=True)
        
        return {
            'best_match': results[0] if results else None,
            'all_results': results
        }


# 便捷函数
def compare_with_template(user_metrics: Dict, template: Dict, 
                         config: Optional[Dict] = None) -> Dict:
    """
    便捷函数：对比用户动作与模板
    
    Args:
        user_metrics: 用户指标
        template: 标准模板
        config: 配置字典
        
    Returns:
        对比结果
    """
    comparator = ActionComparator(config)
    return comparator.compare_with_template(user_metrics, template)


if __name__ == "__main__":
    import json
    from pathlib import Path
    
    # 测试
    user_file = "data/processed/test_metrics.json"
    template_file = "data/templates/parallel_turn_pro.json"
    
    if Path(user_file).exists() and Path(template_file).exists():
        with open(user_file, 'r', encoding='utf-8') as f:
            user_metrics = json.load(f)
        
        with open(template_file, 'r', encoding='utf-8') as f:
            template = json.load(f)
        
        comparator = ActionComparator()
        result = comparator.compare_with_template(user_metrics, template)
        
        print(f"Similarity score: {result['overall']['similarity_score']:.1f}%")
        print(f"DTW distance: {result['overall']['dtw_distance']:.2f}")
    else:
        print("Test files not found. Please run extraction and metrics first.")
