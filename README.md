This project implements a Python program to arrange a set of images of random sizes and shapes into a PDF, minimizing total space while preserving each image's original aspect ratio.

## Features

- Automatically crops images to visible content by removing transparent borders
- Packs images optimally on fixed-size PDF pages (A4)
- Preserves aspect ratio and scales images to fit pages
- Generates a multi-page PDF output containing all packed images

## Requirements

- Python 3.7 or above
- Dependencies listed in `requirements.txt`:
  - Pillow
  - reportlab

## Installation

1. Clone this repository.
2. Create a virtual environment
3. Activate the environment and install dependencies
 
 ## Usage

1. Place your images (PNG, JPEG) in the `input_images/` folder. You can generate sample images using:
2. Run the packing script:
3. The packed output PDF will be generated as `output.pdf

## How It Works

- Loads and crops images to their visible bounding box to reduce wasted space
- Uses a simple shelf-based packing algorithm sorting images by height
- Each image is resized proportionally to fit within the A4 page dimensions, with padding between images
- Images are placed row-by-row; new pages are created as needed
- PDF is generated using the `reportlab` library with precise image placement.

