import os
from pathlib import Path
from PIL import Image
import imagehash
import pandas as pd
from tqdm import tqdm

# =========================
# SETTINGS
# =========================

# Change this to your dataset folder
DATASET_DIR = r"/home/ezz-mahdy/gitRepos/CV-Model-0/dataSetTunning/DS"

# Similarity threshold
# 0 = identical
# Higher = more different images are considered duplicates
HASH_DISTANCE = 5

# Output CSV
OUTPUT_CSV = "duplicate_images.csv"


# =========================
# FIND IMAGES
# =========================

extensions = {
    ".jpg", ".jpeg", ".png",
    ".bmp", ".webp", ".tif", ".tiff"
}

image_paths = [
    p for p in Path(DATASET_DIR).rglob("*")
    if p.suffix.lower() in extensions
]

print(f"Found {len(image_paths)} images.")


# =========================
# CALCULATE PERCEPTUAL HASH
# =========================

hashes = {}

print("Calculating image hashes...")

for path in tqdm(image_paths):
    try:
        with Image.open(path) as img:
            # Convert to RGB to avoid problems with RGBA/grayscale images
            img = img.convert("RGB")

            # Perceptual hash
            img_hash = imagehash.phash(img)

            hashes[path] = img_hash

    except Exception as e:
        print(f"Could not process {path}: {e}")


# =========================
# FIND DUPLICATES
# =========================

print("Searching for duplicate images...")

duplicates = []

paths = list(hashes.keys())

for i in tqdm(range(len(paths))):
    for j in range(i + 1, len(paths)):

        path1 = paths[i]
        path2 = paths[j]

        distance = hashes[path1] - hashes[path2]

        if distance <= HASH_DISTANCE:

            duplicates.append({
                "image_1": str(path1),
                "image_2": str(path2),
                "hash_distance": distance
            })


# =========================
# SAVE RESULTS
# =========================

df = pd.DataFrame(duplicates)

if len(df) > 0:
    df = df.sort_values("hash_distance")
    df.to_csv(OUTPUT_CSV, index=False)

    print("\nDuplicates found!")
    print(f"Number of duplicate pairs: {len(df)}")
    print(f"Results saved to: {OUTPUT_CSV}")

else:
    print("\nNo duplicate images found.")