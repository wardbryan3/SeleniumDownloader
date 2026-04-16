"""
Scheduling functionality for automated downloads
"""

import threading
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

class DownloadScheduler:
    """Manages scheduled downloads"""
    
    def __init__(self, config_manager, download_callback: Callable):
        self.config_manager = config_manager
        self.download_callback = download_callback
        self.jobs: List[Dict[str, Any]] = []
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the scheduler in a background thread"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        
        def scheduler_loop():
            while self.running:
                self.run_pending()
                time.sleep(60)  # Check every minute
        
        self.thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.thread.start()
        logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def run_pending(self):
        """Run all jobs that are due"""
        scheduled_config = self.config_manager.get_scheduled_config()
        
        if not scheduled_config.get("enabled", False):
            return
        
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_weekday = now.strftime('%a')
        
        for job in self.jobs:
            # Check if time matches
            if job['time'] != current_time:
                continue
            
            # Check if we already ran this job at this time
            if job['last_run'] and job['last_run'].strftime('%Y-%m-%d %H:%M') == now.strftime('%Y-%m-%d %H:%M'):
                continue
            
            # Check schedule type
            if job['type'] == 'daily':
                should_run = True
            elif job['type'] == 'weekly':
                should_run = current_weekday in job['days']
            else:
                should_run = False
            
            if should_run:
                try:
                    job['func']()
                    job['last_run'] = now
                    logger.info(f"Ran scheduled job at {current_time}")
                except Exception as e:
                    logger.error(f"Error in scheduled job: {e}")
    
    def update_from_config(self):
        """Update scheduler based on current configuration"""
        self.jobs.clear()
        
        scheduled_config = self.config_manager.get_scheduled_config()
        
        if not scheduled_config.get("enabled", False):
            logger.info("Scheduler disabled")
            return
        
        schedule_type = scheduled_config.get("schedule_type", "daily")
        time_str = scheduled_config.get("time", "06:00")
        
        # Validate time format
        try:
            datetime.strptime(time_str, '%H:%M')
        except ValueError:
            logger.error(f"Invalid time format: {time_str} - using 06:00")
            time_str = "06:00"
        
        # Map full day names to abbreviated
        from config import DAY_MAPPING
        days = scheduled_config.get("days", [])
        abbreviated_days = [DAY_MAPPING.get(day, day[:3]) for day in days]
        
        # Create job function based on configuration
        def create_job_function():
            if scheduled_config.get("download_all", True):
                # Run all downloads
                return self.download_callback
            else:
                # Run only selected sources
                selected_sources = scheduled_config.get("selected_sources", [])
                def selected_downloads():
                    logger.info(f"Running scheduled downloads for: {selected_sources}")
                    # This would need to be implemented based on your source structure
                    self.download_callback()
                return selected_downloads
        
        job_func = create_job_function()
        
        self.jobs.append({
            'func': job_func,
            'type': schedule_type,
            'time': time_str,
            'days': abbreviated_days,
            'last_run': None
        })
        
        if schedule_type == "daily":
            logger.info(f"Scheduled daily downloads at {time_str}")
        elif schedule_type == "weekly":
            logger.info(f"Scheduled weekly downloads on {', '.join(days)} at {time_str}")