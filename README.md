# 🏷️ LabelAI – Dataset Annotation Tool

## 📌 Overview  
**LabelAI** is a dataset annotation tool designed for creating, managing, and exporting labeled datasets for computer vision tasks.  
It supports multiple model formats (YOLO, RetinaNet, Pascal VOC, COCO, etc.) and provides a simple, user-friendly interface for labeling images and managing projects.  

With LabelAI, you can:  
- Create new labeling projects with your desired model format.  
- Annotate images with bounding boxes, segmentation masks, or keypoints.  
- Export datasets in popular formats (YOLO, VOC, COCO).  
- Reopen existing projects and continue from where you left off.  
- Maintain a clean and organized dataset structure.  

---

## ✨ Features  
- 🎯 **Multi-model support** – YOLOv8, RetinaNet, Pascal VOC, COCO.  
- 📂 **Project-based workflow** – All data is stored inside a parent project folder.  
- 🖼️ **Image annotation** – Bounding boxes, class labels, and metadata.  
- 🔄 **Resume projects** – Open existing projects without losing work.  
- 📦 **Export-ready datasets** – Automatically structured as:  


- 🛠️ **Error handling** – Safe project reopening and label validation.  
- ⚡ **Lightweight & fast** – Built in Python, runs locally with no external dependencies beyond standard ML tooling.  

---

## 📁 Project Structure  

LabelAI/
│── main.py # Entry point
│── ui/ # UI components
│ ├── main_window.py
│ ├── annotation_panel.py
│ └── ...
│── utils/ # Helper functions (file handling, exports, etc.)
│── models/ # Model format definitions
│── projects/ # Saved projects
│── README.md
└── requirements.txt


---

## 🚀 Installation  

### 1. Clone the repo  
```bash
git clone https://github.com/your-username/LabelAI.git
cd LabelAI

# Create the environment
python -m venv .venv

# Activate the environment
# Linux/Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

python main.py


## ▶️ Workflow  

1. **Create a new project** – Give it a name and select your target model format.  
2. **Import images** – Add all images you want to annotate.  
3. **Annotate** – Draw bounding boxes/masks and assign class labels.  
4. **Save progress** – Close the tool anytime; reopen projects later to resume.  
5. **Export dataset** – Get a YOLO, COCO, or VOC-ready structure with one click.  

---

## 📤 Export Formats  

- **YOLO** → one `.txt` file per image (with the same filename).  
- **Pascal VOC** → one `.xml` file per image (with the same filename).  
- **COCO / RetinaNet** → a single `annotations.json` file inside the `labels/` directory.  

---

## ⚠️ Known Issues  

- When reopening projects, string-only annotations may cause crashes (handled in a recent fix).  
- The default model selection always starts as YOLO (currently being updated to respect user choice on reopen).  

---

## 🛠️ Tech Stack  

- **Language**: Python 3.9+  
- **UI**: PyQt / Tkinter (depending on the build)  
- **ML Formats Supported**: YOLOv8, Pascal VOC, COCO, RetinaNet  
- **Other Libraries**: `torch`, `opencv-python`, `json`, `xml.etree`, etc.  

---

## 🤝 Contributing  

Contributions are welcome!  

1. Fork the repository.  
2. Create a new branch:  
   ```bash
   git checkout -b feature/my-new-feature
