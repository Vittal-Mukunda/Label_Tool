class RetinaNetAdapter:
    """Dummy adapter for the RetinaNet model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'RetinaNet' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
