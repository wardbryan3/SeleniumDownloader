"""
Shared constants for download handling
"""

ALLOWED_EXTENSIONS = {'.zip', '.mp3', '.wav', '.pdf', '.rar', '.7z', '.tar', '.gz'}

EXCLUDED_EXTENSIONS = {'.part', '.crdownload', '.tmp', '.download', '.xpi', '.so', '.lock'}

# macOS Finder metadata files (._AppleDouble, .DS_Store variants)
EXCLUDED_PREFIXES = {'.fea', '.X'}
