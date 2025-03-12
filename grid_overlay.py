#!/usr/bin/env python3
"""
Grid Overlay Module for Android Screenshots

This module provides functionality to add a numbered grid overlay on screenshots
to help identify specific touch areas on an Android device screen.
"""

from PIL import Image, ImageDraw, ImageFont
import os
import math

class GridOverlay:
    """
    A class to overlay a numbered grid on screenshots based on average adult finger touch size.
    
    The class adds a semi-transparent grid with numbered cells to help identify
    specific areas on a screenshot for reference or automation purposes.
    """
    
    def __init__(self, finger_touch_size_mm=7, ppi=405, screen_resolution=(1080, 2400)):
        """
        Initialize the GridOverlay class.
        
        Args:
            finger_touch_size_mm (int): Average finger touch size in millimeters.
                                        Default is 9mm (typical adult finger touch).
            ppi (int): Pixels per inch of the target device. Default is 405 PPI.
            screen_resolution (tuple): Screen resolution as (width, height) in pixels.
                                      Default is (2400, 1080).
        """
        # Standard conversion: 1 inch = 25.4 mm
        self.ppi = ppi
        self.screen_resolution = screen_resolution
        
        # Convert mm to pixels based on PPI
        self.finger_size_pixels = int((finger_touch_size_mm / 25.4) * self.ppi)
        
        # Grid line properties
        self.grid_color = (255, 0, 0, 100)  # Less opaque red
        self.grid_line_width = 1
        
        # Grid number properties
        self.font_size = int(self.finger_size_pixels / 3)  # Adjust based on grid size
        self.font_color = (0, 0, 255, 150)  # Less bright blue
        
        # Background overlay properties
        self.overlay_color = (255, 255, 255, 60)  # White with much lower opacity (60/255)
        
    def set_ppi(self, ppi):
        """
        Set the PPI value and recalculate the finger size in pixels.
        
        Args:
            ppi (int): Pixels per inch value of the target device.
        """
        self.ppi = ppi
        self.finger_size_pixels = int((9 / 25.4) * self.ppi)
        self.font_size = int(self.finger_size_pixels / 3)
        
    def set_screen_resolution(self, width, height):
        """
        Set the screen resolution of the target device.
        
        Args:
            width (int): Screen width in pixels.
            height (int): Screen height in pixels.
        """
        self.screen_resolution = (width, height)
        
    def apply_grid_to_image(self, image_path, output_path=None):
        """
        Apply a numbered grid overlay to the provided screenshot.
        
        Args:
            image_path (str): Path to the input screenshot image.
            output_path (str, optional): Path to save the output image.
                If not provided, will save with '_grid' suffix.
                
        Returns:
            str: Path to the saved output image.
        """
        # If output path is not specified, create one
        if output_path is None:
            base_name, ext = os.path.splitext(image_path)
            output_path = f"{base_name}_grid{ext}"
            
        # Open the image
        img = Image.open(image_path)
        
        # Convert image to RGBA if it's not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create a semi-transparent white overlay
        background_overlay = Image.new('RGBA', img.size, self.overlay_color)
        
        # Composite the background overlay onto the original image
        img_with_overlay = Image.alpha_composite(img, background_overlay)
        
        # Create a transparent overlay for drawing the grid and numbers
        grid_overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(grid_overlay)
        
        # Calculate grid dimensions
        width, height = img.size
        cols = math.ceil(width / self.finger_size_pixels)
        rows = math.ceil(height / self.finger_size_pixels)
        
        # Try to load a font, fall back to default if not available
        try:
            font = ImageFont.truetype("Arial", self.font_size)
        except IOError:
            font = ImageFont.load_default()
        
        # Draw vertical lines
        for i in range(cols + 1):
            x = i * self.finger_size_pixels
            draw.line([(x, 0), (x, height)], fill=self.grid_color, width=self.grid_line_width)
            
        # Draw horizontal lines
        for i in range(rows + 1):
            y = i * self.finger_size_pixels
            draw.line([(0, y), (width, y)], fill=self.grid_color, width=self.grid_line_width)
            
        # Add numbers to grid cells
        cell_number = 1
        for row in range(rows):
            for col in range(cols):
                x = col * self.finger_size_pixels + 5  # Offset from corner
                y = row * self.finger_size_pixels + 5  # Offset from corner
                
                # Draw the cell number
                draw.text((x, y), str(cell_number), font=font, fill=self.font_color)
                cell_number += 1
        
        # Composite the grid overlay onto the image with background overlay
        result = Image.alpha_composite(img_with_overlay, grid_overlay)
        
        # Save the result
        if result.mode == 'RGBA' and output_path.lower().endswith('.jpg'):
            # Convert to RGB for JPG (which doesn't support alpha)
            result = result.convert('RGB')
        
        result.save(output_path)
        
        return output_path

    def apply_grid_to_multiple_images(self, image_directory, pattern='*.png', output_dir=None):
        """
        Apply grid overlay to multiple images in a directory.
        
        Args:
            image_directory (str): Directory containing images.
            pattern (str): Glob pattern to match image files.
            output_dir (str, optional): Directory to save output images.
                If not provided, images will be saved in the same directory with '_grid' suffix.
                
        Returns:
            list: Paths to all processed images.
        """
        import glob
        
        # Find all matching images
        image_paths = glob.glob(os.path.join(image_directory, pattern))
        processed_paths = []
        
        for image_path in image_paths:
            if output_dir:
                base_name = os.path.basename(image_path)
                output_path = os.path.join(output_dir, f"{os.path.splitext(base_name)[0]}_grid{os.path.splitext(base_name)[1]}")
            else:
                output_path = None
                
            processed_path = self.apply_grid_to_image(image_path, output_path)
            processed_paths.append(processed_path)
            
        return processed_paths

    def get_coordinates_for_grid(self, grid_number, image_width=None, image_height=None):
        """
        Calculate the center coordinates (x, y) for a given grid number based on image/screen dimensions.
        
        Args:
            grid_number (int): The grid cell number (starting from 1).
            image_width (int, optional): Width of the target image/screen in pixels.
                If None, uses self.screen_resolution[0].
            image_height (int, optional): Height of the target image/screen in pixels.
                If None, uses self.screen_resolution[1].
            
        Returns:
            tuple: (x, y) coordinates of the center of the grid cell.
            
        Raises:
            ValueError: If grid_number is out of valid range for the given dimensions.
        """
        # Use screen resolution if image dimensions not provided
        if image_width is None:
            image_width = self.screen_resolution[0]
        if image_height is None:
            image_height = self.screen_resolution[1]
                
        cols = math.ceil(image_width / self.finger_size_pixels)
        rows = math.ceil(image_height / self.finger_size_pixels)
        total_cells = cols * rows

        if grid_number < 1 or grid_number > total_cells:
            raise ValueError(f"Grid number must be between 1 and {total_cells}")

        # Calculate row and column indices (0-based)
        row = (grid_number - 1) // cols
        col = (grid_number - 1) % cols

        # Calculate cell boundaries
        x_start = col * self.finger_size_pixels
        y_start = row * self.finger_size_pixels

        # Adjust end positions to not exceed image dimensions
        x_end = min(x_start + self.finger_size_pixels, image_width)
        y_end = min(y_start + self.finger_size_pixels, image_height)

        # Calculate center coordinates
        x_center = (x_start + x_end) // 2
        y_center = (y_start + y_end) // 2

        return (x_center, y_center)

    def get_grid_map(self, image_width=None, image_height=None):
        """
        Generate a mapping of all grid numbers to their center coordinates.
        
        Args:
            image_width (int, optional): Width of the target image/screen in pixels.
                If None, uses self.screen_resolution[0].
            image_height (int, optional): Height of the target image/screen in pixels.
                If None, uses self.screen_resolution[1].
            
        Returns:
            dict: Mapping of grid numbers to (x, y) coordinates.
        """
        # Use screen resolution if image dimensions not provided
        if image_width is None:
            image_width = self.screen_resolution[0]
        if image_height is None:
            image_height = self.screen_resolution[1]
                
        cols = math.ceil(image_width / self.finger_size_pixels)
        rows = math.ceil(image_height / self.finger_size_pixels)
        total_cells = cols * rows
        
        grid_map = {}
        for grid_num in range(1, total_cells + 1):
            grid_map[grid_num] = self.get_coordinates_for_grid(grid_num, image_width, image_height)
            
        return grid_map


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        # Create a grid overlay with default settings for a modern Android device (405 PPI)
        grid = GridOverlay(ppi=405, screen_resolution=(1080, 2400))
        output_path = grid.apply_grid_to_image(image_path)
        print(f"Grid overlay applied. Output saved to: {output_path}")
        
        # Example of getting coordinates for grid number 42
        try:
            x, y = grid.get_coordinates_for_grid(77)
            print(f"Coordinates for grid #77: ({x}, {y})")
        except ValueError as e:
            print(f"Note: {e}")
    else:
        print("Please provide an image path. Usage: python grid_overlay.py <image_path>")
