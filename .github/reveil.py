import os
import re
from playwright.sync_api import sync_playwright

url = os.environ.get("URL_SITE", "")
if not url:
    raise SystemExit("La variable URL_SITE n'est pas définie dans les réglages GitHub")

with sync_playwright() as p:
    navigateur = p.chromium.launch()
    page = navigateur.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=120_000)
    page.wait_for_timeout(8_000)

    bouton = page.get_by_role("button", name=re.compile("back up", re.IGNORECASE))
    if bouton.count() > 0:
        print("Le site dormait : on le réveille")
        bouton.first.click()
        page.wait_for_timeout(90_000)   
    else:
        print("Le site est déjà réveillé")
        page.wait_for_timeout(20_000)   

    navigateur.close()