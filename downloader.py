from selenium import webdriver
from selenium.webdriver.firefox.service import Service 
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta
import os
import glob
import time
import zipfile
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import sys
import json

# Configuration
CONFIG_FILE = "download_config.json"
download_dir = os.path.join(os.getcwd(), "downloads")
driver = None  # Global driver variable

# Custom Scheduler Implementation
class Scheduler:
    def __init__(self):
        self.jobs = []
        self.running = False
        self.thread = None
    
    def add_job(self, job_func, schedule_type, time_str, days=None):
        """Add a job to the scheduler"""
        if days is None:
            days = []
        job = {
            'func': job_func,
            'type': schedule_type,
            'time': time_str,
            'days': days,
            'last_run': None
        }
        self.jobs.append(job)
    
    def clear_jobs(self):
        """Clear all scheduled jobs"""
        self.jobs.clear()
    
    def should_run_job(self, job):
        """Check if a job should run now"""
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_weekday = now.strftime('%a')  # Mon, Tue, etc.
        
        # Check if time matches
        if job['time'] != current_time:
            return False
        
        # Check if we already ran this job at this time
        if job['last_run'] and job['last_run'].strftime('%Y-%m-%d %H:%M') == now.strftime('%Y-%m-%d %H:%M'):
            return False
        
        # Check schedule type
        if job['type'] == 'daily':
            return True
        elif job['type'] == 'weekly':
            return current_weekday in job['days']
        
        return False
    
    def run_pending(self):
        """Run all jobs that are due"""
        for job in self.jobs:
            if self.should_run_job(job):
                try:
                    job['func']()
                    job['last_run'] = datetime.now()
                    log_message(f"✓ Ran scheduled job at {datetime.now().strftime('%H:%M')}")
                except Exception as e:
                    log_message(f"✗ Error in scheduled job: {e}")
    
    def start(self):
        """Start the scheduler in a background thread"""
        self.running = True
        
        def scheduler_loop():
            while self.running:
                self.run_pending()
                time.sleep(60)  # Check every minute
        
        self.thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False

# Create global scheduler instance
scheduler = Scheduler()

# Load configuration
def load_config():
    default_config = {
        "download_dir": os.path.join(os.getcwd(), "downloads"),
        "auto_close_browser": True,
        "retry_attempts": 2,
        "email": "m@tnet.biz",
        "password": "F!",
        "scheduled_downloads": {
            "enabled": False,
            "schedule_type": "daily",  # daily, weekly
            "time": "06:00",
            "days": [],  # For weekly: ["Monday", "Tuesday", etc.]
            "download_all": True,
            "selected_sources": []  # If download_all is False
        }
    }
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                saved_config = json.load(f)
                # Merge with default config to ensure all keys exist
                for key, value in default_config.items():
                    if key not in saved_config:
                        saved_config[key] = value
                return saved_config
    except:
        pass
    return default_config

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

config = load_config()
download_dir = config["download_dir"]

def find_coming_weekday(weekday):
    today = datetime.now().date()
    days_until_weekday = (weekday - today.weekday() + 7) % 7 
    if days_until_weekday == 0 and today.weekday() == 1:
        days_until_weekday = 7
    coming_weekday = today + timedelta(days=days_until_weekday)
    return coming_weekday.strftime('%m%d%y')

def setOptions():
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    options = Options()
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "audio/mpeg")
    options.set_preference("media.play-stand-alone", False)
    options.set_preference("pdfjs.disabled", True)
    return options

def initialize_browser():
    """Initialize the browser only when needed"""
    global driver
    if driver is None:
        try:
            options = setOptions()
            
            # Use webdriver_manager to automatically download/use geckodriver
            service = Service(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options)
            
            log_message("Browser started successfully")
            return True
        except Exception as e:
            log_message(f"Error starting browser: {e}")
            messagebox.showerror("Browser Error", f"Could not start browser: {e}")
            return False
    return True



def close_browser():
    """Close the browser if it's open"""
    global driver
    if driver is not None:
        try:
            driver.quit()
            driver = None
            log_message("Browser closed")
        except:
            pass

def findLatestFile():
    time.sleep(3)
    list_of_files = glob.glob(os.path.join(download_dir, '*'))
    return max(list_of_files, key=os.path.getctime) if list_of_files else None

