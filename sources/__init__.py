"""
Sources package initialization
"""

from .melinda_myers import MelindaMyersDownloader
from .northwest_outdoors import NorthwestOutdoorsDownloader
from .whittler import WhittlerDownloader
from .westwood_one import WestwoodOneDownloader
from .clear_out_west import ClearOutWestDownloader

def create_downloader(source_name: str, browser_manager, config_manager):
    """Factory function to create downloader instances"""
    downloaders = {
        "Melinda Myers": MelindaMyersDownloader,
        "Northwest Outdoors": NorthwestOutdoorsDownloader,
        "Whittler": WhittlerDownloader,
        "Westwood One": WestwoodOneDownloader,
        "Clear Out West": ClearOutWestDownloader
    }
    
    downloader_class = downloaders.get(source_name)
    if downloader_class:
        return downloader_class(browser_manager, config_manager)
    
    raise ValueError(f"Unknown download source: {source_name}")

__all__ = [
    'MelindaMyersDownloader',
    'NorthwestOutdoorsDownloader',
    'WhittlerDownloader',
    'WestwoodOneDownloader',
    'ClearOutWestDownloader',
    'create_downloader'
]
