"""
Audio Download Manager - Main Entry Point
Downloads shows for a radio station

Usage:
    python main.py              - Run GUI
    python main.py --download-all - Run downloads in CLI mode (no GUI)
    python main.py --source "Melinda Myers" - Download from specific source
"""

import os
import sys
import logging
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_logging(log_to_file=True):
    """Configure logging for the application"""
    logger = logging.getLogger("audio_downloader")
    logger.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    if log_to_file:
        file_handler = logging.FileHandler("audio_downloader.log")
        file_handler.setLevel(logging.DEBUG)
        
        for module in ['sources', 'sources.base', 'browser_manager', 'download_utils']:
            mod_logger = logging.getLogger(module)
            mod_logger.setLevel(logging.DEBUG)
            mod_logger.addHandler(file_handler)
        
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    console_format = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    return logger

def run_cli_downloads():
    """Run downloads in CLI mode without GUI"""
    from config import ConfigManager, DOWNLOAD_SOURCES
    from browser_manager import BrowserManager
    from sources import create_downloader
    
    logger = logging.getLogger("audio_downloader")
    logger.info("=" * 50)
    logger.info("AUDIO DOWNLOAD MANAGER - CLI MODE")
    logger.info("=" * 50)
    
    config = ConfigManager()
    logger.info(f"Test mode: {config.is_test_mode()}")
    logger.info(f"Output directory: {config.get_output_base_dir()}")
    logger.info(f"Browser download dir: {config.get_browser_download_dir()}")
    logger.info("")
    
    config.ensure_folders()
    config.clear_browser_download_dir()
    logger.info("Cleared browser download directory")
    logger.info("")
    
    results = {}
    
    browser_manager = BrowserManager(config)
    
    try:
        for source_name in DOWNLOAD_SOURCES.keys():
            logger.info("")
            logger.info(f"--- Downloading from: {source_name} ---")
            
            config.clear_browser_download_dir()
            
            downloader = create_downloader(source_name, browser_manager, config)
            
            try:
                success = downloader.download()
                results[source_name] = success
                
                if success:
                    logger.info(f"✓ {source_name}: SUCCESS")
                else:
                    logger.error(f"✗ {source_name}: FAILED")
            except Exception as e:
                logger.error(f"✗ {source_name}: ERROR - {e}")
                results[source_name] = False
    finally:
        browser_manager.close_browser()
    
    logger.info("")
    logger.info("=" * 50)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("=" * 50)
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for source_name, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        logger.info(f"  {source_name}: {status}")
    
    logger.info("")
    logger.info(f"Total: {success_count}/{total_count} successful")
    
    return all(results.values())

def run_single_source(source_name):
    """Download from a single source"""
    from config import ConfigManager, DOWNLOAD_SOURCES
    from browser_manager import BrowserManager
    from sources import create_downloader
    
    logger = logging.getLogger("audio_downloader")
    
    if source_name not in DOWNLOAD_SOURCES:
        logger.error(f"Unknown source: {source_name}")
        logger.info(f"Available sources: {list(DOWNLOAD_SOURCES.keys())}")
        return False
    
    logger.info("=" * 50)
    logger.info(f"DOWNLOADING: {source_name}")
    logger.info("=" * 50)
    
    config = ConfigManager()
    browser_manager = BrowserManager(config)
    downloader = create_downloader(source_name, browser_manager, config)
    
    try:
        success = downloader.download()
        if success:
            logger.info(f"✓ {source_name}: SUCCESS")
        else:
            logger.error(f"✗ {source_name}: FAILED")
        return success
    except Exception as e:
        logger.error(f"✗ {source_name}: ERROR - {e}")
        return False
    finally:
        browser_manager.close_browser()

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(
        description="Audio Download Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                      Run GUI mode
  python main.py --download-all       Download from all sources
  python main.py --source "Melinda Myers"  Download from specific source
        """
    )
    
    parser.add_argument(
        '--download-all',
        action='store_true',
        help='Run downloads for all sources in CLI mode (no GUI)'
    )
    
    parser.add_argument(
        '--source',
        type=str,
        help='Download from a specific source (e.g., "Melinda Myers")'
    )
    
    args = parser.parse_args()
    
    if args.download_all:
        setup_logging()
        logger = logging.getLogger("audio_downloader")
        success = run_cli_downloads()
        sys.exit(0 if success else 1)
    
    elif args.source:
        setup_logging()
        success = run_single_source(args.source)
        sys.exit(0 if success else 1)
    
    else:
        setup_logging(log_to_file=True)
        logger = logging.getLogger("audio_downloader")
        
        try:
            from gui import AudioDownloaderGUI
            
            logger.info("Starting Audio Download Manager (GUI Mode)")
            app = AudioDownloaderGUI()
            app.run()
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            print(f"Fatal error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
