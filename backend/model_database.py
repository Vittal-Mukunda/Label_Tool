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
MODEL_DATABASE = {
    "Bounding Box": {
        "description": "General Object Detection",
        "models": [
            {"name": "YOLOv8", "adapter": "YOLOAdapter", "tool": "bbox"},
            {"name": "RetinaNet", "adapter": "RetinaNetAdapter", "tool": "bbox"},
            {"name": "Faster R-CNN", "adapter": "FasterRCNNAdapter", "tool": "bbox"},
            {"name": "EfficientDet", "adapter": "EfficientDetAdapter", "tool": "bbox"},
            {"name": "SSD", "adapter": "SSDAdapter", "tool": "bbox"},
            {"name": "GroundingDINO", "adapter": "GroundingDINOAdapter", "tool": "bbox"},
            {"name": "GroundingDINO / OWL-ViT", "adapter": "GroundingDINOAdapter", "tool": "bbox"},
        ]
    },
    "Polygons/Mask": {
        "description": "Precise Shape & Differentiation",
        "models": [
            {"name": "Mask R-CNN", "adapter": "MaskRCNNAdapter", "tool": "polygon"},
            {"name": "DeepLabv3+", "adapter": "DeepLabv3Adapter", "tool": "polygon"},
            {"name": "U-Net", "adapter": "UNetAdapter", "tool": "polygon"},
            {"name": "SegFormer", "adapter": "SegFormerAdapter", "tool": "polygon"},
            {"name": "Segment Anything (SAM)", "adapter": "SAMAdapter", "tool": "prompt"},
            {"name": "Detectron2", "adapter": "Detectron2Adapter", "tool": "polygon"},
            {"name": "MMDetection", "adapter": "MMDetectionAdapter", "tool": "polygon"},
        ]
    },
    "Keypoints": {
        "description": "Detect Object Structure & Landmarks",
        "models": [
            {"name": "OpenPose", "adapter": "OpenPoseAdapter", "tool": "keypoint"},
            {"name": "HRNet", "adapter": "HRNetAdapter", "tool": "keypoint"},
            {"name": "MediaPipe Pose", "adapter": "MediaPipePoseAdapter", "tool": "keypoint"},
            {"name": "PoseTrack", "adapter": "PoseTrackAdapter", "tool": "keypoint"},
        ]
    },
    "Object IDs": {
        "description": "Track Objects Consistently Over Time",
        "models": [
            {"name": "DeepSORT", "adapter": "DeepSORTAdapter", "tool": "bbox"},
            {"name": "ByteTrack", "adapter": "ByteTrackAdapter", "tool": "bbox"},
            {"name": "BoT-SORT", "adapter": "BoTSORTAdapter", "tool": "bbox"},
            {"name": "FairMOT", "adapter": "FairMOTAdapter", "tool": "bbox"},
            {"name": "CenterTrack", "adapter": "CenterTrackAdapter", "tool": "bbox"},
            {"name": "TraDeS / QDTrack", "adapter": "TraDeSAdapter", "tool": "bbox"},
            {"name": "PoseTrack", "adapter": "PoseTrackAdapter", "tool": "bbox"},
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
