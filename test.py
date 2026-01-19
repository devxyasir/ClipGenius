from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

COOKIE_FILE = "cookies.txt"   # rename your file to cookies.txt

def load_netscape_cookies(driver, path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue

            parts = line.strip().split("\t")
            if len(parts) != 7:
                continue

            domain, flag, path_, secure, expiry, name, value = parts

            cookie = {
                "name": name,
                "value": value,
                "domain": domain.lstrip("."),  # selenium requirement
                "path": path_,
                "secure": secure.upper() == "TRUE"
            }

            # Selenium often fails on expiry
            try:
                driver.add_cookie(cookie)
            except:
                pass


options = Options()

# CLEAN selenium profile (DO NOT use real chrome profile)
options.add_argument(r"--user-data-dir=C:\selenium_gemini_profile")

# Match real Chrome UA (important for Google)
options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-first-run")
options.add_argument("--no-default-browser-check")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# MUST open domain first
driver.get("https://gemini.google.com")

# Load cookies
load_netscape_cookies(driver, COOKIE_FILE)

# Refresh to apply login
driver.refresh()
