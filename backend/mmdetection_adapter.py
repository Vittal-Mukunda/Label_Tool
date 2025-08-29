class MMDetectionAdapter:
    """Dummy adapter for the MMDetection model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'MMDetection' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
