import os
import socket
import subprocess
import sys
import time
import webbrowser
import ctypes
from ctypes import wintypes
from tkinter import StringVar, Tk, ttk, messagebox
from urllib.request import urlopen


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_URL = "http://localhost:8501"


if os.name == "nt":
    class _JobObjectBasicLimitInformation(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
            ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.POINTER(ctypes.c_ulong)),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]


    class _IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", wintypes.ULARGE_INTEGER),
            ("WriteOperationCount", wintypes.ULARGE_INTEGER),
            ("OtherOperationCount", wintypes.ULARGE_INTEGER),
            ("ReadTransferCount", wintypes.ULARGE_INTEGER),
            ("WriteTransferCount", wintypes.ULARGE_INTEGER),
            ("OtherTransferCount", wintypes.ULARGE_INTEGER),
        ]


    class _JobObjectExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _JobObjectBasicLimitInformation),
            ("IoInfo", _IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]


    def _create_kill_on_close_job():
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        job_handle = kernel32.CreateJobObjectW(None, None)
        if not job_handle:
            return None

        limits = _JobObjectExtendedLimitInformation()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE
        success = kernel32.SetInformationJobObject(
            job_handle,
            9,  # JobObjectExtendedLimitInformation
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        )
        if not success:
            kernel32.CloseHandle(job_handle)
            return None
        return job_handle


    def _assign_to_job(job_handle, process_handle):
        if not job_handle:
            return False
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        return bool(kernel32.AssignProcessToJobObject(job_handle, process_handle))
else:
    def _create_kill_on_close_job():
        return None


    def _assign_to_job(job_handle, process_handle):
        return False


class DashboardLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Intelligence System")
        self.root.geometry("560x260")
        self.root.resizable(False, False)
        self.root.configure(bg="#eef3ff")

        self.server_process = None
        self.job_handle = _create_kill_on_close_job()
        self.url_var = StringVar(value=DEFAULT_URL)

        title = ttk.Label(
            root,
            text="Dashboard Launcher",
            font=("Segoe UI", 18, "bold"),
            background="#eef3ff",
            foreground="#1d3557",
        )
        title.pack(pady=(18, 5))

        subtitle = ttk.Label(
            root,
            text="Launch and manage your local Data Intelligence dashboard",
            font=("Segoe UI", 10),
            background="#eef3ff",
            foreground="#495057",
        )
        subtitle.pack(pady=(0, 12))

        url_frame = ttk.Frame(root, padding=10, style="Card.TFrame")
        url_frame.pack(fill="x", padx=24)

        ttk.Label(url_frame, text="Local URL", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Entry(url_frame, textvariable=self.url_var, width=60, font=("Segoe UI", 10)).pack(fill="x", pady=(6, 0))

        button_frame = ttk.Frame(root)
        button_frame.pack(pady=16)

        self.start_btn = ttk.Button(button_frame, text="Start App", command=self.start_app, width=16)
        self.start_btn.grid(row=0, column=0, padx=8)

        self.stop_btn = ttk.Button(button_frame, text="Stop App", command=self.stop_app, width=16)
        self.stop_btn.grid(row=0, column=1, padx=8)

        open_btn = ttk.Button(button_frame, text="Open Browser", command=self.open_browser, width=16)
        open_btn.grid(row=0, column=2, padx=8)

        self.status_var = StringVar(value="Ready")
        self.status_label = ttk.Label(
            root,
            textvariable=self.status_var,
            foreground="#2d6a4f",
            font=("Segoe UI", 10, "bold"),
            background="#eef3ff",
        )
        self.status_label.pack(pady=(0, 14))

        self.root.protocol("WM_DELETE_WINDOW", self.close_launcher)
        self.refresh_status()

    def _normalize_url(self, value):
        candidate = value.strip()
        if not candidate:
            return DEFAULT_URL
        if not candidate.startswith(("http://", "https://")):
            candidate = "http://" + candidate
        return candidate

    def _is_port_open(self, host="localhost", port=8501):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.connect((host, port))
            return True
        except OSError:
            return False
        finally:
            sock.close()

    def _wait_for_server(self, timeout=20):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._is_port_open():
                return True
            time.sleep(0.5)
        return False

    def refresh_status(self):
        if self.server_process and self.server_process.poll() is None:
            self.status_var.set("Server is running")
            self.status_label.configure(foreground="#2d6a4f")
            self.start_btn.state(["disabled"])
            self.stop_btn.state(["!disabled"])
        else:
            self.status_var.set("Ready")
            self.status_label.configure(foreground="#2d6a4f")
            self.start_btn.state(["!disabled"])
            self.stop_btn.state(["disabled"])

    def start_app(self):
        if self.server_process and self.server_process.poll() is None:
            self.status_var.set("Server is already running")
            self.status_label.configure(foreground="#0b7285")
            return

        self.status_var.set("Starting dashboard...")
        self.status_label.configure(foreground="#d97706")
        self.root.update_idletasks()

        try:
            self.server_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    "app.py",
                    "--server.headless",
                    "true",
                    "--server.port",
                    "8501",
                ],
                cwd=PROJECT_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if self.job_handle and not _assign_to_job(self.job_handle, self.server_process._handle):
                self.status_var.set("Could not attach shutdown tracking")

            if self._wait_for_server():
                self.status_var.set("Dashboard started successfully")
                self.status_label.configure(foreground="#2d6a4f")
                messagebox.showinfo("Dashboard Started", "The app is running on localhost:8501")
            else:
                self.status_var.set("Server did not respond in time")
                self.status_label.configure(foreground="#c1121f")
                messagebox.showwarning("Warning", "The app was launched, but it did not respond on the expected port.")
        except Exception as exc:
            self.status_var.set("Could not start the app")
            self.status_label.configure(foreground="#c1121f")
            messagebox.showerror("Startup Error", f"Unable to start the dashboard:\n{exc}")

        self.refresh_status()

    def stop_app(self):
        if self.server_process is None or self.server_process.poll() is not None:
            self.status_var.set("No app is running")
            self.status_label.configure(foreground="#495057")
            return

        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(self.server_process.pid), "/T", "/F"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                self.server_process.terminate()
            self.server_process.wait(timeout=10)
            self.status_var.set("Dashboard stopped")
            self.status_label.configure(foreground="#495057")
            messagebox.showinfo("Stopped", "The dashboard has been stopped successfully.")
        except Exception as exc:
            self.status_var.set("Stop failed")
            self.status_label.configure(foreground="#c1121f")
            messagebox.showerror("Error", f"Could not stop the dashboard:\n{exc}")
        finally:
            self.server_process = None
            self.refresh_status()

    def close_launcher(self):
        self.stop_app()
        if self.job_handle:
            ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle(self.job_handle)
            self.job_handle = None
        self.root.destroy()

    def open_browser(self):
        url = self._normalize_url(self.url_var.get())
        try:
            webbrowser.open(url)
            self.status_var.set(f"Opening {url}")
            self.status_label.configure(foreground="#2d6a4f")
        except Exception as exc:
            self.status_var.set("Browser could not open")
            self.status_label.configure(foreground="#e91c2a")
            messagebox.showerror("Browser Error", f"Could not open the browser:\n{exc}")


if __name__ == "__main__":
    root = Tk()
    app = DashboardLauncher(root)
    root.mainloop()
