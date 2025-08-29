import os
import json
import shutil
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
import numpy as np
from PIL import Image, ImageDraw

# ---------------------------
# Base Exporter
# ---------------------------

class Exporter(ABC):
    """Abstract base class for annotation exporters."""
    
    def __init__(self, annotations_data, output_dir, class_map, project_name=None, model_name=None):
        self.annotations_data = annotations_data
        self.output_dir = output_dir
        self.class_map = class_map
        self.project_name = project_name or "dataset_export"  # Default project name
        self.model_name = model_name
        
        # Create project structure: project_name/images/ and project_name/labels/
        self.project_path = os.path.join(self.output_dir, self.project_name)
        self.images_dir = os.path.join(self.project_path, "images")
        self.labels_dir = os.path.join(self.project_path, "labels")
        
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.labels_dir, exist_ok=True)
    
    @abstractmethod
    def export(self):
        """Exports the annotations to the specified format."""
        pass

# ---------------------------
# COCO Exporter (Fixed for Faster R-CNN and EfficientDet)
# ---------------------------

class COCOExporter(Exporter):
    """
    Exports annotations to COCO format for Faster R-CNN and EfficientDet models.
    Both models require proper COCO JSON format with images, annotations, and categories.
    """
    
    def export(self):
        print(f"Exporting to COCO format in: {self.project_name}/")
        
        # Create a 1-based ID map to ensure COCO compliance
        coco_id_map = {}
        category_id_counter = 1
        sorted_labels = sorted(self.class_map.keys())
        categories_list = []
        
        for label in sorted_labels:
            coco_id_map[label] = category_id_counter
            categories_list.append({"id": category_id_counter, "name": label})
            category_id_counter += 1
        
        coco = {
            "images": [],
            "annotations": [],
            "categories": categories_list  # Always include categories for both models
        }
        
        warnings = []
        ann_id = 1
        
        for img_id, item in enumerate(self.annotations_data, start=1):
            image_path = item.get("image_path")
            if not image_path:
                continue
                
            # Copy image to images/ subfolder
            image_filename = os.path.basename(image_path)
            image_dest_path = os.path.join(self.images_dir, image_filename)
            if os.path.exists(image_path):
                try:
                    shutil.copy(image_path, image_dest_path)
                except Exception as e:
                    warnings.append(f"Could not copy image {image_path} to {image_dest_path}: {e}")
            else:
                warnings.append(f"Source image not found: {image_path}")
                
            coco["images"].append({
                "id": img_id,
                "file_name": image_filename,
                "width": item.get("image_width", 0),
                "height": item.get("image_height", 0)
            })
            
            for ann in item.get("annotations", []):
                label = ann.get("label")
                if label not in coco_id_map:
                    continue
                    
                category_id = coco_id_map[label]
                points = ann.get("points", [])
                bbox, segmentation, area = [], [], 0.0
                
                if ann.get("type") == "polygon":
                    if not points or len(points) < 3:
                        continue
                        
                    seg = points
                    if isinstance(seg[0], list):
                        try:
                            seg = [c for point in seg for c in point]
                        except TypeError:
                            warnings.append(f"Malformed polygon points for '{label}' in {image_path}. Skipping.")
                            continue
                    
                    if len(seg) < 6:
                        continue
                        
                    xs = seg[0::2]
                    ys = seg[1::2]
                    x_min, y_min = min(xs), min(ys)
                    x_max, y_max = max(xs), max(ys)
                    
                    width, height = x_max - x_min, y_max - y_min
                    
                    # Skip zero-area bounding boxes
                    if width <= 0 or height <= 0:
                        warnings.append(f"Zero-area polygon for '{label}' in {image_path}. Skipping.")
                        continue
                    
                    bbox = [x_min, y_min, width, height]
                    segmentation = [seg]
                    
                    # Shoelace formula for area
                    poly_area = 0.0
                    for i in range(0, len(seg), 2):
                        x1, y1 = seg[i], seg[i+1]
                        x2, y2 = seg[(i+2) % len(seg)], seg[(i+3) % len(seg)]
                        poly_area += x1 * y2 - x2 * y1
                    area = abs(poly_area) / 2.0
                    
                elif ann.get("type") == "bbox":
                    if len(points) != 4:
                        continue
                        
                    x_min, y_min, x_max, y_max = points
                    width, height = x_max - x_min, y_max - y_min
                    
                    # Skip zero-area bounding boxes
                    if width <= 0 or height <= 0:
                        warnings.append(f"Zero-area bbox for '{label}' in {image_path}. Skipping.")
                        continue
                    
                    bbox = [x_min, y_min, width, height]
                    area = float(width * height)
                    
                    # Create segmentation from bbox coordinates
                    segmentation = [[x_min, y_min, x_max, y_min, x_max, y_max, x_min, y_max]]
                    
                else:
                    continue  # Skip unknown annotation types
                
                coco["annotations"].append({
                    "id": ann_id,
                    "image_id": img_id,
                    "category_id": category_id,
                    "bbox": [round(v, 2) for v in bbox],
                    "segmentation": segmentation,
                    "area": round(area, 2),
                    "iscrowd": 0
                })
                ann_id += 1
        
        # Save annotations.json to labels/ subfolder
        outpath = os.path.join(self.labels_dir, "annotations.json")
        with open(outpath, "w") as f:
            json.dump(coco, f, indent=2)
            
        print(f"Export completed successfully to: {self.project_path}")
        return warnings

