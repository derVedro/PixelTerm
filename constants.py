#!/usr/bin/env python3
"""
PixelTerm Constants Definition
"""

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}

# Preload configuration
DEFAULT_PRELOAD_SIZE = 10
PRELOAD_SLEEP_TIME = 0.05

# Chafa command configuration
CHAFA_CMD = 'chafa'
DEFAULT_CHAFA_ARGS = [
    '--color-space', 'rgb',
    '--dither', 'none',
    '--relative', 'off',
    '--optimize', '9',
    '--margin-right', '0',
    '--work', '9'
]

# Display configuration
DEFAULT_SCALE = 1.0
SCALE_STEP = 0.1
MIN_SCALE = 0.1
MAX_SCALE = 3.0

# Keyboard controls
KEY_LEFT = '\x1b[D'
KEY_RIGHT = '\x1b[C'
KEY_LEFT_ALT = '\x1bOD'
KEY_RIGHT_ALT = '\x1bOC'
KEY_CTRL_C = '\x03'

# Error messages
ERR_CHAFA_NOT_FOUND = "Error: chafa command not found"
ERR_CHAFA_INSTALL_HINT = "Please install chafa: brew install chafa (macOS) or sudo apt-get install chafa (Ubuntu)"
ERR_PATH_NOT_EXISTS = "Error: Path does not exist"
ERR_NOT_DIRECTORY = "Error: Not a directory"
ERR_NOT_FILE = "Error: Not a file"
ERR_UNSUPPORTED_FORMAT = "Error: Unsupported image format"