def downloadMelindaMyers(update_callback=None):
    if not initialize_browser():
        return False
        
    try:
        # Create melinda myers directory
        melinda_dir = os.path.join(download_dir, "Melinda Myers")
        os.makedirs(melinda_dir, exist_ok=True)
        
        total_steps = 5  # Monday, Tuesday, Wednesday, Thursday, Friday
        current_step = 0
        
        # Download 3x series (Monday, Wednesday, Friday)
        for i in range(0, 5, 2):
            # Update progress
            current_step += 1
            if update_callback:
                progress = (current_step / total_steps) * 100
                update_callback(progress, f"Downloading Melinda Myers - 3x Series ({current_step}/{total_steps})")
            
            # Navigate to a webpage
            driver.get("https://www.melindamyers.com/media/") 

            # Locate the link element
            link_element = driver.find_element(By.PARTIAL_LINK_TEXT, "Audio_Tips_3x") 

            # Click link
            link_element.click()

            # Download file
            weekday = find_coming_weekday(i)
            download_link = driver.find_element(By.PARTIAL_LINK_TEXT, weekday)
            download_link.click()

            latestFile = findLatestFile()
            
            match i:
                case 0:
                    os.rename(latestFile, os.path.join(melinda_dir, "MMMON.mp3"))
                case 2:
                    os.rename(latestFile, os.path.join(melinda_dir, "MMWED.mp3"))
                case 4:
                    os.rename(latestFile, os.path.join(melinda_dir, "MMFRI.mp3"))
        
        # Download 5x series (Tuesday, Thursday)
        for i in range(1, 4, 2):
            # Update progress
            current_step += 1
            if update_callback:
                progress = (current_step / total_steps) * 100
                update_callback(progress, f"Downloading Melinda Myers - 5x Series ({current_step}/{total_steps})")
            
            # Navigate to a webpage
            driver.get("https://www.melindamyers.com/media/") 

            # Locate the link element
            link_element = driver.find_element(By.PARTIAL_LINK_TEXT, "Audio_Tips_5x") 

            # Click link
            link_element.click()

            # Download file
            weekday = find_coming_weekday(i)
            download_link = driver.find_element(By.PARTIAL_LINK_TEXT, weekday)
            download_link.click()

            latestFile = findLatestFile()
            
            match i:
                case 1:
                    os.rename(latestFile, os.path.join(melinda_dir, "MMTUE.mp3"))
                case 3:
                    os.rename(latestFile, os.path.join(melinda_dir, "MMTHU.mp3"))
        
        # Auto-close browser if enabled
        if config["auto_close_browser"]:
            close_browser()
        
        return True
    except Exception as e:
        print(f"Error in downloadMelindaMyers: {e}")
        # Auto-close browser even on error if enabled
        if config["auto_close_browser"]:
            close_browser()
        return False

def downloadNWO(update_callback=None):
    if not initialize_browser():
        return False
        
    try:
        total_steps = 4
        current_step = 0
        
        # Step 1: Navigate and click download
        current_step += 1
        if update_callback:
            update_callback(25, "Downloading Northwest Outdoors - Accessing download page")
        driver.get("***REMOVED***") 

        time.sleep(10)
        wait = WebDriverWait(driver, 30)
        link_element = wait.until(EC.element_to_be_clickable(driver.find_element(By.XPATH, "/html/body/div[1]/span/span/div/span/div/div/div/div/div[2]/div/div[1]/span/div/div[2]/span[1]/button/span/span/span")))
                                                                                        
        # Click link
        link_element.click()

        # Step 2: Confirm download
        current_step += 1
        if update_callback:
            update_callback(50, "Downloading Northwest Outdoors - Starting download")
        wait = WebDriverWait(driver, 10)
        link_element = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[9]/div/div/div/div[3]/div/span/button/span")))
        link_element.click()

        time.sleep(145)

        # Step 3: Process downloaded file
        current_step += 1
        if update_callback:
            update_callback(75, "Downloading Northwest Outdoors - Extracting files")
        latest_file = findLatestFile()

        NWO_DIR = os.path.join(download_dir, "NorthwestOutdoors")

        with zipfile.ZipFile(latest_file, 'r') as zip_ref:
            zip_ref.extractall(NWO_DIR)

        # Step 4: Cleanup
        current_step += 1
        if update_callback:
            update_callback(100, "Downloading Northwest Outdoors - Finalizing")
        os.remove(latest_file)
        
        # Auto-close browser if enabled
        if config["auto_close_browser"]:
            close_browser()
        
        return True
    except Exception as e:
        print(f"Error in downloadNWO: {e}")
        # Auto-close browser even on error if enabled
        if config["auto_close_browser"]:
            close_browser()
        return False