# ---------------------------
# YOLO Exporter (Enhanced)
# ---------------------------

class YOLOExporter(Exporter):
    """Exports annotations to YOLO format with a structured project folder."""
    
    def export(self):
        print(f"Exporting to YOLO format in: {self.project_name}/")
        print(f" └── {self.project_name}/")
        print(f"     ├── images/")
        print(f"     └── labels/")
        
        warnings = []
        
        for item in self.annotations_data:
            image_path = item.get("image_path")
            if not image_path:
                warnings.append("Skipping item with missing 'image_path'.")
                continue
                
            if not os.path.exists(image_path):
                warnings.append(f"Source image not found, cannot copy: {image_path}")
                continue
            
            image_filename = os.path.basename(image_path)
            txt_filename = f"{os.path.splitext(image_filename)[0]}.txt"
            
            # Define destination paths within the project structure
            label_dest_path = os.path.join(self.labels_dir, txt_filename)
            image_dest_path = os.path.join(self.images_dir, image_filename)
            
            # Copy the image file to the 'images' subdirectory
            try:
                shutil.copy(image_path, image_dest_path)
            except Exception as e:
                warnings.append(f"Could not copy image {image_path} to {image_dest_path}: {e}")
                continue
            
            image_width = item.get("image_width")
            image_height = item.get("image_height")
            
            if not image_width or not image_height:
                warnings.append(f"Missing dimensions for {image_path}. Skipping label generation.")
                continue
            
            lines = []
            for ann in item.get("annotations", []):
                if ann.get("type") == "polygon":
                    points = ann.get("points", [])
                    if not points:
                        continue
                    
                    if isinstance(points[0], list):
                        points = [c for point in points for c in point]
                    
                    if len(points) < 6:
                        continue
                    
                    xs = points[0::2]; ys = points[1::2]
                    x_min, y_min, x_max, y_max = min(xs), min(ys), max(xs), max(ys)
                    
                elif ann.get("type") == "bbox":
                    points = ann.get("points")
                    if not isinstance(points, list) or len(points) != 4:
                        continue
                    x_min, y_min, x_max, y_max = points
                else:
                    continue
                
                label = ann.get("label")
                if label not in self.class_map:
                    continue
                
                class_id = self.class_map[label]
                
                x_center = ((x_min + x_max) / 2) / image_width
                y_center = ((y_min + y_max) / 2) / image_height
                w = (x_max - x_min) / image_width
                h = (y_max - y_min) / image_height
                
                lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")
            
            with open(label_dest_path, "w") as f:
                f.write("\n".join(lines))
        
        print(f"Export completed successfully to: {self.project_path}")
        return warnings

