# Face Recognition Identification System

A real-time **Face Recognition Identification System** that enables users to enroll individuals and identify new faces by comparing them against an enrolled face database.

The system implements a complete face recognition pipeline consisting of **face detection, face alignment, face embedding generation, similarity-based matching, and threshold-based unknown-face rejection**.

---

## Overview

Traditional image classification approaches require a fixed set of classes and generally require retraining when a new person is added.

This project uses an **embedding-based face recognition approach**. Each enrolled face is converted into a numerical feature representation (embedding), which is stored in a vector database. When a new face is detected, its embedding is compared with the enrolled embeddings using cosine similarity.

If the similarity score exceeds the configured threshold, the system identifies the corresponding person. Otherwise, the face is classified as **Unknown**.

### Recognition Pipeline

```text
Input Image / Camera
        │
        ▼
   Face Detection
      (SCRFD)
        │
        ▼
  Face Alignment
        │
        ▼
  ArcFace Model
        │
        ▼
Face Embedding (512-D)
        │
        ▼
   Normalization
        │
        ▼
 FAISS Similarity Search
        │
        ▼
Best Similarity Score
        │
    ┌───┴────┐
    │        │
  ≥ τ       < τ
    │        │
    ▼        ▼
  Known    Unknown
```

---

## Key Features

* Face detection using SCRFD
* Facial landmark detection and face alignment
* ArcFace-based face embeddings
* 512-dimensional normalized embeddings
* Cosine similarity-based face matching
* FAISS vector similarity search
* Configurable recognition threshold
* Unknown-face rejection
* Individual face enrollment
* Image-based enrollment
* Camera-based enrollment
* Batch enrollment
* SQLite database integration
* Real-time face recognition
* FastAPI backend
* PyQt6 desktop interface
* React web dashboard
* Recognition and attendance logging
* Evaluation framework
* Docker support

---

## System Architecture

```text
                 ┌─────────────────────┐
                 │   Camera / Image     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Face Detection    │
                 │       SCRFD         │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Face Alignment    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   ArcFace Model     │
                 │  Face Embeddings    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   FAISS Matcher     │
                 │ Cosine Similarity   │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Threshold Decision  │
                 └──────────┬──────────┘
                            │
                    ┌───────┴────────┐
                    ▼                ▼
                 KNOWN             UNKNOWN
                    │
                    ▼
             SQLite Database
```

---

# Technology Stack

| Component               | Technology           |
| ----------------------- | -------------------- |
| Programming Language    | Python               |
| Face Detection          | SCRFD                |
| Face Recognition        | ArcFace              |
| Face Analysis Framework | InsightFace          |
| Similarity Search       | FAISS                |
| Similarity Metric       | Cosine Similarity    |
| Database                | SQLite               |
| Backend                 | FastAPI              |
| Desktop GUI             | PyQt6                |
| Web Dashboard           | React + Vite         |
| Communication           | REST API + WebSocket |
| Containerization        | Docker               |

---

# Face Detection

The system uses **SCRFD (Sample and Computation Redistribution for Efficient Face Detection)** through the InsightFace framework.

The detector identifies faces in the input frame and provides:

* Bounding boxes
* Detection confidence
* Five-point facial landmarks

These landmarks are subsequently used for face alignment.

---

# Face Alignment

Before generating the embedding, each detected face is aligned to a standard facial template.

The alignment process uses the detected facial landmarks to normalize:

* Position
* Scale
* Rotation
* Face orientation

The aligned face is resized to:

```text
112 × 112 pixels
```

This provides a consistent input format for the ArcFace recognition model.

---

# Face Embeddings

The aligned face is passed through **ArcFace** to generate a numerical representation of the person's facial characteristics.

The resulting embedding is:

```text
512-dimensional
```

The embedding is L2-normalized before being stored and compared.

Conceptually:

```text
Face Image
     ↓
ArcFace
     ↓
512-Dimensional Vector
     ↓
L2 Normalization
     ↓
FAISS Index
```

Using embeddings allows new individuals to be enrolled without retraining a complete classification model.

---

# Similarity-Based Matching

The system uses **cosine similarity** to compare a query face embedding with the enrolled embeddings.

For normalized embeddings:

```text
similarity(f₁, f₂) = f₁ · f₂
```

The system searches for the enrolled identity with the highest similarity score.

FAISS is used to perform efficient nearest-neighbour vector search.

---

# Unknown Face Rejection

A face recognition system should not always assign a detected face to the closest enrolled identity.

