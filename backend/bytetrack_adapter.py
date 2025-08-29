class ByteTrackAdapter:
    """Dummy adapter for the ByteTrack model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'ByteTrack' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
