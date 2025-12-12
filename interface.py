#!/usr/bin/env python3
"""
PixelTerm 用户界面模块
处理键盘输入和用户交互
"""

import os
import sys
import termios
import tty
from contextlib import contextmanager
from typing import Optional, Callable


class Interface:
    """终端用户界面"""
    
    def __init__(self):
        self.old_settings = None
        self.help_text = """
🖼️  PixelTerm - Terminal Image Viewer

📋 Shortcuts:
  ←/→     Previous/Next image
  a/d     Alternative left/right keys
  i       Show/hide image information
  r       Delete current image
  q       Quit program
  Ctrl+C  Force exit
        """
    
    def setup_terminal(self):
        """Setup terminal in raw mode"""
        try:
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
        except:
            # If unable to setup terminal mode, use normal input
            pass
    
    def restore_terminal(self):
        """恢复终端设置"""
        if self.old_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            except:
                pass
    
    
    
    def get_key(self) -> Optional[str]:
        """获取键盘输入"""
        try:
            if self.old_settings:
                # 原始模式 - 无超时，直接等待
                return sys.stdin.read(1)
            else:
                # 普通模式
                return input().strip()
        except:
            return None
    
    
    
    
    
    
    
    
    
    @contextmanager
    def _terminal_mode_switch(self):
        """终端模式切换上下文管理器"""
        temp_settings = self.old_settings
        try:
            if self.old_settings:
                self.restore_terminal()
            yield
        finally:
            if temp_settings:
                try:
                    self.old_settings = temp_settings
                    tty.setraw(sys.stdin.fileno())
                except:
                    self.old_settings = None
    
    def show_image_info(self, image_path, total_count: int, current_index: int):
        """Show detailed image information"""
        import os
        from PIL import Image
        
        with self._terminal_mode_switch():
            try:
                print(f"\n{'='*60}")
                print(f"📸 Image Details")
                print(f"{'='*60}")
                
                # Basic information
                print(f"📁 Filename: {image_path.name}")
                print(f"📂 Path: {image_path.parent}")
                print(f"📄 Index: {current_index + 1}/{total_count}")
                
                # File size
                file_size = os.path.getsize(image_path)
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                elif file_size < 1024 * 1024 * 1024:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                else:
                    size_str = f"{file_size / (1024 * 1024 * 1024):.1f} GB"
                print(f"💾 File size: {size_str}")
                
                # Image dimensions and format information
                try:
                    with Image.open(image_path) as img:
                        width, height = img.size
                        print(f"📐 Dimensions: {width} x {height} pixels")
                        print(f"🎨 Format: {img.format}")
                        print(f"🎭 Color mode: {img.mode}")
                        
                        # Calculate aspect ratio
                        if height > 0:
                            aspect_ratio = width / height
                            print(f"📏 Aspect ratio: {aspect_ratio:.2f}")
                        
                        # If EXIF information exists, display basic info
                        if hasattr(img, '_getexif') and img._getexif():
                            exif = img._getexif()
                            if exif:
                                print(f"📷 Contains EXIF information")
                except Exception as e:
                    print(f"❌ Unable to read image information: {e}")
                
                print(f"{'='*60}")
                
            except Exception as e:
                print(f"\n❌ Error displaying information: {e}")
    
    def show_directory_list(self, directories: list):
        """Show directory list"""
        if not directories:
            print("\n📁 No subdirectories in current directory")
            return
        
        print("\n📁 Subdirectory list:")
        for i, dirname in enumerate(directories):
            print(f"  {i+1}. {dirname}")
        print("\nEnter directory name to enter, or press Esc to cancel:")
    
    def prompt_directory(self) -> Optional[str]:
        """Prompt for directory name"""
        with self._terminal_mode_switch():
            try:
                dirname = input("Enter directory name: ").strip()
                return dirname if dirname else None
            except:
                return None
    
    
    
    def show_error(self, message: str):
        """Show error message"""
        with self._terminal_mode_switch():
            try:
                print(f"\n❌ Error: {message}")
                input("Press any key to continue...")
            except:
                pass
    
    def show_info(self, message: str):
        """Show info message"""
        with self._terminal_mode_switch():
            try:
                print(f"\nℹ️  {message}")
                input("Press any key to continue...")
            except:
                pass


class InputHandler:
    """输入处理器"""
    
    def __init__(self, interface: Interface):
        self.interface = interface
        self.handlers = {}
        self.running = True
    
    def register_handler(self, key: str, handler: Callable):
        """注册按键处理函数"""
        self.handlers[key] = handler
    
    def handle_input(self, key: str) -> bool:
        """处理输入"""
        if key in self.handlers:
            return self.handlers[key]()
        return False
    
    def stop(self):
        """停止处理循环"""
        self.running = False


if __name__ == "__main__":
    interface = Interface()
    interface.setup_terminal()
    
    try:
        print(interface.help_text)
    finally:
        interface.restore_terminal()