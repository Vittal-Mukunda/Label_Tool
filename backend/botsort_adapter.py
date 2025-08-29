class BoTSORTAdapter:
    """Dummy adapter for the BoTSORT model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'BoTSORT' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