# ---------------------------
# GroundingDINO and OWL-ViT Exporter
# ---------------------------

class GroundingDINOStrictExporter(Exporter):
    """
    Exports annotations to a strict GroundingDINO format.
    The format is a dictionary with "boxes," "scores," and "labels."
    """
    
    def export(self):
        print(f"Exporting to strict GroundingDINO format in: {self.project_name}/")
        
        boxes = []
        scores = []
        labels = []
        warnings = []
        
        for item in self.annotations_data:
            image_path = item.get("image_path")
            if not image_path:
                warnings.append("Skipping item with missing 'image_path'.")
                continue
            
            # Copy image to images/ subfolder
            image_filename = os.path.basename(image_path)
            image_dest_path = os.path.join(self.images_dir, image_filename)
            if os.path.exists(image_path):
                try:
                    shutil.copy(image_path, image_dest_path)
                except Exception as e:
                    warnings.append(f"Could not copy image {image_path} to {image_dest_path}: {e}")
            else:
                warnings.append(f"Source image not found: {image_path}")
            
            for ann in item.get("annotations", []):
                label = ann.get("label")
                if label not in self.class_map:
                    warnings.append(f"Label '{label}' not in class map. Skipping annotation in {image_path}.")
                    continue
                
                points = ann.get("points", [])
                
                if ann.get("type") == "polygon":
                    if not points or len(points) < 3:
                        warnings.append(f"Skipping malformed polygon with < 3 points in {image_path}.")
                        continue
                    
                    if isinstance(points[0], list):
                        try:
                            points = [c for point in points for c in point]
                        except TypeError:
                            warnings.append(f"Malformed polygon points for '{label}' in {image_path}. Skipping.")
                            continue
                    
                    if len(points) < 6:
                        warnings.append(f"Skipping malformed polygon with < 6 values in {image_path}.")
                        continue
                    
                    xs = points[0::2]
                    ys = points[1::2]
                    x_min, y_min = min(xs), min(ys)
                    x_max, y_max = max(xs), max(ys)
                    
                elif ann.get("type") == "bbox":
                    if not isinstance(points, list) or len(points) != 4:
                        warnings.append(f"Skipping malformed bbox in {image_path}.")
                        continue
                    x_min, y_min, x_max, y_max = points
                else:
                    continue
                
                boxes.append([round(x_min, 2), round(y_min, 2), round(x_max, 2), round(y_max, 2)])
                scores.append(ann.get("score", 1.0))
                labels.append(label)
        
        export_data = {
            "boxes": boxes,
            "scores": scores,
            "labels": labels
        }
        
        # Save annotations.json to labels/ subfolder
        output_path = os.path.join(self.labels_dir, "annotations.json")
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Successfully exported {len(boxes)} annotations")
        print(f"Export completed successfully to: {self.project_path}")
        return warnings

