#!/usr/bin/env python3
"""
IntelliSwarm — Export Draw.io Diagrams to High-Resolution PNG
Renders all 23 .drawio files in the current directory into:
  - png/             (300 DPI, solid white background for printing/documents)
  - png_transparent/ (300 DPI, pure black lines/text on transparent background)
"""

import os
import sys
import glob
import subprocess
import shutil
from PIL import Image
import numpy as np

def run_cmd(cmd, desc=None):
    if desc:
        print(desc)
    res = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error: {res.stderr}")
        return False
    return True

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    tmp_pdf = os.path.join(base_dir, "tmp_pdf")
    out_png = os.path.join(base_dir, "png")
    out_trans = os.path.join(base_dir, "png_transparent")

    print("=" * 60)
    print("  IntelliSwarm — Export Draw.io Diagrams to High-Res PNG")
    print("=" * 60)
    print(f"Directory: {base_dir}")

    # 1. Clean & prepare folders
    if os.path.exists(tmp_pdf):
        run_cmd(f"docker run --rm -v '{base_dir}':/data alpine rm -rf /data/tmp_pdf")
    os.makedirs(tmp_pdf, exist_ok=True)
    os.makedirs(out_png, exist_ok=True)
    os.makedirs(out_trans, exist_ok=True)

    # 2. Render all .drawio diagrams to vector PDF using headless Draw.io
    print("\n[Step 1/3] Exporting draw.io diagrams to vector PDF...")
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{base_dir}:/data",
        "rlespinasse/drawio-export",
        "--format", "pdf",
        "--crop",
        "--border", "20",
        "--remove-page-suffix",
        "--output", "tmp_pdf",
        "/data"
    ]
    res = subprocess.run(docker_cmd)
    if res.returncode != 0:
        print("Draw.io export failed!")
        sys.exit(1)

    # 3. Convert PDFs to 300 DPI PNGs (Standard & Transparent)
    print("\n[Step 2/3] Rendering 300 DPI PNGs (Standard & Transparent)...")
    pdf_files = sorted(glob.glob(os.path.join(tmp_pdf, "*.pdf")))
    total = len(pdf_files)
    print(f"Found {total} PDF files.")

    for idx, pdf in enumerate(pdf_files, 1):
        base_name = os.path.splitext(os.path.basename(pdf))[0]
        prefix = os.path.join(out_png, f"tmp_{base_name}")

        # Render PDF to PNG at 300 DPI
        cmd = ["pdftoppm", "-png", "-r", "300", pdf, prefix]
        subprocess.run(cmd, capture_output=True)

        pages = sorted(glob.glob(f"{prefix}*.png"))
        if not pages:
            print(f"Warning: Failed to render {base_name}")
            continue

        # Save standard PNG
        std_png = os.path.join(out_png, f"{base_name}.png")
        shutil.move(pages[0], std_png)
        for extra in pages[1:]:
            os.remove(extra)

        # Generate transparent PNG
        img = Image.open(std_png).convert("RGBA")
        arr = np.array(img, dtype=np.uint8)

        # Grayscale lightness
        gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        alpha = np.clip(255 - gray, 0, 255).astype(np.uint8)

        # Set pure black lines and text with inverted alpha
        arr[:, :, 0] = 0
        arr[:, :, 1] = 0
        arr[:, :, 2] = 0
        arr[:, :, 3] = alpha

        trans_img = Image.fromarray(arr, "RGBA")
        trans_png = os.path.join(out_trans, f"{base_name}.png")
        trans_img.save(trans_png)

        print(f"[{idx:02d}/{total}] {base_name}.png ({img.size[0]}x{img.size[1]} px)")

    # 4. Clean up temporary PDF folder
    print("\n[Step 3/3] Cleaning up temporary files...")
    run_cmd(f"docker run --rm -v '{base_dir}':/data alpine rm -rf /data/tmp_pdf")

    print("\n" + "=" * 60)
    print("  SUCCESS: All PNGs generated!")
    print(f"    - Standard (white bg):    {out_png}/")
    print(f"    - Transparent (clear bg): {out_trans}/")
    print("=" * 60)

if __name__ == "__main__":
    main()
