class DeepSORTAdapter:
    """Dummy adapter for the DeepSORT model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'DeepSORT' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
