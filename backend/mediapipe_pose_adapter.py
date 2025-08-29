class MediaPipePoseAdapter:
    """Dummy adapter for the MediaPipePose model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'MediaPipePose' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
