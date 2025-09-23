import json

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

app = FastAPI()

#url = "https://nigeriapropertycentre.com/for-rent/flats-apartments/lagos?q=for-rent+flats-apartments+lagos&"

def initialize_driver():
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument('--headless=new')

    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    #chrome_options.add_argument(f'user-agent={ua.random}')
    # Disable WebRTC
    chrome_options.add_argument('--disable-webrtc')
    chrome_options.add_experimental_option('prefs', {'webrtc.ip_handling_policy': 'disable_non_proxied_udp'})
    chrome_options.add_experimental_option('prefs', {'webrtc.multiple_routes_enabled': False})
    #if proxy:
    #    chrome_options.add_argument(f'--proxy-server={proxy}')
    driver = webdriver.Chrome( options=chrome_options)
    return driver

def scrape_property_details(driver):
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
    except NoSuchElementException:
        data["details"] = {}

    return data
# harvest specific number of pages or all pages(25)
def harvest_apartments(start_url: str, max_pages: int=25):
    """
    Generator that streams apartment data page by page.
    """

    driver = initialize_driver()

    try:
        driver.get(start_url)

        # Wait for an element to be present (e.g., a specific element with a CSS selector)
        try:
            WebDriverWait(driver, 360).until(
                EC.presence_of_element_located((By.XPATH, "//ul[@role='navigation']/li[last()-1]/a"))
            )
            print("Element found, page is ready!")
        except:
            print("Element not found within 30 seconds, proceeding anyway or handling error.")
        # detect last page if needed
        last_page_number = int(driver.find_element(By.XPATH, "//ul[@role='navigation']/li[last()-1]/a").text)
        print(last_page_number)
        #last_page_number = 1  # demo

        while True:
            current_page = 1
            last_page_number = int(driver.find_element(By.XPATH, "//ul[@role='navigation']/li[last()-1]/a").text)

            # --- build page URL correctly ---
            if "?" in start_url:
                page_url = f"{start_url}&page={current_page}"
            else:
                page_url = f"{start_url}?page={current_page}"
            driver.get(start_url)
            # Wait for an element to be present (e.g., a specific element with a CSS selector)
            try:
                WebDriverWait(driver, 360).until(
                    EC.presence_of_element_located((By.XPATH, "//ul[@role='navigation']/li[last()-1]/a"))
                )
                print("Element found, page is ready!")
            except:
                print("Element not found within 360 seconds, proceeding anyway or handling error.")
            # Optionally, handle the timeout (e.g., exit or retry)
            page_blocks = driver.find_elements(By.CLASS_NAME, "wp-block-body")
            print(f"Found {len(page_blocks)} listings on page {current_page}", flush=True)

            for block in range(len(page_blocks)):
                try:
                    page_blocks = driver.find_elements(By.CLASS_NAME, "wp-block-body")

                    # locate the link inside the block
                    link_elem = WebDriverWait(page_blocks[block], 360).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "a"))
                    )
                    link_href = link_elem.get_attribute("href")

                    # open property in same tab
                    driver.execute_script("arguments[0].click();", link_elem)
                    WebDriverWait(driver,360).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".property-details"))
                    )

                    apartment = scrape_property_details(driver)
                    print("Scraped:", apartment.get("title"), flush=True)

                    with open("data.txt", "a", encoding="utf-8") as f:
                        f.write(apartment.get("description", "") + "\n")

                    # ✅ yield as soon as one item is scraped
                    yield json.dumps(apartment) + "\n"

                except Exception as e:
                    yield json.dumps({"error": f"failed on listing: {str(e)}"}) + "\n"
                finally:
                    driver.back()
                    WebDriverWait(driver, 360).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, "wp-block-body"))
                    )
                    time.sleep(3)

            if current_page >= last_page_number or current_page >= max_pages: 
                break
            else:
                current_page +=1
    finally:
        driver.quit()


@app.get("/scrape")
def scrape(
    url: str = Query(..., description="Listing URL to scrape"),
    max_page: int = Query(25, description="Maximum number of pages to scrape")  #  default = 25
):

    """
    Call:  GET /scrape?url=https://nigeriapropertycentre.com/for-rent/flats-apartments/lagos?q=for-rent+flats-apartments+lagos&
    Streams apartments one-by-one as JSON lines.
    """
    return StreamingResponse(harvest_apartments(url, max_page), media_type="application/json")












