# C:\LabelAI\ui\annotation_panel.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, 
                             QLineEdit, QPushButton, QHBoxLayout, QMessageBox, QToolButton, QStyle,
                             QGroupBox, QCheckBox, QDoubleSpinBox, QFormLayout, QScrollArea)
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QIcon

class AnnotationListItem(QWidget):
    pinStateChanged = pyqtSignal(int, bool)  # ann_index, is_pinned

    def __init__(self, text, ann_index, is_pinned):
        super().__init__()
        self.ann_index = ann_index
        self._is_pinned = is_pinned

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(5)

        self.label = QLabel(text)
        layout.addWidget(self.label, 1)

        self.pin_button = QToolButton()
        self.pin_button.setCheckable(True)
        self.pin_button.setFixedSize(24, 24)
        self.pin_button.setIconSize(QSize(18, 18))
        self.pin_button.setAutoRaise(True)
        self.pin_button.clicked.connect(self.pin_toggled)
        
        layout.addWidget(self.pin_button)
        self.update_pin_state(self._is_pinned)

    def pin_toggled(self):
        self._is_pinned = self.pin_button.isChecked()
        self.update_pin_state(self._is_pinned)
        self.pinStateChanged.emit(self.ann_index, self._is_pinned)

    def update_pin_state(self, is_pinned):
        self._is_pinned = is_pinned
        self.pin_button.setChecked(is_pinned)
        style = self.style()
        icon = style.standardIcon(QStyle.SP_DialogApplyButton if is_pinned else QStyle.SP_DialogCloseButton)
        self.pin_button.setIcon(icon)
        self.pin_button.setToolTip("Pinned (cannot be moved)" if is_pinned else "Unpinned (can be moved)")


