"""
Sources package initialization
"""

from .melinda_myers import MelindaMyersDownloader
from .northwest_outdoors import NorthwestOutdoorsDownloader, NorthwestOutdoorsPromoDownloader
from .whittler import WhittlerDownloader
from .clear_out_west import ClearOutWestDownloader
from .weekend_in_the_country import WeekendInTheCountryDownloader

def create_downloader(source_name: str, browser_manager, config_manager):
    """Factory function to create downloader instances"""
    downloaders = {
        "Melinda Myers": MelindaMyersDownloader,
        "Northwest Outdoors": NorthwestOutdoorsDownloader,
        "Download Promo": NorthwestOutdoorsPromoDownloader,
        "Whittler": WhittlerDownloader,
        "Clear Out West": ClearOutWestDownloader,
        "Weekend In The Country": WeekendInTheCountryDownloader
    }
    
    downloader_class = downloaders.get(source_name)
    if downloader_class:
        return downloader_class(browser_manager, config_manager)
    
    raise ValueError(f"Unknown download source: {source_name}")

__all__ = [
    'MelindaMyersDownloader',
    'NorthwestOutdoorsDownloader',
    'NorthwestOutdoorsPromoDownloader',
    'WhittlerDownloader',
    'ClearOutWestDownloader',
    'WeekendInTheCountryDownloader',
    'create_downloader'
]
