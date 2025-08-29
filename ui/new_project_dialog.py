# C:\LabelAI\ui\new_project_dialog.py

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QDialogButtonBox,
                             QMessageBox)
from PyQt5.QtCore import Qt

from backend.model_database import MODEL_DATABASE

class NewProjectDialog(QDialog):
    def __init__(self, existing_projects, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Project")
        self.setMinimumWidth(400)
        
        self.existing_projects = [p.lower() for p in existing_projects]
        self.project_name = ""
        self.annotation_goal = ""
        self.model_name = ""

        # Layouts
        layout = QVBoxLayout(self)
        form_layout = QVBoxLayout()
        
        # Project Name
        name_label = QLabel("Project Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., 'City_Traffic_Analysis'")
        self.name_input.textChanged.connect(self.validate_form)
        
        # Annotation Goal
        goal_label = QLabel("1. Select Annotation Goal:")
        self.goal_combo = QComboBox()
        self.goal_combo.addItem("", "Select a goal...")
        for goal, data in MODEL_DATABASE.items():
            self.goal_combo.addItem(f"{goal} → {data['description']}", userData=goal)
        self.goal_combo.currentIndexChanged.connect(self.update_model_options)

        # Model Selection
        model_label = QLabel("2. Select Model (compatible with goal):")
        self.model_combo = QComboBox()
        self.model_combo.setEnabled(False) # Disabled until a goal is selected
        self.model_combo.currentIndexChanged.connect(self.validate_form)
        
        # Add to form layout
        form_layout.addWidget(name_label)
        form_layout.addWidget(self.name_input)
        form_layout.addSpacing(15)
        form_layout.addWidget(goal_label)
        form_layout.addWidget(self.goal_combo)
        form_layout.addSpacing(15)
        form_layout.addWidget(model_label)
        form_layout.addWidget(self.model_combo)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        # Add layouts to main dialog
        layout.addLayout(form_layout)
        layout.addSpacing(20)
        layout.addWidget(self.button_box)

        self.validate_form()

    def update_model_options(self):
        """
        Dynamically populates the model dropdown based on the selected annotation goal.
        """
        self.model_combo.clear()
        selected_goal = self.goal_combo.currentData()
        
        if selected_goal and selected_goal in MODEL_DATABASE:
            self.model_combo.setEnabled(True)
            self.model_combo.addItem("", "Select a model...")
            self.model_combo.addItems([model['name'] for model in MODEL_DATABASE[selected_goal]["models"]])
        else:
            self.model_combo.setEnabled(False)
            self.model_combo.addItem("", "Select a goal first...")
        
        self.validate_form()

    def validate_form(self):
        """
        Enable or disable the OK button based on form validity.
        """
        is_name_valid = bool(self.name_input.text().strip())
        is_goal_selected = self.goal_combo.currentIndex() > 0
        is_model_selected = self.model_combo.currentIndex() > 0
        
        can_create = is_name_valid and is_goal_selected and is_model_selected
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(can_create)

    def accept(self):
        """
        Overrides the default accept behavior to perform validation.
        """
        project_name = self.name_input.text().strip()
        
        if project_name.lower() in self.existing_projects:
            QMessageBox.warning(self, "Validation Error", "A project with this name already exists.")
            return

        # If validation passes, store the values and accept the dialog
        self.project_name = project_name
        self.annotation_goal = self.goal_combo.currentData()
        self.model_name = self.model_combo.currentText()
        super().accept()

    def get_project_details(self):
        """
        Returns the captured project details if the dialog was accepted.
        """
        return self.project_name, self.annotation_goal, self.model_name
