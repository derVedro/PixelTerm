#!/usr/bin/env python3
"""
PixelTerm File Browser Module
Handles directory browsing and image file management
"""

import os
import sys
import tempfile
import hashlib
import shutil
from typing import List, Optional, Dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from constants import SUPPORTED_FORMATS, DEFAULT_PRELOAD_SIZE, PRELOAD_SLEEP_TIME
from chafa_wrapper import ChafaWrapper


class FileBrowser:
    """File browser"""
    
    def __init__(self):
        self.current_directory = Path.cwd()
        self.image_files: List[Path] = []
        self.current_index = 0
        
        # chafa pre-render cache - keep only current image and one before/after in memory
        self.render_cache: Dict[Path, str] = {}
        self.preload_size = DEFAULT_PRELOAD_SIZE
        self.preload_enabled = True
        
        # Temporary file cache directory
        self.temp_dir = tempfile.mkdtemp(prefix="pixelterm_cache_")
        self.file_cache_range = 10  # Store 10 images before/after to temporary files
        
        # Thread pool for pre-rendering
        self.render_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="chafa_render")
    
    def set_directory(self, directory: str) -> bool:
        """Set current directory"""
        try:
            path = Path(directory).resolve()
            if not path.exists():
                print(f"Error: Path does not exist {directory}")
                return False
            
            if not path.is_dir():
                print(f"Error: Not a directory {directory}")
                return False
            
            self.current_directory = path
            self.refresh_file_list()
            return True
            
        except Exception as e:
            print(f"Error setting directory: {e}")
            return False
    
    def set_image_file(self, filepath: str) -> bool:
        """Set single image file"""
        try:
            path = Path(filepath).resolve()
            if not path.exists():
                print(f"Error: File does not exist {filepath}")
                return False
            
            if not path.is_file():
                print(f"Error: Not a file {filepath}")
                return False
            
            if not self.is_image_file(path):
                print(f"Error: Unsupported image format {filepath}")
                return False
            
            # Set file's directory
            self.current_directory = path.parent
            self.refresh_file_list()
            
            # Find current file index in list
            for i, img_file in enumerate(self.image_files):
                if img_file == path:
                    self.current_index = i
                    return True
            
            # If not found, add to list
            self.image_files.append(path)
            self.image_files.sort()
            for i, img_file in enumerate(self.image_files):
                if img_file == path:
                    self.current_index = i
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error setting image file: {e}")
            return False
    
    def refresh_file_list(self):
        """Refresh current directory's image file list"""
        self.image_files.clear()
        self.render_cache.clear()  # Clear memory cache
        
        # Clear temporary file cache
        self._clear_temp_cache()
        
        try:
            for item in self.current_directory.iterdir():
                if item.is_file() and self.is_image_file(item):
                    self.image_files.append(item)
            
            # Sort by filename
            self.image_files.sort()
            self.current_index = 0
            
            # Start pre-rendering
            self.preload_renders()
            
        except Exception as e:
            print(f"Error reading directory: {e}")
    
    def preload_renders(self):
        """Pre-render images"""
        if not self.image_files or not self.preload_enabled:
            return
        
        # Submit pre-render tasks to thread pool
        self.render_executor.submit(self._render_worker)
    
    
    
    def _render_worker(self):
        """Pre-render worker thread"""
        import time
        try:
            # Pre-render 10 images before/after current to temporary files
            start_idx = max(0, self.current_index - self.file_cache_range)
            end_idx = min(len(self.image_files), self.current_index + self.file_cache_range + 1)
            
            for i in range(start_idx, end_idx):
                if i != self.current_index:  # Skip current image
                    img_path = self.image_files[i]
                    
                    # Check if already cached to temporary file
                    if not self._get_cache_file_path(img_path).exists():
                        try:
                            # Use ChafaWrapper to pre-render
                            rendered = ChafaWrapper.render_image(str(img_path))
                            if rendered:
                                # Save to temporary file
                                self._save_to_temp_cache(img_path, rendered)
                                
                                # If in memory cache range, also save to memory
                                if self._is_in_memory_range(img_path):
                                    self.render_cache[img_path] = rendered
                            
                            time.sleep(PRELOAD_SLEEP_TIME)  # Avoid using too much CPU
                        except Exception:
                            pass  # Ignore failed rendering
            
            # Clear memory cache, keep only current image and one before/after
            self._cleanup_memory_cache()
            
        except Exception:
            pass  # Ignore pre-rendering errors
    
    def _cleanup_memory_cache(self):
        """Clean up memory cache, keep only current image and one before/after"""
        if not self.image_files:
            return
        
        # Find images that should be kept in memory
        to_keep = set()
        start_idx = max(0, self.current_index - 1)
        end_idx = min(len(self.image_files), self.current_index + 2)
        
        for i in range(start_idx, end_idx):
            to_keep.add(self.image_files[i])
        
        # Clean up memory cache not in retention range
        to_remove = []
        for img_path in self.render_cache:
            if img_path not in to_keep:
                to_remove.append(img_path)
        
        for img_path in to_remove:
            del self.render_cache[img_path]
    
    def _get_cache_file_path(self, img_path: Path) -> Path:
        """Get cache file path for image"""
        # Use file path hash as cache filename to avoid long paths and special characters
        path_str = str(img_path.absolute())
        hash_obj = hashlib.md5(path_str.encode())
        cache_filename = f"{hash_obj.hexdigest()}.txt"
        return Path(self.temp_dir) / cache_filename
    
    def _clear_temp_cache(self):
        """Clear temporary file cache"""
        try:
            if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            self.temp_dir = tempfile.mkdtemp(prefix="pixelterm_cache_")
        except Exception:
            pass
    
    def _save_to_temp_cache(self, img_path: Path, rendered_data: str):
        """Save rendered data to temporary file"""
        try:
            cache_file = self._get_cache_file_path(img_path)
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(rendered_data)
        except Exception:
            pass
    
    def _load_from_temp_cache(self, img_path: Path) -> Optional[str]:
        """Load rendered data from temporary file"""
        try:
            cache_file = self._get_cache_file_path(img_path)
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception:
            pass
        return None
    
    def _is_in_memory_range(self, img_path: Path) -> bool:
        """Check if image should be in memory cache range (current and one before/after)"""
        if not self.image_files:
            return False
        
        try:
            img_index = self.image_files.index(img_path)
            return abs(img_index - self.current_index) <= 1
        except ValueError:
            return False
    
    def get_rendered_image(self, img_path: Path) -> Optional[str]:
        """Get pre-rendered image data"""
        # First check memory cache
        if img_path in self.render_cache:
            return self.render_cache[img_path]
        
        # If not in memory cache, try loading from temporary file
        cached_data = self._load_from_temp_cache(img_path)
        if cached_data:
            # If image is in memory cache range, load to memory
            if self._is_in_memory_range(img_path):
                self.render_cache[img_path] = cached_data
            return cached_data
        
        return None
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'render_executor'):
            self.render_executor.shutdown(wait=False)
        
        # Clear temporary file cache
        try:
            if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def is_image_file(self, filepath: Path) -> bool:
        """Check if file is supported image format"""
        return filepath.suffix.lower() in SUPPORTED_FORMATS
    
    def get_image_count(self) -> int:
        """Get current directory image count"""
        return len(self.image_files)
    
    def get_current_image(self) -> Optional[Path]:
        """Get current image path"""
        if 0 <= self.current_index < len(self.image_files):
            return self.image_files[self.current_index]
        return None
    
    def next_image(self) -> bool:
        """Switch to next image"""
        if not self.image_files:
            return False
        
        self.current_index = (self.current_index + 1) % len(self.image_files)
        
        # 更新内存缓存，确保当前图片在内存中
        self._update_memory_cache_on_switch()
        
        # Trigger pre-rendering
        self.preload_renders()
        return True
    
    def previous_image(self) -> bool:
        """Switch to previous image"""
        if not self.image_files:
            return False
        
        self.current_index = (self.current_index - 1) % len(self.image_files)
        
        # 更新内存缓存，确保当前图片在内存中
        self._update_memory_cache_on_switch()
        
        # 触发预渲染
        self.preload_renders()
        return True
    
    def _update_memory_cache_on_switch(self):
        """切换图片时更新内存缓存"""
        if not self.image_files:
            return
        
        # 确保当前图片在内存缓存中
        current_img = self.get_current_image()
        if current_img and current_img not in self.render_cache:
            # 尝试从临时文件加载
            cached_data = self._load_from_temp_cache(current_img)
            if cached_data:
                self.render_cache[current_img] = cached_data
        
        # 清理不在内存范围内的缓存
        self._cleanup_memory_cache()
    
    
    
    
    
    def get_directory_info(self) -> str:
        """Get current directory info"""
        return f"📁 {self.current_directory} ({len(self.image_files)} 张图片)"
    
    
    
    def go_up_directory(self) -> bool:
        """Go up to parent directory"""
        parent = self.current_directory.parent
        if parent != self.current_directory:  # Avoid reaching root directory
            self.current_directory = parent
            self.refresh_file_list()
            return True
        return False
    
    def enter_subdirectory(self, subdir_name: str) -> bool:
        """Enter subdirectory"""
        subdir = self.current_directory / subdir_name
        if subdir.is_dir():
            self.current_directory = subdir
            self.refresh_file_list()
            return True
        return False
    
    def get_subdirectories(self) -> List[str]:
        """Get subdirectories of current directory"""
        subdirs = []
        try:
            for item in self.current_directory.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    subdirs.append(item.name)
            subdirs.sort()
        except Exception:
            pass
        return subdirs


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python file_browser.py <directory_path>")
        sys.exit(1)
    
    browser = FileBrowser()
    if browser.set_directory(sys.argv[1]):
        print(f"Directory: {browser.get_directory_info()}")
    print(f"Image count: {browser.get_image_count()}")
    
    current = browser.get_current_image()
    if current:
        print(f"Current image: {current}")
    else:
        print("Cannot set directory")