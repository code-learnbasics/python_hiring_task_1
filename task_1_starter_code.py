import os
import argparse
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.utils import ImageReader
import math

'''In the code below , I used Simple rectangle algorithm and shelf packing algorithm to pack images in pages
I also made a function for command line interface '''
INPUT_DIR = "input_images"
OUTPUT_PDF = "output.pdf"
PAGE_SIZE = A4  # width, height in points (1 pt = 1/72 inch) 

class RectanglePacker:
    """ This class Implements a simple rectangle packing algorithm"""
    
    def __init__(self, page_width, page_height, padding=10):
        self.page_width = page_width
        self.page_height = page_height
        self.padding = padding
        self.pages = []
        self.current_page = []
        self.current_y = 0
        self.current_row_height = 0
        self.current_x = 0
        
    def pack_images(self, images_data):
        """Pack images into pages using a simple shelf packing algorithm"""
        # Sort images by height (tallest first) for better packing
        images_data.sort(key=lambda x: x['height'], reverse=True)
        
        for img_data in images_data:
            self._place_image(img_data)
            
        # Add the last page if it has images
        if self.current_page:
            self.pages.append(self.current_page)
            
        return self.pages
    
    def _place_image(self, img_data):
        """Place a single image on the current page"""
        img_width = img_data['width'] + self.padding
        img_height = img_data['height'] + self.padding
        
        # If image is wider than page, scale it down
        if img_width > self.page_width:
            scale_factor = self.page_width / img_width
            img_width = self.page_width
            img_height *= scale_factor
            img_data['width'] = self.page_width - self.padding
            img_data['height'] = img_height - self.padding
            img_data['scaled'] = True
        
        # Check if we need a new page
        if not self.current_page or self.current_y + img_height > self.page_height:
            if self.current_page:
                self.pages.append(self.current_page)
            self.current_page = []
            self.current_y = 0
            self.current_x = 0
            self.current_row_height = 0
        
        # Check if image fits in current row
        if self.current_x + img_width <= self.page_width:
           
            x_pos = self.current_x
            y_pos = self.current_y
        else:
           
            self.current_y += self.current_row_height
            self.current_x = 0
            self.current_row_height = 0
            x_pos = 0
            y_pos = self.current_y
            
            
            if y_pos + img_height > self.page_height:
                if self.current_page:
                    self.pages.append(self.current_page)
                self.current_page = []
                self.current_y = 0
                self.current_x = 0
                x_pos = 0
                y_pos = 0
        
        # Update positions
        self.current_x = x_pos + img_width
        self.current_row_height = max(self.current_row_height, img_height)
        
        # Add image to current page
        img_data['x'] = x_pos + self.padding / 2
        img_data['y'] = y_pos + self.padding / 2
        self.current_page.append(img_data)

def preprocess_image(image_path: str):
  
    image = Image.open(image_path)
    
    # Convert RGBA to RGB if image has transparency
    if image.mode in ('RGBA', 'LA'):
        # Create a white background
        background = Image.new('RGB', image.size, (255, 255, 255))
        
        # If image has alpha channel, composite with white background
        if image.mode == 'RGBA':
            background.paste(image, mask=image.split()[-1])
            image = background
        else:
            image = image.convert('RGB')
    

    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)
    
    return image

def compress_images(input_image_path: str, output_image_path: str, compression_level: int=5):
    """Compress images to minimize PDF size

    Args:
        input_image_path (str): The path of the input image
        output_image_path (str): The path to save the compressed image
        compression_level (int) default 5: The compression level Ex: 0-9 where 0 is no compression and 9 is maximum compression

    Returns:
        str: The path of the compressed image
    """
    image = Image.open(input_image_path)
    
    # Calculate quality based on compression level (0-100 scale)
    quality = max(10, 100 - (compression_level * 10))
    
    # Convert to RGB if necessary for JPEG compression
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Save with compression
    image.save(output_image_path, 'JPEG', quality=quality, optimize=True)
    
    return output_image_path

