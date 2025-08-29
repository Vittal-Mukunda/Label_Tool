# C:\LabelAI\backend\model_manager.py
import importlib.util
import subprocess
import sys

class ModelManager:
    def __init__(self):
        self.models = {}
        self.active_model = None

    def register_model(self, name, model_class):
        self.models[name] = model_class

    def set_active_model(self, name):
        if name in self.models:
            # Instantiate the class when it's set as active
            self.active_model = self.models[name]()
            print(f"Active model set to {name}")
        else:
            raise ValueError(f"Model {name} not found!")

    def is_library_installed(self, library_name):
        """Checks if a given library is installed."""
        if library_name is None:
            return True # No specific library required
        spec = importlib.util.find_spec(library_name)
        return spec is not None

    def install_library(self, library_name):
        """Installs a given library using pip."""
        if library_name is None:
            return True # Should not happen if called after a check
        try:
            print(f"Attempting to install {library_name}...")
            # Use sys.executable to ensure pip from the correct environment is used
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", library_name],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"Successfully installed {library_name}.")
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {library_name}.")
            print(f"Pip Error: {e.stderr}")
            return False

    def run(self, *args, **kwargs):
        if self.active_model is None:
            raise RuntimeError("No model selected!")
        # Pass all arguments to the adapter's infer method
        return self.active_model.infer(*args, **kwargs)