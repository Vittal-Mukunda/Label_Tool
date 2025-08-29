class PoseTrackAdapter:
    """Dummy adapter for the PoseTrack model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'PoseTrack' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
