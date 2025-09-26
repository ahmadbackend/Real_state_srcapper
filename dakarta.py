from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains # for right clikc
import  time, random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re

from decouple import  config
from fastapi import  Query, APIRouter


# setting proxy config
proxy_host = config("PROXY_HOST")
proxy_port = config("PROXY_PORT")
proxy_user = config("proxy_user")
proxy_pass = config("proxy_pass")
proxy_string = f"{proxy_host}:{proxy_port}"  #cc-us-city-new_york-sessid-test123.bc.pr.oxylabs.io:7777# Add proxy
# Add proxy authentication via extension
#method to handle initial slide pop up


house_urls=[]
data = []
def initialize_driver():


    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US,en;q=0.9")
    options.add_experimental_option(
        "prefs",
        {"profile.default_content_setting_values.notifications": 2}
    )

    driver = uc.Chrome(options=options, headless=False)

    return driver
def split_price_currency(price_currency: str):
    # Remove normal & non-breaking spaces
    cleaned = price_currency.replace("\u202f", "").replace(" ", "")
    # Extract numbers
    numbers = re.findall(r"\d+", cleaned)
    amount = int("".join(numbers)) if numbers else 0
    # Extract everything that is NOT a digit
    currency = re.sub(r"\d+", "", cleaned)
    return amount, currency.strip()



def handle_popups(driver, timeout=5):
    """
    Dismiss Google Translate banner, cookies consent,
    and notification popups if they appear.
    """
    wait = WebDriverWait(driver, timeout)

    try:
        cookies_btn = wait.until(
            EC.element_to_be_clickable(
                # Common selectors—adjust to your site
                (By.ID, "onetrust-accept-btn-handler")
            )
        )
        cookies_btn.click()
        print("[✔] Cookies accepted")
    except Exception as e:
        print("[i] No cookies popup found", e)



    # 3️⃣ Browser/website notification popup (HTML modal)
    try:
        notif_btn = wait.until(
            EC.element_to_be_clickable(
                (By.ID, "onesignal-slidedown-allow-button")
            )
        )
        notif_btn.click()
        print("[✔] Notification request accepted/dismissed")
    except Exception as e:
        print("[i] No HTML notification popup found", e)

    # 1️⃣ Google Translate bar (example selector)
    try:
        # Use a stable element that won't trigger navigation (like the ad container)
        empty_area = wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "ins.bn.bn--970-90.search-bn.search-bn--desktop-header"  # adjust if needed
            ))
        )
        ActionChains(driver).context_click(empty_area).perform()
        #ActionChains(driver).send_keys(Keys.ESCAPE).perform()

        print("[✔] Google Translate dismissed by right-click")
    except Exception as e:
        print("[i] No Google Translate banner found", e)
def single_page_data_collection(url):
    single_page_data = []
    driver = initialize_driver()
    wait = WebDriverWait(driver, 50)  # wait up to 50 seconds

    driver.get(url)
    time.sleep(10)
    handle_popups(driver, 20)
    house_blocks = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "listings-cards__list-item")))

    for house in house_blocks:

        details = {}
        try:
            url = house.find_element(By.CSS_SELECTOR, "a.listing-card__inner").get_attribute("href")
            house_urls.append(url)
            house_title = house.find_element(By.CLASS_NAME, "listing-card__header__title").text
            house_tags_container = house.find_element(By.CLASS_NAME, "listing-card__header__tags")
            house_tags = [tag.text for tag in house_tags_container.find_elements(By.TAG_NAME, "span")]
            house_location = house.find_element(By.CLASS_NAME, "listing-card__header__location").text
            house_date = house.find_element(By.CLASS_NAME, "listing-card__header__date").text
            #price + unit
            house_price_mixed_currency = house.find_element(By.CLASS_NAME, "listing-card__price__value").text
            house_price, house_currency = split_price_currency(house_price_mixed_currency)
            details["title"] = house_title
            details["house_tags"] = house_tags
            details["house_price"] = house_price
            details["house_currency"] = house_currency
            details["house_date"] = house_date
            details["house_location"] = house_location
            details["url"] = url
            single_page_data.append(details)
            #print(details)

        except Exception as e:
            print("something wrong ", e)
        #refind them after clicking back
    print(single_page_data)
    collect_each_house_description(driver, single_page_data)
    driver.quit()
    return single_page_data

def collect_each_house_description(driver, page_data):

    for index, url in enumerate (house_urls):
        time.sleep(random.randint(1, 12))
        driver.get(url)
        wait = WebDriverWait(driver, 50)
        time.sleep(random.randint(1, 12))

        # ✅ Wait until the <div class="listing-item__description"> is visible
        description_div = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".listing-item__description p"))
        ).text
        page_data[index]["description"] = description_div
        time.sleep(random.randint(1, 12))

def navigate_over_pages(web_url, max_pages=2):
    for page in range(1, max_pages+1):
        url = f"{web_url}?page={page}" if page >1 else web_url
        data.append(single_page_data_collection(url))
        print(data)

    return data


router = APIRouter(
    prefix="/dakarta",
    tags = ["Dakarta"]  # For Swagger grouping
)
navigate_over_pages("https://www.expat-dakar.com/appartements-a-louer/dakar", 1)
"""
@router.get("/")
def get_data(url: str = Query(..., description="Listing URL to scrape"),
        max_page: int = Query(3, description="Maximum number of pages to scrape") ):
    return navigate_over_pages(url, max_page)
"""