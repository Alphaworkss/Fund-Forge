import os
import sys
import time
import subprocess
import threading
import urllib.request
import webbrowser
import tkinter as tk
from tkinter import messagebox

# Path configuration for PyInstaller standalone executable vs Python script
if getattr(sys, 'frozen', False):
    # Executing as compiled binary (.exe)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Executing as standard python script (.pyw / .py)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Fallback to current working directory if folders are not relative to executable
if not os.path.exists(os.path.join(BASE_DIR, "backend")):
    BASE_DIR = os.getcwd()

BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
PUBLIC_DIR = os.path.join(FRONTEND_DIR, "public")

class SarmayaSaazLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("SarmayaSaaz — Platform Controller")
        self.root.geometry("620x480")
        self.root.resizable(False, False)
        
        # Color Palette (Dark Theme matching SarmayaSaaz design system)
        self.BG_DARK = "#0b1326"
        self.SURFACE = "#171f33"
        self.BORDER = "#2d3449"
        self.TEXT_PRIMARY = "#dae2fd"
        self.TEXT_SECONDARY = "#908f9e"
        self.INDIGO = "#818cf8"
        self.EMERALD = "#4edea3"
        self.ROSE = "#ffb2b7"

        self.root.configure(bg=self.BG_DARK)

        # Process references
        self.backend_process = None
        self.frontend_process = None
        self.hidden_features_enabled = False
        self.is_monitoring = True

        self._build_ui()
        
        # Start background health monitoring thread
        self.monitor_thread = threading.Thread(target=self._health_monitor_loop, daemon=True)
        self.monitor_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        # Header Container
        header_frame = tk.Frame(self.root, bg=self.SURFACE, highlightbackground=self.BORDER, highlightthickness=1)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = tk.Label(
            header_frame,
            text="SarmayaSaaz AI Platform",
            font=("Segoe UI", 18, "bold"),
            fg=self.TEXT_PRIMARY,
            bg=self.SURFACE
        )
        title_label.pack(anchor="w", padx=20, pady=(15, 2))

        subtitle_label = tk.Label(
            header_frame,
            text="Desktop Server Controller & Management Terminal",
            font=("Segoe UI", 9),
            fg=self.TEXT_SECONDARY,
            bg=self.SURFACE
        )
        subtitle_label.pack(anchor="w", padx=20, pady=(0, 15))

        # Status Cards Container
        status_frame = tk.Frame(self.root, bg=self.BG_DARK)
        status_frame.pack(fill="x", padx=20, pady=10)

        # Backend Status Badge
        self.backend_card = tk.Frame(status_frame, bg=self.SURFACE, highlightbackground=self.BORDER, highlightthickness=1)
        self.backend_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(self.backend_card, text="BACKEND API (PORT 8000)", font=("Consolas", 8, "bold"), fg=self.TEXT_SECONDARY, bg=self.SURFACE).pack(anchor="w", padx=15, pady=(12, 2))
        self.backend_status_lbl = tk.Label(self.backend_card, text="● OFFLINE", font=("Consolas", 11, "bold"), fg=self.ROSE, bg=self.SURFACE)
        self.backend_status_lbl.pack(anchor="w", padx=15, pady=(0, 12))

        # Frontend Status Badge
        self.frontend_card = tk.Frame(status_frame, bg=self.SURFACE, highlightbackground=self.BORDER, highlightthickness=1)
        self.frontend_card.pack(side="right", fill="both", expand=True, padx=(10, 0))

        tk.Label(self.frontend_card, text="FRONTEND DASHBOARD (PORT 3000)", font=("Consolas", 8, "bold"), fg=self.TEXT_SECONDARY, bg=self.SURFACE).pack(anchor="w", padx=15, pady=(12, 2))
        self.frontend_status_lbl = tk.Label(self.frontend_card, text="● OFFLINE", font=("Consolas", 11, "bold"), fg=self.ROSE, bg=self.SURFACE)
        self.frontend_status_lbl.pack(anchor="w", padx=15, pady=(0, 12))

        # Main Action Controls
        controls_frame = tk.Frame(self.root, bg=self.SURFACE, highlightbackground=self.BORDER, highlightthickness=1)
        controls_frame.pack(fill="x", padx=20, pady=10)

        btn_container = tk.Frame(controls_frame, bg=self.SURFACE)
        btn_container.pack(padx=20, pady=15)

        self.btn_start = tk.Button(
            btn_container,
            text="▶ Start Platform",
            font=("Segoe UI", 10, "bold"),
            bg=self.INDIGO,
            fg="#131e8c",
            activebackground=self.EMERALD,
            activeforeground="#131e8c",
            relief="flat",
            padx=15, pady=8,
            cursor="hand2",
            command=self.start_servers
        )
        self.btn_start.pack(side="left", padx=5)

        self.btn_stop = tk.Button(
            btn_container,
            text="■ Stop Platform",
            font=("Segoe UI", 10, "bold"),
            bg="#222a3d",
            fg=self.ROSE,
            activebackground=self.ROSE,
            activeforeground="#131e8c",
            relief="flat",
            padx=15, pady=8,
            cursor="hand2",
            command=self.stop_servers
        )
        self.btn_stop.pack(side="left", padx=5)

        self.btn_browser = tk.Button(
            btn_container,
            text="🌐 Open Browser",
            font=("Segoe UI", 10, "bold"),
            bg="#0b1326",
            fg=self.TEXT_PRIMARY,
            activebackground=self.INDIGO,
            activeforeground="#131e8c",
            relief="flat",
            padx=15, pady=8,
            cursor="hand2",
            command=self.open_browser
        )
        self.btn_browser.pack(side="left", padx=5)

        # Feature Toggles Container
        toggles_frame = tk.Frame(self.root, bg=self.SURFACE, highlightbackground=self.BORDER, highlightthickness=1)
        toggles_frame.pack(fill="x", padx=20, pady=(0, 20))

        tk.Label(
            toggles_frame,
            text="PLATFORM CONFIGURATION & HIDDEN FEATURES",
            font=("Consolas", 8, "bold"),
            fg=self.TEXT_SECONDARY,
            bg=self.SURFACE
        ).pack(anchor="w", padx=20, pady=(12, 4))

        toggle_subframe = tk.Frame(toggles_frame, bg=self.SURFACE)
        toggle_subframe.pack(fill="x", padx=20, pady=(0, 12))

        self.btn_toggle_features = tk.Button(
            toggle_subframe,
            text="🔒 Hidden Features: DISABLED",
            font=("Segoe UI", 9, "bold"),
            bg="#0b1326",
            fg=self.TEXT_SECONDARY,
            activebackground=self.INDIGO,
            relief="flat",
            padx=10, pady=4,
            cursor="hand2",
            command=self.toggle_hidden_features
        )
        self.btn_toggle_features.pack(side="left")

        self.lbl_feature_hint = tk.Label(
            toggle_subframe,
            text="(Paper Trading, Simulator & News Feed)",
            font=("Segoe UI", 8),
            fg=self.TEXT_SECONDARY,
            bg=self.SURFACE
        )
        self.lbl_feature_hint.pack(side="left", padx=10)

    def toggle_hidden_features(self):
        self.hidden_features_enabled = not self.hidden_features_enabled
        if self.hidden_features_enabled:
            self.btn_toggle_features.config(
                text="🔓 Hidden Features: ACTIVATED",
                bg=self.EMERALD,
                fg="#003824"
            )
            messagebox.showinfo(
                "Hidden Features Activated",
                "Hidden features (Paper Trading & News Overlay) are now ENABLED!\n\nClick 'Start Platform' or 'Open Browser' to launch with hidden features active."
            )
        else:
            self.btn_toggle_features.config(
                text="🔒 Hidden Features: DISABLED",
                bg="#0b1326",
                fg=self.TEXT_SECONDARY
            )
            messagebox.showinfo(
                "Hidden Features Disabled",
                "Hidden features are now DISABLED!\n\nClick 'Start Platform' or 'Open Browser' to launch with hidden features disabled."
            )

        # Sync runtime JSON configuration
        self._sync_frontend_env()

    def _sync_frontend_env(self):
        """Write feature-flags.json and .env.local into frontend"""
        flag_bool = self.hidden_features_enabled
        flag_val = "true" if flag_bool else "false"

        # 1. Write public/feature-flags.json for static runtime fetching
        try:
            if not os.path.exists(PUBLIC_DIR):
                os.makedirs(PUBLIC_DIR, exist_ok=True)
            json_file_path = os.path.join(PUBLIC_DIR, "feature-flags.json")
            with open(json_file_path, "w", encoding="utf-8") as f:
                f.write(f'{{"enableHiddenFeatures": {flag_val}}}\n')
        except Exception as e:
            print(f"Warning writing feature-flags.json: {e}")

        # 2. Write frontend/.env.local
        try:
            env_file_path = os.path.join(FRONTEND_DIR, ".env.local")
            with open(env_file_path, "w", encoding="utf-8") as f:
                f.write(f"NEXT_PUBLIC_ENABLE_HIDDEN_FEATURES={flag_val}\n")
        except Exception as e:
            print(f"Warning writing .env.local: {e}")

    def start_servers(self):
        # Verify Directory Paths
        if not os.path.exists(BACKEND_DIR) or not os.path.exists(FRONTEND_DIR):
            messagebox.showerror(
                "Directory Path Error",
                f"Could not locate workspace directories.\n\nBackend Path: {BACKEND_DIR}\nFrontend Path: {FRONTEND_DIR}"
            )
            return

        # Sync runtime JSON feature flags
        self._sync_frontend_env()

        # Start Backend (Uvicorn FastAPI via python executable)
        if not self._check_port_active(8000):
            try:
                cmd_backend = ["python", "-m", "uvicorn", "app.main:app", "--port", "8000"]
                self.backend_process = subprocess.Popen(
                    cmd_backend,
                    cwd=BACKEND_DIR,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
            except Exception as e:
                messagebox.showerror("Backend Startup Error", f"Failed to launch FastAPI backend: {e}")

        # Start Frontend (Next.js npm run dev)
        if not self._check_port_active(3000):
            try:
                env = os.environ.copy()
                env["NEXT_PUBLIC_ENABLE_HIDDEN_FEATURES"] = "true" if self.hidden_features_enabled else "false"

                cmd_frontend = ["cmd", "/c", "npm", "run", "dev"] if os.name == 'nt' else ["npm", "run", "dev"]
                self.frontend_process = subprocess.Popen(
                    cmd_frontend,
                    cwd=FRONTEND_DIR,
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
            except Exception as e:
                messagebox.showerror("Frontend Startup Error", f"Failed to launch Next.js frontend: {e}")

        # Auto open browser after 3.5 seconds
        self.root.after(3500, self.open_browser)

    def _kill_process_on_port(self, port):
        """Robustly find and terminate all processes listening on a given port on Windows."""
        if os.name == 'nt':
            try:
                output = subprocess.check_output(
                    f'netstat -ano | findstr LISTENING | findstr :{port}',
                    shell=True,
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                for line in output.strip().split('\n'):
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        if pid.isdigit() and pid != '0':
                            subprocess.run(
                                f'taskkill /F /PID {pid} /T',
                                shell=True,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
            except Exception:
                pass

    def stop_servers(self):
        # Kill backend process handle if active
        if self.backend_process:
            try:
                self.backend_process.terminate()
            except Exception:
                pass
            self.backend_process = None

        # Kill frontend process handle if active
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
            except Exception:
                pass
            self.frontend_process = None

        # Force kill any remaining processes listening on ports 8000 and 3000
        self._kill_process_on_port(8000)
        self._kill_process_on_port(3000)

        messagebox.showinfo("Platform Servers Stopped", "SarmayaSaaz backend (Port 8000) and frontend (Port 3000) have been fully stopped.")

    def open_browser(self):
        self._sync_frontend_env()
        url = "http://localhost:3000/?hidden_features=true" if self.hidden_features_enabled else "http://localhost:3000/?hidden_features=false"
        webbrowser.open(url)

    def _check_port_active(self, port):
        try:
            url = f"http://127.0.0.1:{port}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=1) as response:
                return True
        except Exception:
            return False

    def _health_monitor_loop(self):
        while self.is_monitoring:
            backend_live = self._check_port_active(8000)
            frontend_live = self._check_port_active(3000)

            def update_labels():
                if backend_live:
                    self.backend_status_lbl.config(text="● ONLINE (Port 8000)", fg=self.EMERALD)
                else:
                    self.backend_status_lbl.config(text="● OFFLINE", fg=self.ROSE)

                if frontend_live:
                    self.frontend_status_lbl.config(text="● ONLINE (Port 3000)", fg=self.EMERALD)
                else:
                    self.frontend_status_lbl.config(text="● OFFLINE", fg=self.ROSE)

            try:
                self.root.after(0, update_labels)
            except Exception:
                break
            time.sleep(2)

    def on_close(self):
        self.is_monitoring = False
        self.stop_servers()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SarmayaSaazLauncher(root)
    root.mainloop()
