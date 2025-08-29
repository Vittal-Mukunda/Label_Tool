class SSDAdapter:
    """Dummy adapter for the SSD model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'SSD' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