class GroundingDINOExporter(Exporter):
    """
    Exports annotations to a JSON list format compatible with GroundingDINO and OWL-ViT.
    The format is a list of dictionaries, each with "bbox", "score", and "label".
    """
    
    def export(self):
        print(f"Exporting to GroundingDINO/OWL-ViT format in: {self.project_name}/")
        
        export_data = []
        warnings = []
        
        for item in self.annotations_data:
            image_path = item.get("image_path")
            if not image_path:
                warnings.append("Skipping item with missing 'image_path'.")
                continue
            
            # Copy image to images/ subfolder
            image_filename = os.path.basename(image_path)
            image_dest_path = os.path.join(self.images_dir, image_filename)
            if os.path.exists(image_path):
                try:
                    shutil.copy(image_path, image_dest_path)
                except Exception as e:
                    warnings.append(f"Could not copy image {image_path} to {image_dest_path}: {e}")
            else:
                warnings.append(f"Source image not found: {image_path}")
            
            for ann in item.get("annotations", []):
                label = ann.get("label")
                if label not in self.class_map:
                    warnings.append(f"Label '{label}' not in class map. Skipping annotation in {image_path}.")
                    continue
                
                points = ann.get("points", [])
                
                if ann.get("type") == "polygon":
                    if not points or len(points) < 3:
                        warnings.append(f"Skipping malformed polygon with < 3 points in {image_path}.")
                        continue
                    
                    # Flatten points if they are in [[x1, y1], [x2, y2]] format
                    if isinstance(points[0], list):
                        try:
                            points = [c for point in points for c in point]
                        except TypeError:
                            warnings.append(f"Malformed polygon points for '{label}' in {image_path}. Skipping.")
                            continue
                    
                    if len(points) < 6:
                        warnings.append(f"Skipping malformed polygon with < 6 values in {image_path}.")
                        continue
                    
                    xs = points[0::2]
                    ys = points[1::2]
                    x_min, y_min = min(xs), min(ys)
                    x_max, y_max = max(xs), max(ys)
                    
                elif ann.get("type") == "bbox":
                    if not isinstance(points, list) or len(points) != 4:
                        warnings.append(f"Skipping malformed bbox in {image_path}.")
                        continue
                    x_min, y_min, x_max, y_max = points
                else:
                    # Skip unsupported annotation types
                    continue
                
                export_data.append({
                    "bbox": [round(x_min, 2), round(y_min, 2), round(x_max, 2), round(y_max, 2)],
                    "score": ann.get("score", 1.0),  # Use existing score or default to 1.0
                    "label": label
                })
        
        # Save annotations.json to labels/ subfolder
        output_path = os.path.join(self.labels_dir, "annotations.json")
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Successfully exported {len(export_data)} annotations")
        print(f"Export completed successfully to: {self.project_path}")
        return warnings

# ---------------------------
# SSD Exporter
# ---------------------------

class SSDExporter(Exporter):
    """
    Exports annotations to a simplified JSON format suitable for SSD models.
    The format is a list of dictionaries, each with "image" and "annotations".
    """
    
    def export(self):
        print(f"Exporting to SSD JSON format in: {self.project_name}/")
        
        export_data = []
        warnings = []
        
        for item in self.annotations_data:
            image_path = item.get("image_path")
            if not image_path:
                warnings.append("Skipping item with missing 'image_path'.")
                continue
            
            # Copy image to images/ subfolder
            image_filename = os.path.basename(image_path)
            image_dest_path = os.path.join(self.images_dir, image_filename)
            if os.path.exists(image_path):
                try:
                    shutil.copy(image_path, image_dest_path)
                except Exception as e:
                    warnings.append(f"Could not copy image {image_path} to {image_dest_path}: {e}")
            else:
                warnings.append(f"Source image not found: {image_path}")
                
            image_annotations = []
            
            for ann in item.get("annotations", []):
                label = ann.get("label")
                if not label:
                    warnings.append(f"Skipping annotation with missing 'label' in {image_path}.")
                    continue
                
                points = ann.get("points", [])
                
                if ann.get("type") == "polygon":
                    if not points or len(points) < 3:
                        warnings.append(f"Skipping malformed polygon with < 3 points in {image_path}.")
                        continue
                    
                    if isinstance(points[0], list):
                        try:
                            points = [c for point in points for c in point]
                        except TypeError:
                            warnings.append(f"Malformed polygon points for '{label}' in {image_path}. Skipping.")
                            continue
                    
                    if len(points) < 6:
                        warnings.append(f"Skipping malformed polygon with < 6 values in {image_path}.")
                        continue
                    
                    xs = points[0::2]
                    ys = points[1::2]
                    x_min, y_min = min(xs), min(ys)
                    x_max, y_max = max(xs), max(ys)
                    
                elif ann.get("type") == "bbox":
                    if not isinstance(points, list) or len(points) != 4:
                        warnings.append(f"Skipping malformed bbox in {image_path}.")
                        continue
                    x_min, y_min, x_max, y_max = points
                else:
                    continue
                
                image_annotations.append({
                    "category": label,
                    "bbox": [round(x_min, 2), round(y_min, 2), round(x_max, 2), round(y_max, 2)]
                })
            
            export_data.append({
                "image": image_filename,
                "annotations": image_annotations
            })
        
        # Save annotations.json to labels/ subfolder
        output_path = os.path.join(self.labels_dir, "annotations.json")
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Successfully exported {len(export_data)} images")
        print(f"Export completed successfully to: {self.project_path}")
        return warnings

