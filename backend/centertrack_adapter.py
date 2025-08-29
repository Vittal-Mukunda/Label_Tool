class CenterTrackAdapter:
    """Dummy adapter for the CenterTrack model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'CenterTrack' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