def downloadWhittler(update_callback=None):
    if not initialize_browser():
        return False
        
    try:
        total_steps = 5
        current_step = 0
        
        # Step 1: Navigate and click download
        current_step += 1
        if update_callback:
            update_callback(20, "Downloading Whittler - Accessing download page")
        driver.get("***REMOVED***") 

        time.sleep(10)
        wait = WebDriverWait(driver, 30)
        link_element = wait.until(EC.element_to_be_clickable(driver.find_element(By.XPATH, "/html/body/div[1]/span/span/div/span/div/div/div/div/div[2]/div/div[1]/span/div/div[2]/span[1]/button/span/span/span")))
                                                                                        
        # Click link
        link_element.click()

        # Step 2: Confirm download
        current_step += 1
        if update_callback:
            update_callback(40, "Downloading Whittler - Starting download")
        wait = WebDriverWait(driver, 10)
        link_element = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[9]/div/div/div/div[3]/div/span/button/span")))
        link_element.click()

        time.sleep(145)

        # Step 3: Process downloaded file
        current_step += 1
        if update_callback:
            update_callback(60, "Downloading Whittler - Extracting files")
        latest_file = findLatestFile()

        whittler_DIR = os.path.join(download_dir, "Whittler")

        with zipfile.ZipFile(latest_file, 'r') as zip_ref:
            zip_ref.extractall(whittler_DIR)

        os.remove(latest_file)

        # Step 4: Rename files
        current_step += 1
        if update_callback:
            update_callback(80, "Downloading Whittler - Renaming files")
        part_mapping = {
            "Part A": "Whittler1",
            "Part B": "Whittler2", 
            "Part C": "Whittler3",
            "Part D": "Whittler4"
        }
        
        for old_part, new_name in part_mapping.items():
            pattern = os.path.join(whittler_DIR, f"*{old_part}*.mp3")
            files = glob.glob(pattern)
            
            for file_path in files:
                new_filename = f"{new_name}.mp3"
                new_path = os.path.join(whittler_DIR, new_filename)
                
                os.rename(file_path, new_path)
                print(f"Renamed: {os.path.basename(file_path)} -> {new_filename}")

        # Step 5: Complete
        current_step += 1
        if update_callback:
            update_callback(100, "Downloading Whittler - Complete")
        
        # Auto-close browser if enabled
        if config["auto_close_browser"]:
            close_browser()
        
        return True
    except Exception as e:
        print(f"Error in downloadWhittler: {e}")
        # Auto-close browser even on error if enabled
        if config["auto_close_browser"]:
            close_browser()
        return False

import zipfile
import os
from pathlib import Path

