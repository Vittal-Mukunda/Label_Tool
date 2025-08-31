# backend/keypoint_adapters.py

class OpenPoseAdapter:
    """Placeholder for the OpenPose model inference logic."""
    def infer(self, image_path):
        print(f"Running OpenPose on {image_path}")
        # Dummy data for a single person
        dummy_keypoints = {
            "type": "keypoint",
            "label": "person",
            "points": [
                [250, 150, 0.9], [270, 145, 0.85], [240, 145, 0.88], [280, 180, 0.92],
                [230, 180, 0.91], [320, 250, 0.8], [200, 250, 0.79], [350, 320, 0.82],
                [180, 320, 0.81], [300, 100, 0.75], [220, 100, 0.76], [360, 80, 0.7],
                [170, 80, 0.69], [260, 240, 0.95], [260, 300, 0.94]
            ],
            # COCO skeleton format
            "skeleton": [
                [0, 1], [0, 2], [1, 3], [2, 4], [5, 6], [5, 7], [7, 9],
                [6, 8], [8, 10], [5, 11], [6, 12], [11, 12], [11, 13], [12, 14]
            ]
        }
        return [dummy_keypoints]

class HRNetAdapter:
    """Placeholder for the HRNet model inference logic."""
    def infer(self, image_path):
        print(f"Running HRNet on {image_path}")
        # Dummy data for a single person
        dummy_keypoints = {
            "type": "keypoint",
            "label": "person",
            "points": [
                [255, 155, 0.9], [275, 150, 0.85], [245, 150, 0.88], [285, 185, 0.92],
                [235, 185, 0.91], [325, 255, 0.8], [205, 255, 0.79], [355, 325, 0.82],
                [185, 325, 0.81], [305, 105, 0.75], [225, 105, 0.76], [365, 85, 0.7],
                [175, 85, 0.69], [265, 245, 0.95], [265, 305, 0.94]
            ],
            "skeleton": [
                [0, 1], [0, 2], [1, 3], [2, 4], [5, 6], [5, 7], [7, 9],
                [6, 8], [8, 10], [5, 11], [6, 12], [11, 12], [11, 13], [12, 14]
            ]
        }
        return [dummy_keypoints]

class MediaPipePoseAdapter:
    """Placeholder for the MediaPipe Pose model inference logic."""
    def infer(self, image_path):
        print(f"Running MediaPipe Pose on {image_path}")
        # Dummy data for a single person
        dummy_keypoints = {
            "type": "keypoint",
            "label": "person",
            "points": [
                [260, 160, 0.9], [280, 155, 0.85], [250, 155, 0.88], [290, 190, 0.92],
                [240, 190, 0.91], [330, 260, 0.8], [210, 260, 0.79], [360, 330, 0.82],
                [190, 330, 0.81], [310, 110, 0.75], [230, 110, 0.76], [370, 90, 0.7],
                [180, 90, 0.69], [270, 250, 0.95], [270, 310, 0.94]
            ],
            "skeleton": [
                [0, 1], [0, 2], [1, 3], [2, 4], [5, 6], [5, 7], [7, 9],
                [6, 8], [8, 10], [5, 11], [6, 12], [11, 12], [11, 13], [12, 14]
            ]
        }
        return [dummy_keypoints]

class PoseTrackAdapter:
    """Placeholder for the PoseTrack model inference logic."""
    def infer(self, image_path):
        print(f"Running PoseTrack on {image_path}")
        # Dummy data for two people to test multi-person support
        person1_keypoints = {
            "type": "keypoint",
            "label": "person",
            "track_id": 1,
            "points": [
                [150, 150, 0.9], [170, 145, 0.85], [140, 145, 0.88], [180, 180, 0.92],
                [130, 180, 0.91], [220, 250, 0.8], [100, 250, 0.79], [250, 320, 0.82],
                [80, 320, 0.81], [200, 100, 0.75], [120, 100, 0.76], [260, 80, 0.7],
                [70, 80, 0.69], [160, 240, 0.95], [160, 300, 0.94]
            ],
            "skeleton": [
                [0, 1], [0, 2], [1, 3], [2, 4], [5, 6], [5, 7], [7, 9],
                [6, 8], [8, 10], [5, 11], [6, 12], [11, 12], [11, 13], [12, 14]
            ]
        }
        person2_keypoints = {
            "type": "keypoint",
            "label": "person",
            "track_id": 2,
            "points": [
                [350, 150, 0.9], [370, 145, 0.85], [340, 145, 0.88], [380, 180, 0.92],
                [330, 180, 0.91], [420, 250, 0.8], [300, 250, 0.79], [450, 320, 0.82],
                [280, 320, 0.81], [400, 100, 0.75], [320, 100, 0.76], [460, 80, 0.7],
                [270, 80, 0.69], [360, 240, 0.95], [360, 300, 0.94]
            ],
            "skeleton": [
                [0, 1], [0, 2], [1, 3], [2, 4], [5, 6], [5, 7], [7, 9],
                [6, 8], [8, 10], [5, 11], [6, 12], [11, 12], [11, 13], [12, 14]
            ]
        }
        return [person1_keypoints, person2_keypoints]
