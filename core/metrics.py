"""
关节角度计算模块

基于 MediaPipe 提取的骨骼关键点，计算滑雪运动相关的关节角度和指标
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from loguru import logger


class AngleCalculator:
    """滑雪运动关节角度计算器"""
    
    # MediaPipe 关键点索引
    KEYPOINT_INDICES = {
        'nose': 0,
        'left_shoulder': 11,
        'right_shoulder': 12,
        'left_elbow': 13,
        'right_elbow': 14,
        'left_wrist': 15,
        'right_wrist': 16,
        'left_hip': 23,
        'right_hip': 24,
        'left_knee': 25,
        'right_knee': 26,
        'left_ankle': 27,
        'right_ankle': 28,
        'left_heel': 29,
        'right_heel': 30,
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化角度计算器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.window_size = self.config.get('window_size', 10)
        logger.info("AngleCalculator initialized")
    
    def calculate_angle(self, point_a: np.ndarray, point_b: np.ndarray, 
                       point_c: np.ndarray) -> float:
        """
        计算三点形成的角度（点 B 为顶点）
        
        Args:
            point_a: 点 A 坐标 (x, y, z)
            point_b: 点 B 坐标（顶点）
            point_c: 点 C 坐标
            
        Returns:
            角度值（度）
        """
        # 转换为 numpy 数组
        a = np.array(point_a)
        b = np.array(point_b)
        c = np.array(point_c)
        
        # 检查 NaN
        if np.any(np.isnan(a)) or np.any(np.isnan(b)) or np.any(np.isnan(c)):
            return float('nan')
        
        # 计算向量
        ba = a - b
        bc = c - b
        
        # 计算角度
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)  # 防止数值误差
        
        angle = np.degrees(np.arccos(cosine_angle))
        
        return float(angle)
    
    def calculate_knee_angle(self, keypoints: List[Dict], side: str = 'left') -> float:
        """
        计算膝盖角度（髋 - 膝 - 踝）
        
        Args:
            keypoints: 关键点列表
            side: 'left' 或 'right'
            
        Returns:
            膝盖角度（度）
        """
        if side == 'left':
            hip_idx = self.KEYPOINT_INDICES['left_hip']
            knee_idx = self.KEYPOINT_INDICES['left_knee']
            ankle_idx = self.KEYPOINT_INDICES['left_ankle']
        else:
            hip_idx = self.KEYPOINT_INDICES['right_hip']
            knee_idx = self.KEYPOINT_INDICES['right_knee']
            ankle_idx = self.KEYPOINT_INDICES['right_ankle']
        
        hip = [keypoints[hip_idx]['x'], keypoints[hip_idx]['y'], keypoints[hip_idx]['z']]
        knee = [keypoints[knee_idx]['x'], keypoints[knee_idx]['y'], keypoints[knee_idx]['z']]
        ankle = [keypoints[ankle_idx]['x'], keypoints[ankle_idx]['y'], keypoints[ankle_idx]['z']]
        
        return self.calculate_angle(hip, knee, ankle)
    
    def calculate_hip_angle(self, keypoints: List[Dict], side: str = 'left') -> float:
        """
        计算髋关节角度（肩 - 髋 - 膝）
        
        Args:
            keypoints: 关键点列表
            side: 'left' 或 'right'
            
        Returns:
            髋关节角度（度）
        """
        if side == 'left':
            shoulder_idx = self.KEYPOINT_INDICES['left_shoulder']
            hip_idx = self.KEYPOINT_INDICES['left_hip']
            knee_idx = self.KEYPOINT_INDICES['left_knee']
        else:
            shoulder_idx = self.KEYPOINT_INDICES['right_shoulder']
            hip_idx = self.KEYPOINT_INDICES['right_hip']
            knee_idx = self.KEYPOINT_INDICES['right_knee']
        
        shoulder = [keypoints[shoulder_idx]['x'], keypoints[shoulder_idx]['y'], keypoints[shoulder_idx]['z']]
        hip = [keypoints[hip_idx]['x'], keypoints[hip_idx]['y'], keypoints[hip_idx]['z']]
        knee = [keypoints[knee_idx]['x'], keypoints[knee_idx]['y'], keypoints[knee_idx]['z']]
        
        return self.calculate_angle(shoulder, hip, knee)
    
    def calculate_shoulder_angle(self, keypoints: List[Dict], side: str = 'left') -> float:
        """
        计算肩关节角度（髋 - 肩 - 肘）
        
        Args:
            keypoints: 关键点列表
            side: 'left' 或 'right'
            
        Returns:
            肩关节角度（度）
        """
        if side == 'left':
            hip_idx = self.KEYPOINT_INDICES['left_hip']
            shoulder_idx = self.KEYPOINT_INDICES['left_shoulder']
            elbow_idx = self.KEYPOINT_INDICES['left_elbow']
        else:
            hip_idx = self.KEYPOINT_INDICES['right_hip']
            shoulder_idx = self.KEYPOINT_INDICES['right_shoulder']
            elbow_idx = self.KEYPOINT_INDICES['right_elbow']
        
        hip = [keypoints[hip_idx]['x'], keypoints[hip_idx]['y'], keypoints[hip_idx]['z']]
        shoulder = [keypoints[shoulder_idx]['x'], keypoints[shoulder_idx]['y'], keypoints[shoulder_idx]['z']]
        elbow = [keypoints[elbow_idx]['x'], keypoints[elbow_idx]['y'], keypoints[elbow_idx]['z']]
        
        return self.calculate_angle(hip, shoulder, elbow)
    
    def calculate_forward_lean(self, keypoints: List[Dict]) -> float:
        """
        计算身体前倾角度（肩膀相对于髋部的前倾）
        
        滑雪关键指标：前倾角度反映重心位置
        
        Args:
            keypoints: 关键点列表
            
        Returns:
            前倾角度（度），正值表示前倾
        """
        # 取左右肩膀和髋部的中点
        left_shoulder = self.KEYPOINT_INDICES['left_shoulder']
        right_shoulder = self.KEYPOINT_INDICES['right_shoulder']
        left_hip = self.KEYPOINT_INDICES['left_hip']
        right_hip = self.KEYPOINT_INDICES['right_hip']
        
        shoulder_x = (keypoints[left_shoulder]['x'] + keypoints[right_shoulder]['x']) / 2
        shoulder_y = (keypoints[left_shoulder]['y'] + keypoints[right_shoulder]['y']) / 2
        
        hip_x = (keypoints[left_hip]['x'] + keypoints[right_hip]['x']) / 2
        hip_y = (keypoints[left_hip]['y'] + keypoints[right_hip]['y']) / 2
        
        # 计算肩膀相对于髋部的水平偏移（在相机坐标系中，y 轴向下）
        # 负值表示前倾（肩膀在髋部前方）
        lean_angle = np.degrees(np.arctan2(shoulder_x - hip_x, hip_y - shoulder_y))
        
        return float(lean_angle)
    
    def calculate_symmetry_score(self, keypoints: List[Dict]) -> float:
        """
        计算左右对称性评分
        
        滑雪关键指标：左右腿动作应该对称
        
        Args:
            keypoints: 关键点列表
            
        Returns:
            对称性评分（0-100），100 表示完全对称
        """
        # 计算左右膝盖角度差
        left_knee = self.calculate_knee_angle(keypoints, 'left')
        right_knee = self.calculate_knee_angle(keypoints, 'right')
        
        # 计算左右髋关节角度差
        left_hip = self.calculate_hip_angle(keypoints, 'left')
        right_hip = self.calculate_hip_angle(keypoints, 'right')
        
        # 计算对称性评分
        if np.isnan(left_knee) or np.isnan(right_knee) or np.isnan(left_hip) or np.isnan(right_hip):
            return float('nan')
        
        knee_diff = abs(left_knee - right_knee)
        hip_diff = abs(left_hip - right_hip)
        
        # 角度差越小，评分越高（假设 30 度差异为 0 分）
        symmetry_score = 100 - (knee_diff + hip_diff) / 2 * (100 / 30)
        symmetry_score = max(0, min(100, symmetry_score))
        
        return float(symmetry_score)
    
    def calculate_all_metrics(self, skeleton_data: Dict) -> Dict:
        """
        计算所有运动指标
        
        Args:
            skeleton_data: 骨骼数据字典
            
        Returns:
            包含所有指标的字典
        """
        metrics = {
            'video_info': skeleton_data['video_info'],
            'frames': []
        }
        
        logger.info(f"Calculating metrics for {len(skeleton_data['frames'])} frames")
        
        for frame_data in skeleton_data['frames']:
            keypoints = frame_data['keypoints']
            
            # 检查是否有有效数据
            if np.isnan(keypoints[0]['x']):
                metrics['frames'].append({
                    'frame_idx': frame_data['frame_idx'],
                    'timestamp': frame_data['timestamp'],
                    'metrics': {}
                })
                continue
            
            frame_metrics = {
                'frame_idx': frame_data['frame_idx'],
                'timestamp': frame_data['timestamp'],
                'metrics': {
                    'left_knee_angle': self.calculate_knee_angle(keypoints, 'left'),
                    'right_knee_angle': self.calculate_knee_angle(keypoints, 'right'),
                    'left_hip_angle': self.calculate_hip_angle(keypoints, 'left'),
                    'right_hip_angle': self.calculate_hip_angle(keypoints, 'right'),
                    'left_shoulder_angle': self.calculate_shoulder_angle(keypoints, 'left'),
                    'right_shoulder_angle': self.calculate_shoulder_angle(keypoints, 'right'),
                    'forward_lean': self.calculate_forward_lean(keypoints),
                    'symmetry_score': self.calculate_symmetry_score(keypoints)
                }
            }
            
            metrics['frames'].append(frame_metrics)
        
        logger.info("Metrics calculation complete")
        return metrics
    
    def smooth_metrics(self, metrics: Dict) -> Dict:
        """
        对指标进行平滑处理（移动平均）
        
        Args:
            metrics: 指标字典
            
        Returns:
            平滑后的指标字典
        """
        smoothed = {
            'video_info': metrics['video_info'],
            'frames': []
        }
        
        metric_names = ['left_knee_angle', 'right_knee_angle', 'left_hip_angle', 
                       'right_hip_angle', 'forward_lean', 'symmetry_score']
        
        for i, frame_data in enumerate(metrics['frames']):
            smoothed_frame = {
                'frame_idx': frame_data['frame_idx'],
                'timestamp': frame_data['timestamp'],
                'metrics': {}
            }
            
            for metric_name in metric_names:
                if metric_name not in frame_data['metrics']:
                    continue
                
                # 获取窗口数据
                start_idx = max(0, i - self.window_size // 2)
                end_idx = min(len(metrics['frames']), i + self.window_size // 2 + 1)
                
                window_values = []
                for j in range(start_idx, end_idx):
                    value = metrics['frames'][j]['metrics'].get(metric_name)
                    if value is not None and not np.isnan(value):
                        window_values.append(value)
                
                # 计算移动平均
                if window_values:
                    smoothed_frame['metrics'][metric_name] = float(np.mean(window_values))
                else:
                    smoothed_frame['metrics'][metric_name] = float('nan')
            
            smoothed['frames'].append(smoothed_frame)
        
        return smoothed


# 便捷函数
def calculate_angles(skeleton_data: Dict, config: Optional[Dict] = None) -> Dict:
    """
    便捷函数：计算骨骼角度
    
    Args:
        skeleton_data: 骨骼数据
        config: 配置字典
        
    Returns:
        指标字典
    """
    calculator = AngleCalculator(config)
    metrics = calculator.calculate_all_metrics(skeleton_data)
    return calculator.smooth_metrics(metrics)


if __name__ == "__main__":
    import json
    from pathlib import Path
    
    # 测试数据
    test_file = "data/processed/test_skeleton.json"
    
    if Path(test_file).exists():
        with open(test_file, 'r', encoding='utf-8') as f:
            skeleton_data = json.load(f)
        
        calculator = AngleCalculator()
        metrics = calculator.calculate_all_metrics(skeleton_data)
        
        print(f"Calculated metrics for {len(metrics['frames'])} frames")
        print(f"Sample metrics (frame 0): {metrics['frames'][0]['metrics']}")
    else:
        print(f"Test file not found: {test_file}")
        print("Please run extraction.py first")
