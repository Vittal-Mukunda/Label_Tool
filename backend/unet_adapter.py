class UNetAdapter:
    """Dummy adapter for the UNet model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'UNet' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