# ---------------------------
# Pascal VOC Exporter
# ---------------------------

class PascalVOCExporter(Exporter):
    """Exports annotations to Pascal VOC XML format."""
    
    def export(self):
        print(f"Exporting to Pascal VOC format in: {self.project_name}/")
        
        warnings = []
        
        for item in self.annotations_data:
            image_path = item.get("image_path")
            if not image_path:
                continue
            
            # Copy image to images/ subfolder
            image_filename = os.path.basename(image_path)
            image_dest_path = os.path.join(self.images_dir, image_filename)
            if os.path.exists(image_path):
                try:
                    shutil.copy(image_path, image_dest_path)
                except Exception as e:
                    warnings.append(f"Could not copy image {image_path} to {image_dest_path}: {e}")
            else:
                warnings.append(f"Source image not found: {image_path}")
            
            xml_filename = f"{os.path.splitext(image_filename)[0]}.xml"
            xml_filepath = os.path.join(self.labels_dir, xml_filename)
            
            root = ET.Element("annotation")
            ET.SubElement(root, "filename").text = image_filename
            
            size = ET.SubElement(root, "size")
            ET.SubElement(size, "width").text = str(item.get("image_width", 0))
            ET.SubElement(size, "height").text = str(item.get("image_height", 0))
            ET.SubElement(size, "depth").text = "3"
            
            for ann in item.get("annotations", []):
                if ann.get("type") != "bbox":
                    continue
                
                label = ann.get("label")
                if label not in self.class_map:
                    continue
                
                points = ann.get("points")
                if not isinstance(points, list) or len(points) != 4:
                    continue
                
                x_min, y_min, x_max, y_max = points
                
                obj = ET.SubElement(root, "object")
                ET.SubElement(obj, "name").text = label
                
                bndbox = ET.SubElement(obj, "bndbox")
                ET.SubElement(bndbox, "xmin").text = str(int(x_min))
                ET.SubElement(bndbox, "ymin").text = str(int(y_min))
                ET.SubElement(bndbox, "xmax").text = str(int(x_max))
                ET.SubElement(bndbox, "ymax").text = str(int(y_max))
            
            tree = ET.ElementTree(root)
            tree.write(xml_filepath, encoding='utf-8', xml_declaration=True)
        
        print(f"Export completed successfully to: {self.project_path}")
        return warnings

# ---------------------------
# DeepSORT Exporter
# ---------------------------

class DeepSORTExporter(Exporter):
    """Exports annotations to DeepSORT (MOT) format."""
    
    def export(self):
        print(f"Exporting to DeepSORT (MOT) format in: {self.project_name}/")
        
        lines = []
        warnings = []
        
        for frame_id, item in enumerate(self.annotations_data, start=1):
            image_path = item.get("image_path")
            if image_path:
                # Copy image to images/ subfolder
                image_filename = os.path.basename(image_path)
                image_dest_path = os.path.join(self.images_dir, image_filename)
                if os.path.exists(image_path):
                    try:
                        shutil.copy(image_path, image_dest_path)
                    except Exception as e:
                        warnings.append(f"Could not copy image {image_path} to {image_dest_path}: {e}")
                else:
                    warnings.append(f"Source image not found: {image_path}")
            
            for ann in item.get("annotations", []):
                if ann.get("type") != "bbox":
                    continue
                
                track_id = ann.get("track_id", -1)
                points = ann.get("points")
                if not isinstance(points, list) or len(points) != 4:
                    continue
                
                x_min, y_min, x_max, y_max = points
                w, h = x_max - x_min, y_max - y_min
                lines.append(f"{frame_id},{track_id},{x_min},{y_min},{w},{h},1,-1,-1,-1")
        
        # Save gt.txt to labels/ subfolder
        outpath = os.path.join(self.labels_dir, "gt.txt")
        with open(outpath, "w") as f:
            f.write("\n".join(lines))
        
        print(f"Export completed successfully to: {self.project_path}")
        return warnings