class AnnotationPanel(QWidget):
    activeLabelChanged = pyqtSignal(str)
    classLabelsChanged = pyqtSignal()
    annotationsUpdated = pyqtSignal(list)
    keypointDisplayOptionsChanged = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setObjectName("AnnotationPanel")
        
        self.current_annotations = []
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # --- Class Labels Group Box ---
        class_group_box = QGroupBox("Class Labels")
        class_layout = QVBoxLayout(class_group_box)
        
        self.label_list = QListWidget()
        self.label_list.currentItemChanged.connect(self.on_label_selection_changed)
        class_layout.addWidget(self.label_list)
        
        add_layout = QHBoxLayout()
        self.new_label_input = QLineEdit()
        self.new_label_input.setPlaceholderText("Enter new label...")
        self.new_label_input.returnPressed.connect(self.add_new_label)
        
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_new_label)
        add_layout.addWidget(self.new_label_input)
        add_layout.addWidget(add_button)
        class_layout.addLayout(add_layout)

        delete_label_button = QPushButton("Delete Selected Label")
        delete_label_button.clicked.connect(self.delete_selected_label)
        class_layout.addWidget(delete_label_button)
        
        main_layout.addWidget(class_group_box)
        
        # --- Keypoint Display Options ---
        self.kp_options_group = QGroupBox("Keypoint Options")
        kp_layout = QFormLayout(self.kp_options_group)
        
        self.show_keypoints_checkbox = QCheckBox("Show Keypoints")
        self.show_keypoints_checkbox.setChecked(True)
        self.show_keypoints_checkbox.stateChanged.connect(self.on_display_options_changed)
        kp_layout.addRow(self.show_keypoints_checkbox)

        self.show_skeleton_checkbox = QCheckBox("Show Skeleton")
        self.show_skeleton_checkbox.setChecked(True)
        self.show_skeleton_checkbox.stateChanged.connect(self.on_display_options_changed)
        kp_layout.addRow(self.show_skeleton_checkbox)

        self.confidence_spinbox = QDoubleSpinBox()
        self.confidence_spinbox.setRange(0.0, 1.0)
        self.confidence_spinbox.setSingleStep(0.05)
        self.confidence_spinbox.setValue(0.5)
        self.confidence_spinbox.valueChanged.connect(self.on_display_options_changed)
        kp_layout.addRow("Confidence Threshold:", self.confidence_spinbox)
        
        main_layout.addWidget(self.kp_options_group)
        self.kp_options_group.setVisible(False)
        
        # --- Image Annotations Group Box ---
        annotation_group_box = QGroupBox("Image Annotations")
        annotation_layout = QVBoxLayout(annotation_group_box)

        self.annotation_list = QListWidget()
        self.annotation_list.setSelectionMode(QListWidget.ExtendedSelection)
        annotation_layout.addWidget(self.annotation_list)

        delete_annotation_button = QPushButton("Delete Selected Annotation(s)")
        delete_annotation_button.clicked.connect(self.delete_selected_annotations)
        annotation_layout.addWidget(delete_annotation_button)

        main_layout.addWidget(annotation_group_box)
        
        main_layout.addStretch()

    def on_label_selection_changed(self, current, previous):
        if current:
            self.activeLabelChanged.emit(current.text())
        else:
            self.activeLabelChanged.emit("")

    def add_new_label(self):
        label_text = self.new_label_input.text().strip()
        if label_text:
            items = [self.label_list.item(i).text() for i in range(self.label_list.count())]
            if label_text not in items:
                self.label_list.addItem(label_text)
                self.label_list.setCurrentRow(self.label_list.count() - 1)
                self.classLabelsChanged.emit()
        self.new_label_input.clear()

    def delete_selected_label(self):
        selected_items = self.label_list.selectedItems()
        if not selected_items: return
        
        label_to_delete = selected_items[0].text()
        
        reply = QMessageBox.question(self, 'Delete Label', 
            f"You are about to delete the class label '{label_to_delete}'.\n\nDo you also want to remove all annotations with this label from the CURRENT image?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if reply == QMessageBox.Cancel:
            return

        self.label_list.takeItem(self.label_list.row(selected_items[0]))
        self.classLabelsChanged.emit()

        if reply == QMessageBox.Yes:
            self.current_annotations = [ann for ann in self.current_annotations if ann.get("label") != label_to_delete]
            self.annotationsUpdated.emit(self.current_annotations)
            self.update_annotations(self.current_annotations)

    def delete_selected_annotations(self):
        selected_list_rows = sorted([self.annotation_list.row(item) for item in self.annotation_list.selectedItems()], reverse=True)
        if not selected_list_rows: return

        ann_idx_map = self.annotation_list.property("ann_idx_map") or {}
        
        ann_indices_to_delete = sorted(list(set(ann_idx_map[row] for row in selected_list_rows if row in ann_idx_map)), reverse=True)

        if not ann_indices_to_delete: return

        for ann_index in ann_indices_to_delete:
            if 0 <= ann_index < len(self.current_annotations):
                del self.current_annotations[ann_index]
            
        self.annotationsUpdated.emit(self.current_annotations)
        self.update_annotations(self.current_annotations)

    def on_pin_state_changed(self, ann_index, is_pinned):
        if 0 <= ann_index < len(self.current_annotations):
            self.current_annotations[ann_index]['pinned'] = is_pinned
            self.annotationsUpdated.emit(self.current_annotations)

    def update_annotations(self, annotations):
        self.current_annotations = annotations
        self.annotation_list.clear()
        
        ann_idx_map = {}
        list_idx = 0

        for i, ann in enumerate(self.current_annotations):
            if isinstance(ann, dict):
                label = ann.get("label", "N/A")
                ann_type = ann.get("type", "N/A").upper()
                if "pinned" not in ann:
                    ann["pinned"] = False
                is_pinned = ann.get("pinned", False)

                item = QListWidgetItem(self.annotation_list)
                list_item_widget = AnnotationListItem(f"{i+1}: [{ann_type}] {label}", i, is_pinned)
                list_item_widget.pinStateChanged.connect(self.on_pin_state_changed)
                
                item.setSizeHint(list_item_widget.sizeHint())
                self.annotation_list.addItem(item)
                self.annotation_list.setItemWidget(item, list_item_widget)
                ann_idx_map[list_idx] = i
                list_idx += 1

                if ann.get("type") == "keypoint":
                    points = ann.get("points", [])
                    for j, point in enumerate(points):
                        if len(point) == 3:
                            x, y, conf = point
                            kp_item_text = f"  - KP {j}: ({x:.2f}, {y:.2f}), C: {conf:.2f}"
                        else:
                            x, y = point
                            kp_item_text = f"  - KP {j}: ({x:.2f}, {y:.2f})"

                        kp_item = QListWidgetItem(kp_item_text)
                        kp_item.setFlags(kp_item.flags() & ~Qt.ItemIsSelectable)
                        self.annotation_list.addItem(kp_item)
                        list_idx += 1
            else:
                item = QListWidgetItem(f"{i+1}: [Error] Invalid Annotation")
                self.annotation_list.addItem(item)
                list_idx += 1
        
        self.annotation_list.setProperty("ann_idx_map", ann_idx_map)

    def get_class_labels(self):
        return [self.label_list.item(i).text() for i in range(self.label_list.count())]

    def load_class_labels(self, labels):
        self.label_list.clear()
        self.label_list.addItems(labels)

    def select_label_by_index(self, index):
        if 0 <= index < self.label_list.count():
            self.label_list.setCurrentRow(index)

    def on_display_options_changed(self):
        options = {
            "show_keypoints": self.show_keypoints_checkbox.isChecked(),
            "show_skeleton": self.show_skeleton_checkbox.isChecked(),
            "confidence_threshold": self.confidence_spinbox.value()
        }
        self.keypointDisplayOptionsChanged.emit(options)

    def set_keypoint_options_visibility(self, visible):
        self.kp_options_group.setVisible(visible)

    def clear_all(self):
        self.label_list.clear()
        self.annotation_list.clear()
        self.current_annotations = []
        self.new_label_input.clear()
        self.set_keypoint_options_visibility(False)