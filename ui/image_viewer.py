from PyQt5.QtWidgets import QApplication, QLabel, QMessageBox
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QPolygonF, QBrush
from PyQt5.QtCore import Qt, QPoint, QRect, QPointF, QRectF, pyqtSignal, QSizeF

class ImageViewer(QLabel):
    annotationsChanged = pyqtSignal()
    promptMade = pyqtSignal(QPoint)
    toolChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.pixmap = None
        self.annotations = []
        self.setMinimumSize(1, 1)

        self.active_tool = "bbox"
        self.active_label = None
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.current_polygon_points = []
        self.setMouseTracking(True)

        self.scale = 1.0
        self.fit_in_view_scale = 1.0
        self.pan_offset = QPointF(0.0, 0.0)
        self.pan_start_pos = QPoint()
        self.setFocusPolicy(Qt.StrongFocus)

        # For editing
        self.hovered_ann_index = -1
        self.hovered_point_index = -1
        self.selected_ann_index = -1
        self.selected_point_index = -1
        self.hovered_segment_ann_index = -1
        self.hovered_segment_index = -1

        # For bordering
        self.ctrl_pressed = False
        self.bordering_ann_index = -1
        self.bordering_start_pt_index = -1
        self.bordering_path_preview = []

        # For moving
        self.moving_ann_index = -1
        self.grab_offset = QPoint()
        self.moving_ann_initial_coords = None

        # Keypoint display options
        self.show_keypoints = True
        self.show_skeleton = True
        self.confidence_threshold = 0.5

    def set_keypoint_display_options(self, options):
        """Sets the display options for keypoints and triggers a repaint."""
        self.show_keypoints = options.get("show_keypoints", True)
        self.show_skeleton = options.get("show_skeleton", True)
        self.confidence_threshold = options.get("confidence_threshold", 0.5)
        self.update()

    def wheelEvent(self, event):
        if not self.pixmap:
            return
        
        zoom_factor = 1.25 if event.angleDelta().y() > 0 else 1 / 1.25
        new_scale = self.scale * zoom_factor
        
        # Limit zoom out
        if new_scale < self.fit_in_view_scale:
            new_scale = self.fit_in_view_scale

        mouse_pos = event.pos()
        mouse_x_rel_to_image = (mouse_pos.x() - self.pan_offset.x()) / self.scale
        mouse_y_rel_to_image = (mouse_pos.y() - self.pan_offset.y()) / self.scale
        
        self.scale = new_scale
        
        self.pan_offset.setX(mouse_pos.x() - mouse_x_rel_to_image * self.scale)
        self.pan_offset.setY(mouse_pos.y() - mouse_y_rel_to_image * self.scale)
        self.update()

    def keyPressEvent(self, event):
        key = event.key()
        
        # Panning with arrow keys
        pan_speed = 15
        if key == Qt.Key_Up:
            self.pan_offset.setY(self.pan_offset.y() + pan_speed)
        elif key == Qt.Key_Down:
            self.pan_offset.setY(self.pan_offset.y() - pan_speed)
        elif key == Qt.Key_Left:
            self.pan_offset.setX(self.pan_offset.x() + pan_speed)
        elif key == Qt.Key_Right:
            self.pan_offset.setX(self.pan_offset.x() - pan_speed)
            
        # Zooming with + and -
        elif key == Qt.Key_Plus or key == Qt.Key_Equal:
            self.scale *= 1.25
        elif key == Qt.Key_Minus:
            self.scale /= 1.25
            
        # Finalize polygon with Enter/Return
        elif key == Qt.Key_Return or key == Qt.Key_Enter or key == Qt.Key_N:
            if self.active_tool == 'polygon' and len(self.current_polygon_points) > 2:
                self.finalize_polygon()

        # Delete selected annotation or last polygon point
        elif key == Qt.Key_Delete or key == Qt.Key_Backspace:
            if self.selected_ann_index != -1:
                del self.annotations[self.selected_ann_index]
                self.selected_ann_index = -1
                self.hovered_ann_index = -1
                self.annotationsChanged.emit()
            elif self.active_tool == 'polygon' and self.current_polygon_points:
                self.current_polygon_points.pop()
        
        # Switch tools
        elif key == Qt.Key_B:
            self.toolChanged.emit("bbox")
        elif key == Qt.Key_P:
            self.toolChanged.emit("polygon")

        elif key == Qt.Key_Control:
            self.ctrl_pressed = True
        else:
            super().keyPressEvent(event)
            
        self.update()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = False
            self.bordering_path_preview = [] # Clear preview
            self.update()
        super().keyReleaseEvent(event)

    def find_closest_vertex(self, pos, max_dist=10):
        closest_ann_index = -1
        closest_point_index = -1
        min_dist_sq = max_dist ** 2

        for i, ann in enumerate(self.annotations):
            points_to_check = []
            if ann.get("type") == "polygon":
                points_to_check = ann.get("coords", [])
            elif ann.get("type") == "keypoint":
                points_to_check = ann.get("points", [])

            for j, p_coords in enumerate(points_to_check):
                p = QPointF(p_coords[0], p_coords[1])
                widget_p = self.to_widget_coords(p)
                dist_sq = (pos.x() - widget_p.x())**2 + (pos.y() - widget_p.y())**2
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    closest_ann_index = i
                    closest_point_index = j
        return closest_ann_index, closest_point_index

    def find_closest_segment(self, pos, max_dist=10):
        closest_ann_index = -1
        closest_segment_index = -1
        min_dist_sq = max_dist ** 2

        for i, ann in enumerate(self.annotations):
            if ann.get("type") == "polygon":
                points = [self.to_widget_coords(QPointF(p[0], p[1])) for p in ann["coords"]]
                for j in range(len(points)):
                    p1 = points[j]
                    p2 = points[(j + 1) % len(points)]
                    
                    line_vec = p2 - p1
                    point_vec = pos - p1
                    line_len_sq = line_vec.x()**2 + line_vec.y()**2
                    if line_len_sq == 0:
                        dist_sq = point_vec.x()**2 + point_vec.y()**2
                    else:
                        t = max(0, min(1, (point_vec.x() * line_vec.x() + point_vec.y() * line_vec.y()) / line_len_sq))
                        closest_point = p1 + t * line_vec
                        dist_sq = (pos - closest_point).x()**2 + (pos - closest_point).y()**2

                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        closest_ann_index = i
                        closest_segment_index = j
        return closest_ann_index, closest_segment_index

    def get_display_rect(self):
        if not self.pixmap:
            return QRectF()
        return QRectF(self.pan_offset, QSizeF(self.pixmap.width() * self.scale, self.pixmap.height() * self.scale))

    def to_relative_coords(self, point):
        if not self.pixmap:
            return None
        display_rect = self.get_display_rect()
        relative_x = (point.x() - display_rect.x()) / display_rect.width()
        relative_y = (point.y() - display_rect.y()) / display_rect.height()
        
        # Clamp coordinates to be within the 0.0 to 1.0 range
        relative_x = max(0.0, min(1.0, relative_x))
        relative_y = max(0.0, min(1.0, relative_y))
        
        return QPointF(relative_x, relative_y)

    def to_widget_coords(self, point):
        display_rect = self.get_display_rect()
        abs_x = point.x() * display_rect.width() + display_rect.x()
        abs_y = point.y() * display_rect.height() + display_rect.y()
        return QPoint(int(abs_x), int(abs_y))

    def to_absolute_image_coords(self, point):
        if not self.pixmap or self.pixmap.isNull():
            return None
        rel_coords = self.to_relative_coords(point)
        if rel_coords is None:
            return None
        abs_x = rel_coords.x() * self.pixmap.width()
        abs_y = rel_coords.y() * self.pixmap.height()
        return (int(abs_x), int(abs_y))

    def set_tool(self, tool_name):
        self.active_tool = tool_name
        self.current_polygon_points = []
        self.start_point, self.end_point = QPoint(), QPoint()
        self.setCursor(Qt.CrossCursor if self.active_tool == "prompt" else Qt.ArrowCursor)
        self.update()

    def set_active_label(self, label):
        self.active_label = label

    def load_image(self, path):
        self.pixmap = QPixmap(path)
        if not self.pixmap:
            return

        self.setMinimumSize(1, 1) # Allow the widget to shrink
        
        # Calculate the scale factor to fit the image in the view
        if self.width() > 0 and self.height() > 0:
            w_ratio = self.width() / self.pixmap.width()
            h_ratio = self.height() / self.pixmap.height()
            self.fit_in_view_scale = min(w_ratio, h_ratio)
            self.scale = self.fit_in_view_scale
        else:
            # If the widget is not yet sized, default to 1.0
            self.fit_in_view_scale = 1.0
            self.scale = 1.0
            
        self.pan_offset = QPointF(0.0, 0.0)
        self.update()

    def center_on_point(self, point_rel):
        """Centers the view on a point given in relative image coordinates."""
        if not self.pixmap:
            return
        
        # Point in absolute image coordinates
        abs_x = point_rel.x() * self.pixmap.width()
        abs_y = point_rel.y() * self.pixmap.height()
        
        # Desired center of the widget
        widget_center_x = self.width() / 2
        widget_center_y = self.height() / 2
        
        # New pan offset
        self.pan_offset.setX(widget_center_x - abs_x * self.scale)
        self.pan_offset.setY(widget_center_y - abs_y * self.scale)
        self.update()

    def get_image_details(self):
        if not self.pixmap: return None, 0, 0
        return self.property("image_path"), self.pixmap.width(), self.pixmap.height()

    def load_annotations(self, annotations):
        self.annotations = annotations
        self.update()

    def mousePressEvent(self, event):
        # --- PANNING ---
        if event.button() == Qt.MiddleButton:
            self.pan_start_pos = event.pos()
            return

        if event.button() == Qt.LeftButton:
            # --- MOVING/SELECTING ANNOTATION ---
            if not self.current_polygon_points:
                clicked_ann_index = self.find_clicked_annotation(event.pos())
                if clicked_ann_index != -1:
                    self.selected_ann_index = clicked_ann_index
                    if not self.annotations[clicked_ann_index].get("pinned", True):
                        self.moving_ann_index = clicked_ann_index
                        ann = self.annotations[clicked_ann_index]
                        if ann['type'] == 'bbox':
                            self.moving_ann_initial_coords = list(ann['coords'])
                            origin_rel = QPointF(ann['coords'][0], ann['coords'][1])
                        else: # polygon
                            self.moving_ann_initial_coords = [list(p) for p in ann['coords']]
                            origin_rel = QPointF(ann['coords'][0][0], ann['coords'][0][1])

                        origin_widget = self.to_widget_coords(origin_rel)
                        self.grab_offset = event.pos() - origin_widget
                        return

            # --- BORDERING LOGIC ---
            if self.active_tool == "polygon" and self.ctrl_pressed:
                ann_idx, pt_idx = self.find_closest_vertex(event.pos())
                if pt_idx != -1:
                    # Start bordering
                    if self.bordering_ann_index == -1:
                        self.bordering_ann_index = ann_idx
                        self.bordering_start_pt_index = pt_idx
                        coords = self.annotations[ann_idx]['coords'][pt_idx]
                        self.current_polygon_points.append(self.to_widget_coords(QPointF(coords[0], coords[1])))
                        self.update()
                        return
                    # End bordering
                    elif self.bordering_ann_index == ann_idx:
                        for p in self.bordering_path_preview:
                            self.current_polygon_points.append(p)
                        self.bordering_ann_index = -1
                        self.bordering_start_pt_index = -1
                        self.bordering_path_preview = []
                        self.update()
                        return

            # --- EDITING ACTIONS (if not drawing new polygon) ---
            if not self.current_polygon_points:
                mods = event.modifiers()
                # Insert point on segment with Shift+Click
                if mods & Qt.ShiftModifier:
                    ann_idx, seg_idx = self.find_closest_segment(event.pos())
                    if seg_idx != -1:
                        new_point_rel = self.to_relative_coords(event.pos())
                        if new_point_rel:
                            self.annotations[ann_idx]["coords"].insert(seg_idx + 1, [new_point_rel.x(), new_point_rel.y()])
                            self.annotationsChanged.emit()
                            self.selected_ann_index = ann_idx
                            self.selected_point_index = seg_idx + 1
                            self.update()
                        return
                
                ann_idx, pt_idx = self.find_closest_vertex(event.pos())
                # Delete point with Alt+Click
                if mods & Qt.AltModifier and pt_idx != -1:
                    if len(self.annotations[ann_idx]["coords"]) > 3:
                        del self.annotations[ann_idx]["coords"][pt_idx]
                        self.annotationsChanged.emit()
                        self.update()
                    return

                # Select point for dragging
                if pt_idx != -1:
                    self.selected_ann_index = ann_idx
                    self.selected_point_index = pt_idx
                    return

            # --- KEYPOINT SELECTION ---
            if self.active_tool == "keypoint":
                ann_idx, pt_idx = self.find_closest_vertex(event.pos())
                if pt_idx != -1:
                    self.selected_ann_index = ann_idx
                    self.selected_point_index = pt_idx
                    return
            
        # --- DRAWING ACTIONS ---
        # Reset selection and bordering if we click on empty space to draw
        self.selected_ann_index = -1
        self.selected_point_index = -1
        self.bordering_ann_index = -1
        self.bordering_start_pt_index = -1
        
        if self.active_tool == "prompt" and event.button() == Qt.LeftButton:
            if not self.active_label: QMessageBox.warning(self, "No Label", "Please select a class label first."); return
            self.promptMade.emit(event.pos())
            return

        if self.active_tool == "bbox" and event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
        elif self.active_tool == "polygon":
            if event.button() == Qt.LeftButton:
                self.current_polygon_points.append(event.pos())
            elif event.button() == Qt.RightButton:
                if self.current_polygon_points:
                    self.current_polygon_points.pop()
        self.update()

    def mouseMoveEvent(self, event):
        self.setCursor(Qt.ArrowCursor) # Reset cursor initially

        if event.buttons() & Qt.MiddleButton:
            self.pan_offset += event.pos() - self.pan_start_pos
            self.pan_start_pos = event.pos()
            self.update()
            return

        if event.buttons() & Qt.LeftButton and self.selected_point_index != -1:
            new_pos = self.to_relative_coords(event.pos())
            if new_pos:
                ann = self.annotations[self.selected_ann_index]
                if ann['type'] == 'polygon':
                    ann["coords"][self.selected_point_index] = [new_pos.x(), new_pos.y()]
                elif ann['type'] == 'keypoint':
                    ann["points"][self.selected_point_index][0] = new_pos.x()
                    ann["points"][self.selected_point_index][1] = new_pos.y()
                self.annotationsChanged.emit()
            self.update()
            return

        if event.buttons() & Qt.LeftButton and self.moving_ann_index != -1:
            ann = self.annotations[self.moving_ann_index]
            new_origin_widget = event.pos() - self.grab_offset
            new_origin_rel = self.to_relative_coords(new_origin_widget)

            if new_origin_rel and self.moving_ann_initial_coords:
                if ann['type'] == 'bbox':
                    initial_origin_rel = QPointF(self.moving_ann_initial_coords[0], self.moving_ann_initial_coords[1])
                    delta_rel = new_origin_rel - initial_origin_rel
                    ann['coords'][0] = self.moving_ann_initial_coords[0] + delta_rel.x()
                    ann['coords'][1] = self.moving_ann_initial_coords[1] + delta_rel.y()
                else: # polygon
                    initial_origin_rel = QPointF(self.moving_ann_initial_coords[0][0], self.moving_ann_initial_coords[0][1])
                    delta_rel = new_origin_rel - initial_origin_rel
                    for i, p_initial in enumerate(self.moving_ann_initial_coords):
                        ann['coords'][i][0] = p_initial[0] + delta_rel.x()
                        ann['coords'][i][1] = p_initial[1] + delta_rel.y()

                self.annotationsChanged.emit()
                self.update()
            return

        if self.active_tool == "polygon" and self.current_polygon_points and (event.modifiers() & Qt.ShiftModifier):
            if (event.pos() - self.current_polygon_points[-1]).manhattanLength() > 15:
                self.current_polygon_points.append(event.pos())
                self.update()

        # Hovering logic
        self.hovered_ann_index, self.hovered_point_index = -1, -1
        self.hovered_segment_ann_index, self.hovered_segment_index = -1, -1
        
        if self.ctrl_pressed and self.active_tool == 'polygon':
            self.hovered_ann_index, self.hovered_point_index = self.find_closest_vertex(event.pos())
            if self.bordering_ann_index != -1:
                self.update_bordering_preview(event.pos())
        elif not self.current_polygon_points:
            mods = QApplication.keyboardModifiers()
            if mods & Qt.ShiftModifier:
                self.hovered_segment_ann_index, self.hovered_segment_index = self.find_closest_segment(event.pos())
            
            if self.hovered_segment_index == -1:
                self.hovered_ann_index, self.hovered_point_index = self.find_closest_vertex(event.pos())

        if self.hovered_point_index != -1 or self.hovered_segment_index != -1:
            self.setCursor(Qt.PointingHandCursor)
        elif self.active_tool == 'prompt':
            self.setCursor(Qt.CrossCursor)
        elif self.active_tool == "bbox" and event.buttons() & Qt.LeftButton:
            self.end_point = event.pos()
        self.update()

    def update_bordering_preview(self, mouse_pos):
        self.bordering_path_preview = []
        hover_ann_idx, hover_pt_idx = self.find_closest_vertex(mouse_pos)

        if hover_ann_idx != self.bordering_ann_index or hover_pt_idx == self.bordering_start_pt_index:
            return

        start_idx = self.bordering_start_pt_index
        end_idx = hover_pt_idx
        source_coords = self.annotations[self.bordering_ann_index]['coords']
        num_points = len(source_coords)

        # Path 1 (CW)
        path1 = []
        curr = (start_idx + 1) % num_points
        while curr != end_idx:
            path1.append(curr)
            curr = (curr + 1) % num_points
        path1.append(end_idx)

        # Path 2 (CCW)
        path2 = []
        curr = (start_idx - 1 + num_points) % num_points
        while curr != end_idx:
            path2.append(curr)
            curr = (curr - 1 + num_points) % num_points
        path2.append(end_idx)

        final_indices = path1 if len(path1) < len(path2) else path2
        
        for i in final_indices:
            p_coords = source_coords[i]
            self.bordering_path_preview.append(self.to_widget_coords(QPointF(p_coords[0], p_coords[1])))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected_ann_index, self.selected_point_index = -1, -1
            self.moving_ann_index = -1
            self.moving_ann_initial_coords = None
            if self.active_tool == "bbox":
                self.finalize_bbox()

    def find_clicked_annotation(self, pos):
        # Iterate backwards to select the top-most annotation
        for i in range(len(self.annotations) - 1, -1, -1):
            ann = self.annotations[i]
            ann_type = ann.get("type")
            
            if ann_type == "polygon":
                polygon_points = [self.to_widget_coords(QPointF(p[0], p[1])) for p in ann['coords']]
                if QPolygonF(polygon_points).containsPoint(QPointF(pos), Qt.OddEvenFill):
                    return i
            elif ann_type == "bbox":
                coords = ann['coords']
                # The bbox coords are x, y, width, height, so create a QRectF
                rel_rect = QRectF(coords[0], coords[1], coords[2], coords[3])
                
                # Convert relative corners to widget coordinates
                p1 = self.to_widget_coords(rel_rect.topLeft())
                p2 = self.to_widget_coords(rel_rect.bottomRight())
                
                if QRect(p1, p2).contains(pos):
                    return i
            elif ann_type == "keypoint":
                # Consider a click on a keypoint annotation if it's near any of its points
                for p_coords in ann['points']:
                    p = self.to_widget_coords(QPointF(p_coords[0], p_coords[1]))
                    if (p - pos).manhattanLength() < 10: # 10px tolerance
                        return i
        return -1

    def finalize_bbox(self):
        if not self.active_label:
            QMessageBox.warning(self, "No Label Selected", "Please select a class label before annotating.")
            self.start_point, self.end_point = QPoint(), QPoint()
            self.update()
            return
        
        start_rel, end_rel = self.to_relative_coords(self.start_point), self.to_relative_coords(self.end_point)
        self.start_point, self.end_point = QPoint(), QPoint()
        
        if start_rel and end_rel:
            rect = QRectF(start_rel, end_rel).normalized()
            # If the rectangle is too small, don't create an annotation
            if rect.width() < 0.001 and rect.height() < 0.001:
                return
            
            self.annotations.append({"label": self.active_label, "type": "bbox", "coords": [rect.x(), rect.y(), rect.width(), rect.height()], "pinned": True})
            self.annotationsChanged.emit()
            # Removed the call to self.center_on_point(rect.center())
            self.update()

    def finalize_polygon(self):
        if not self.active_label:
            QMessageBox.warning(self, "No Label Selected", "Please select a class label before annotating.")
            self.current_polygon_points = []
            self.update()
            return
            
        relative_points = [self.to_relative_coords(p) for p in self.current_polygon_points]
        self.current_polygon_points = []
        relative_points = [p for p in relative_points if p is not None]
        
        if len(relative_points) > 2:
            self.annotations.append({"label": self.active_label, "type": "polygon", "coords": [[p.x(), p.y()] for p in relative_points], "pinned": True})
            self.annotationsChanged.emit()
            
            # Calculate centroid and center on it
            sum_x = sum(p.x() for p in relative_points)
            sum_y = sum(p.y() for p in relative_points)
            centroid = QPointF(sum_x / len(relative_points), sum_y / len(relative_points))
            self.center_on_point(centroid)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        if not self.pixmap:
            painter.drawText(self.rect(), Qt.AlignCenter, "No image loaded")
            return

        display_rect = self.get_display_rect()
        painter.drawPixmap(display_rect.toRect(), self.pixmap, self.pixmap.rect())

        painter.setRenderHint(QPainter.Antialiasing)
        
        for i, ann in enumerate(self.annotations):
            label, coords = ann.get("label", "N/A"), ann.get("coords", [])
            
            is_selected = (i == self.selected_ann_index)
            pen_color = QColor(255, 255, 0, 220) if is_selected else QColor(0, 255, 0, 180)
            pen_width = 4 if is_selected else 2
            painter.setPen(QPen(pen_color, pen_width))

            if ann.get("type") == "bbox" and len(coords) == 4:
                p1 = self.to_widget_coords(QPointF(coords[0], coords[1]))
                p2 = self.to_widget_coords(QPointF(coords[0] + coords[2], coords[1] + coords[3]))
                widget_rect = QRect(p1, p2)
                painter.drawRect(widget_rect)
                painter.drawText(widget_rect.left(), widget_rect.top() - 5, label)

            elif ann.get("type") == "polygon" and coords:
                polygon_points = [self.to_widget_coords(QPointF(p[0], p[1])) for p in coords]
                if len(polygon_points) > 1:
                    brush_color = QColor(255, 255, 0, 60) if is_selected else QColor(0, 255, 0, 40)
                    painter.setBrush(brush_color)
                    painter.drawPolygon(QPolygonF(polygon_points))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawText(polygon_points[0].x(), polygon_points[0].y() - 5, label)

            elif ann.get("type") == "keypoint" and coords:
                points = ann.get("points", [])
                skeleton = ann.get("skeleton", [])
                
                # Draw skeleton
                if self.show_skeleton:
                    painter.setPen(QPen(QColor(0, 255, 255, 150), 2))
                    for connection in skeleton:
                        p1_idx, p2_idx = connection
                        if p1_idx < len(points) and p2_idx < len(points):
                            # Check confidence of both points
                            if points[p1_idx][2] >= self.confidence_threshold and points[p2_idx][2] >= self.confidence_threshold:
                                p1_coords = points[p1_idx]
                                p2_coords = points[p2_idx]
                                p1 = self.to_widget_coords(QPointF(p1_coords[0], p1_coords[1]))
                                p2 = self.to_widget_coords(QPointF(p2_coords[0], p2_coords[1]))
                                painter.drawLine(p1, p2)

                # Draw keypoints
                if self.show_keypoints:
                    for j, p_coords in enumerate(points):
                        if p_coords[2] >= self.confidence_threshold:
                            p = self.to_widget_coords(QPointF(p_coords[0], p_coords[1]))
                            is_hovered = self.hovered_ann_index == i and self.hovered_point_index == j
                            is_selected = self.selected_ann_index == i and self.selected_point_index == j

                            radius = 6 if is_hovered or is_selected else 4
                            brush_color = QColor(255, 255, 0, 220) if is_selected else QColor(255, 0, 255, 200)
                            
                            painter.setBrush(brush_color)
                            painter.setPen(Qt.NoPen)
                            painter.drawEllipse(p, radius, radius)


                # --- Vertex and Segment Drawing ---
                if self.ctrl_pressed:
                    # Draw all vertices for snapping
                    painter.setPen(Qt.NoPen)
                    for j, p in enumerate(polygon_points):
                        is_hovered = self.hovered_ann_index == i and self.hovered_point_index == j
                        brush_color = QColor(0, 255, 255, 220) if is_hovered else QColor(255, 165, 0, 200)
                        painter.setBrush(brush_color)
                        painter.drawEllipse(p, 5, 5)
                else:
                    # Draw vertices for editing (on hover)
                    if i == self.hovered_ann_index and self.hovered_point_index != -1:
                        p = polygon_points[self.hovered_point_index]
                        painter.setBrush(QBrush(QColor(255, 255, 0, 220)))
                        painter.setPen(Qt.NoPen)
                        painter.drawEllipse(p, 5, 5)

                    # Highlight hovered segment for editing
                    if i == self.hovered_segment_ann_index and self.hovered_segment_index != -1:
                        p1 = polygon_points[self.hovered_segment_index]
                        p2 = polygon_points[(self.hovered_segment_index + 1) % len(polygon_points)]
                        painter.setPen(QPen(QColor(255, 0, 255, 220), 3, Qt.DashLine))
                        painter.drawLine(p1, p2)
        
        painter.setBrush(Qt.NoBrush)

        # Draw current annotation in progress
        pen = QPen(QColor(255, 255, 0), 2)
        painter.setPen(pen)
        if self.active_tool == "bbox" and not self.start_point.isNull():
            painter.drawRect(QRect(self.start_point, self.end_point))
        elif self.active_tool == "polygon" and self.current_polygon_points:
            # Draw preview for auto-bordering
            if self.bordering_path_preview:
                preview_pen = QPen(QColor(0, 150, 255, 200), 4, Qt.DotLine)
                painter.setPen(preview_pen)
                path_to_draw = QPolygonF([self.current_polygon_points[-1]] + self.bordering_path_preview)
                painter.drawPolyline(path_to_draw)
            
            # Draw the regular polyline for the new polygon
            painter.setPen(pen)
            points = self.current_polygon_points + [self.mapFromGlobal(self.cursor().pos())]
            painter.drawPolyline(QPolygonF(points))