class SegFormerAdapter:
    """Dummy adapter for the SegFormer model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'SegFormer' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
