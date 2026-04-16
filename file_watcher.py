# [file name]: file_watcher.py (new file)
"""
Simple file system watcher for download detection
"""

import os
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

class DownloadHandler(FileSystemEventHandler):
    """Handle file system events for downloads"""
    
    def __init__(self, download_dir, callback):
        self.download_dir = download_dir
        self.callback = callback
        self.files_created = set()
    
    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            logger.debug(f"File created: {os.path.basename(file_path)}")
            self.files_created.add(file_path)
            
            # Check if this is a completed file (not temporary)
            if not any(file_path.endswith(ext) for ext in ['.part', '.crdownload', '.tmp']):
                # Call the callback with the file path
                self.callback(file_path)

def watch_for_download(download_dir, timeout=30):
    """Watch for file creation events and return the downloaded file"""
    import threading
    from queue import Queue
    
    result_queue = Queue()
    
    def download_callback(file_path):
        result_queue.put(file_path)
    
    event_handler = DownloadHandler(download_dir, download_callback)
    observer = Observer()
    observer.schedule(event_handler, download_dir, recursive=False)
    observer.start()
    
    try:
        # Wait for the result
        result = result_queue.get(timeout=timeout)
        observer.stop()
        return result
    except:
        observer.stop()
        return None
    finally:
        observer.join()