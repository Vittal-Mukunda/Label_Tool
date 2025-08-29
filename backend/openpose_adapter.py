class OpenPoseAdapter:
    """Dummy adapter for the OpenPose model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'OpenPose' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
