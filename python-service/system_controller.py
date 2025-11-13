"""
System Controller Module
Handles Windows system automation and control
"""

import subprocess
import psutil
import logging
import requests
import time
from typing import List

logger = logging.getLogger(__name__)

class SystemController:
    def __init__(self):
        self.blocked_sites = set()
        self.browser_extension_url = "http://localhost:5000"
        
    def block_websites(self, sites: List[str]):
        """Block websites by adding to blocked sites list"""
        self.blocked_sites.update(sites)
        logger.info(f"🚫 Blocked {len(sites)} websites")
        
        # Notify browser extension
        self._notify_browser_extension("block_sites", {"sites": list(sites)})
    
    def unblock_websites(self, sites: List[str] = None):
        """Unblock websites"""
        if sites is None:
            self.blocked_sites.clear()
            logger.info("✅ Unblocked all websites")
        else:
            self.blocked_sites.difference_update(sites)
            logger.info(f"✅ Unblocked {len(sites)} websites")
        
        # Notify browser extension
        self._notify_browser_extension("unblock_sites", {"sites": sites or []})
    
    def close_application(self, app_name: str):
        """Close an application by name"""
        try:
            # Use PowerShell to close application
            cmd = f'Get-Process -Name "{app_name}" | Stop-Process -Force'
            subprocess.run(["powershell", "-Command", cmd], 
                         capture_output=True, text=True, check=True)
            logger.info(f"🔚 Closed application: {app_name}")
            return True
        except subprocess.CalledProcessError:
            logger.warning(f"⚠️ Could not close application: {app_name}")
            return False
    
    def minimize_window(self, window_title: str):
        """Minimize a window by title"""
        try:
            cmd = f'''
            Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices;
            public class Win32 {{
                [DllImport("user32.dll")] public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
                [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
            }}';
            $hwnd = [Win32]::FindWindow($null, "{window_title}");
            if ($hwnd -ne [IntPtr]::Zero) {{ [Win32]::ShowWindow($hwnd, 2) }}
            '''
            subprocess.run(["powershell", "-Command", cmd], 
                         capture_output=True, text=True, check=True)
            logger.info(f"📉 Minimized window: {window_title}")
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ Could not minimize window: {window_title}")
            return False
    
    def open_application(self, app_path: str):
        """Open an application"""
        try:
            subprocess.Popen(app_path, shell=True)
            logger.info(f"🚀 Opened application: {app_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Could not open application {app_path}: {e}")
            return False
    
    def run_command(self, command: str):
        """Run a shell command"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            logger.info(f"⚡ Executed command: {command}")
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            logger.error(f"❌ Command failed: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    def set_focus_environment(self):
        """Set up the environment for focus session"""
        logger.info("🎯 Setting up focus environment...")
        
        # Block common distracting sites
        distracting_sites = [
            "youtube.com",
            "facebook.com",
            "twitter.com", 
            "instagram.com",
            "reddit.com",
            "tiktok.com",
            "netflix.com"
        ]
        self.block_websites(distracting_sites)
        
        # Minimize distracting applications
        distracting_apps = ["Spotify", "Discord", "Slack"]
        for app in distracting_apps:
            self.minimize_window(app)
        
        # Set do not disturb mode
        self._set_do_not_disturb(True)
        
        # Notify browser extension to enter focus mode
        self._notify_browser_extension("enter_focus_mode", {})
    
    def set_break_environment(self):
        """Set up the environment for break session"""
        logger.info("☕ Setting up break environment...")
        
        # Allow some entertainment sites during break
        break_allowed_sites = ["youtube.com", "spotify.com"]
        self.unblock_websites(break_allowed_sites)
        
        # Notify browser extension to enter break mode
        self._notify_browser_extension("enter_break_mode", {})
    
    def restore_normal_environment(self):
        """Restore normal environment after sessions"""
        logger.info("🏠 Restoring normal environment...")
        
        # Unblock all sites
        self.unblock_websites()
        
        # Disable do not disturb
        self._set_do_not_disturb(False)
        
        # Notify browser extension to exit session mode
        self._notify_browser_extension("exit_session_mode", {})
    
    def _set_do_not_disturb(self, enabled: bool):
        """Set Windows do not disturb mode"""
        try:
            # Windows 10/11 Focus Assist
            value = 1 if enabled else 0
            cmd = f'New-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CloudStore\\Store\\Cache\\DefaultAccount" -Name "Current" -Value {value} -Force'
            subprocess.run(["powershell", "-Command", cmd], 
                         capture_output=True, text=True)
            logger.info(f"🔔 Do not disturb: {'enabled' if enabled else 'disabled'}")
        except Exception as e:
            logger.warning(f"⚠️ Could not set do not disturb: {e}")
    
    def _notify_browser_extension(self, action: str, data: dict):
        """Send notification to browser extension"""
        try:
            # This would typically send to the browser extension via messaging
            # For now, we'll log the action
            logger.info(f"📨 Browser notification: {action} with data: {data}")
            
            # In a real implementation, this might use native messaging
            # or a local WebSocket connection to communicate with the extension
            
        except Exception as e:
            logger.warning(f"⚠️ Could not notify browser extension: {e}")
    
    def get_running_applications(self) -> List[str]:
        """Get list of currently running applications"""
        try:
            apps = []
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    apps.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return list(set(apps))  # Remove duplicates
        except Exception as e:
            logger.error(f"❌ Could not get running applications: {e}")
            return []
    
    def get_system_stats(self) -> dict:
        """Get system performance statistics"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent if psutil.disk_usage('/') else 0,
                "running_processes": len(psutil.pids())
            }
        except Exception as e:
            logger.error(f"❌ Could not get system stats: {e}")
            return {}