def downloadWWO(update_callback=None):
    if not initialize_browser():
        return False
        
    try:
        total_steps = 10
        current_step = 0
        
        # Get email and password from config
        email = config["email"]
        password = config["password"]
        webmail_URL = 'https://webmail8.userservices.net/'
        westwoodone_URL = 'https://cdn.westwoodone.com/packages'
        


        # Step 1: Navigate to Westwood One
        current_step += 1
        if update_callback:
            update_callback(current_step/total_steps*100, "Downloading Westwood One - Accessing site")
        driver.get(westwoodone_URL)
        time.sleep(5)
        
        # Step 2: Enter email
        current_step += 1
        if update_callback:
            update_callback(current_step/total_steps*100, "Downloading Westwood One - Sending magic link")
        wait = WebDriverWait(driver, 30)
        username_field = wait.until(
            EC.presence_of_element_located((By.ID, "passwordless_email"))
        )
        username_field.send_keys(os.getenv('WEBMAIL_USER', email))

        send_magic_link = driver.find_element(By.XPATH, '/html/body/main/div/div/div[2]/form/div[2]/div/button')
        send_magic_link.click()
        time.sleep(5)

        # Step 3: Login to email
        current_step += 1
        if update_callback:
            update_callback(current_step/total_steps*100, "Downloading Westwood One - Accessing email")
        driver.get(webmail_URL)
        
        # Check if already logged in
        
        email_login_field = driver.find_element(By.ID, 'rcmloginuser')
        email_password_field = driver.find_element(By.ID, 'rcmloginpwd')
        email_login_field.send_keys(email)
        email_password_field.send_keys(password)
        login_button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/form/div[5]/button')
        login_button.click()
        time.sleep(5)

        # Step 4: Find and open magic link email
        current_step += 1
        if update_callback:
            update_callback(current_step/total_steps*100, "Downloading Westwood One - Finding magic link email")
        
        # Wait for the message list to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "messagelist"))
        )
        
        # Find all magic link emails - they're already sorted by date (newest first)
        magic_link_emails = driver.find_elements(By.XPATH, "//tr[contains(@class, 'message')]//a[contains(., 'Your magic link')]")
        
        if not magic_link_emails:
            raise Exception("No magic link emails found")
        
        print(f"Found {len(magic_link_emails)} magic link emails")
        
        # Click the most recent magic link email
        magic_link_emails[0].click()
        time.sleep(10)
        
        # Step 5: Extract magic link from email
        current_step += 1
        if update_callback:
            update_callback(current_step/total_steps*100, "Downloading Westwood One - Extracting magic link")
        
        magic_link = None
        
        # Switch to the iframe and extract the magic link
        try:
            print("Switching to iframe...")
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    login_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Login to CDN')]")
                    if login_links:
                        magic_link = login_links[0].get_attribute('href')
                        print(f"Found magic link: {magic_link}")
                        driver.switch_to.default_content()
                        break
                    driver.switch_to.default_content()
                except:
                    driver.switch_to.default_content()
        except Exception as e:
            print(f"Error extracting magic link: {e}")
            driver.switch_to.default_content()
        
        if not magic_link:
            raise Exception("Could not find magic link in email")
        
        # Step 6: Use magic link to authenticate
        current_step += 1
        if update_callback:
            update_callback(current_step/total_steps*100, "Downloading Westwood One - Authenticating")
        
        print(f"Navigating to magic link: {magic_link}")
        driver.get(magic_link)
        time.sleep(5)
        
        # Verify we're authenticated
        if "packages" in driver.current_url or "cdn.westwoodone.com" in driver.current_url:
            print("Successfully authenticated!")
        else:
            print(f"Current URL after authentication: {driver.current_url}")
        
        # Step 7: Find and click the specific package
        current_step += 1
        if update_callback:
            update_callback(current_step/total_steps*100, "Downloading Westwood One - Finding package")
        
        # Wait for packages page to load
        time.sleep(3)
        
        # Look for the specific package "Country Nights Live w Bev Rainey ROS_A"
        package_link = None
        package_selectors = [
            f"//a[contains(text(), 'Country Nights Live w Bev Rainey ROS_A')]",
            f"//*[contains(text(), 'Country Nights Live w Bev Rainey ROS_A')]",
            f"//a[contains(., 'Country Nights Live')]",
            f"//*[contains(., 'Country Nights Live')]"
        ]
        
        for selector in package_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        package_link = element
                        print(f"Found package link with selector: {selector}")
                        break
                if package_link:
                    break
            except:
                continue
        
        if not package_link:
            raise Exception("Could not find 'Country Nights Live w Bev Rainey ROS_A' package")
        
        # Click the package link
        print("Clicking package link...")
        package_link.click()
        time.sleep(5)
        
        # Step 8: Click download button
        current_step += 1
        if update_callback:
            update_callback(current_step/total_steps*100, "Downloading Westwood One - Downloading files")
        
        # Use the exact XPath you provided
        download_button_xpath = "/html/body/main/div[2]/div/div/div/div/div/table/tbody/tr[1]/td/a"
        
        try:
            # Wait for the download button to be present and clickable
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, download_button_xpath))
            )
            print(f"Found download button with exact XPath")
            print(f"Download button text: {download_button.text}")
            
            # Get the file list before downloading to compare later
            files_before_download = set(glob.glob(os.path.join(download_dir, '*')))
            print(f"Files in download directory before: {len(files_before_download)}")
            
            # Click the download button
            print("Clicking download button...")
            download_button.click()
            time.sleep(145)  # Wait longer for download to complete
            
            print("Download initiated successfully!")
            
        except Exception as e:
            print(f"Error clicking download button: {e}")
            raise Exception(f"Could not click download button: {e}")
        
        # Step 9: Extract ZIP file
        current_step += 1
        if update_callback:
            update_callback(current_step/total_steps*100, "Downloading Westwood One - Extracting files")
        
        # Use your function to find the latest downloaded file
        print("Looking for the downloaded file...")
        downloaded_file = findLatestFile()
        
        if not downloaded_file:
            raise Exception("No downloaded file found")
        
        print(f"Found downloaded file: {downloaded_file}")

                # Define extraction directory
        extract_dir = Path(download_dir, "Westwood One")
        
        # Create extraction directory if it doesn't exist
        extract_dir.mkdir(exist_ok=True)
        print(f"Extraction directory: {extract_dir.absolute()}")
        
        # Check if it's a ZIP file
        if not downloaded_file.lower().endswith('.zip'):
            print(f"Warning: Downloaded file is not a ZIP file: {downloaded_file}")
            # But let's try to extract it anyway in case it's a ZIP with wrong extension
            if not any(downloaded_file.lower().endswith(ext) for ext in ['.zip', '.rar', '.7z']):
                raise Exception(f"Downloaded file is not a supported archive: {downloaded_file}")
        
        # Extract the file
        print(f"Extracting {os.path.basename(downloaded_file)} to {extract_dir}...")
        try:
            with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print(f"Successfully extracted {len(zip_ref.namelist())} files to '{extract_dir}'")
            
            # List extracted files
            extracted_files = list(extract_dir.rglob("*"))
            print(f"Extracted files:")
            for file in extracted_files:
                if file.is_file():
                    print(f"  - {file.name}")
                    
        except zipfile.BadZipFile:
            raise Exception(f"File {downloaded_file} is not a valid ZIP file")
        except Exception as e:
            raise Exception(f"Error extracting file: {e}")
        
        # Step 10: Complete
        current_step += 1
        os.remove(downloaded_file)
        if update_callback:
            update_callback(current_step/total_steps*100, "Downloading Westwood One - Complete")
        
        print("Process completed successfully!")
        print(f"Files extracted to: {extract_dir.absolute()}")
        
        # Auto-close browser if enabled
        if config["auto_close_browser"]:
            close_browser()
        
        return True
        
    except Exception as e:
        print(f"Error in downloadWWO: {e}")
        import traceback
        traceback.print_exc()
        # Auto-close browser even on error if enabled
        if config["auto_close_browser"]:
            close_browser()
        return False

# Enhanced GUI Functions
def update_progress(value, status_text=""):
    """Update progress bar and status from any thread"""
    def update_ui():
        progress_bar['value'] = value
        if status_text:
            status_var.set(status_text)
        root.update_idletasks()
    
    root.after(0, update_ui)