def generate_pdf(input_dir: str, output_pdf_path: str, page_size, compression_level: int = 5):
    """Main function to generate the PDF with optimally packed images

    Args:
        input_dir (str): The input directory containing the images
        output_pdf_path (str): The path to save the generated PDF
        page_size: The page size of the PDF (A4, Letter, etc.)
        compression_level (int): Compression level for images
    """
    
    # Get all image files from input directory
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}
    image_files = []
    
    for file in os.listdir(input_dir):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            image_files.append(os.path.join(input_dir, file))
    
    if not image_files:
        print("No images found in the input directory!")
        return
    
    print(f"Found {len(image_files)} images to process...")
    
    # Preprocess and collect image data
    images_data = []
    temp_dir = "temp_compressed"
    os.makedirs(temp_dir, exist_ok=True)
    
    for i, image_path in enumerate(image_files):
        try:
            # Preprocess image
            processed_image = preprocess_image(image_path)
            
            # Compress image
            temp_path = os.path.join(temp_dir, f"compressed_{i}.jpg")
            processed_image.save(temp_path, 'JPEG', quality=85, optimize=True)
            
            # Get image dimensions (convert to points: 1 inch = 72 points)
            width_pts = processed_image.width * 72 / 200  # Approximate scaling
            height_pts = processed_image.height * 72 / 200
            
            images_data.append({
                'path': temp_path,
                'width': width_pts,
                'height': height_pts,
                'original_path': image_path
            })
            
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
    
    # Pack images using rectangle packing algorithm
    packer = RectanglePacker(page_size[0], page_size[1])
    pages = packer.pack_images(images_data)
    
    # Generate PDF
    c = canvas.Canvas(output_pdf_path, pagesize=page_size)
    
    for page_num, page_images in enumerate(pages):
        print(f"Generating page {page_num + 1} with {len(page_images)} images...")
        
        for img_data in page_images:
            try:
                # Draw image on PDF
                c.drawImage(
                    img_data['path'],
                    img_data['x'],
                    page_size[1] - img_data['y'] - img_data['height'],  # PDF coordinates start from bottom
                    width=img_data['width'],
                    height=img_data['height']
                )
            except Exception as e:
                print(f"Error drawing image {img_data['original_path']}: {e}")
        
        # Add page number
        c.setFont("Helvetica", 10)
        c.drawString(30, 30, f"Page {page_num + 1}")
        
        # Create new page if there are more images
        if page_num < len(pages) - 1:
            c.showPage()
    
    c.save()
    print(f"PDF generated successfully: {output_pdf_path}")
    
    # Clean up temporary files
    try:
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)
    except:
        print("Note: Could not clean up temporary files")

def main():
    """Command line interface for the PDF generator"""
    parser = argparse.ArgumentParser(description='Pack images into PDF efficiently')
    parser.add_argument('--input', '-i', default=INPUT_DIR, help='Input directory containing images')
    parser.add_argument('--output', '-o', default=OUTPUT_PDF, help='Output PDF file path')
    parser.add_argument('--page-size', '-p', choices=['A4', 'letter'], default='A4', help='Page size')
    parser.add_argument('--compression', '-c', type=int, default=5, help='Compression level (0-9)')
    
    args = parser.parse_args()
    
    # Set page size
    page_size = A4 if args.page_size == 'A4' else letter
    
    # Validate compression level
    compression_level = max(0, min(9, args.compression))
    
    print(f"Generating PDF with:")
    print(f"  Input directory: {args.input}")
    print(f"  Output file: {args.output}")
    print(f"  Page size: {args.page_size}")
    print(f"  Compression level: {compression_level}")
    
    generate_pdf(args.input, args.output, page_size, compression_level)

if __name__ == "__main__":
    # Run as command line interface or with default values
    import sys
    if len(sys.argv) > 1:
        main()
    else:
        print("Running with default parameters...")
        generate_pdf(INPUT_DIR, OUTPUT_PDF, PAGE_SIZE)