"""拾词桌面启动器：启动本地服务并打开默认浏览器。"""

from __future__ import annotations

import logging
import threading
import time
import urllib.error
import urllib.request
import webbrowser

import uvicorn

from app.config import app_data_dir
from app.main import app


HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def app_is_running() -> bool:
    try:
        with urllib.request.urlopen(f"{URL}/api/health", timeout=1) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


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
    if app_is_running():
        webbrowser.open(URL)
        return
    threading.Thread(target=open_when_ready, daemon=True).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning", access_log=False)


if __name__ == "__main__":
    main()
