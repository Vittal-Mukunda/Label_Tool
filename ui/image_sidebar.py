# C:\LabelAI\ui\image_sidebar.py

import os
from typing import List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton, QListWidgetItem, 
    QHBoxLayout, QMessageBox, QStyle, QListView, QLabel
)
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QIcon, QFont


class ImageSidebar(QWidget):
    """
    A sidebar widget to display a grid of image thumbnails from a directory.

    Provides functionality to add, delete, and select images.

    Signals:
        imageSelected (str): Emitted when an image is double-clicked, providing its path.
        addImagesClicked (): Emitted when the 'Add' button is clicked.
        imagesDeleted (list): Emitted with a list of image paths to be deleted.
    """
    
    # --- Class Constants for easier configuration ---
    MIN_WIDTH = 180
    MAX_WIDTH = 280
    ICON_SIZE = QSize(120, 120)
    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')

    # --- Signals ---
    imageSelected = pyqtSignal(str)
    addImagesClicked = pyqtSignal()
    imagesDeleted = pyqtSignal(list)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setMinimumWidth(self.MIN_WIDTH)
        self.setMaximumWidth(self.MAX_WIDTH)
        self._init_ui()
        self._apply_styles()

    def _init_ui(self) -> None:
        """Initialize the user interface and layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)  # Increased margins
        main_layout.setSpacing(12)  # Increased spacing

        # --- Header Label ---
        self.header_label = QLabel("Project Images")
        self.header_label.setAlignment(Qt.AlignCenter)
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(10)
        self.header_label.setFont(header_font)
        main_layout.addWidget(self.header_label)

        # --- Button Layout ---
        button_layout = self._create_button_layout()
        main_layout.addLayout(button_layout)
        
        # --- Image List Widget ---
        self.image_list_widget = QListWidget()
        self.image_list_widget.setIconSize(self.ICON_SIZE)
        self.image_list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.image_list_widget.setViewMode(QListView.IconMode)
        self.image_list_widget.setResizeMode(QListView.Adjust)
        self.image_list_widget.setMovement(QListWidget.Static)
        self.image_list_widget.setFlow(QListView.LeftToRight)  # Arrange items left-to-right
        self.image_list_widget.setWrapping(True)  # Wrap items to the next line
        self.image_list_widget.setSpacing(8)  # Add spacing between items
        self.image_list_widget.setContentsMargins(8, 8, 8, 8)  # Internal margins

        # --- Connections ---
        self.image_list_widget.itemDoubleClicked.connect(self._activate_item)

        # --- Assemble Layout ---
        main_layout.addWidget(self.image_list_widget)

    def _create_button_layout(self) -> QHBoxLayout:
        """Create the layout with Add and Delete buttons."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)  # Space between buttons
        button_layout.setContentsMargins(0, 5, 0, 5)  # Vertical margins

        # Use standard icons for a cleaner look
        add_icon = self.style().standardIcon(QStyle.SP_FileDialogNewFolder)
        delete_icon = self.style().standardIcon(QStyle.SP_TrashIcon)

        self.add_button = QPushButton(add_icon, " Add")
        self.add_button.setToolTip("Add images to the current project")
        self.add_button.setMinimumHeight(32)  # Set minimum height
        self.add_button.clicked.connect(self.addImagesClicked)

        self.delete_button = QPushButton(delete_icon, " Delete")
        self.delete_button.setToolTip("Delete selected images (and annotations)")
        self.delete_button.setMinimumHeight(32)  # Set minimum height
        self.delete_button.clicked.connect(self._handle_delete_request)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        
        return button_layout

    def _apply_styles(self) -> None:
        """Apply custom styles to the sidebar components."""
        # Style the main widget
        self.setStyleSheet("""
            ImageSidebar {
                background-color: #f8f9fa;
                border-right: 1px solid #dee2e6;
            }
            
            QLabel {
                color: #495057;
                padding: 8px 0px;
                border-bottom: 1px solid #e9ecef;
                margin-bottom: 8px;
            }
            
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: 500;
                color: #495057;
            }
            
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            
            QPushButton:pressed {
                background-color: #dee2e6;
                border-color: #6c757d;
            }
            
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
            }
            
            QListWidget::item {
                background-color: transparent;
                border: 2px solid transparent;
                border-radius: 8px;
                padding: 4px;
                margin: 2px;
            }
            
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
            }
            
            QListWidget::item:hover {
                background-color: #f5f5f5;
                border: 2px solid #bdbdbd;
            }
        """)

    def _handle_delete_request(self) -> None:
        """Confirm and initiate the deletion of selected images."""
        selected_items = self.image_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Delete Images", "No images selected.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_items)} image(s)?\n\n"
            "This will also delete their annotation files and cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            paths_to_delete = [item.data(Qt.UserRole) for item in selected_items]
            self.imagesDeleted.emit(paths_to_delete)

    def _activate_item(self, item: QListWidgetItem) -> None:
        """Emit a signal with the path of the activated (double-clicked) item."""
        path = item.data(Qt.UserRole)
        if path:
            self.imageSelected.emit(path)

    def populate_from_directory(self, image_dir: str) -> None:
        """Scan a directory and populate the list with image thumbnails."""
        self.image_list_widget.clear()
        if not os.path.isdir(image_dir):
            return

        image_count = 0
        for filename in sorted(os.listdir(image_dir)):
            if filename.lower().endswith(self.IMAGE_EXTENSIONS):
                full_path = os.path.join(image_dir, filename)
                
                # NOTE: Loading many large images into QIcon on the main thread
                # can cause the UI to freeze. For better performance with large
                # datasets, consider creating thumbnails in a background thread.
                item = QListWidgetItem(QIcon(full_path), os.path.basename(filename))
                item.setData(Qt.UserRole, full_path)
                item.setToolTip(f"Double-click to open: {filename}")
                item.setSizeHint(QSize(140, 140))  # Set consistent item size
                
                self.image_list_widget.addItem(item)
                image_count += 1
        
        # Update header to show count
        self.header_label.setText(f"Project Images ({image_count})")

    def remove_items_by_path(self, paths: List[str]) -> None:
        """Remove items from the list widget that match the given paths."""
        paths_set = set(paths)
        removed_count = 0
        
        for i in range(self.image_list_widget.count() - 1, -1, -1):
            item = self.image_list_widget.item(i)
            if item and item.data(Qt.UserRole) in paths_set:
                self.image_list_widget.takeItem(i)
                removed_count += 1
        
        # Update header count
        remaining_count = self.image_list_widget.count()
        self.header_label.setText(f"Project Images ({remaining_count})")

    def clear_all(self) -> None:
        """Clear all images from the sidebar."""
        self.image_list_widget.clear()
        self.header_label.setText("Project Images (0)")

    def select_next_image(self) -> None:
        """Select and activate the next image in the list."""
        current_row = self.image_list_widget.currentRow()
        if current_row + 1 < self.image_list_widget.count():
            next_item = self.image_list_widget.item(current_row + 1)
            self.image_list_widget.setCurrentItem(next_item)
            self._activate_item(next_item)

    def select_prev_image(self) -> None:
        """Select and activate the previous image in the list."""
        current_row = self.image_list_widget.currentRow()
        if current_row > 0:
            prev_item = self.image_list_widget.item(current_row - 1)
            self.image_list_widget.setCurrentItem(prev_item)
            self._activate_item(prev_item)

    def get_selected_image_paths(self) -> List[str]:
        """Get paths of currently selected images."""
        selected_items = self.image_list_widget.selectedItems()
        return [item.data(Qt.UserRole) for item in selected_items if item.data(Qt.UserRole)]

    def select_image_by_path(self, image_path: str) -> bool:
        """Select an image by its file path. Returns True if found and selected."""
        for i in range(self.image_list_widget.count()):
            item = self.image_list_widget.item(i)
            if item and item.data(Qt.UserRole) == image_path:
                self.image_list_widget.setCurrentItem(item)
                return True
        return False