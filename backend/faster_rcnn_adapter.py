class FasterRCNNAdapter:
    """Dummy adapter for the FasterRCNN model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'FasterRCNN' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
