"""
Batch enroll faces from a directory structure.

Usage:
    python enroll_batch.py --data faces/

Directory structure:
    faces/
      Alice/
        img1.jpg
        img2.jpg
      Bob/
        photo.png

Each subfolder name is used as the identity name.
"""
import argparse
import os
import sys

import cv2
import numpy as np

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from face_detector import FaceDetector
from face_recognizer import FaceRecognizer
from feature_matcher import FeatureMatcher


def enroll_directory(data_dir: str, db_dir: str, model_pack: str, threshold: float):
    print(f"Loading models ({model_pack}) ...")
    detector  = FaceDetector(model_pack=model_pack)
    recognizer = FaceRecognizer(model_pack=model_pack)
    matcher   = FeatureMatcher(threshold=threshold)
    matcher.load(db_dir)

    enrolled = 0
    skipped  = 0

    for name in sorted(os.listdir(data_dir)):
        person_dir = os.path.join(data_dir, name)
        if not os.path.isdir(person_dir):
            continue

        print(f"\n  Enrolling: {name}")
        for fname in sorted(os.listdir(person_dir)):
            fpath = os.path.join(person_dir, fname)
            img = cv2.imread(fpath)
            if img is None:
                print(f"    [SKIP] cannot read {fname}")
                skipped += 1
                continue

            faces = detector.detect(img)
            if not faces:
                print(f"    [SKIP] no face in {fname}")
                skipped += 1
                continue

            face = faces[0]
            if face["kps"] is None:
                print(f"    [SKIP] no landmarks in {fname}")
                skipped += 1
                continue

            emb = recognizer.get_embedding(img, face["kps"])
            matcher.add(name, emb)
            print(f"    ✓ {fname}")
            enrolled += 1

    matcher.save(db_dir)
    print(f"\n=== Enrolled {enrolled} faces, skipped {skipped} ===")
    print(f"Database: {matcher.index.ntotal} vectors, {len(matcher.list_identities())} identities")


def main():
    p = argparse.ArgumentParser(description="Batch face enrollment")
    p.add_argument("--data",      default="faces",          help="Root directory with subfolders per person")
    p.add_argument("--db",        default="data/face_db",   help="Face DB output directory")
    p.add_argument("--model",     default="buffalo_sc",      help="insightface model pack")
    p.add_argument("--threshold", default=0.4, type=float,  help="Cosine similarity threshold")
    args = p.parse_args()

    enroll_directory(args.data, args.db, args.model, args.threshold)


if __name__ == "__main__":
    main()
