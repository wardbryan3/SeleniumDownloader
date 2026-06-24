"""
GUI application for Audio Download Manager
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
import logging
from datetime import datetime

try:
    from config import ConfigManager, DOWNLOAD_SOURCES
    from browser_manager import BrowserManager
    from sources import create_downloader
except ImportError as e:
    print(f"Import error in gui.py: {e}")
    raise

logger = logging.getLogger(__name__)

COLORS = {
    'bg': '#181818',
    'surface': '#242424',
    'button': '#2e2e2e',
    'button_hover': '#3c3c3c',
    'button_active': '#4a4a4a',
    'light_text': '#f0f0f0',
    'dim_text': '#a0a0a0',
    'accent': '#0ea5e9',
    'success': '#22c55e',
    'error': '#ef4444',
    'warning': '#f59e0b',
    'tab_bg': '#242424',
    'tab_selected': '#181818',
    'tab_active': '#2e2e2e',
    'border': '#3a3a3a',
    'trough': '#181818',
    'indicator': '#0ea5e9',
}

class AudioDownloaderGUI:
    """Main GUI application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Audio Download Manager")
        self.root.geometry("600x750")
        
        self.config_manager = ConfigManager()
        self.browser_manager = BrowserManager(self.config_manager)
        
        self._download_lock = threading.Lock()
        
        self.status_var = tk.StringVar(value="Ready to download")
        self.progress_bar = None
        self.log_text = None
        
        self.setup_gui()
        self.apply_dark_theme()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        """Setup the GUI interface"""
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = ttk.Label(
            header_frame,
            text="Audio Download Manager",
            font=("Arial", 16, "bold"),
            anchor='center'
        )
        title_label.pack(fill=tk.X)
        
        settings_btn = ttk.Button(
            header_frame,
            text="\u2699",
            command=self.show_settings,
            width=3,
            style='Toolbutton'
        )
        settings_btn.place(relx=1.0, rely=0.5, x=-5, anchor='e')
        
        all_btn = ttk.Button(
            main_frame,
            text="Download Global Features",
            command=self.run_all_downloads,
            width=30
        )
        all_btn.pack(pady=(0, 5))

        promo_btn = ttk.Button(
            main_frame,
            text="Download Promo",
            command=self.create_download_handler("Download Promo"),
            width=30
        )
        promo_btn.pack(pady=(0, 20))

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
                text=f"{source_name}",
                command=self.create_download_handler(source_name),
                width=35
            )
            btn.pack(pady=3)
        
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
            wrap=tk.WORD,
            bg=COLORS['surface'],
            fg=COLORS['light_text'],
            insertbackground=COLORS['light_text'],
            relief='flat'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
    
    def apply_dark_theme(self):
        """Apply dark theme using ttk.Style"""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.', background=COLORS['bg'], foreground=COLORS['light_text'])

        style.configure('TFrame', background=COLORS['bg'])
        style.configure('TLabelframe', background=COLORS['bg'])
        style.configure('TLabelframe.Label', background=COLORS['bg'], foreground=COLORS['light_text'])
        style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['light_text'])

        style.configure(
            'TButton',
            background=COLORS['button'],
            foreground=COLORS['light_text'],
            bordercolor=COLORS['border'],
            lightcolor=COLORS['button'],
            darkcolor=COLORS['button'],
            padding=6
        )
        style.map(
            'TButton',
            background=[('active', COLORS['button_hover']), ('pressed', COLORS['button_active'])],
            foreground=[('active', COLORS['light_text']), ('pressed', COLORS['light_text'])],
            lightcolor=[('active', COLORS['button_hover']), ('pressed', COLORS['button_active'])],
            darkcolor=[('active', COLORS['button_hover']), ('pressed', COLORS['button_active'])]
        )

        style.configure(
            'TNotebook',
            background=COLORS['bg'],
            bordercolor=COLORS['border'],
            tabmargins=[2, 5, 2, 0]
        )
        style.configure(
            'TNotebook.Tab',
            background=COLORS['tab_bg'],
            foreground=COLORS['light_text'],
            padding=[10, 4],
            bordercolor=COLORS['border']
        )
        style.map(
            'TNotebook.Tab',
            background=[('selected', COLORS['tab_selected']), ('active', COLORS['tab_active'])],
            foreground=[('selected', COLORS['light_text']), ('active', COLORS['light_text'])]
        )

        style.configure('TCheckbutton', background=COLORS['bg'], foreground=COLORS['light_text'], indicatorcolor=COLORS['surface'])
        style.map('TCheckbutton', indicatorcolor=[('selected', COLORS['accent']), ('active', COLORS['button_hover'])])
        style.configure('TRadiobutton', background=COLORS['bg'], foreground=COLORS['light_text'], indicatorcolor=COLORS['surface'])
        style.map('TRadiobutton', indicatorcolor=[('selected', COLORS['accent']), ('active', COLORS['button_hover'])])

        style.configure(
            'TEntry',
            fieldbackground=COLORS['surface'],
            foreground=COLORS['light_text'],
            insertcolor=COLORS['light_text'],
            bordercolor=COLORS['border'],
            lightcolor=COLORS['border'],
            darkcolor=COLORS['border']
        )

        style.configure(
            'TSpinbox',
            fieldbackground=COLORS['surface'],
            foreground=COLORS['light_text'],
            insertcolor=COLORS['light_text'],
            bordercolor=COLORS['border'],
            lightcolor=COLORS['border'],
            darkcolor=COLORS['border'],
            arrowcolor=COLORS['light_text']
        )

        style.configure(
            'TProgressbar',
            background=COLORS['accent'],
            troughcolor=COLORS['trough'],
            bordercolor=COLORS['bg'],
            lightcolor=COLORS['accent'],
            darkcolor=COLORS['accent']
        )

        style.configure(
            'TCombobox',
            fieldbackground=COLORS['surface'],
            foreground=COLORS['light_text'],
            background=COLORS['button'],
            arrowcolor=COLORS['light_text'],
            bordercolor=COLORS['border'],
            lightcolor=COLORS['border'],
            darkcolor=COLORS['border']
        )
        style.map(
            'TCombobox',
            fieldbackground=[('readonly', COLORS['surface'])],
            selectbackground=[('readonly', COLORS['accent'])],
            selectforeground=[('readonly', COLORS['light_text'])]
        )

        self.root.configure(bg=COLORS['bg'])
    
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
                        self.status_var.set(f"Done - {source_name} completed!")
                        self.log_message(f"Done - {source_name} completed successfully")
                    else:
                        self.status_var.set(f"FAIL - {source_name} failed")
                        self.log_message(f"FAIL - {source_name} download failed")
                except Exception as e:
                    self.status_var.set(f"FAIL - {source_name} error")
                    self.log_message(f"Error in {source_name}: {str(e)}")
                finally:
                    self.root.after(2000, lambda: self.progress_bar.configure(value=0))
            
            threading.Thread(target=download_thread, daemon=True).start()
        
        return handler
    
    def download_with_retry(self, source_name: str) -> bool:
        """Wrapper function to automatically retry failed downloads"""
        max_retries = self.config_manager.get("retry_attempts", 2)
        
        if not self._download_lock.acquire(blocking=False):
            self.log_message(f"Another download in progress, skipping {source_name}")
            return False
        
        try:
            downloader = create_downloader(source_name, self.browser_manager, self.config_manager)
            
            for attempt in range(max_retries + 1):
                try:
                    success = downloader.download(self.update_progress)
                    if success:
                        return True
                    elif attempt < max_retries:
                        self.log_message(f"Retrying {source_name} (attempt {attempt + 1})...")
                        time.sleep(3)
                except Exception as e:
                    if attempt < max_retries:
                        self.log_message(f"Error in {source_name}, retrying... ({str(e)})")
                        time.sleep(3)
            
            self.log_message(f"{source_name} failed after {max_retries + 1} attempts")
            return False
        finally:
            self._download_lock.release()
    
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
    
    def show_summary_popup(self, success_count: int, total_count: int, failed_list: list):
        """Show a summary when downloads complete"""
        summary_window = tk.Toplevel(self.root)
        summary_window.title("Download Summary")
        summary_window.geometry("400x250")
        summary_window.transient(self.root)
        summary_window.grab_set()
        summary_window.configure(bg=COLORS['bg'])
        
        if failed_list:
            message = f"Completed: {success_count}/{total_count} downloads\n\nFailed:\n" + "\n".join(f"• {item}" for item in failed_list)
            icon = "Warning:"
            title = "Downloads Partially Completed"
        else:
            message = f"All {total_count} downloads completed successfully!"
            icon = "Success"
            title = "Downloads Completed"
        
        ttk.Label(summary_window, text=icon, font=("Arial", 24)).pack(pady=10)
        ttk.Label(summary_window, text=title, font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Label(summary_window, text=message, wraplength=350).pack(pady=10, padx=20)
        ttk.Button(summary_window, text="OK", command=summary_window.destroy).pack(pady=10)
    
    def show_settings(self):
        """Show settings window"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("550x550")
        settings_window.transient(self.root)
        settings_window.grab_set()
        settings_window.configure(bg=COLORS['bg'])
        
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        general_frame = ttk.Frame(notebook, padding="15")
        notebook.add(general_frame, text="General")
        
        paths_frame = ttk.Frame(notebook, padding="15")
        notebook.add(paths_frame, text="Paths")
        
        auth_frame = ttk.Frame(notebook, padding="15")
        notebook.add(auth_frame, text="Auth")
        
        urls_frame = ttk.Frame(notebook, padding="15")
        notebook.add(urls_frame, text="URLs")
        
        ttk.Label(general_frame, text="General Settings", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        ttk.Label(general_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, pady=10)
        output_dir_var = tk.StringVar(value=self.config_manager.get("output_dir", "downloads"))
        ttk.Entry(general_frame, textvariable=output_dir_var, width=30).grid(row=1, column=1, sticky=tk.W, pady=10)
        ttk.Button(general_frame, text="Browse", command=lambda: output_dir_var.set(filedialog.askdirectory() or output_dir_var.get())).grid(row=1, column=2, padx=5, pady=10)
        
        auto_close_var = tk.BooleanVar(value=self.config_manager.get("auto_close_browser", True))
        ttk.Checkbutton(
            general_frame,
            text="Auto-close browser after downloads",
            variable=auto_close_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Label(general_frame, text="Retry Attempts:").grid(row=3, column=0, sticky=tk.W, pady=10)
        retry_var = tk.StringVar(value=str(self.config_manager.get("retry_attempts", 2)))
        ttk.Spinbox(general_frame, from_=0, to=5, textvariable=retry_var, width=5).grid(row=3, column=1, sticky=tk.W, pady=10)
        
        ttk.Label(paths_frame, text="Paths", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        ttk.Label(paths_frame, text="Tag File:").grid(row=1, column=0, sticky=tk.W, pady=8)
        tag_var = tk.StringVar(value=self.config_manager.get("tag_file", ""))
        ttk.Entry(paths_frame, textvariable=tag_var, width=35).grid(row=1, column=1, sticky=tk.W, pady=8)
        ttk.Button(paths_frame, text="...", width=3, command=lambda: tag_var.set(filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3")]) or tag_var.get())).grid(row=1, column=2, padx=5)

        ttk.Label(paths_frame, text="Browser Download Dir:").grid(row=2, column=0, sticky=tk.W, pady=8)
        browser_download_dir_var = tk.StringVar(value=self.config_manager.get("browser_download_dir", ""))
        ttk.Entry(paths_frame, textvariable=browser_download_dir_var, width=35).grid(row=2, column=1, sticky=tk.W, pady=8)
        ttk.Button(paths_frame, text="Browse", command=lambda: browser_download_dir_var.set(filedialog.askdirectory() or browser_download_dir_var.get())).grid(row=2, column=2, padx=5)
        
        ttk.Label(auth_frame, text="Authentication", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        ttk.Label(auth_frame, text="Clear Out West Password:").grid(row=1, column=0, sticky=tk.W, pady=8)
        cow_password_var = tk.StringVar(value=self.config_manager.get("cow_password", ""))
        ttk.Entry(auth_frame, textvariable=cow_password_var, width=35, show="*").grid(row=1, column=1, sticky=tk.W, pady=8)

        ttk.Label(auth_frame, text="WITC FTP Server:").grid(row=2, column=0, sticky=tk.W, pady=8)
        witc_ftp_server_var = tk.StringVar(value=self.config_manager.get("witc_ftp_server", ""))
        ttk.Entry(auth_frame, textvariable=witc_ftp_server_var, width=35).grid(row=2, column=1, sticky=tk.W, pady=8)

        ttk.Label(auth_frame, text="WITC FTP Username:").grid(row=3, column=0, sticky=tk.W, pady=8)
        witc_ftp_username_var = tk.StringVar(value=self.config_manager.get("witc_ftp_username", ""))
        ttk.Entry(auth_frame, textvariable=witc_ftp_username_var, width=35).grid(row=3, column=1, sticky=tk.W, pady=8)

        ttk.Label(auth_frame, text="WITC FTP Password:").grid(row=4, column=0, sticky=tk.W, pady=8)
        witc_ftp_password_var = tk.StringVar(value=self.config_manager.get("witc_ftp_password", ""))
        ttk.Entry(auth_frame, textvariable=witc_ftp_password_var, width=35, show="*").grid(row=4, column=1, sticky=tk.W, pady=8)
        
        ttk.Label(urls_frame, text="Source URLs", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        urls = self.config_manager.get("urls", {})
        ttk.Label(urls_frame, text="Northwest Outdoors:").grid(row=1, column=0, sticky=tk.W, pady=8)
        northwest_outdoors_url_var = tk.StringVar(value=urls.get("northwest_outdoors", ""))
        ttk.Entry(urls_frame, textvariable=northwest_outdoors_url_var, width=45).grid(row=1, column=1, sticky=tk.W, pady=8)
        
        ttk.Label(urls_frame, text="Whittler:").grid(row=2, column=0, sticky=tk.W, pady=8)
        whittler_url_var = tk.StringVar(value=urls.get("whittler", ""))
        ttk.Entry(urls_frame, textvariable=whittler_url_var, width=45).grid(row=2, column=1, sticky=tk.W, pady=8)
        
        def save_settings():
            self.config_manager.set("output_dir", output_dir_var.get())
            self.config_manager.set("auto_close_browser", auto_close_var.get())
            self.config_manager.set("retry_attempts", int(retry_var.get()))
            self.config_manager.set("tag_file", tag_var.get())
            self.config_manager.set("cow_password", cow_password_var.get())
            self.config_manager.set("browser_download_dir", browser_download_dir_var.get())
            self.config_manager.set("witc_ftp_server", witc_ftp_server_var.get())
            self.config_manager.set("witc_ftp_username", witc_ftp_username_var.get())
            self.config_manager.set("witc_ftp_password", witc_ftp_password_var.get())
            self.config_manager.set("urls", {
                "northwest_outdoors": northwest_outdoors_url_var.get(),
                "whittler": whittler_url_var.get(),
            })
            self.config_manager.save()
            messagebox.showinfo("Settings", "Settings saved successfully!")
            settings_window.destroy()
        
        btn_frame = ttk.Frame(settings_window)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="Save", command=save_settings).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=settings_window.destroy).pack(side=tk.LEFT)
    
    def on_closing(self):
        """Handle application closing"""
        self.browser_manager.close_browser()
        self.root.destroy()
    
    def run(self):
        """Start the GUI application"""
        self.log_message("Application started - Browser will open when downloads begin")
        self.root.mainloop()
