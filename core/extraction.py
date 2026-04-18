"""
MediaPipe 骨骼提取模块

从滑雪视频中提取人体骨骼关键点（33 个 BlazePose 关键点）
输出格式：JSON 或 CSV
"""

import cv2
import mediapipe as mp
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Optional, Union
from loguru import logger
from tqdm import tqdm


class SkeletonExtractor:
    """滑雪视频骨骼关键点提取器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化提取器
        
        Args:
            config: 配置字典，包含 mediapipe 相关参数
        """
        self.config = config or {}
        
        # MediaPipe Pose 配置
        model_complexity = self.config.get('model_complexity', 1)
        smooth_landmarks = self.config.get('smooth_landmarks', True)
        min_detection_confidence = self.config.get('min_detection_confidence', 0.5)
        min_tracking_confidence = self.config.get('min_tracking_confidence', 0.5)
        
        # 初始化 MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            smooth_landmarks=smooth_landmarks,
            enable_segmentation=False,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        logger.info("SkeletonExtractor initialized with MediaPipe BlazePose")
    
    def extract_from_video(self, video_path: str, output_path: Optional[str] = None, 
                          output_format: str = 'json') -> Dict:
        """
        从视频中提取骨骼关键点
        
        Args:
            video_path: 输入视频路径
            output_path: 输出文件路径（可选）
            output_format: 输出格式 ('json' 或 'csv')
            
        Returns:
            包含骨骼数据的字典
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        logger.info(f"Starting skeleton extraction from {video_path.name}")
        
        # 打开视频
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(f"Video info: {fps}fps, {total_frames}frames, {width}x{height}")
        
        # 存储骨骼数据
        skeleton_data = {
            'video_info': {
                'path': str(video_path),
                'fps': fps,
                'total_frames': total_frames,
                'width': width,
                'height': height
            },
            'frames': [],
            'keypoints': self._get_keypoint_names()
        }
        
        frame_idx = 0
        pbar = tqdm(total=total_frames, desc="Extracting skeletons")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # 转换为 RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            
            # MediaPipe 推理
            results = self.pose.process(image)
            
            # 提取关键点
            frame_data = {
                'frame_idx': frame_idx,
                'timestamp': frame_idx / fps,
                'keypoints': []
            }
            
            if results.pose_landmarks:
                for landmark in results.pose_landmarks.landmark:
                    frame_data['keypoints'].append({
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z,
                        'visibility': landmark.visibility
                    })
            else:
                # 未检测到人，填充 NaN
                frame_data['keypoints'] = [{'x': float('nan'), 'y': float('nan'), 
                                           'z': float('nan'), 'visibility': 0.0}] * 33
            
            skeleton_data['frames'].append(frame_data)
            frame_idx += 1
            pbar.update(1)
        
        cap.release()
        self.pose.close()
        pbar.close()
        
        logger.info(f"Extraction complete: {len(skeleton_data['frames'])} frames processed")
        
        # 保存结果
        if output_path:
            self.save(skeleton_data, output_path, output_format)
        
        return skeleton_data
    
    def save(self, skeleton_data: Dict, output_path: str, format: str = 'json'):
        """
        保存骨骼数据
        
        Args:
            skeleton_data: 骨骼数据字典
            output_path: 输出路径
            format: 格式 ('json' 或 'csv')
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(skeleton_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved JSON to {output_path}")
        
        elif format == 'csv':
            import pandas as pd
            # 转换为 DataFrame
            rows = []
            for frame in skeleton_data['frames']:
                row = {'frame_idx': frame['frame_idx'], 'timestamp': frame['timestamp']}
                for i, kp in enumerate(frame['keypoints']):
                    row[f'kp_{i}_x'] = kp['x']
                    row[f'kp_{i}_y'] = kp['y']
                    row[f'kp_{i}_z'] = kp['z']
                    row[f'kp_{i}_vis'] = kp['visibility']
                rows.append(row)
            
            df = pd.DataFrame(rows)
            df.to_csv(output_path, index=False)
            logger.info(f"Saved CSV to {output_path}")
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _get_keypoint_names(self) -> List[str]:
        """返回 33 个关键点的名称"""
        return [
            "nose", "left_eye_inner", "left_eye", "left_eye_outer",
            "right_eye_inner", "right_eye", "right_eye_outer",
            "left_ear", "right_ear", "mouth_left", "mouth_right",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_pinky", "right_pinky",
            "left_index", "right_index", "left_thumb", "right_thumb",
            "left_hip", "right_hip", "left_knee", "right_knee",
            "left_ankle", "right_ankle", "left_heel", "right_heel",
            "left_foot_index", "right_foot_index"
        ]
    
    def visualize(self, video_path: str, output_path: str, 
                 skeleton_data: Optional[Dict] = None):
        """
        在视频上可视化骨骼关键点
        
        Args:
            video_path: 输入视频路径
            output_path: 输出视频路径
            skeleton_data: 预提取的骨骼数据（可选，避免重复提取）
        """
        if skeleton_data is None:
            skeleton_data = self.extract_from_video(video_path)
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for frame_data in tqdm(skeleton_data['frames'], desc="Visualizing"):
            ret, frame = cap.read()
            if not ret:
                break
            
            # 重建 landmarks
            landmarks = []
            for kp in frame_data['keypoints']:
                if not np.isnan(kp['x']):
                    landmarks.append(mp.solutions.pose.NormalizedLandmark(
                        x=kp['x'], y=kp['y'], z=kp['z'], visibility=kp['visibility']
                    ))
            
            if landmarks:
                # 绘制骨骼
                self.mp_drawing.draw_landmarks(
                    frame,
                    mp.solutions.pose.PoseLandmarkList(landmarks),
                    self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style_spec()
                )
            
            out.write(frame)
        
        cap.release()
        out.release()
        logger.info(f"Visualization saved to {output_path}")


# 便捷函数
def extract_skeleton(video_path: str, output_path: Optional[str] = None, 
                    config: Optional[Dict] = None) -> Dict:
    """
    便捷函数：从视频提取骨骼
    
    Args:
        video_path: 视频路径
        output_path: 输出路径（可选）
        config: 配置字典
        
    Returns:
        骨骼数据字典
    """
    extractor = SkeletonExtractor(config)
    return extractor.extract_from_video(video_path, output_path)


if __name__ == "__main__":
    # 测试示例
    import yaml
    
    # 加载配置
    config_path = Path(__file__).parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    else:
        config = {}
    
    # 测试视频（需要替换为实际路径）
    test_video = "data/raw/test_skiing.mp4"
    
    if Path(test_video).exists():
        extractor = SkeletonExtractor(config.get('mediapipe', {}))
        result = extractor.extract_from_video(
            test_video, 
            "data/processed/test_skeleton.json",
            output_format='json'
        )
        print(f"Extracted {len(result['frames'])} frames")
    else:
        print(f"Test video not found: {test_video}")
        print("Please place a test video in data/raw/ folder")
