from selenium.webdriver.chrome import webdriver

from selenium import  webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import NoSuchElementException
#fastapi for converting it to api endpoint

from selenium_stealth import stealth
import undetected_chromedriver as uc
import random
import time
from fake_useragent import UserAgent
import tempfile, uuid

data = []
main_url = "https://nigeriapropertycentre.com/"


ua = UserAgent()

def initialize_driver():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--lang=en-US,en;q=0.9')
    user_data_dir = tempfile.mkdtemp(prefix="chrome-profile-" + str(uuid.uuid4()))
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(f'user-agent={ua.random}')
    # Disable WebRTC
    chrome_options.add_argument("--remote-debugging-port=0")

    chrome_options.add_argument('--disable-webrtc')
    chrome_options.add_experimental_option('prefs', {'webrtc.ip_handling_policy': 'disable_non_proxied_udp'})
    chrome_options.add_experimental_option('prefs', {'webrtc.multiple_routes_enabled': False})
    # chrome_options.add_argument(f'--proxy-server=https://{proxy_string}')
    chrome_options.add_argument('--disable-crash-reporter')
    chrome_options.add_argument('--no-crash-upload')
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--enable-webgl")
    chrome_options.add_argument("--enable-gpu")

    driver = webdriver.Chrome(options=chrome_options)
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win64",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL",
            fix_hairline=True)
    return driver


def all_pages_looping(url, max_pages=2):
    for i in range(1, max_pages + 1):  # as pages do not start from zero
        try:
            url_to_scrape = url + f"&page={i}" if i > 1 else url
            data.append(scrape_single_page(url_to_scrape))
        except Exception as e:
            print(e, "from all_pages_looping")
        print(data)
    return data


def scrape_single_page(url):
    single_page_data = []
    single_page_urls = []
    driver = initialize_driver()
    wait = WebDriverWait(driver, 35)
    driver.get(url)
    time.sleep(random.randint(5, 20))
    try:

        house_blocks = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "wp-block-body")))
        for index, house in enumerate(house_blocks):
            details = {"real_title": house.find_element(By.CLASS_NAME, "content-title").text,
                       "real_currency": house.find_elements(By.CLASS_NAME, "price")[0].text,
                       "real_price": house.find_elements(By.CLASS_NAME, "price")[1].text,
                       "house_url": house.find_elements(By.CSS_SELECTOR, ".wp-block-content a")[
                           0].get_attribute("href")}
            single_page_urls.append(details["house_url"])
            print(details)
            single_page_data.append(details)

        collect_each_house_details(driver, single_page_urls, single_page_data)
    except Exception as e:
        print(e, "scrape_single_page")
    driver.quit()
    return single_page_data


def collect_each_house_details(driver, page_urls, page_details):
    for index, url in enumerate(page_urls):
        driver.get(url)
        time.sleep(random.randint(3, 12))

        data = {
            "description": "",
            "details": {}
        }

        try:
            # ✅ Extract Property Description (handles multi-line text and <br>)
            desc_el = driver.find_element(By.CSS_SELECTOR, "p[itemprop='description']")
            # Replace <br> with newline to preserve formatting
            description_html = desc_el.get_attribute("innerHTML")
            description_text = description_html.replace("<br>", "\n").replace("<br/>", "\n").strip()
            # Clean up multiple spaces/newlines
            page_details[index]["description"] = ' '.join(description_text.split())
        except NoSuchElementException:
            page_details[index]["description"] = None

        try:
            # ✅ Extract Property Details table key-value pairs
            rows = driver.find_elements(By.CSS_SELECTOR, "table.table.table-bordered.table-striped tr")
            details = {}
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                for cell in cells:
                    # Each cell looks like: <strong>Key:</strong> Value
                    strongs = cell.find_elements(By.TAG_NAME, "strong")
                    if strongs:
                        key = strongs[0].text.replace(":", "").strip()
                        # Get text excluding the <strong> element
                        # Remove the key from the cell text to isolate value
                        value = cell.text.replace(strongs[0].text, "").strip(" :\n\t")
                        if key:
                            details[key] = value if value else None
                        current_url = driver.current_url
                        details["current_url"] = current_url  # getting house url directly
            page_details[index]["details"] = details
        except NoSuchElementException:
            page_details[index]["details"] = {}
        except Exception as e:
            print(e, "collect_each_house")
    return page_details  # every page with every house full details

