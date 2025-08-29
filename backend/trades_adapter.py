class TraDeSAdapter:
    """Dummy adapter for the TraDeS model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'TraDeS' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
