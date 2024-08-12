from pathlib import Path

from app.settings.movies_config import app

BASE_DIR = Path(__file__).parent.resolve()
XHS_SERVER = "http://127.0.0.1:11901"
LOCAL_CHROME_PATH = app.get("local_chrome_path", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")   # change me necessary！ for example C:/Program Files/Google/Chrome/Application/chrome.exe
