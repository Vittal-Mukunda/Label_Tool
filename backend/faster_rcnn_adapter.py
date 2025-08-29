class FasterRCNNAdapter:
    """Dummy adapter for the Faster R-CNN model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'Faster R-CNN' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
