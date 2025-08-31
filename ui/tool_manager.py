def get_available_tools(model_name: str):
    if model_name in ["Mask R-CNN", "Detectron2", "MMDetection"]:
        return ["Polygon Tool", "SAM Tool", "Bounding Box Tool"]
    elif model_name in ["DeepLabv3+", "U-Net", "SegFormer"]:
        return ["Mask Tool", "SAM Tool", "Bounding Box Tool"]
    else:
        return ["Bounding Box Tool"]