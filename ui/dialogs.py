from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QFormLayout, QFileDialog

class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Project")
        self.setFixedSize(400, 150)

        self.projectName = QLineEdit(self)
        self.projectPath = QLineEdit(self)
        self.projectPath.setReadOnly(True)

        browseButton = QPushButton("Browse...")
        browseButton.clicked.connect(self.browse_path)

        createButton = QPushButton("Create", self)
        createButton.clicked.connect(self.accept)

        layout = QFormLayout(self)
        layout.addRow("Project Name:", self.projectName)
        layout.addRow("Project Location:", self.projectPath)
        layout.addWidget(browseButton)
        layout.addWidget(createButton)

    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Project Location")
        if path:
            self.projectPath.setText(path)

    def get_project_data(self):
        return {
            "name": self.projectName.text(),
            "path": self.projectPath.text()
        }

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox

class HotkeyGuideDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hotkey Guide")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)

        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(self.get_hotkey_html())
        
        layout.addWidget(text_browser)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def get_hotkey_html(self):
        return """
        <html>
        <head>
            <style>
                body { font-family: sans-serif; }
                h2 { color: #D32F2F; }
                h3 { border-bottom: 1px solid #ccc; padding-bottom: 5px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                code { background-color: #eee; padding: 2px 4px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h2>LabelAI Hotkey Guide</h2>

            <h3>General Navigation</h3>
            <table>
                <tr><th>Key</th><th>Action</th></tr>
                <tr><td><code>Ctrl + N</code></td><td>New Project</td></tr>
                <tr><td><code>Ctrl + O</code></td><td>Open Project (Back to Welcome Screen)</td></tr>
                <tr><td><code>Ctrl + S</code></td><td>Save All Annotations</td></tr>
                <tr><td><code>Ctrl + Shift + S</code></td><td>Export Annotations</td></tr>
                <tr><td><code>Esc</code></td><td>Cancel current action (e.g., exit drawing mode)</td></tr>
            </table>

            <h3>Image Navigation</h3>
            <table>
                <tr><th>Key</th><th>Action</th></tr>
                <tr><td><code>&larr; &uarr; &darr; &rarr;</code></td><td>Pan image</td></tr>
                <tr><td><code>+ / -</code></td><td>Zoom in / out</td></tr>
                <tr><td><code>Page Up</code></td><td>Previous Image</td></tr>
                <tr><td><code>Page Down</code></td><td>Next Image</td></tr>
            </table>

            <h3>Annotation Tools</h3>
            <table>
                <tr><th>Key</th><th>Action</th></tr>
                <tr><td><code>B</code></td><td>Select Bounding Box tool</td></tr>
                <tr><td><code>P</code></td><td>Select Polygon tool</td></tr>
                <tr><td><code>Enter</code> or <code>N</code></td><td>Finish drawing polygon</td></tr>
                <tr><td><code>Backspace</code></td><td>Remove last point of a polygon</td></tr>
            </table>
            
            <h3>Editing Annotations</h3>
            <table>
                <tr><th>Key</th><th>Action</th></tr>
                <tr><td><code>Delete</code></td><td>Delete the currently selected annotation</td></tr>
            </table>

            <h3>Labels & Classes</h3>
            <table>
                <tr><th>Key</th><th>Action</th></tr>
                <tr><td><code>1, 2, 3, ...</code></td><td>Quick assign class label</td></tr>
            </table>
        </body>
        </html>
        """