To prevent incorrect identification, the system uses a configurable similarity threshold.

### Current Configuration

```text
SIM_THRESHOLD = 0.4
```

The decision process is:

```text
Similarity ≥ 0.4
        ↓
   Known Person

Similarity < 0.4
        ↓
      Unknown
```

The threshold can be adjusted according to evaluation results and the operating environment.

A lower threshold may increase false acceptances, while a higher threshold may increase false rejections.

---

# Enrollment

The enrollment workflow creates an identity in the face database.

```text
Capture / Upload Face
        ↓
   Detect Face
        ↓
  Align Face
        ↓
Generate Embedding
        ↓
Normalize Embedding
        ↓
Store in FAISS
        ↓
Store Identity Information
```

### Supported Enrollment Methods

* Camera
* Image file
* Batch folder

### Batch Enrollment Structure

```text
faces/
├── Person_1/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── image3.jpg
│
├── Person_2/
│   ├── image1.jpg
│   └── image2.jpg
│
└── Person_3/
    ├── image1.jpg
    └── image2.jpg
```

---

# Application Interfaces

## Desktop Application

The PyQt6 application provides an interface for:

* Face enrollment
* Camera access
* Image-based recognition
* Real-time recognition

Run:

```bash
cd gui
pip install -r requirements.txt
python main.py
```

The backend should be running before starting the GUI.

---

## Backend API

The FastAPI backend manages:

* Face detection
* Face embeddings
* Face matching
* Enrollment
* Database operations
* WebSocket communication

Run:

```bash
cd backend
pip install -r requirements.txt
python main.py
```

API:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

## Web Dashboard

The React dashboard provides interfaces for:

* Recognition statistics
* Attendance history
* Unknown detections
* Identity enrollment
* Identity management

Run:

```bash
cd dashboard
npm install
npm run dev
```

---

# Configuration

The following environment variables can be configured:

| Variable        | Default              | Description                          |
| --------------- | -------------------- | ------------------------------------ |
| `MODEL_PACK`    | `buffalo_sc`         | InsightFace model pack               |
| `SIM_THRESHOLD` | `0.4`                | Similarity threshold for recognition |
| `FACE_DB_DIR`   | `data/face_db`       | FAISS index directory                |
| `SQL_DB`        | `data/attendance.db` | SQLite database path                 |

Example:

```bash
SIM_THRESHOLD=0.5
```

---

# Evaluation

The project includes an evaluation workflow for measuring recognition performance using labeled known and unknown face samples.

The evaluation framework supports:

* Accuracy
* Precision
* Recall
* F1 Score
* False Acceptance Rate (FAR)
* False Rejection Rate (FRR)
* True Positives (TP)
* True Negatives (TN)
* False Positives (FP)
* False Negatives (FN)
* Recognition latency
* Threshold comparison
* Confusion matrix

### Evaluation Dataset Structure

```text
data/
└── evaluation/
    ├── known/
    │   ├── Person_1/
    │   ├── Person_2/
    │   └── Person_3/
    │
    └── unknown/
        ├── unknown_01.jpg
        ├── unknown_02.jpg
        └── unknown_03.jpg
```

The `known` dataset contains images of enrolled individuals.

The `unknown` dataset contains images of individuals who are not enrolled.

### Evaluation Results

The final results should be generated using the evaluation dataset and recorded below.

| Metric          | Result |
| --------------- | -----: |
| Accuracy        |      — |
| Precision       |      — |
| Recall          |      — |
| F1 Score        |      — |
| FAR             |      — |
| FRR             |      — |
| TP              |      — |
| TN              |      — |
| FP              |      — |
| FN              |      — |
| Average Latency |      — |

> The evaluation values should be updated with the actual results obtained from the test dataset. No results are manually estimated or fabricated.

---

# Failure Cases and Limitations

The recognition performance can be affected by several real-world conditions.

### Poor Lighting

Insufficient or excessive lighting can reduce face detection and embedding quality.

### Extreme Pose

Large head rotations can make facial landmarks and recognition embeddings less reliable.

### Occlusion

Masks, sunglasses, hands, or other objects covering facial features can reduce recognition accuracy.

### Motion Blur

Fast movement or camera shake can produce low-quality face images.

### Low Resolution

Very small or low-resolution faces may not contain sufficient information for reliable recognition.

### Similar-Looking Individuals

Individuals with similar facial characteristics may produce relatively close embeddings.

### Multiple Faces