class PlaceholderExporter(Exporter):
    """A placeholder for models that do not have a dedicated exporter yet."""

    def export(self):
        print(f"Exporting for model: {self.model_name}")
        print("Warning: This model does not have a specific export format yet.")
        print("Annotations will be saved in a generic COCO format as a fallback.")

        # Fallback to COCOExporter logic
        coco_exporter = COCOExporter(self.annotations_data, self.output_dir, self.class_map, self.project_name, self.model_name)
        return coco_exporter.export()

# ---------------------------
# Dispatcher
# ---------------------------

EXPORTER_MAPPING = {
    # Implemented Exporters
    "YOLOv8": YOLOExporter,
    "SSD": SSDExporter,
    "GroundingDINO": GroundingDINOStrictExporter,
    "GroundingDINO / OWL-ViT": GroundingDINOExporter,
    "DeepSORT": DeepSORTExporter,

    # Models that can use COCO as a default
    "RetinaNet": COCOExporter,
    "Faster R-CNN": COCOExporter,
    "EfficientDet": COCOExporter,
    "Mask R-CNN": COCOExporter,
    "Segment Anything (SAM)": COCOExporter,
    "Detectron2": COCOExporter,
    "MMDetection": COCOExporter,
    "OpenPose": COCOExporter,
    "HRNet": COCOExporter,
    "MediaPipe Pose": COCOExporter,

    # Models without a clear format, using a placeholder for now
    "DeepLabv3+": PlaceholderExporter,
    "U-Net": PlaceholderExporter,
    "SegFormer": PlaceholderExporter,
    "PoseTrack": PlaceholderExporter,
    "ByteTrack": PlaceholderExporter,
    "BoT-SORT": PlaceholderExporter,
    "FairMOT": PlaceholderExporter,
    "CenterTrack": PlaceholderExporter,
    "TraDeS / QDTrack": PlaceholderExporter,
}

