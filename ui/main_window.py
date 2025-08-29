import os
import json
import shutil
from PyQt5.QtWidgets import (QMainWindow, QAction, QFileDialog, QTabWidget, 
                             QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSplitter, QStackedWidget, QMessageBox, QActionGroup, QStyle, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from .image_viewer import ImageViewer
from .annotation_panel import AnnotationPanel
from .welcome_screen import WelcomeScreen
from .image_sidebar import ImageSidebar
from backend.model_manager import ModelManager
from backend.project_manager import ProjectManager
from backend.model_database import get_models_for_task
from backend.yolo_inference import YOLOAdapter
from backend.sam_inference import SAMAdapter
from backend import exporter
from backend.model_database import get_model_info

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.project_manager = ProjectManager(base_projects_dir="LabelAI_Projects")
        self.model_manager = ModelManager()
        # Register the model adapter classes with the model manager
        self.model_manager.register_model("YOLOAdapter", YOLOAdapter)
        self.model_manager.register_model("SAMAdapter", SAMAdapter)
        
        self.current_active_label = None
        self.current_model_info = None
        
        self.setWindowTitle("LabelAI")
        self.resize(1400, 900) # Increased default size for the new layout

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        self.welcome_screen = WelcomeScreen(self.project_manager)
        self.welcome_screen.projectSelected.connect(self.load_project_ui)
        
        self.main_widget = QWidget()
        self.setup_main_ui(self.main_widget)
        
        self.stack.addWidget(self.welcome_screen)
        self.stack.addWidget(self.main_widget)
        
        self.stack.setCurrentWidget(self.welcome_screen)
        self.menuBar().setVisible(False)

    def setup_main_ui(self, parent_widget):
        # --- NEW LAYOUT WITH EXPORT BUTTON ---
        # Main vertical layout
        main_layout = QVBoxLayout(parent_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top part with the splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter, 1) # Give splitter stretch factor

        # 1. Left Sidebar for Image Previews
        self.image_sidebar = ImageSidebar()
        self.image_sidebar.addImagesClicked.connect(self.add_images_to_project)
        self.image_sidebar.imageSelected.connect(self.open_image_tab)
        self.image_sidebar.imagesDeleted.connect(self.delete_images)

        # 2. Nested splitter for the main work area
        work_area_splitter = QSplitter(Qt.Horizontal)
        
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.annotation_panel = AnnotationPanel()
        self.annotation_panel.activeLabelChanged.connect(self.on_active_label_changed)
        self.annotation_panel.classLabelsChanged.connect(self.save_project_state)
        self.annotation_panel.annotationsUpdated.connect(self.on_annotations_updated_from_panel)
        
        work_area_splitter.addWidget(self.tabs)
        work_area_splitter.addWidget(self.annotation_panel)
        work_area_splitter.setSizes([900, 300])

        main_splitter.addWidget(self.image_sidebar)
        main_splitter.addWidget(work_area_splitter)
        main_splitter.setSizes([200, 1200])

        # Bottom part with the export button
        export_layout = QHBoxLayout()
        export_layout.addStretch() # Pushes the button to the right
        
        self.export_button = QPushButton("Export")
        self.export_button.setDisabled(True)
        self.export_button.setStyleSheet("background-color: #A0A0A0; color: #FFFFFF; padding: 8px 16px; border-radius: 4px;")
        self.export_button.clicked.connect(self.handle_export)
        
        export_layout.addWidget(self.export_button)
        main_layout.addLayout(export_layout)
        # --- END OF NEW LAYOUT ---
        
        menubar = self.menuBar()
        self.file_menu = menubar.addMenu("File")
        style = self.style()
        # Renamed action for clarity
        add_images_action = QAction(style.standardIcon(QStyle.SP_DialogOpenButton), "Add Images to Project...", self)
        add_images_action.triggered.connect(self.add_images_to_project)
        self.file_menu.addAction(add_images_action)
        
        save_action = QAction(style.standardIcon(QStyle.SP_DialogSaveButton), "Save All Annotations", self)
        save_action.triggered.connect(self.save_all_annotations)
        self.file_menu.addAction(save_action)

        self.file_menu.addSeparator()

        back_to_projects_action = QAction(style.standardIcon(QStyle.SP_ArrowBack), "Back to Projects", self)
        back_to_projects_action.triggered.connect(self.prompt_save_and_return_to_welcome)
        self.file_menu.addAction(back_to_projects_action)
        
        self.models_menu = menubar.addMenu("Models")
        self.models_menu.setDisabled(True)
        self.tools_menu = menubar.addMenu("Tools")
        self.tools_menu.setDisabled(True)

    def load_project_ui(self, project_name, model_name=None):
        # Reset UI from any previous project
        self.reset_project_ui()

        # Open the project directory and load its configuration
        if not self.project_manager.open_project(project_name):
            QMessageBox.critical(self, "Error", f"Failed to open project '{project_name}'.")
            return

        self.setWindowTitle(f"LabelAI - {project_name}")
        
        # Load project state, which includes the annotation goal
        state = self.project_manager.load_state()
        if not state or "annotation_goal" not in state:
            QMessageBox.critical(self, "Error", "Project is corrupted or missing its annotation goal.")
            self.stack.setCurrentWidget(self.welcome_screen)
            return

        # Switch to the main UI
        self.stack.setCurrentWidget(self.main_widget)
        self.menuBar().setVisible(True)

        # --- DYNAMIC UI SETUP BASED ON GOAL ---
        annotation_goal = state.get("annotation_goal")
        if not annotation_goal:
            QMessageBox.critical(self, "Error", "Project is missing its annotation goal definition.")
            self.stack.setCurrentWidget(self.welcome_screen)
            return

        # If model_name wasn't passed (e.g., when opening an existing project), get it from state
        if not model_name:
            model_name = state.get("model")

        self.update_menus_for_goal(annotation_goal, model_name)
        
        # Populate the sidebar with existing images
        self.image_sidebar.populate_from_directory(self.project_manager.get_image_dir())
        
        # Load class labels and other state
        class_labels = state.get("class_labels", [])
        self.annotation_panel.load_class_labels(class_labels)
        self.load_project_state(state)

    def update_menus_for_goal(self, annotation_goal, active_model_name=None):
        """
        Dynamically populates the Models menu and activates the specified model.
        """
        self.models_menu.clear()
        self.tools_menu.clear()
        self.models_menu.setDisabled(False)
        self.tools_menu.setDisabled(False)

        models = get_models_for_task(annotation_goal)
        if not models:
            self.models_menu.addAction(QAction("No models available for this goal", self, enabled=False))
            self.tools_menu.setDisabled(True)
            return

        model_group = QActionGroup(self)
        for model_info in models:
            model_action = QAction(model_info['name'], self, checkable=True)
            model_action.triggered.connect(lambda checked, m=model_info: self.activate_model(m))
            self.models_menu.addAction(model_action)
            model_group.addAction(model_action)

        # Find and activate the correct model
        active_model_action = None
        active_model_info = None

        if active_model_name:
            for i, model_info in enumerate(models):
                if model_info['name'] == active_model_name:
                    active_model_action = self.models_menu.actions()[i]
                    active_model_info = model_info
                    break
        
        # Fallback to the first model if the desired one isn't found or specified
        if not active_model_action and models:
            active_model_action = self.models_menu.actions()[0]
            active_model_info = models[0]
            # If we fell back, update the project state to include the model
            if self.project_manager.is_project_active():
                self.project_manager.save_state({"model": active_model_info['name']})

        # Activate the determined model
        if active_model_action:
            active_model_action.setChecked(True)
            self.activate_model(active_model_info)

    def activate_model(self, model_info):
        """
        Activates the selected model, updates the UI, and populates the Tools menu.
        """
        self.current_model_info = model_info
        # --- FIX ---
        # Set the active model in the model manager
        if model_info and 'adapter' in model_info:
            self.model_manager.set_active_model(model_info['adapter'])
        # --- END FIX ---
        print(f"Selected model: {self.current_model_info['name']}")

        # Update export button
        self.export_button.setText(f"Export for {self.current_model_info['name']}")
        self.export_button.setStyleSheet("background-color: #D32F2F; color: #FFFFFF; padding: 8px 16px; border-radius: 4px;")
        
        # Check if the button should be enabled
        active_viewer = self.tabs.currentWidget()
        if isinstance(active_viewer, ImageViewer) and active_viewer.annotations:
            self.export_button.setDisabled(False)
        else:
            self.export_button.setDisabled(True)

        # --- NEW: Populate Tools Menu ---
        self.tools_menu.clear()
        self.tools_menu.setDisabled(False)
        
        model_info = get_model_info(model_info['name'])
        if not model_info:
            no_tools_action = QAction("No tools for this model", self)
            no_tools_action.setDisabled(True)
            self.tools_menu.addAction(no_tools_action)
            return

        tool_group = QActionGroup(self)
        
        tool_name = model_info.get("tool")
        if tool_name:
            tool_action = QAction(tool_name, self, checkable=True)
            tool_action.triggered.connect(lambda checked, t=tool_name: self.set_active_tool(t))
            self.tools_menu.addAction(tool_action)
            tool_group.addAction(tool_action)
            
            # Automatically select the first tool in the list
            first_tool_action = self.tools_menu.actions()[0]
            first_tool_action.setChecked(True)
            self.set_active_tool(tool_name)

    def set_active_tool(self, tool_name):
        """Sets the active drawing tool in the current image viewer."""
        active_viewer = self.tabs.currentWidget()
        if isinstance(active_viewer, ImageViewer):
            active_viewer.set_tool(tool_name)
            self.statusBar().showMessage(f"Activated tool: {tool_name}", 3000)
        else:
            self.statusBar().showMessage("Please open an image to use a tool.", 3000)

    def add_images_to_project(self):
        """Opens a dialog to select multiple images and copies them to the project."""
        if not self.project_manager.is_project_active(): return
        
        image_dir = self.project_manager.get_image_dir()
        file_filter = "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        
        # Use getOpenFileNames for multi-selection
        paths, _ = QFileDialog.getOpenFileNames(self, "Add Images", os.path.expanduser("~"), file_filter, options=QFileDialog.DontUseNativeDialog)
        
        if paths:
            copied_count = 0
            for path in paths:
                try:
                    shutil.copy(path, image_dir)
                    copied_count += 1
                except shutil.SameFileError:
                    pass # File is already in the project
                except Exception as e:
                    print(f"Could not copy file {path}: {e}")
            
            if copied_count > 0:
                self.image_sidebar.populate_from_directory(image_dir)
            
            QMessageBox.information(self, "Success", f"Added {copied_count} new image(s) to the project.")

    def delete_images(self, image_paths):
        """Deletes image files and their corresponding annotation files."""
        if not self.project_manager.is_project_active(): return

        deleted_count = 0
        for path in image_paths:
            # Close the tab if the image is open
            for i in range(self.tabs.count()):
                if self.tabs.widget(i).property("image_path") == path:
                    self.tabs.removeTab(i)
                    break
            
            # Delete the image file
            try:
                os.remove(path)
                deleted_count += 1
            except OSError as e:
                print(f"Error deleting image file {path}: {e}")
                continue

            # Delete the corresponding annotation file
            filename = os.path.basename(path)
            self.project_manager.delete_annotations(filename)

        if deleted_count > 0:
            QMessageBox.information(self, "Success", f"Deleted {deleted_count} image(s).")
            # Refresh the sidebar to show the updated list of images
            self.image_sidebar.populate_from_directory(self.project_manager.get_image_dir())

    def open_image_tab(self, path):
        """Opens an image from a given path (called by the sidebar)."""
        if path and os.path.exists(path):
            # Check if this image is already open in a tab
            for i in range(self.tabs.count()):
                if self.tabs.widget(i).property("image_path") == path:
                    self.tabs.setCurrentIndex(i)
                    return

            viewer = ImageViewer()
            viewer.load_image(path)
            viewer.setProperty("image_path", path)
            viewer.annotationsChanged.connect(lambda v=viewer: self.on_annotations_changed_in_viewer(v))
            viewer.promptMade.connect(self.handle_sam_prompt)
            
            self.load_annotations_for_viewer(viewer, path)
            filename = os.path.basename(path)
            self.tabs.addTab(viewer, filename)
            self.tabs.setCurrentWidget(viewer)
            self.on_annotations_changed_in_viewer(viewer)

    def save_all_annotations(self):
        """Saves annotations for all currently open tabs."""
        if not self.project_manager.is_project_active(): return
        for i in range(self.tabs.count()):
            viewer = self.tabs.widget(i)
            self._save_annotations_for_viewer(viewer)
        QMessageBox.information(self, "Saved", "All open annotations have been saved.")

    def closeEvent(self, event):
        """Saves everything before closing the application."""
        if self.project_manager.is_project_active():
            self.save_all_annotations()
            self.save_project_state()
            print("Project saved. Closing application.")
        
        event.accept()

    def prompt_save_and_return_to_welcome(self):
        """Asks the user if they want to save before returning to the welcome screen."""
        if not self.project_manager.is_project_active():
            self.return_to_welcome_screen()
            return

        reply = QMessageBox.question(self, "Save Changes?",
                                     "Do you want to save your changes before returning to the project list?",
                                     QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                     QMessageBox.Save)

        if reply == QMessageBox.Save:
            self.save_all_annotations()
            self.save_project_state()
            self.return_to_welcome_screen()
        elif reply == QMessageBox.Discard:
            self.return_to_welcome_screen()
        else: # Cancel
            pass

    def return_to_welcome_screen(self):
        """Resets the UI and switches back to the welcome screen."""
        self.reset_project_ui()
        self.stack.setCurrentWidget(self.welcome_screen)
        self.menuBar().setVisible(False)
        self.setWindowTitle("LabelAI")
        self.project_manager.close_project() # Add a method to formally close the project

    def reset_project_ui(self):
        """Clears all project-specific UI elements."""
        self.tabs.clear()
        self.annotation_panel.clear_all()
        self.image_sidebar.clear_all()
        self.models_menu.clear()
        self.models_menu.setDisabled(True)
        self.tools_menu.clear()
        self.tools_menu.setDisabled(True)
        self.current_active_label = None
        self.current_model_info = None
        self.export_button.setText("Export")
        self.export_button.setDisabled(True)
        self.export_button.setStyleSheet("background-color: #A0A0A0; color: #FFFFFF; padding: 8px 16px; border-radius: 4px;")

    def handle_export(self):
        """Handles the full export workflow."""
        if not self.current_model_info:
            QMessageBox.warning(self, "No Model Selected", "Please select a model from the 'Models' menu first.")
            return

        if not self.project_manager.is_project_active():
            QMessageBox.warning(self, "No Project Active", "Cannot export without an active project.")
            return
            
        # 1. Ask for output directory
        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory", os.path.expanduser("~"), QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog)
        
        if not output_dir:
            return # User cancelled

        # 2. Gather all annotations from the project
        all_annotations = []
        annotation_dir = self.project_manager.get_annotation_dir()
        for filename in os.listdir(annotation_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(annotation_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        all_annotations.append(data)
                except Exception as e:
                    print(f"Could not read or parse annotation file {filename}: {e}")
        
        if not all_annotations:
            QMessageBox.information(self, "No Annotations", "There are no annotations in this project to export.")
            return

        # 3. Get class map
        class_labels = self.annotation_panel.get_class_labels()
        class_map = {label: i for i, label in enumerate(class_labels)}

        # 4. Call the exporter
        try:
            model_name = self.current_model_info['name']
            warnings = exporter.export_annotations(all_annotations, output_dir, model_name, class_map)
            
            # 5. Show success message
            success_message = f"Annotations successfully exported for {model_name} to:\n{output_dir}"
            if warnings:
                warnings_text = "\n\nWarnings:\n- " + "\n- ".join(warnings)
                success_message += warnings_text
            
            QMessageBox.information(self, "Export Complete", success_message)
        
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"An error occurred during export: {e}")

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for the main window."""
        key = event.key()
        
        # Shortcut for selecting class labels with number keys 1-9
        if Qt.Key_1 <= key <= Qt.Key_9:
            index = key - Qt.Key_1
            self.annotation_panel.select_label_by_index(index)
        else:
            super().keyPressEvent(event)

    # --- Other methods like on_active_label_changed, set_active_tool, etc. remain largely the same ---
    # Minor changes might be needed to adapt to the new auto-save logic.
    def on_active_label_changed(self, label):
        self.current_active_label = label
        active_viewer = self.tabs.currentWidget()
        if isinstance(active_viewer, ImageViewer):
            active_viewer.set_active_label(label)
        active_viewer = self.tabs.currentWidget()
        if isinstance(active_viewer, ImageViewer):
            active_viewer.set_active_label(label)

    def on_tab_changed(self, index):
        self.on_active_label_changed(self.current_active_label)
        active_viewer = self.tabs.currentWidget()
        if isinstance(active_viewer, ImageViewer):
             self.annotation_panel.update_annotations(active_viewer.annotations)

    def save_project_state(self):
        if not self.project_manager.is_project_active(): return
        open_files = [self.tabs.widget(i).property("image_path") for i in range(self.tabs.count())]
        class_labels = self.annotation_panel.get_class_labels()
        state_data = { "open_files": open_files, "class_labels": class_labels }
        self.project_manager.save_state(state_data)

    def on_annotations_changed_in_viewer(self, viewer):
        if viewer:
            self.annotation_panel.update_annotations(viewer.annotations)
            self._save_annotations_for_viewer(viewer)

            # Enable/disable export button based on annotations
            if self.current_model_info and viewer.annotations:
                self.export_button.setDisabled(False)
            else:
                self.export_button.setDisabled(True)

    def on_annotations_updated_from_panel(self, annotations):
        viewer = self.tabs.currentWidget()
        if isinstance(viewer, ImageViewer):
            viewer.load_annotations(annotations)
            self._save_annotations_for_viewer(viewer)

    def _save_annotations_for_viewer(self, viewer):
        if not (viewer and self.project_manager.is_project_active()): return
        
        image_path, image_w, image_h = viewer.get_image_details()
        
        if image_path and image_w > 0 and image_h > 0:
            image_filename = os.path.basename(image_path)
            self.project_manager.save_annotations(
                image_filename, 
                viewer.annotations, 
                image_path, 
                image_w, 
                image_h
            )

    def load_annotations_for_viewer(self, viewer, image_path):
        if not self.project_manager.is_project_active(): return
        image_filename = os.path.basename(image_path)
        annotations = self.project_manager.load_annotations(image_filename)
        if annotations:
            viewer.load_annotations(annotations)

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if widget:
            widget.deleteLater()
        self.tabs.removeTab(index)

    def run_model(self):
        pass

    def handle_sam_prompt(self, point):
        """
        This function is triggered when the user clicks in "prompt" mode.
        It runs the SAM model and adds the result to the annotations.
        """
        active_viewer = self.tabs.currentWidget()
        if not isinstance(active_viewer, ImageViewer):
            return

        # Ensure a model that uses the 'prompt' tool is active
        if not self.current_model_info or self.current_model_info.get("tool") != "prompt":
            QMessageBox.warning(self, "Wrong Tool", "Please select a model that uses the 'prompt' tool (like SAM) from the Models menu.")
            return

        image_path = active_viewer.property("image_path")
        
        # Convert the widget point to absolute image coordinates for the SAM model
        # This requires the to_absolute_image_coords method in ImageViewer
        prompt_point_absolute = active_viewer.to_absolute_image_coords(point)
        if not prompt_point_absolute:
            return # Click was outside the image area

        print(f"Running SAM on {os.path.basename(image_path)} with prompt at absolute coords {prompt_point_absolute}...")
        
        # Call the model manager with the correct arguments for SAMAdapter
        try:
            # The model returns a list of new annotations (usually just one polygon)
            new_annotations = self.model_manager.run(image_path=image_path, prompt_point=prompt_point_absolute)
            
            if new_annotations:
                # Add the new AI-generated annotations to the viewer's list
                active_viewer.annotations.extend(new_annotations)
                # Emit the signal to update the UI and save the new data
                active_viewer.annotationsChanged.emit()
                self.statusBar().showMessage("SAM annotation added successfully!", 3000)
            else:
                self.statusBar().showMessage("SAM did not return a valid object for this point.", 4000)

        except Exception as e:
            print(f"SAM Inference Error: {e}")
            QMessageBox.critical(self, "SAM Inference Error", f"An error occurred while running the model: {e}")

    def load_project_state(self, state=None):
        if state is None:
            state = self.project_manager.load_state()
        open_files = state.get("open_files", [])
        for file_path in open_files:
            if os.path.exists(file_path):
                self.open_image_tab(file_path)
