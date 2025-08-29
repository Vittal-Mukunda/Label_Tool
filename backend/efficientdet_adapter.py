class EfficientDetAdapter:
    """Dummy adapter for the EfficientDet model."""
    def infer(self, *args, **kwargs):
        print(f"Warning: The 'EfficientDet' model is not fully implemented. This is a placeholder.")
        # Return an empty list to signify no annotations were produced
        return []
