"""
Shared constants for download handling
"""

ALLOWED_EXTENSIONS = {'.zip', '.mp3', '.wav', '.pdf', '.rar', '.7z', '.tar', '.gz'}

EXCLUDED_EXTENSIONS = {'.part', '.crdownload', '.tmp', '.download', '.xpi', '.so', '.lock'}

# Prefixes of system/metadata/temp files to ignore during download detection
EXCLUDED_PREFIXES = {'.fea', '.X'}
