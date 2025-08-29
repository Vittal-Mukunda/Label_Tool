class Detectron2Adapter:
    """Dummy adapter for the Detectron2 model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'Detectron2' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
