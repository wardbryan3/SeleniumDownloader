"""
GUI application for Audio Download Manager
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
import sys
import logging
from datetime import datetime

try:
    from config import ConfigManager, DOWNLOAD_SOURCES
    from browser_manager import BrowserManager
    from scheduler import DownloadScheduler
    from sources import create_downloader
    from update_checker import UpdateChecker
    from __init__ import __version__
except ImportError as e:
    print(f"Import error in gui.py: {e}")
    raise

logger = logging.getLogger(__name__)

COLORS = {
    'dark_bg': '#1e1e1e',
    'dark_frame': '#2d2d2d',
    'dark_button': '#3c3c3c',
    'dark_button_hover': '#4a4a4a',
    'light_text': '#e0e0e0',
    'dim_text': '#a0a0a0',
    'accent': '#0078d4',
    'success': '#4caf50',
    'error': '#f44336',
    'warning': '#ff9800',
    'test_mode': '#ff9800',
}

LIGHT_COLORS = {
    'bg': '#f0f0f0',
    'frame': '#ffffff',
    'text': '#000000',
    'button': '#e0e0e0',
}

class AudioDownloaderGUI:
    """Main GUI application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Audio Download Manager")
        self.root.geometry("600x750")
        
        self.config_manager = ConfigManager()
        self.browser_manager = BrowserManager(self.config_manager)
        
        self.scheduler = DownloadScheduler(
            self.config_manager,
            self.run_all_downloads_silent
        )
        
        self.status_var = tk.StringVar(value="Ready to download")
        self.progress_bar = None
        self.log_text = None
        self.update_available = False
        self.latest_version = ""
        self.update_url = ""
        self.dark_mode = tk.BooleanVar(value=self.config_manager.get("dark_mode", True))
        
        self.setup_gui()
        self.setup_scheduler()
        self.check_for_updates()
        self.apply_theme()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def check_for_updates(self):
        """Check for updates on startup in background thread"""
        def check():
            checker = UpdateChecker(__version__)
            update_available, version, url, _ = checker.check_for_update()
            
            if update_available:
                self.update_available = True
                self.latest_version = version
                self.update_url = url
                
                def show_notification():
                    if messagebox.askyesno(
                        "Update Available",
                        f"A new version ({version}) is available!\n\n"
                        f"You are currently running version {__version__}.\n\n"
                        f"Would you like to visit the releases page to download it?"
                    ):
                        import webbrowser
                        webbrowser.open(url)
                
                self.root.after(0, show_notification)
        
        threading.Thread(target=check, daemon=True).start()
    
    def setup_gui(self):
        """Setup the GUI interface"""
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        test_mode = self.config_manager.get("test_mode", True)
        if test_mode:
            test_banner = tk.Frame(main_frame, bg=COLORS['test_mode'], height=30)
            test_banner.pack(fill=tk.X, pady=(0, 10))
            test_banner.pack_propagate(False)
            tk.Label(
                test_banner,
                text="⚠ TEST MODE - Downloads go to local folder, not Dropbox",
                bg=COLORS['test_mode'],
                fg='#000',
                font=("Arial", 10, "bold")
            ).pack(pady=5)
        
        title_label = ttk.Label(
            main_frame,
            text="📥 Audio Download Manager",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 15))
        
        all_btn = ttk.Button(
            main_frame,
            text="⬇ Download All",
            command=self.run_all_downloads,
            width=30
        )
        all_btn.pack(pady=(0, 20))
        
        sources_label = ttk.Label(
            main_frame,
            text="Downloads:",
            font=("Arial", 11, "bold")
        )
        sources_label.pack(pady=(0, 5))
        
        sources_frame = ttk.Frame(main_frame)
        sources_frame.pack(fill=tk.X, pady=(0, 15))
        
        sources = list(DOWNLOAD_SOURCES.keys())
        for i, source_name in enumerate(sources):
            btn = ttk.Button(
                sources_frame,
                text=f"📁 {source_name}",
                command=self.create_download_handler(source_name),
                width=35
            )
            btn.pack(pady=3)
        
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=(0, 15))
        
        settings_btn = ttk.Button(
            buttons_frame,
            text="⚙ Settings",
            command=self.show_settings,
            width=15
        )
        settings_btn.pack(side=tk.LEFT, padx=5)
        
        scheduler_btn = ttk.Button(
            buttons_frame,
            text="🕐 Scheduler",
            command=self.show_scheduler_window,
            width=15
        )
        scheduler_btn.pack(side=tk.LEFT, padx=5)
        
        dark_toggle = ttk.Checkbutton(
            buttons_frame,
            text="🌙 Dark",
            variable=self.dark_mode,
            command=self.toggle_dark_mode,
            style='Switch.TCheckbutton'
        )
        dark_toggle.pack(side=tk.LEFT, padx=15)
        
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient='horizontal',
            mode='determinate',
            length=550,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X)
        
        status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            wraplength=550
        )
        status_label.pack(pady=(5, 10))
        
        log_frame = ttk.LabelFrame(main_frame, text="Download Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            width=70,
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
    
    def toggle_dark_mode(self):
        """Toggle dark mode"""
        self.config_manager.set("dark_mode", self.dark_mode.get())
        self.apply_theme()
    
    def apply_theme(self):
        """Apply dark or light theme using ttk.Style"""
        style = ttk.Style()
        
        if self.dark_mode.get():
            style.theme_use('clam')
            style.configure('.', background=COLORS['dark_bg'])
            style.configure('.', foreground=COLORS['light_text'])
            style.configure('TFrame', background=COLORS['dark_bg'])
            style.configure('TLabelframe', background=COLORS['dark_bg'])
            style.configure('TLabelframe.Label', background=COLORS['dark_bg'], foreground=COLORS['light_text'])
            style.configure('TLabel', background=COLORS['dark_bg'], foreground=COLORS['light_text'])
            style.configure('TButton', background=COLORS['dark_button'], foreground=COLORS['light_text'])
            style.map('TButton', background=[('active', COLORS['dark_button_hover'])])
            style.configure('TCheckbutton', background=COLORS['dark_bg'], foreground=COLORS['light_text'])
            style.configure('TRadiobutton', background=COLORS['dark_bg'], foreground=COLORS['light_text'])
            style.configure('TEntry', fieldbackground=COLORS['dark_frame'], foreground=COLORS['light_text'])
            self.root.configure(bg=COLORS['dark_bg'])
        else:
            style.theme_use('default')
            style.configure('.', background='SystemButtonFace')
            style.configure('TFrame', background='SystemButtonFace')
            style.configure('TLabelframe', background='SystemButtonFace')
            style.configure('TLabelframe.Label', background='SystemButtonFace')
            style.configure('TLabel', background='SystemButtonFace')
            style.configure('TButton', background='SystemButtonFace')
            style.configure('TCheckbutton', background='SystemButtonFace')
            style.configure('TRadiobutton', background='SystemButtonFace')
            style.configure('TEntry', fieldbackground='white')
            self.root.configure(bg='SystemButtonFace')
    
    def setup_scheduler(self):
        """Setup and start the scheduler"""
        self.scheduler.update_from_config()
        self.scheduler.start()
        self.log_message("Scheduler started")
    
    def log_message(self, message: str):
        """Add message to log viewer"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"{timestamp} - {message}\n"
        
        def update_log():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, log_entry)
            self.log_text.config(state=tk.DISABLED)
            self.log_text.see(tk.END)
        
        self.root.after(0, update_log)
        logger.info(message)
    
    def update_progress(self, value: float, status_text: str = ""):
        """Update progress bar and status from any thread"""
        def update_ui():
            self.progress_bar['value'] = value
            if status_text:
                self.status_var.set(status_text)
            self.root.update_idletasks()
        
        self.root.after(0, update_ui)
    
    def create_download_handler(self, source_name: str):
        """Create a handler for download buttons"""
        def handler():
            self.progress_bar['value'] = 0
            self.status_var.set(f"Starting {source_name}...")
            self.log_message(f"Starting {source_name} download...")
            
            def download_thread():
                try:
                    success = self.download_with_retry(source_name)
                    if success:
                        self.status_var.set(f"✓ {source_name} completed!")
                        self.log_message(f"✓ {source_name} completed successfully")
                    else:
                        self.status_var.set(f"✗ {source_name} failed")
                        self.log_message(f"✗ {source_name} download failed")
                except Exception as e:
                    self.status_var.set(f"✗ {source_name} error")
                    self.log_message(f"Error in {source_name}: {str(e)}")
                finally:
                    self.root.after(2000, lambda: self.progress_bar.configure(value=0))
            
            threading.Thread(target=download_thread, daemon=True).start()
        
        return handler
    
    def download_with_retry(self, source_name: str) -> bool:
        """Wrapper function to automatically retry failed downloads"""
        max_retries = self.config_manager.get("retry_attempts", 2)
        
        downloader = create_downloader(source_name, self.browser_manager, self.config_manager)
        
        for attempt in range(max_retries + 1):
            try:
                success = downloader.download(self.update_progress)
                if success:
                    return True
                elif attempt < max_retries:
                    self.log_message(f"↻ Retrying {source_name} (attempt {attempt + 1})...")
                    time.sleep(3)
            except Exception as e:
                if attempt < max_retries:
                    self.log_message(f"↻ Error in {source_name}, retrying... ({str(e)})")
                    time.sleep(3)
        
        self.log_message(f"✗ {source_name} failed after {max_retries + 1} attempts")
        return False
    
    def run_all_downloads(self):
        """Run all downloads with progress"""
        def download_all_thread():
            sources = list(DOWNLOAD_SOURCES.keys())
            success_count = 0
            failed_downloads = []
            
            for i, source_name in enumerate(sources):
                progress = (i / len(sources)) * 100
                self.update_progress(
                    progress,
                    f"Downloading all - Starting: {source_name} ({i+1}/{len(sources)})"
                )
                
                success = self.download_with_retry(source_name)
                if success:
                    success_count += 1
                else:
                    failed_downloads.append(source_name)
            
            self.update_progress(100, "All downloads completed!")
            self.show_summary_popup(success_count, len(sources), failed_downloads)
        
        threading.Thread(target=download_all_thread, daemon=True).start()
    
    def run_all_downloads_silent(self):
        """Run all downloads without showing progress dialogs (for scheduler)"""
        def download_all_thread():
            sources = list(DOWNLOAD_SOURCES.keys())
            success_count = 0
            total_count = len(sources)
            
            for source_name in sources:
                try:
                    downloader = create_downloader(source_name, self.browser_manager, self.config_manager)
                    success = downloader.download()
                    if success:
                        success_count += 1
                        self.log_message(f"✓ {source_name} completed")
                    else:
                        self.log_message(f"✗ {source_name} failed")
                except Exception as e:
                    self.log_message(f"✗ Error in {source_name}: {e}")
            
            self.log_message(f"Scheduled downloads: {success_count}/{total_count} successful")
        
        threading.Thread(target=download_all_thread, daemon=True).start()
    
    def show_summary_popup(self, success_count: int, total_count: int, failed_list: list):
        """Show a summary when downloads complete"""
        summary_window = tk.Toplevel(self.root)
        summary_window.title("Download Summary")
        summary_window.geometry("400x250")
        summary_window.transient(self.root)
        summary_window.grab_set()
        
        if failed_list:
            message = f"Completed: {success_count}/{total_count} downloads\n\nFailed:\n" + "\n".join(f"• {item}" for item in failed_list)
            icon = "⚠️"
            title = "Downloads Partially Completed"
        else:
            message = f"All {total_count} downloads completed successfully!"
            icon = "✅"
            title = "Downloads Completed"
        
        ttk.Label(summary_window, text=icon, font=("Arial", 24)).pack(pady=10)
        ttk.Label(summary_window, text=title, font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Label(summary_window, text=message, wraplength=350).pack(pady=10, padx=20)
        ttk.Button(summary_window, text="OK", command=summary_window.destroy).pack(pady=10)
    
    def show_scheduler_window(self):
        """Show scheduler configuration window"""
        scheduler_window = tk.Toplevel(self.root)
        scheduler_window.title("Scheduler Configuration")
        scheduler_window.geometry("450x400")
        scheduler_window.transient(self.root)
        scheduler_window.grab_set()
        
        main_frame = ttk.Frame(scheduler_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="🕐 Download Scheduler", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        sched_enabled = tk.BooleanVar(value=self.config_manager.get("scheduled_downloads", {}).get("enabled", False))
        ttk.Checkbutton(
            main_frame,
            text="Enable scheduled downloads",
            variable=sched_enabled
        ).pack(anchor=tk.W, pady=5)
        
        sched_type = tk.StringVar(value=self.config_manager.get("scheduled_downloads", {}).get("schedule_type", "daily"))
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, pady=10)
        ttk.Label(type_frame, text="Schedule:").pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="Daily", variable=sched_type, value="daily").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(type_frame, text="Weekly", variable=sched_type, value="weekly").pack(side=tk.LEFT)
        
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(fill=tk.X, pady=10)
        ttk.Label(time_frame, text="Time (24h):").pack(side=tk.LEFT)
        time_var = tk.StringVar(value=self.config_manager.get("scheduled_downloads", {}).get("time", "06:00"))
        ttk.Entry(time_frame, textvariable=time_var, width=8).pack(side=tk.LEFT, padx=10)
        
        days_frame = ttk.LabelFrame(main_frame, text="Days (for weekly)", padding="10")
        days_frame.pack(fill=tk.X, pady=10)
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        saved_days = self.config_manager.get("scheduled_downloads", {}).get("days", [])
        day_vars = {}
        for i, day in enumerate(days):
            day_vars[day] = tk.BooleanVar(value=day in saved_days)
            ttk.Checkbutton(days_frame, text=day[:3], variable=day_vars[day]).pack(side=tk.LEFT, padx=5)
        
        def save_scheduler():
            selected_days = [day for day, var in day_vars.items() if var.get()]
            sched_config = {
                "enabled": sched_enabled.get(),
                "schedule_type": sched_type.get(),
                "time": time_var.get(),
                "days": selected_days,
                "download_all": True,
                "selected_sources": []
            }
            self.config_manager.set("scheduled_downloads", sched_config)
            self.scheduler.update_from_config()
            messagebox.showinfo("Scheduler", "Schedule saved successfully!")
            scheduler_window.destroy()
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Save", command=save_scheduler).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=scheduler_window.destroy).pack(side=tk.LEFT)
    
    def show_settings(self):
        """Show settings window"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x550")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        general_frame = ttk.Frame(notebook, padding="15")
        notebook.add(general_frame, text="General")
        
        paths_frame = ttk.Frame(notebook, padding="15")
        notebook.add(paths_frame, text="Paths")
        
        auth_frame = ttk.Frame(notebook, padding="15")
        notebook.add(auth_frame, text="Auth")
        
        ttk.Label(general_frame, text="⚙ General Settings", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        test_mode_var = tk.BooleanVar(value=self.config_manager.get("test_mode", True))
        ttk.Checkbutton(
            general_frame,
            text="Test Mode (downloads to local folder, not Dropbox)",
            variable=test_mode_var
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        auto_close_var = tk.BooleanVar(value=self.config_manager.get("auto_close_browser", True))
        ttk.Checkbutton(
            general_frame,
            text="Auto-close browser after downloads",
            variable=auto_close_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Label(general_frame, text="Retry Attempts:").grid(row=3, column=0, sticky=tk.W, pady=10)
        retry_var = tk.StringVar(value=str(self.config_manager.get("retry_attempts", 2)))
        ttk.Spinbox(general_frame, from_=0, to=5, textvariable=retry_var, width=5).grid(row=3, column=1, sticky=tk.W, pady=10)
        
        ttk.Label(general_frame, text="Test Downloads Dir:").grid(row=4, column=0, sticky=tk.W, pady=10)
        test_dir_var = tk.StringVar(value=self.config_manager.get("test_downloads_dir", "downloads"))
        ttk.Entry(general_frame, textvariable=test_dir_var, width=30).grid(row=4, column=1, sticky=tk.W, pady=10)
        ttk.Button(general_frame, text="Browse", command=lambda: test_dir_var.set(filedialog.askdirectory() or test_dir_var.get())).grid(row=4, column=2, padx=5, pady=10)
        
        ttk.Label(paths_frame, text="📁 Dropbox Paths", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        ttk.Label(paths_frame, text="Global Features:").grid(row=1, column=0, sticky=tk.W, pady=8)
        global_var = tk.StringVar(value=self.config_manager.get("global_features_dir", ""))
        gf_entry = ttk.Entry(paths_frame, textvariable=global_var, width=35)
        gf_entry.grid(row=1, column=1, sticky=tk.W, pady=8)
        ttk.Button(paths_frame, text="...", width=3, command=lambda: global_var.set(filedialog.askdirectory() or global_var.get())).grid(row=1, column=2, padx=5)
        
        ttk.Label(paths_frame, text="WWO SPOTS:").grid(row=2, column=0, sticky=tk.W, pady=8)
        wwo_var = tk.StringVar(value=self.config_manager.get("wwo_spots_dir", ""))
        ttk.Entry(paths_frame, textvariable=wwo_var, width=35).grid(row=2, column=1, sticky=tk.W, pady=8)
        ttk.Button(paths_frame, text="...", width=3, command=lambda: wwo_var.set(filedialog.askdirectory() or wwo_var.get())).grid(row=2, column=2, padx=5)
        
        ttk.Label(paths_frame, text="Promos:").grid(row=3, column=0, sticky=tk.W, pady=8)
        promos_var = tk.StringVar(value=self.config_manager.get("promos_dir", ""))
        ttk.Entry(paths_frame, textvariable=promos_var, width=35).grid(row=3, column=1, sticky=tk.W, pady=8)
        ttk.Button(paths_frame, text="...", width=3, command=lambda: promos_var.set(filedialog.askdirectory() or promos_var.get())).grid(row=3, column=2, padx=5)
        
        ttk.Label(paths_frame, text="Tag File:").grid(row=4, column=0, sticky=tk.W, pady=8)
        tag_var = tk.StringVar(value=self.config_manager.get("tag_file", ""))
        ttk.Entry(paths_frame, textvariable=tag_var, width=35).grid(row=4, column=1, sticky=tk.W, pady=8)
        ttk.Button(paths_frame, text="...", width=3, command=lambda: tag_var.set(filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3")]) or tag_var.get())).grid(row=4, column=2, padx=5)
        
        ttk.Label(auth_frame, text="🔐 Authentication", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        ttk.Label(auth_frame, text="Required for Westwood One downloads").grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        ttk.Label(auth_frame, text="Email:").grid(row=2, column=0, sticky=tk.W, pady=8)
        email_var = tk.StringVar(value=self.config_manager.get("email", ""))
        ttk.Entry(auth_frame, textvariable=email_var, width=35).grid(row=2, column=1, sticky=tk.W, pady=8)
        
        ttk.Label(auth_frame, text="Password:").grid(row=3, column=0, sticky=tk.W, pady=8)
        password_var = tk.StringVar(value=self.config_manager.get("password", ""))
        ttk.Entry(auth_frame, textvariable=password_var, width=35, show="*").grid(row=3, column=1, sticky=tk.W, pady=8)
        
        ttk.Label(auth_frame, text="Clear Out West Password:").grid(row=4, column=0, sticky=tk.W, pady=8)
        cow_password_var = tk.StringVar(value=self.config_manager.get("cow_password", ""))
        ttk.Entry(auth_frame, textvariable=cow_password_var, width=35, show="*").grid(row=4, column=1, sticky=tk.W, pady=8)
        
        def save_settings():
            self.config_manager.set("test_mode", test_mode_var.get())
            self.config_manager.set("auto_close_browser", auto_close_var.get())
            self.config_manager.set("retry_attempts", int(retry_var.get()))
            self.config_manager.set("test_downloads_dir", test_dir_var.get())
            self.config_manager.set("global_features_dir", global_var.get())
            self.config_manager.set("wwo_spots_dir", wwo_var.get())
            self.config_manager.set("promos_dir", promos_var.get())
            self.config_manager.set("tag_file", tag_var.get())
            self.config_manager.set("email", email_var.get())
            self.config_manager.set("password", password_var.get())
            self.config_manager.set("cow_password", cow_password_var.get())
            self.config_manager.save()
            messagebox.showinfo("Settings", "Settings saved successfully!")
            settings_window.destroy()
        
        btn_frame = ttk.Frame(settings_window)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="Save", command=save_settings).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=settings_window.destroy).pack(side=tk.LEFT)
    
    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit? This will close the browser if it's open."):
            self.scheduler.stop()
            self.browser_manager.close_browser()
            self.root.destroy()
            sys.exit()
    
    def run(self):
        """Start the GUI application"""
        self.log_message("Application started - Browser will open when downloads begin")
        self.root.mainloop()
