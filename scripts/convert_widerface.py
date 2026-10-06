"""
Convert WIDER FACE dataset annotations to YOLO format.

Usage:
    python convert_widerface.py --split train
    python convert_widerface.py --split val

Expected directory layout (run from project root or pass --root):
    WIDERFACE/
      WIDER_train/images/<category>/<image>.jpg
      WIDER_val/images/<category>/<image>.jpg
      wider_face_split/
        wider_face_train_bbx_gt.txt
        wider_face_val_bbx_gt.txt

Output:
    dataset/train/images/  ← symlink or copy of original images
    dataset/train/labels/  ← YOLO .txt files
    dataset/val/images/
    dataset/val/labels/
"""

import argparse
import os
import shutil

import cv2


def convert(ann_file: str, image_dir: str, label_dir: str) -> tuple[int, int]:
    """
    Parse WIDER FACE annotation file and write YOLO labels.
    Returns (total_images, total_faces).
    """
    os.makedirs(label_dir, exist_ok=True)

    with open(ann_file) as f:
        lines = f.readlines()

    total_images = 0
    total_faces = 0
    i = 0

    while i < len(lines):
        img_rel = lines[i].strip()
        i += 1
        num_faces = int(lines[i].strip())
        i += 1

        img_path = os.path.join(image_dir, img_rel)

        if not os.path.exists(img_path):
            print(f"  [SKIP] missing: {img_path}")
            i += max(1, num_faces)
            continue

        img = cv2.imread(img_path)
        if img is None:
            print(f"  [SKIP] unreadable: {img_path}")
            i += max(1, num_faces)
            continue

        h, w = img.shape[:2]
        label_rel = img_rel.replace(".jpg", ".txt").replace(".jpeg", ".txt")
        label_path = os.path.join(label_dir, label_rel)
        os.makedirs(os.path.dirname(label_path), exist_ok=True)

        annotations = []

        if num_faces == 0:
            i += 1  # skip "0 0 0 0 0 0 0 0 0 0" dummy line
        else:
            for _ in range(num_faces):
                parts = lines[i].split()
                i += 1
                x, y, bw, bh = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])

                if bw <= 0 or bh <= 0:
                    continue

                # WIDER FACE → YOLO normalised centre format
                xc = (x + bw / 2) / w
                yc = (y + bh / 2) / h
                nw = bw / w
                nh = bh / h

                # Clamp to [0,1]
                xc = max(0.0, min(1.0, xc))
                yc = max(0.0, min(1.0, yc))
                nw = max(0.0, min(1.0, nw))
                nh = max(0.0, min(1.0, nh))

                annotations.append(f"0 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}")
                total_faces += 1

        with open(label_path, "w") as lf:
            lf.write("\n".join(annotations))

        total_images += 1

    return total_images, total_faces


def copy_images(image_dir: str, out_image_dir: str, ann_file: str):
    """Copy referenced images to dataset/split/images."""
    os.makedirs(out_image_dir, exist_ok=True)
    with open(ann_file) as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        img_rel = lines[i].strip()
        i += 1
        num_faces = int(lines[i].strip())
        i += max(1, num_faces) + 1

        src = os.path.join(image_dir, img_rel)
        dst = os.path.join(out_image_dir, img_rel)
        if os.path.exists(src) and not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)


def main():
    parser = argparse.ArgumentParser(description="WIDER FACE → YOLO converter")
    parser.add_argument("--split", choices=["train", "val", "both"], default="both")
    parser.add_argument("--root", default="WIDERFACE", help="Path to WIDERFACE directory")
    parser.add_argument("--out", default="dataset", help="Output dataset directory")
    parser.add_argument("--copy-images", action="store_true", help="Copy images to output dir")
    args = parser.parse_args()

    splits = ["train", "val"] if args.split == "both" else [args.split]

    for split in splits:
        print(f"\n=== Processing {split} ===")
        ann_map = {"train": "wider_face_train_bbx_gt.txt", "val": "wider_face_val_bbx_gt.txt"}
        img_map = {"train": "WIDER_train/images",          "val": "WIDER_val/images"}

        ann_file  = os.path.join(args.root, "wider_face_split", ann_map[split])
        image_dir = os.path.join(args.root, img_map[split])
        label_dir = os.path.join(args.out, split, "labels")

        if not os.path.exists(ann_file):
            print(f"  Annotation file not found: {ann_file}")
            continue

        n_imgs, n_faces = convert(ann_file, image_dir, label_dir)
        print(f"  Converted {n_imgs} images, {n_faces} faces → {label_dir}")

        if args.copy_images:
            out_img_dir = os.path.join(args.out, split, "images")
            copy_images(image_dir, out_img_dir, ann_file)
            print(f"  Images copied to {out_img_dir}")

    print("\nDone.")


if __name__ == "__main__":
    main()