def log_message(message):
    """Add message to log viewer"""
    if 'log_text' in globals():
        log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_text.insert(tk.END, f"{timestamp} - {message}\n")
        log_text.config(state=tk.DISABLED)
        log_text.see(tk.END)

def download_with_retry(func, name, max_retries=2):
    """Wrapper function to automatically retry failed downloads"""
    for attempt in range(max_retries + 1):
        try:
            success = func()
            if success:
                log_message(f"✓ {name} completed successfully")
                return True
            elif attempt < max_retries:
                log_message(f"↻ Retrying {name} (attempt {attempt + 1})...")
                time.sleep(3)
        except Exception as e:
            if attempt < max_retries:
                log_message(f"↻ Error in {name}, retrying... ({str(e)})")
                time.sleep(3)
    
    log_message(f"✗ {name} failed after {max_retries + 1} attempts")
    return False

def run_download_function(func, name):
    def wrapper():
        progress_bar['value'] = 0
        status_var.set(f"Starting {name}...")
        log_message(f"Starting {name} download...")
        
        def download_thread():
            try:
                success = download_with_retry(lambda: func(update_progress), name, config["retry_attempts"])
                if success:
                    status_var.set(f"✓ {name} completed!")
                    messagebox.showinfo("Success", f"{name} download completed successfully!")
                else:
                    status_var.set(f"✗ {name} failed")
                    messagebox.showerror("Error", f"{name} download failed after retries.")
            except Exception as e:
                status_var.set(f"✗ {name} error")
                log_message(f"Error in {name}: {str(e)}")
                messagebox.showerror("Error", f"Error downloading {name}: {str(e)}")
            finally:
                root.after(2000, lambda: progress_bar.configure(value=0))
        
        threading.Thread(target=download_thread, daemon=True).start()
    return wrapper

def run_all_downloads():
    def download_all_thread():
        functions = [
            ("Melinda Myers", downloadMelindaMyers),
            ("Northwest Outdoors", downloadNWO),
            ("Whittler", downloadWhittler),
            ("Westwood One", downloadWWO)
        ]
        
        success_count = 0
        failed_downloads = []
        
        for i, (name, func) in enumerate(functions):
            progress = (i / len(functions)) * 100
            update_progress(progress, f"Downloading all - Starting: {name} ({i+1}/{len(functions)})")
            
            success = download_with_retry(func, name, config["retry_attempts"])
            if success:
                success_count += 1
            else:
                failed_downloads.append(name)
        
        update_progress(100, "All downloads completed!")
        show_summary_popup(success_count, len(functions), failed_downloads)
    
    threading.Thread(target=download_all_thread, daemon=True).start()

def run_all_downloads_silent():
    """Run all downloads without showing progress dialogs (for scheduler)"""
    def download_all_thread():
        functions = [
            ("Melinda Myers", downloadMelindaMyers),
            ("Northwest Outdoors", downloadNWO),
            ("Whittler", downloadWhittler),
            ("Westwood One", downloadWWO)
        ]
        
        success_count = 0
        total_count = len(functions)
        
        for name, func in functions:
            try:
                success = func()
                if success:
                    success_count += 1
                    log_message(f"✓ {name} completed")
                else:
                    log_message(f"✗ {name} failed")
            except Exception as e:
                log_message(f"✗ Error in {name}: {e}")
        
        log_message(f"Scheduled downloads completed: {success_count}/{total_count} successful")
    
    threading.Thread(target=download_all_thread, daemon=True).start()

def show_summary_popup(success_count, total_count, failed_list):
    """Show a friendly summary when downloads complete"""
    summary_window = tk.Toplevel(root)
    summary_window.title("Download Summary")
    summary_window.geometry("400x250")
    summary_window.transient(root)
    summary_window.grab_set()
    
    if failed_list:
        message = f"Completed: {success_count}/{total_count} downloads\n\nFailed:\n" + "\n".join(f"• {item}" for item in failed_list)
        icon = "⚠️"
        title = "Downloads Partially Completed"
    else:
        message = f"All {total_count} downloads completed successfully! 🎉"
        icon = "✅"
        title = "Downloads Completed"
    
    ttk.Label(summary_window, text=icon, font=("Arial", 24)).pack(pady=10)
    ttk.Label(summary_window, text=title, font=("Arial", 12, "bold")).pack(pady=5)
    ttk.Label(summary_window, text=message, wraplength=350).pack(pady=10, padx=20)
    ttk.Button(summary_window, text="OK", command=summary_window.destroy).pack(pady=10)

