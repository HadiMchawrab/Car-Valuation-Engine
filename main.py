from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def extract_ad_links():
    # Setup Chrome WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    driver.get("https://www.dubizzle.com.lb/vehicles/cars-for-sale/")
    
    time.sleep(5)
    
    # Find all anchor elements
    all_links = driver.find_elements(By.TAG_NAME, 'a')
    
    ad_links_set = set()
    for link in all_links:
        try:
            href = link.get_attribute('href')
            if href and '/ad/' in href:
                ad_links_set.add(href)
                print(f"Found ad link: {href}") 
        except Exception as e:
            print(f"Error with a link: {e}")
    
    # Convert set back to list for return value
    ad_links = list(ad_links_set)
    
    print(f"\nTotal unique ad links found: {len(ad_links)}")
    
    # Close the browser
    driver.quit()
    
    return ad_links

if __name__ == "__main__":
    ad_links = extract_ad_links()
