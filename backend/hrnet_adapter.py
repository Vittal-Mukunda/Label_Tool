class HRNetAdapter:
    """Dummy adapter for the HRNet model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'HRNet' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
