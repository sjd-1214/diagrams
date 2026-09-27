#!/usr/bin/env python3
import os
import glob
import subprocess
import shutil
from PIL import Image
import numpy as np

def convert_all(pdf_dir, out_png_dir, out_png_trans_dir):
    os.makedirs(out_png_dir, exist_ok=True)
    os.makedirs(out_png_trans_dir, exist_ok=True)

    pdf_files = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))
    print(f"Found {len(pdf_files)} PDF files in {pdf_dir}")

    for idx, pdf in enumerate(pdf_files, 1):
        base_name = os.path.splitext(os.path.basename(pdf))[0]
        temp_prefix = os.path.join(out_png_dir, f"tmp_{base_name}")

        # Render PDF to PNG at 300 DPI (crisp high-resolution vector rasterization)
        cmd = ["pdftoppm", "-png", "-r", "300", pdf, temp_prefix]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Error rendering {pdf}: {res.stderr}")
            continue

        rendered_pages = sorted(glob.glob(f"{temp_prefix}*.png"))
        if not rendered_pages:
            print(f"Warning: No PNG output for {pdf}")
            continue

        primary_png = rendered_pages[0]
        final_png = os.path.join(out_png_dir, f"{base_name}.png")
        shutil.move(primary_png, final_png)

        # Remove any extra pages if multi-page
        for extra in rendered_pages[1:]:
            os.remove(extra)

        # Create transparent version
        img = Image.open(final_png).convert("RGBA")
        arr = np.array(img, dtype=np.uint8)

        # Calculate alpha channel: inverted grayscale lightness
        gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        alpha = np.clip(255 - gray, 0, 255).astype(np.uint8)

        # Set pure black lines and text with calculated alpha
        arr[:, :, 0] = 0
        arr[:, :, 1] = 0
        arr[:, :, 2] = 0
        arr[:, :, 3] = alpha

        trans_img = Image.fromarray(arr, "RGBA")
        final_trans_png = os.path.join(out_png_trans_dir, f"{base_name}.png")
        trans_img.save(final_trans_png)

        print(f"[{idx:02d}/26] Processed {base_name}.png ({img.size[0]}x{img.size[1]} px)")

    print("All diagrams converted successfully!")

if __name__ == "__main__":
    import sys
    pdf_dir = sys.argv[1] if len(sys.argv) > 1 else "/home/theajmalrazaq/Downloads/diagrams-drawio-files/export"
    out_dir = "/home/theajmalrazaq/Downloads/intelliswarm-diagrams-fixed-v2/png"
    out_trans_dir = "/home/theajmalrazaq/Downloads/intelliswarm-diagrams-fixed-v2/png_transparent"
    convert_all(pdf_dir, out_dir, out_trans_dir)
