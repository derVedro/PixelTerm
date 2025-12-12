#!/usr/bin/env python3
"""
PixelTerm Image Display Module
Uses chafa command line tool to display images in terminal
"""

import os
import subprocess
import sys
from typing import Optional, Tuple
from pathlib import Path
from PIL import Image
from chafa_wrapper import ChafaWrapper


class ImageViewer:
    """Terminal image viewer"""
    
    def __init__(self, width: int = 80, height: int = 24):
        self.width = width
        self.height = height
        from constants import SUPPORTED_FORMATS
        self.supported_formats = SUPPORTED_FORMATS
    
    def get_terminal_size(self) -> Tuple[int, int]:
        """Get terminal size"""
        try:
            import shutil
            size = shutil.get_terminal_size()
            return size.columns, size.lines
        except:
            return 80, 24
    
    
    
    def is_image_file(self, filepath: str) -> bool:
        """Check if file is supported image format"""
        _, ext = os.path.splitext(filepath.lower())
        return ext in self.supported_formats
    
    
    
    def display_image(self, filepath: str, scale: float = 1.0, file_browser=None) -> bool:
        """Display image using chafa"""
        try:
            # Try to use pre-rendered data
            rendered_output = None
            if file_browser:
                rendered_output = file_browser.get_rendered_image(Path(filepath))
            
            if rendered_output:
                # Use pre-rendered data, output directly
                print(rendered_output, end='')
                return True
            
            # If no pre-rendered data, use ChafaWrapper for real-time rendering
            rendered = ChafaWrapper.render_image(filepath, scale)
            if rendered:
                print(rendered, end='')
                return True
            
            return False
                
        except Exception:
            return False
    
    def clear_display_area(self):
        """Clear current display area"""
        term_width, term_height = self.get_terminal_size()
        # Move cursor to top-left corner
        print('\033[H', end='', flush=True)
        # Clear entire screen
        print('\033[2J', end='', flush=True)
        # Flush output immediately to ensure clear command takes effect
        sys.stdout.flush()
    
    def display_filename(self, filepath: str):
        """Display filename centered below image"""
        try:
            # Get terminal width
            term_width, _ = self.get_terminal_size()
            
            # Get filename (without path)
            filename = Path(filepath).name
            
            # Calculate center position
            filename_len = len(filename)
            if filename_len < term_width:
                # 计算左边距以居中显示
                left_padding = (term_width - filename_len) // 2
                centered_filename = ' ' * left_padding + filename
            else:
                # If filename is too long, truncate and add ellipsis
                max_len = term_width - 3  # 留出省略号的空间
                if max_len > 0:
                    centered_filename = filename[:max_len] + '...'
                else:
                    centered_filename = '...'
            
            # Move to bottom of terminal (second to last line)
            print(f'\033[{self.get_terminal_size()[1]-1};1H', end='')
            
            # Clear line and display filename
            print('\033[K', end='')  # 清除当前行
            print(f'\033[36m{centered_filename}\033[0m', end='')  # Display filename in cyan
            
            # Flush output immediately
            sys.stdout.flush()
        except Exception:
            # If filename display fails, ignore silently
            pass
    
    def display_image_with_info(self, filepath: str, scale: float = 1.0, clear_first: bool = True, file_browser=None) -> bool:
        """Display image"""
        if clear_first:
            # Clear display area
            self.clear_display_area()
        print('\033[?25l', end='')  # Hide cursor
        
        # Display image
        result = self.display_image(filepath, scale, file_browser)
        
        # Display filename centered below image
        if result:
            self.display_filename(filepath)
        
        # Show cursor after display
        print('\033[?25h', end='', flush=True)  # Show cursor
        
        return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python image_viewer.py <image_path>")
        sys.exit(1)
    
    viewer = ImageViewer()
    viewer.display_image_with_info(sys.argv[1])