# Scheduler Functions
def update_scheduler():
    """Update the schedule based on current configuration"""
    scheduler.clear_jobs()
    
    if not config["scheduled_downloads"]["enabled"]:
        log_message("Scheduler disabled")
        return
    
    schedule_type = config["scheduled_downloads"]["schedule_type"]
    time_str = config["scheduled_downloads"]["time"]
    
    # Validate time format
    try:
        datetime.strptime(time_str, '%H:%M')
    except ValueError:
        log_message(f"Invalid time format: {time_str} - using 06:00")
        time_str = "06:00"
        config["scheduled_downloads"]["time"] = time_str
    
    job_func = create_scheduled_job()
    
    # Map full day names to abbreviated
    day_map = {
        "Monday": "Mon", "Tuesday": "Tue", "Wednesday": "Wed",
        "Thursday": "Thu", "Friday": "Fri", "Saturday": "Sat", "Sunday": "Sun"
    }
    
    days = config["scheduled_downloads"]["days"]
    abbreviated_days = [day_map.get(day, day[:3]) for day in days]
    
    scheduler.add_job(job_func, schedule_type, time_str, abbreviated_days)
    
    if schedule_type == "daily":
        log_message(f"Scheduled daily downloads at {time_str}")
    elif schedule_type == "weekly":
        log_message(f"Scheduled weekly downloads on {', '.join(days)} at {time_str}")

def run_scheduler():
    """Run the scheduler in a background thread"""
    scheduler.start()
    log_message("Scheduler started")

def create_scheduled_job():
    """Create a job function for scheduled downloads"""
    def scheduled_download_job():
        log_message("🕒 Starting scheduled download...")
        
        # Run in a separate thread to avoid blocking the scheduler
        def run_download():
            if config["scheduled_downloads"]["download_all"]:
                # Run all downloads
                run_all_downloads_silent()
            else:
                # Run only selected sources
                selected_sources = config["scheduled_downloads"]["selected_sources"]
                source_map = {
                    "Melinda Myers": downloadMelindaMyers,
                    "Northwest Outdoors": downloadNWO,
                    "Whittler": downloadWhittler,
                    "Westwood One": downloadWWO
                }
                
                for source_name in selected_sources:
                    if source_name in source_map:
                        log_message(f"Scheduled download: {source_name}")
                        try:
                            source_map[source_name]()
                        except Exception as e:
                            log_message(f"Error in scheduled download {source_name}: {e}")
        
        # Start the download in a separate thread
        download_thread = threading.Thread(target=run_download, daemon=True)
        download_thread.start()
    
    return scheduled_download_job

