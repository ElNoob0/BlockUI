
from flask import Flask, request, jsonify, abort
import ctypes
import os
import subprocess
import secrets
import time
from ctypes import wintypes

app = Flask(__name__)

# CONFIGURATION
PORT = 5000

# Change this to your web app's actual address
ALLOWED_ORIGINS = {
    "http://127.0.0.1:5500"
}

# Generate a private API token
TOKEN = secrets.token_urlsafe(32)

# Applications that the website is allowed to launch
APPS = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "paint": ["mspaint.exe"],
}

# Keep track of processes launched through this server
processes = {}


def focus_or_flash_process_window(process_id, timeout=3):
    if os.name != "nt":
        return "window_not_found"

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    enum_windows_proc = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
    )
    user32.EnumWindows.argtypes = [enum_windows_proc, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD)
    ]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetWindow.restype = wintypes.HWND
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.GetForegroundWindow.restype = wintypes.HWND

    class FlashWindowInfo(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.UINT),
            ("hwnd", wintypes.HWND),
            ("dwFlags", wintypes.DWORD),
            ("uCount", wintypes.UINT),
            ("dwTimeout", wintypes.DWORD),
        ]

    user32.FlashWindowEx.argtypes = [ctypes.POINTER(FlashWindowInfo)]
    user32.FlashWindowEx.restype = wintypes.BOOL

    window_handles = []

    @enum_windows_proc
    def collect_process_windows(hwnd, _):
        window_process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(
            hwnd, ctypes.byref(window_process_id)
        )
        if (
            window_process_id.value == process_id
            and user32.IsWindowVisible(hwnd)
            and not user32.GetWindow(hwnd, 4)
        ):
            window_handles.append(hwnd)
        return True

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        window_handles.clear()
        user32.EnumWindows(collect_process_windows, 0)
        if window_handles:
            break
        time.sleep(0.1)

    if not window_handles:
        return "window_not_found"

    hwnd = window_handles[0]
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)

    user32.SetForegroundWindow(hwnd)
    time.sleep(0.1)
    if user32.GetForegroundWindow() == hwnd:
        return "foreground"

    flash_info = FlashWindowInfo(
        ctypes.sizeof(FlashWindowInfo),
        hwnd,
        2 | 4 | 8,
        0,
        0,
    )
    user32.FlashWindowEx(ctypes.byref(flash_info))
    return "flashing"


@app.before_request
def security_check():
    if not request.path.startswith("/api/"):
        return

    origin = request.headers.get("Origin")

    if origin not in ALLOWED_ORIGINS:
        abort(403, "Origin not allowed")

    if request.method == "OPTIONS":
        return

    if request.headers.get("X-Launcher-Token") != TOKEN:
        abort(401, "Invalid API token")


@app.after_request
def cors_headers(response):
    origin = request.headers.get("Origin")

    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, OPTIONS"
        )
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, X-Launcher-Token"
        )
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        response.headers["Vary"] = "Origin"

    return response


@app.route("/api/apps", methods=["GET", "OPTIONS"])
def get_apps():
    return jsonify(list(APPS.keys()))



@app.route("/api/launch", methods=["POST", "OPTIONS"])
def launch_app():
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True) or {}
    executable = data.get("path")

    if not executable:
        return jsonify({"error": "Missing executable path"}), 400

    try:
        process = subprocess.Popen([executable])
        focus_status = focus_or_flash_process_window(process.pid)

        return jsonify({
            "status": "launched",
            "path": executable,
            "pid": process.pid,
            "focus": focus_status
        })

    except Exception as error:
        return jsonify({"error": str(error)}), 500



@app.route("/api/status", methods=["GET", "OPTIONS"])
def get_status():
    return jsonify({
        app_id: {
            "running": process.poll() is None,
            "pid": process.pid
        }
        for app_id, process in processes.items()
    })


if __name__ == "__main__":
    print("--------------------------------")
    print(" LOCAL APPLICATION LAUNCHER")
    print("--------------------------------")
    print(f"Server: http://127.0.0.1:{PORT}")
    print(f"API Token: {TOKEN}")
    print("--------------------------------")

    app.run(
        host="127.0.0.1",
        port=PORT,
        debug=False
    )