def export_annotations(annotations, output_dir, model_name, class_map, project_name=None):
    """Dispatches annotation export task to the correct exporter class."""
    if model_name not in EXPORTER_MAPPING:
        raise ValueError(f"Exporter for {model_name} not implemented.")
    
    exporter_cls = EXPORTER_MAPPING[model_name]
    # Pass the project_name and model_name to the exporter's constructor
    exporter = exporter_cls(annotations, output_dir, class_map, project_name, model_name=model_name)
    warnings = exporter.export()
    
    if warnings:
        print("\nExport completed with warnings:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("\nExport completed successfully.")
    
    return warnings

# ---------------------------
# Example Usage
# ---------------------------

def export_to_mask(project_annotations, output_dir, class_map):
    """
    Converts all polygon annotations in a project into PNG mask files.
    
    Args:
        project_annotations (dict): A dictionary where keys are image filenames 
                                  and values are the neutral JSON annotation data.
        output_dir (str): The folder where the PNG masks will be saved.
        class_map (dict): A mapping from class names to integer IDs (e.g., {"fish": 1, "boat": 2}).
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"Starting mask export to {output_dir}...")
    
    for image_filename, data in project_annotations.items():
        # Create a blank, black canvas (NumPy array)
        mask_array = np.zeros((data["height"], data["width"]), dtype=np.uint8)
        
        # Convert to a Pillow Image to use its powerful drawing tools
        mask_image = Image.fromarray(mask_array)
        draw = ImageDraw.Draw(mask_image)
        
        for ann in data["annotations"]:
            if ann.get("type") == "polygon":
                label = ann["label"]
                class_id = class_map.get(label, 0)  # Default to 0 (background) if label is missing
                
                # Pillow's polygon tool needs a flat list of coordinates: [x1, y1, x2, y2, ...]
                polygon_points = [tuple(p) for p in ann["points"]]
                if len(polygon_points) > 2:
                    # "Paint" the polygon onto the canvas using its integer class ID
                    draw.polygon(polygon_points, outline=class_id, fill=class_id)
        
        # Save the final mask image as a lossless PNG
        mask_filename = os.path.splitext(image_filename)[0] + "_mask.png"
        mask_path = os.path.join(output_dir, mask_filename)
        mask_image.save(mask_path)
    
    print("Mask export complete.")

if __name__ == '__main__':
    # Test setup
    os.makedirs("./tmp_images", exist_ok=True)
    with open("./tmp_images/image1.jpg", "w") as f:
        f.write("dummy")
    with open("./tmp_images/image2.jpg", "w") as f:
        f.write("dummy")
    
    mock_annotations_data = [
        {"image_path": "./tmp_images/image1.jpg", "image_width": 1920, "image_height": 1080,
         "annotations": [{"label": "car", "type": "polygon", "points": [100,200,150,200,150,250,100,250]},
                        {"label": "person", "type": "bbox", "points": [300,400,350,500]}]},
        {"image_path": "./tmp_images/image2.jpg", "image_width": 1280, "image_height": 720,
         "annotations": [{"label": "person", "type": "polygon", "points": [50,50,100,55,110,100,40,90]}]}
    ]
    
    universal_class_map = {"person": 0, "car": 1}
    output_directory = "./exported_annotations"
    
    print("--- Testing Export for Faster R-CNN (COCO Format) ---")
    export_annotations(
        annotations=mock_annotations_data,
        output_dir=output_directory,
        model_name="Faster R-CNN",
        class_map=universal_class_map,
        project_name="FasterRCNN_Dataset"
    )
    
    print("\n--- Testing Export for EfficientDet (COCO Format) ---")
    export_annotations(
        annotations=mock_annotations_data,
        output_dir=output_directory,
        model_name="EfficientDet",
        class_map=universal_class_map,
        project_name="EfficientDet_Dataset"
    )
    
    print("\n--- Testing Export for YOLOv8 with Custom Project Name ---")
    export_annotations(
        annotations=mock_annotations_data,
        output_dir=output_directory,
        model_name="YOLOv8",
        class_map=universal_class_map,
        project_name="YOLOv8_CustomProject"
    )
    
    print("\n--- Testing Export for YOLOv8 without Project Name ---")
    export_annotations(
        annotations=mock_annotations_data,
        output_dir=output_directory,
        model_name="YOLOv8",
        class_map=universal_class_map
        # No project_name provided - will use default "dataset_export"
    )
    
    print("\n--- Testing Export for GroundingDINO / OWL-ViT ---")
    export_annotations(
        annotations=mock_annotations_data,
        output_dir=output_directory,
        model_name="GroundingDINO / OWL-ViT",
        class_map=universal_class_map,
        project_name="GroundingDINO_Dataset"
    )
    
    print("\n--- Testing Export for SSD ---")
    export_annotations(
        annotations=mock_annotations_data,
        output_dir=output_directory,
        model_name="SSD",
        class_map=universal_class_map,
        project_name="SSD_Dataset"
    )
    
    print("\n--- Testing Export for Pascal VOC ---")
    export_annotations(
        annotations=mock_annotations_data,
        output_dir=output_directory,
        model_name="Pascal VOC",
        class_map=universal_class_map,
        project_name="PascalVOC_Dataset"
    )
    
    # Clean up test files
    shutil.rmtree("./tmp_images")