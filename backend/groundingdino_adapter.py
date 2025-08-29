class GroundingDINOAdapter:
    """Dummy adapter for the GroundingDINO model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'GroundingDINO' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
