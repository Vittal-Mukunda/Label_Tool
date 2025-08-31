# C:\LabelAI\backend\model_manager.py
import importlib.util
import subprocess
import sys
import importlib.util
import subprocess
import sys
import os
import shutil

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
            return True
            return True
        else:
            # Return False if the model is not registered, instead of crashing
            return False

    def is_library_installed(self, library_name):
        """Checks if a given library is installed."""
        if library_name is None:
            return True # No specific library required
        spec = importlib.util.find_spec(library_name)
        return spec is not None

    def _run_command(self, command, cwd=None):
        """
        Helper to run a command and return success and output.
        Returns: (bool, str) where bool is success and str is a message.
        """
        try:
            print(f"Running command: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                cwd=cwd,
                encoding='utf-8'
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            error_message = f"Command failed: {' '.join(command)}\n\n" \
                            f"Stderr:\n{e.stderr}\n\n" \
                            f"Stdout:\n{e.stdout}"
            print(error_message)
            return False, error_message
        except FileNotFoundError:
            error_message = f"Command not found: '{command[0]}'. Please ensure it is installed and in your system's PATH."
            print(error_message)
            return False, error_message

    def install_library(self, library_name):
        """
        Installs a given library using pip.
        Returns: (bool, str) where bool is success and str is a message.
        """
        if library_name is None:
            return True, "No library required."

        print(f"Attempting to install {library_name}...")

        if library_name == "detectron2":
            return self._install_detectron2()
        else:
            # Return False if the model is not registered, instead of crashing
            return False

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
            success, message = self._run_command([sys.executable, "-m", "pip", "install", library_name])
            if success:
                return True, f"Successfully installed {library_name}."
            else:
                return False, f"Failed to install '{library_name}'.\n\n" + message

    def _install_detectron2(self):
        """
        Handles the special installation process for Detectron2.
        Returns: (bool, str) where bool is success and str is a message.
        """
        
        # 1. Install dependencies
        print("--- Step 1: Installing detectron2 dependencies ---")
        success, msg = self._run_command([sys.executable, "-m", "pip", "install", "cython", "pycocotools-windows"])
        if not success:
            return False, "Failed to install dependencies for Detectron2.\n\n" + msg

        # 2. Clone detectron2
        print("\n--- Step 2: Cloning detectron2 repository ---")
        detectron2_path = os.path.join(os.path.expanduser("~"), "detectron2_repo")
        if os.path.exists(detectron2_path):
            print(f"Removing existing detectron2 repository at {detectron2_path}")
            shutil.rmtree(detectron2_path)
        
        success, msg = self._run_command(["git", "clone", "https://github.com/facebookresearch/detectron2.git", detectron2_path])
        if not success:
            return False, "Failed to clone the Detectron2 repository. Please ensure Git is installed.\n\n" + msg

        # 3. Install detectron2 from source
        print("\n--- Step 3: Installing detectron2 from source ---")
        success, msg = self._run_command([sys.executable, "-m", "pip", "install", "-e", "."], cwd=detectron2_path)
        if not success:
            error_msg = "Failed to build and install Detectron2 from source. " \
                        "This often happens due to a mismatch in PyTorch, CUDA, or C++ compiler versions. " \
                        "Please check the console output for specific errors.\n\n" + msg
            return False, error_msg
        
        return True, "Successfully installed detectron2."

    def run(self, *args, **kwargs):
        if self.active_model is None:
            raise RuntimeError("No model selected!")
        # Pass all arguments to the adapter's infer method
        return self.active_model.infer(*args, **kwargs)

# --- MODIFICATION START ---
# The dummy adapters have been removed from this file.
# They now live in their own respective files.
# --- MODIFICATION END ---