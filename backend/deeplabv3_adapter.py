class DeepLabv3Adapter:
    """Dummy adapter for the DeepLabv3 model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'DeepLabv3' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