def create_scheduler():
    def save_schedule():
        # Get values from UI
        config["scheduled_downloads"]["enabled"] = enable_var.get()
        config["scheduled_downloads"]["schedule_type"] = schedule_type_var.get()
        config["scheduled_downloads"]["time"] = time_var.get()
        config["scheduled_downloads"]["download_all"] = download_all_var.get()
        
        # Get selected days
        selected_days = []
        for day, var in day_vars.items():
            if var.get():
                selected_days.append(day)
        config["scheduled_downloads"]["days"] = selected_days
        
        # Get selected sources if not downloading all
        selected_sources = []
        if not download_all_var.get():
            for source, var in source_vars.items():
                if var.get():
                    selected_sources.append(source)
        config["scheduled_downloads"]["selected_sources"] = selected_sources
        
        save_config(config)
        update_scheduler()
        messagebox.showinfo("Scheduler", "Schedule saved successfully!")
        scheduler_window.destroy()

    def toggle_schedule_type(*args):
        schedule_type = schedule_type_var.get()
        if schedule_type == "daily":
            days_frame.grid_remove()
        elif schedule_type == "weekly":
            days_frame.grid()

    def toggle_download_all(*args):
        if download_all_var.get():
            sources_frame.grid_remove()
        else:
            sources_frame.grid()

    # Create scheduler window
    scheduler_window = tk.Toplevel(root)
    scheduler_window.title("Download Scheduler")
    scheduler_window.geometry("600x800")
    scheduler_window.transient(root)
    scheduler_window.grab_set()

    main_frame = ttk.Frame(scheduler_window, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Title
    ttk.Label(main_frame, text="Download Scheduler", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))

    # Enable scheduling
    enable_var = tk.BooleanVar(value=config["scheduled_downloads"]["enabled"])
    ttk.Checkbutton(main_frame, text="Enable scheduled downloads", variable=enable_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)

    # Schedule type
    ttk.Label(main_frame, text="Schedule Type:").grid(row=2, column=0, sticky=tk.W, pady=5)
    schedule_type_var = tk.StringVar(value=config["scheduled_downloads"]["schedule_type"])
    schedule_combo = ttk.Combobox(main_frame, textvariable=schedule_type_var, values=["daily", "weekly"], state="readonly")
    schedule_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
    schedule_combo.bind('<<ComboboxSelected>>', toggle_schedule_type)

    # Time selection
    ttk.Label(main_frame, text="Start Time:").grid(row=3, column=0, sticky=tk.W, pady=5)
    time_var = tk.StringVar(value=config["scheduled_downloads"]["time"])
    time_entry = ttk.Entry(main_frame, textvariable=time_var, width=10)
    time_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
    ttk.Label(main_frame, text="(24-hour format, e.g., 06:00)").grid(row=4, column=1, sticky=tk.W)

    # Days selection (for weekly)
    days_frame = ttk.Frame(main_frame)
    days_frame.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=10)
    
    ttk.Label(days_frame, text="Download on days:").grid(row=0, column=0, columnspan=7, sticky=tk.W, pady=5)
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_vars = {}
    for i, day in enumerate(days):
        day_vars[day] = tk.BooleanVar(value=day in config["scheduled_downloads"]["days"])
        ttk.Checkbutton(days_frame, text=day, variable=day_vars[day]).grid(row=1, column=i, padx=5)

    # Download selection
    ttk.Label(main_frame, text="Download:").grid(row=6, column=0, sticky=tk.W, pady=10)
    download_all_var = tk.BooleanVar(value=config["scheduled_downloads"]["download_all"])
    ttk.Radiobutton(main_frame, text="All sources", variable=download_all_var, value=True, command=toggle_download_all).grid(row=6, column=1, sticky=tk.W, pady=2)
    ttk.Radiobutton(main_frame, text="Selected sources", variable=download_all_var, value=False, command=toggle_download_all).grid(row=7, column=1, sticky=tk.W, pady=2)

    # Sources selection
    sources_frame = ttk.Frame(main_frame)
    sources_frame.grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=10)
    
    sources = ["Melinda Myers", "Northwest Outdoors", "Whittler", "Westwood One"]
    source_vars = {}
    for i, source in enumerate(sources):
        source_vars[source] = tk.BooleanVar(value=source in config["scheduled_downloads"]["selected_sources"])
        ttk.Checkbutton(sources_frame, text=source, variable=source_vars[source]).grid(row=i, column=0, sticky=tk.W, pady=2)

    # Current schedule status
    status_frame = ttk.LabelFrame(main_frame, text="Current Schedule Status", padding="10")
    status_frame.grid(row=9, column=0, columnspan=2, sticky=tk.W+tk.E, pady=20)
    
    status_text = tk.StringVar()
    status_label = ttk.Label(status_frame, textvariable=status_text, wraplength=400)
    status_label.pack(anchor=tk.W)
    
    def update_status_display():
        if config["scheduled_downloads"]["enabled"]:
            schedule_type = config["scheduled_downloads"]["schedule_type"]
            time_str = config["scheduled_downloads"]["time"]
            
            if schedule_type == "daily":
                status = f"Downloads scheduled daily at {time_str}"
            elif schedule_type == "weekly":
                days_str = ", ".join(config["scheduled_downloads"]["days"])
                status = f"Downloads scheduled weekly on {days_str} at {time_str}"
            
            if config["scheduled_downloads"]["download_all"]:
                status += " - All sources"
            else:
                sources_str = ", ".join(config["scheduled_downloads"]["selected_sources"])
                status += f" - Sources: {sources_str}"
        else:
            status = "Scheduled downloads are disabled"
        
        status_text.set(status)
    
    update_status_display()

    # Buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=10, column=0, columnspan=2, pady=20)
    
    ttk.Button(button_frame, text="Save Schedule", command=save_schedule).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Cancel", command=scheduler_window.destroy).pack(side=tk.LEFT, padx=5)

    # Initial UI state
    toggle_schedule_type()
    toggle_download_all()

