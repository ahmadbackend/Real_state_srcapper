import json
import zipfile, os
from fake_useragent import UserAgent
from selenium_stealth import stealth

ua = UserAgent()
from decouple import  config
from selenium import  common,webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.common.exceptions import NoSuchElementException
#fastapi for converting it to api endpoint
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
# setting proxy config

proxy_host = config("PROXY_HOST")
proxy_port = config("PROXY_PORT")
proxy_user = config("proxy_user")
proxy_pass = config("proxy_pass")
proxy_string = f"{proxy_host}:{proxy_port}"  #cc-us-city-new_york-sessid-test123.bc.pr.oxylabs.io:7777# Add proxy
# Add proxy authentication via extension
manifest_json = """
{
  "version": "1.0.0",
  "manifest_version": 2,
  "name": "ProxyAuth",
  "permissions": ["proxy","tabs","unlimitedStorage","storage","<all_urls>","webRequest","webRequestBlocking"],
  "background": {"scripts": ["background.js"]}

}
"""
background_js = f"""
chrome.webRequest.onAuthRequired.addListener(
  function handler(details) {{
    return {{authCredentials: {{username: "{proxy_user}", password: "{proxy_pass}"}}}};
  }},
  {{urls: ["<all_urls>"]}},
  ['blocking']
);
"""
pluginfile = 'proxy_auth_plugin.zip'
with zipfile.ZipFile(pluginfile, 'w') as zp:
    zp.writestr("manifest.json", manifest_json)
    zp.writestr("background.js", background_js)


app = FastAPI()

#url = "https://nigeriapropertycentre.com/for-rent/flats-apartments/lagos?q=for-rent+flats-apartments+lagos&"

def initialize_driver():
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--lang=en-US,en;q=0.9')

    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(f'user-agent={ua.random}')
    # Disable WebRTC
    chrome_options.add_argument('--disable-webrtc')
    chrome_options.add_experimental_option('prefs', {'webrtc.ip_handling_policy': 'disable_non_proxied_udp'})
    chrome_options.add_experimental_option('prefs', {'webrtc.multiple_routes_enabled': False})
    chrome_options.add_argument(f'--proxy-server=https://{proxy_string}')
    #chrome_options.add_extension(pluginfile)

    driver = webdriver.Chrome( options=chrome_options)
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL",
            fix_hairline=True)
    return driver

def scrape_property_details(driver,real_title, real_currency, real_price):
    details_tab = driver.find_element(By.CSS_SELECTOR, 'ul.tabs li a[href="#tab-1"]')
    """
    WebDriverWait(driver, 360).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'ul.tabs li a[href="#tab-1"]'))
    )
    """
    driver.execute_script("arguments[0].scrollIntoView(true);", details_tab)

    driver.execute_script("arguments[0].click();", details_tab)
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
        data["description"] = ' '.join(description_text.split())
    except NoSuchElementException:
        data["description"] = None

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
                    details["current_url"] = current_url # getting house url directly
        data["details"] = details
        data["real_title", "real_currency", "real_price"] = real_title, real_currency, real_price
    except NoSuchElementException:
        data["details"] = {}

    return data
# harvest specific number of pages or all pages(25)
def harvest_apartments(start_url: str, max_pages: int=25):
    apartments = []  # List to store all apartment data

    max_page_tries = 3
    max_house_tries = 3


        # Wait for an element to be present (e.g., a specific element with a CSS selector)
        # detect last page if needed
    current_page = 1

    while True:
        driver = initialize_driver() # initialize new proxxy for each page

        try:

            if "?" in start_url:
                page_url = f"{start_url}&page={current_page}"
            else:
                page_url = f"{start_url}?page={current_page}"
            driver.get(page_url)
            WebDriverWait(driver, 360).until(
                EC.presence_of_element_located((By.XPATH, "//ul[@role='navigation']/li[last()-1]/a"))
            )
            print("Element found, page is ready!")
            last_page_number = int(driver.find_element(By.XPATH, "//ul[@role='navigation']/li[last()-1]/a").text)
            print(last_page_number)
            try:
                WebDriverWait(driver, 360).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "wp-block-body"))
                )
                print("house blocks found, page is ready!")
                page_blocks = driver.find_elements(By.CLASS_NAME, "wp-block-body")
                print(f"Found {len(page_blocks)} listings on page {current_page}", flush=True)
                for block in range(len(page_blocks)):
                    try:
                        page_blocks = driver.find_elements(By.CLASS_NAME, "wp-block-body")
                        real_title = driver.find_elements(By.CLASS_NAME,"content-title")[block].text
                        real_currency = driver.find_elements(By.CLASS_NAME,"price")[block * 2].text # currency
                        real_price = driver.find_elements(By.CLASS_NAME,"price")[(block * 2) +1].text
                        # locate the link inside the block
                        link_elem = WebDriverWait(page_blocks[block], 360).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "a"))
                        )
                        link_href = link_elem.get_attribute("href")

                        # open property in same tab
                        driver.execute_script("arguments[0].click();", link_elem)
                        WebDriverWait(driver, 360).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".property-details"))
                        )

                        apartment = scrape_property_details(driver, real_title, real_currency, real_price)
                        print("Scraped:", apartment, flush=True)

                        apartments.append(apartment)
                        max_house_tries = 3
                    except Exception as e:
                        # try three time to collect  house data then record the failure
                        if max_house_tries > 0:
                            block -= 1
                            max_house_tries -= 1
                        else:
                            apartments.append(
                                {"error": f"failed on listing {block + 1} of page {current_page}: {str(e)}"})
                    finally:
                        driver.back()
                        WebDriverWait(driver, 360).until(
                            EC.presence_of_all_elements_located((By.CLASS_NAME, "wp-block-body"))
                        )
                        time.sleep(3)

                if current_page >= last_page_number or current_page >= max_pages:
                    driver.quit()

                    break
                else:
                    current_page += 1
                    max_page_tries = 3 # reset after success harvesting
            # record failed pages after 3 tries
            except Exception as e:
                if max_page_tries > 0:
                    current_page -= 1
                    max_page_tries -= 1
                else:
                    apartments.append(
                        {"error": f"failed to harvest data ofpage number {current_page } : {str(e)}"})
                print("Element not found within 360 seconds, proceeding anyway or handling error.")


        except Exception as e:
            print(f"failed to load the url{start_url}: {e}")

    return apartments  # return the results!


@app.get("/scrape")
def scrape(
    url: str = Query(..., description="Listing URL to scrape"),
    max_page: int = Query(2, description="Maximum number of pages to scrape")  #  default = 25
):

    """
    Call:  GET /scrape?url=https://nigeriapropertycentre.com/for-rent/flats-apartments/lagos?q=for-rent+flats-apartments+lagos&
    """
    return harvest_apartments(url, max_page)












