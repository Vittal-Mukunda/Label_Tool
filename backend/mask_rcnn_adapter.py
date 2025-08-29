class MaskRCNNAdapter:
    """Dummy adapter for the MaskRCNN model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'MaskRCNN' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