def create_settings():
    """Settings window with email and password fields"""
    def browse_folder():
        folder = filedialog.askdirectory(initialdir=download_dir)
        if folder:
            folder_var.set(folder)
    
    def save_settings():
        config["download_dir"] = folder_var.get()
        config["auto_close_browser"] = close_var.get()
        config["retry_attempts"] = int(retry_var.get())
        config["email"] = email_var.get()
        config["password"] = password_var.get()
        save_config(config)
        messagebox.showinfo("Settings", "Settings saved successfully!")
        settings_window.destroy()
    
    def close_settings():
        settings_window.destroy()
    
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("500x800") 
    settings_window.transient(root)
    settings_window.grab_set()
    
    # Main frame for settings with centering
    settings_frame = ttk.Frame(settings_window, padding="30")
    settings_frame.pack(fill=tk.BOTH, expand=True)
    
    folder_var = tk.StringVar(value=config["download_dir"])
    close_var = tk.BooleanVar(value=config["auto_close_browser"])
    retry_var = tk.StringVar(value=str(config["retry_attempts"]))
    email_var = tk.StringVar(value=config["email"])
    password_var = tk.StringVar(value=config["password"])
    
    # Title
    title_label = ttk.Label(settings_frame, text="Settings", style="Bold.TLabel")
    title_label.pack(pady=(0, 20))
    
    # Download Folder section (centered)
    folder_frame = ttk.Frame(settings_frame)
    folder_frame.pack(fill=tk.X, pady=10)
    
    ttk.Label(folder_frame, text="Download Folder:").pack(anchor=tk.CENTER)
    
    folder_entry_frame = ttk.Frame(folder_frame)
    folder_entry_frame.pack(fill=tk.X, pady=5)
    folder_entry = ttk.Entry(folder_entry_frame, textvariable=folder_var)
    folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Button(folder_entry_frame, text="Browse...", command=browse_folder).pack(side=tk.RIGHT)
    
    # Email section
    email_frame = ttk.Frame(settings_frame)
    email_frame.pack(fill=tk.X, pady=10)
    
    ttk.Label(email_frame, text="Email:").pack(anchor=tk.CENTER)
    email_entry = ttk.Entry(email_frame, textvariable=email_var, width=40)
    email_entry.pack(pady=5, fill=tk.X)
    
    # Password section
    password_frame = ttk.Frame(settings_frame)
    password_frame.pack(fill=tk.X, pady=10)
    
    ttk.Label(password_frame, text="Password:").pack(anchor=tk.CENTER)
    password_entry = ttk.Entry(password_frame, textvariable=password_var, width=40, show="*")
    password_entry.pack(pady=5, fill=tk.X)
    
    # Auto-close browser option (centered)
    close_frame = ttk.Frame(settings_frame)
    close_frame.pack(fill=tk.X, pady=15)
    ttk.Checkbutton(close_frame, text="Automatically close browser after download", 
                   variable=close_var).pack(anchor=tk.CENTER)
    
    # Retry attempts (centered)
    retry_frame = ttk.Frame(settings_frame)
    retry_frame.pack(fill=tk.X, pady=15)
    
    ttk.Label(retry_frame, text="Retry Attempts:").pack(anchor=tk.CENTER)
    retry_combo = ttk.Combobox(retry_frame, textvariable=retry_var, 
                              values=["0", "1", "2", "3"], width=10)
    retry_combo.pack(pady=5, anchor=tk.CENTER)
    
    # Scheduler button (centered)
    scheduler_btn = ttk.Button(settings_frame, text="Configure Scheduler...", 
                              command=create_scheduler, width=20)
    scheduler_btn.pack(pady=10)
    
    # Button frame for Save and Close (centered)
    button_frame = ttk.Frame(settings_frame)
    button_frame.pack(pady=30)
    
    ttk.Button(button_frame, text="Save Settings", command=save_settings, width=15).pack(side=tk.LEFT, padx=10)
    ttk.Button(button_frame, text="Close", command=close_settings, width=15).pack(side=tk.LEFT, padx=10)

    # Configure style for bold label
    style = ttk.Style()
    style.configure("Bold.TLabel", font=("Arial", 12, "bold"))

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit? This will close the browser if it's open."):
        scheduler.stop()  # Stop the scheduler
        close_browser()
        root.destroy()
        sys.exit()

# Create GUI (browser will not start until a download button is pressed)
root = tk.Tk()
root.title("Audio Download Manager")
root.geometry("600x800")  # Larger main window for better log viewing

# Create main interface
main_frame = ttk.Frame(root, padding="20")
main_frame.pack(fill=tk.BOTH, expand=True)

# Center the title
title_label = ttk.Label(main_frame, text="Audio Download Manager", font=("Arial", 16, "bold"))
title_label.grid(row=0, column=0, pady=(0, 20))

# Download buttons (centered)
download_functions = [
    ("Melinda Myers", downloadMelindaMyers),
    ("Northwest Outdoors", downloadNWO),
    ("Whittler", downloadWhittler),
    ("Westwood One", downloadWWO)
]

for i, (name, func) in enumerate(download_functions):
    btn = ttk.Button(main_frame, text=f"Download {name}", command=run_download_function(func, name), width=25)
    btn.grid(row=i+2, column=0, pady=8)

# Control buttons (centered)
all_btn = ttk.Button(main_frame, text="Download All", command=run_all_downloads, width=25)
all_btn.grid(row=1, column=0, pady=12)

settings_btn = ttk.Button(main_frame, text="Settings", command=create_settings, width=25)
settings_btn.grid(row=len(download_functions)+2, column=0, pady=8)


# Progress bar (centered and expanded)
progress_bar = ttk.Progressbar(main_frame, orient='horizontal', mode='determinate', length=400, maximum=100)
progress_bar.grid(row=len(download_functions)+4, column=0, pady=15, sticky=(tk.W, tk.E))

# Status label (centered)
status_var = tk.StringVar(value="Ready to download - Browser will start when needed")
status_label = ttk.Label(main_frame, textvariable=status_var, wraplength=500)
status_label.grid(row=len(download_functions)+5, column=0, pady=5)

# Log viewer (centered and expanded)
log_frame = ttk.LabelFrame(main_frame, text="Download Log", padding="10")
log_frame.grid(row=len(download_functions)+6, column=0, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))

log_text = scrolledtext.ScrolledText(log_frame, height=12, width=70, wrap=tk.WORD)
log_text.pack(fill=tk.BOTH, expand=True)
log_text.config(state=tk.DISABLED)

# Configure grid weights for centering and expansion
main_frame.columnconfigure(0, weight=1)  # Center everything in column 0
main_frame.rowconfigure(len(download_functions)+6, weight=1)  # Let log viewer expand

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the scheduler when application starts
update_scheduler()
run_scheduler()

log_message("Application started - Browser will open when downloads begin")
log_message("Scheduler started - Scheduled downloads will run automatically")

root.mainloop()