"""拾词桌面启动器：启动本地服务并打开默认浏览器。"""

from __future__ import annotations

import logging
import json
import os
import signal
import threading
import time
import urllib.error
import urllib.request
import webbrowser

import uvicorn

from app.config import app_data_dir
from app.main import APP_API_VERSION, app


HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def running_server() -> dict | None:
    try:
        with urllib.request.urlopen(f"{URL}/api/health", timeout=1) as response:
            if response.status == 200:
                return json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        pass
    return None


def app_is_running() -> bool:
    server = running_server()
    return bool(server and server.get("api_version") == APP_API_VERSION)


def stop_incompatible_instance(server: dict) -> None:
    pid = server.get("pid")
    if server.get("app") != "拾词 API" or not isinstance(pid, int) or pid == os.getpid():
        return
    logging.info("Stopping incompatible desktop instance pid=%s api_version=%s", pid, server.get("api_version"))
    try:
        os.kill(pid, signal.SIGTERM)
    except (OSError, PermissionError):
        logging.exception("Could not stop incompatible desktop instance pid=%s", pid)
        return
    for _ in range(20):
        if running_server() is None:
            return
        time.sleep(0.1)


def open_when_ready() -> None:
    for _ in range(40):
        if app_is_running():
            webbrowser.open(URL)
            return
        time.sleep(0.25)


def main() -> None:
    data_dir = app_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=data_dir / "desktop.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    server = running_server()
    if server and server.get("api_version") == APP_API_VERSION:
        webbrowser.open(URL)
        return
    if server:
        stop_incompatible_instance(server)
    threading.Thread(target=open_when_ready, daemon=True).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning", access_log=False)


if __name__ == "__main__":
    main()
