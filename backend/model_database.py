# C:\LabelAI\backend\model_database.py

"""
Centralized database for all supported AI models.
This file acts as a single source of truth for which models are available
for each specific annotation task. This allows for dynamic UI generation
and a scalable way to add new models.
"""

# The core model database
# Each key is a task category, and the value is a dictionary containing:
#   - 'description': A short description of the task.
#   - 'models': A list of model dictionaries.
# Each model dictionary contains:
#   - 'name': The display name of the model in the UI.
#   - 'adapter': The class name of the adapter responsible for its inference.
#   - 'tool': The name of the tool required for the model.
#   - 'library': The name of the pip package required for the model (optional).
MODEL_DATABASE = {
    "Bounding Box": {
        "description": "General Object Detection",
        "models": [
            {"name": "YOLOv8", "adapter": "YOLOAdapter", "tool": "bbox", "library": "ultralytics"},
            {"name": "RetinaNet", "adapter": "RetinaNetAdapter", "tool": "bbox", "library": "torchvision"},
            {"name": "Faster R-CNN", "adapter": "FasterRCNNAdapter", "tool": "bbox", "library": "torchvision"},
            {"name": "EfficientDet", "adapter": "EfficientDetAdapter", "tool": "bbox", "library": "torchvision"},
            {"name": "SSD", "adapter": "SSDAdapter", "tool": "bbox", "library": "torchvision"},
            {"name": "GroundingDINO", "adapter": "GroundingDINOAdapter", "tool": "bbox", "library": "groundingdino-py"},
            {"name": "GroundingDINO / OWL-ViT", "adapter": "GroundingDINOAdapter", "tool": "bbox", "library": "groundingdino-py"},
        ]
    },
    "Polygons/Mask": {
        "description": "Precise Shape & Differentiation",
        "models": [
            {"name": "Mask R-CNN", "adapter": "MaskRCNNAdapter", "tool": "polygon", "library": "torchvision"},
            {"name": "DeepLabv3+", "adapter": "DeepLabv3Adapter", "tool": "polygon", "library": "torchvision"},
            {"name": "U-Net", "adapter": "UNetAdapter", "tool": "polygon", "library": "segmentation-models-pytorch"},
            {"name": "SegFormer", "adapter": "SegFormerAdapter", "tool": "polygon", "library": "timm"},
            {"name": "Segment Anything (SAM)", "adapter": "SAMAdapter", "tool": "prompt", "library": "segment-anything"},
            {"name": "Detectron2", "adapter": "Detectron2Adapter", "tool": "polygon", "library": "detectron2"},
            {"name": "MMDetection", "adapter": "MMDetectionAdapter", "tool": "polygon", "library": "mmdet"},
        ]
    },
    "Keypoints": {
        "description": "Detect Object Structure & Landmarks",
        "models": [
            {"name": "OpenPose", "adapter": "OpenPoseAdapter", "tool": "keypoint", "library": "torch-openpose"},
            {"name": "HRNet", "adapter": "HRNetAdapter", "tool": "keypoint", "library": "mmpose"},
            {"name": "MediaPipe Pose", "adapter": "MediaPipePoseAdapter", "tool": "keypoint", "library": "mediapipe"},
            {"name": "PoseTrack", "adapter": "PoseTrackAdapter", "tool": "keypoint", "library": None},
        ]
    },
    "Object IDs": {
        "description": "Track Objects Consistently Over Time",
        "models": [
            {"name": "DeepSORT", "adapter": "DeepSORTAdapter", "tool": "bbox", "library": None},
            {"name": "ByteTrack", "adapter": "ByteTrackAdapter", "tool": "bbox", "library": None},
            {"name": "BoT-SORT", "adapter": "BoTSORTAdapter", "tool": "bbox", "library": None},
            {"name": "FairMOT", "adapter": "FairMOTAdapter", "tool": "bbox", "library": None},
            {"name": "CenterTrack", "adapter": "CenterTrackAdapter", "tool": "bbox", "library": None},
            {"name": "TraDeS / QDTrack", "adapter": "TraDeSAdapter", "tool": "bbox", "library": None},
            {"name": "PoseTrack", "adapter": "PoseTrackAdapter", "tool": "bbox", "library": None},
        ]
    }
}

def get_tasks():
    """Returns a list of all available annotation tasks."""
    return list(MODEL_DATABASE.keys())

def get_models_for_task(task_name):
    """Returns a list of models for a given annotation task."""
    return MODEL_DATABASE.get(task_name, {}).get("models", [])

def get_model_info(model_name):
    """Returns the info dictionary for a given model name."""
    for task in MODEL_DATABASE.values():
        for model in task["models"]:
            if model["name"] == model_name:
                return model
    return None
