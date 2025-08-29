# C:\LabelAI\backend\sam_adapter.py

import os
import cv2
import numpy as np
import torch
from segment_anything import sam_model_registry, SamPredictor

def mask_to_polygon(mask):
    """Converts a binary mask to a polygon."""
    # Find contours
    # NOTE: cv2.findContours modifies the source image, so we use a copy
    mask_copy = mask.astype(np.uint8)
    contours, _ = cv2.findContours(mask_copy, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None

    # Find the largest contour by area
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Simplify the contour to reduce the number of points
    epsilon = 0.005 * cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)
    
    # The result from approxPolyDP is a 3D array, so we squeeze it to 2D
    return approx.squeeze().tolist()

class SAMAdapter:
    """Adapter for the Segment Anything Model (SAM)"""
    def __init__(self, model_type="default", device=None):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # This is a common checkpoint name for SAM. The user must provide this file.
        model_checkpoint = "sam_vit_h_4b8939.pth"
        model_path = os.path.join("models", model_checkpoint)
        
        self.device = device
        self.predictor = None

        if not os.path.exists(model_path):
            print(f"--- WARNING ---")
            print(f"SAM model checkpoint not found at: {model_path}")
            print(f"Please download the 'vit_h' model from the official SAM repository and place it in the 'models' directory.")
            print(f"SAM functionality will be disabled.")
            print(f"-----------------")
            return

        try:
            print("Loading SAM model... This may take a moment.")
            sam = sam_model_registry[model_type](checkpoint=model_path)
            sam.to(device=self.device)
            self.predictor = SamPredictor(sam)
            print("SAM model loaded successfully.")
        except Exception as e:
            print(f"Error loading SAM model: {e}")

    def infer(self, image_path, prompt_point):
        """
        Runs SAM inference on an image with a point prompt.

        Args:
            image_path (str): Path to the image file.
            prompt_point (tuple): A tuple (x, y) of the user's click coordinate.

        Returns:
            list: A list containing a dictionary with the polygon annotation, or an empty list if fails.
        """
        if not self.predictor:
            print("Error: SAM model is not loaded. Cannot run inference.")
            return []

        try:
            image = cv2.imread(image_path)
            if image is None:
                print(f"Error: Could not read image at {image_path}")
                return []
            
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Set the image for the predictor. This is a computationally expensive step.
            self.predictor.set_image(image)
            
            input_point = np.array([prompt_point])
            input_label = np.array([1])  # 1 indicates a foreground point

            masks, scores, logits = self.predictor.predict(
                point_coords=input_point,
                point_labels=input_label,
                multimask_output=False,  # We want the single best mask
            )
            
            # The output is a batch, so we take the first mask
            mask = masks[0]
            
            # Convert the boolean mask to a polygon
            polygon_coords = mask_to_polygon(mask)

            if not polygon_coords or len(polygon_coords) < 3:
                return []

            # Normalize coordinates to be relative (0.0 to 1.0)
            h, w, _ = image.shape
            normalized_coords = [[float(x) / w, float(y) / h] for x, y in polygon_coords]

            # Format the output to match the application's annotation structure
            annotation = {
                "type": "polygon",
                "label": "SAM-Object",
                "coords": normalized_coords,
            }

            return [annotation]
        except Exception as e:
            print(f"An error occurred during SAM inference: {e}")
            return []