Frames containing multiple faces require independent processing of each detected face.

### Threshold Selection

An inappropriate threshold can cause:

* False acceptance of an unknown person
* False rejection of an enrolled person

### Limited Enrollment Data

Recognition may become less robust if an individual is enrolled using only a small number of images with limited variation.

---

# Possible Improvements

Future versions of the system could include:

* Automatic threshold optimization using validation data
* More enrollment images per identity
* Improved low-light preprocessing
* Image-quality assessment
* Liveness and anti-spoofing detection
* Better handling of extreme poses
* GPU acceleration
* Multiple embeddings per identity
* Improved unknown-face rejection
* More comprehensive evaluation datasets
* Authentication for dashboard access
* Production deployment configuration

---

# Project Structure

```text
face-recognition-identification-system/
│
├── backend/
│   ├── main.py
│   ├── face_detector.py
│   ├── face_recognizer.py
│   ├── feature_matcher.py
│   ├── database.py
│   └── requirements.txt
│
├── gui/
│   ├── main.py
│   └── requirements.txt
│
├── dashboard/
│   ├── src/
│   │   └── components/
│   │       ├── Dashboard.jsx
│   │       ├── Attendance.jsx
│   │       ├── Unknowns.jsx
│   │       └── Settings.jsx
│   └── ...
│
├── scripts/
│   ├── enroll_batch.py
│   └── convert_widerface.py
│
├── data/
│   ├── face_db/
│   └── evaluation/
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# Installation & Quick Start

## Repository Setup
```bash
git clone https://github.com/Varshini22-bot/face-recognition-identification-system.git
cd face-recognition-identification-system
```

## Prerequisites

* Python 3.10+ (Tested on Python 3.11)
* Node.js and npm (Tested on Node v24+)
* Git
* Webcam for real-time recognition

---

## ⚡ Quick Start (Windows)

Convenient one-click batch scripts are included for quick demonstration:

1. **One-Time Setup**:
   Double-click `setup_environment.bat` (automatically creates virtual environment and installs all dependencies).
2. **Start Backend**:
   Double-click `run_backend.bat` (runs FastAPI server at `http://127.0.0.1:8000`, API docs at `/docs`).
3. **Launch Desktop GUI (PyQt6)**:
   Double-click `run_gui.bat` (opens desktop camera recognition app).
4. **Launch Web Dashboard (React)**:
   Double-click `run_dashboard.bat` (opens web dashboard at `http://localhost:3000`).

---

## 🛠️ Manual Setup

### 1. Backend Setup
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Desktop GUI (PyQt6)
```bash
# With venv activated:
pip install -r gui/requirements.txt
python gui/main.py
```

### 3. Web Dashboard (React + Vite)
```bash
cd dashboard
npm install
npm run dev
```

---

# Docker

The backend and dashboard can also be started using Docker Compose:

```bash
docker compose up --build
```

---

# Cost

This project was developed with a **₹0 / $0 budget**.

The core system uses open-source frameworks, libraries, and models. No paid face-recognition API or commercial recognition service is required for the implementation.

---

# Design Decisions

## Embedding-Based Recognition

Face embeddings were selected instead of a traditional fixed-class classifier because new identities can be enrolled without retraining the complete recognition model.

## ArcFace

ArcFace was selected because it provides discriminative facial embeddings suitable for identity matching.

## Cosine Similarity

Cosine similarity is appropriate for comparing normalized face embeddings and provides an intuitive similarity score for threshold-based recognition.

## FAISS

FAISS was selected to provide efficient vector similarity search as the number of enrolled identities increases.

## Threshold-Based Rejection

A threshold is necessary to prevent the system from forcing every detected face to match an enrolled identity.

## SQLite

SQLite provides lightweight persistent storage without requiring an external database server, which is suitable for a zero-cost local deployment.

---

# References

* InsightFace — Face analysis and recognition framework
* ArcFace — Additive Angular Margin Loss for Deep Face Recognition
* SCRFD — Efficient Face Detection
* FAISS — Efficient Similarity Search and Clustering of Dense Vectors

External libraries and research work are acknowledged as the technical foundations used in the implementation.

---

# Author

**Varshini**

Face Recognition Identification System
GitHub: **Varshini22-bot**

---

## Acknowledgement

This project incorporates open-source technologies and research-based models. Their respective authors and projects are acknowledged in the references above.

The implementation has been configured, integrated, tested, documented, and prepared as an end-to-end Face Recognition Identification System project.
