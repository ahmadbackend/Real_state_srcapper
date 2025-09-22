from selenium import  common,webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import  pandas as pd
import random

from decouple import  config

url = "https://nigeriapropertycentre.com/"
# scrapper initialization commented out proxy and user agent
def initialize_driver():
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument('--headless')  # Run in headless mode
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

driver = initialize_driver()
driver.get(url)
# get the main three options of the website(rent, buy , let)
a_elements = driver.find_elements(By.CSS_SELECTOR, "ul.cat li a")

a_elements_text = [e.text for e in a_elements]
# click to expand search options if not expanded
expand_search = driver.find_element(By.LINK_TEXT,"More search options")

if not expand_search.get_attribute("aria-expanded"):
    expand_search.click()

def options_extractor(drop_down_menu_id):
    select_types = driver.find_element(By.ID, drop_down_menu_id)
    selections = Select(select_types).options
    available_types = [option.text for option in selections]
    return available_types

# all drop down menu options
accommodation_types = options_extractor("tid")
bed_rooms_options = options_extractor("bedrooms")
min_price = options_extractor("minprice")
max_price = options_extractor("maxprice")
furnished = options_extractor("furnished")
serviced = options_extractor("serviced")
shared = options_extractor("shared")
added = options_extractor("added")

key_features = config("KEY_WORDS")
house_code = config("REF_NUMBER")

# fields that accept text input for search (key_words, ref number)
key_words = driver.find_element(By.ID, "keywords")
if key_features :
    key_words.clear()
    key_words.send_keys(key_features)

house_number = driver.find_element(By.ID, "ref")
if house_code :
    house_number.clear()
    house_number.send_keys(key_features)


#print(accommodation_types, bed_rooms_options, max_price, max_price, furnished,\
 #     serviced, shared, added)

user_action = {"buy":config("BUY"), "rent":config("RENT"), "let_out":config("LET")}

driver.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
