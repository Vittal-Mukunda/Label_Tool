class FairMOTAdapter:
    """Dummy adapter for the FairMOT model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'FairMOT' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
