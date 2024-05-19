import threading
import csv
import time
from queue import Queue
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Define the URLs for each website
urls = {
    "Amazon": "https://www.amazon.in/s?k={product_name}",
    "Flipkart": "https://www.flipkart.com/search?q={product_name}"
}

# Prompt the user to enter the product name
product_name = input("Enter the product name: ")

# Initialize the webdriver in headless mode
chrome_options = Options()
# chrome_options.add_argument('--headless')  # Run the browser in headless mode
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=chrome_options)

# Create an event object to signal when the first thread has completed
flipkart_done = threading.Event()

def scrape_flipkart(product_name, driver, result_queue):
    url = urls["Flipkart"].format(product_name=product_name)
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)  # Adjust the timeout value as needed
        products = []
        product_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//*[@class='CGtC98']")))
        for product_element in product_elements:
            title_element = product_element.find_element(By.XPATH, ".//div[@class='KzDlHZ']")
            price_element = product_element.find_element(By.XPATH, ".//div[@class='Nx9bqj _4b5DiR']")
            image_element = product_element.find_element(By.XPATH, ".//img[@class='DByuf4']")
            title = title_element.text
            price = price_element.text
            image_url = image_element.get_attribute('src')
            products.append({"title": title, "price": price, "image_url": image_url})
        result_queue.put(products)
    except Exception as e:
        print(f"Error scraping data from Flipkart: {e}")
        result_queue.put([])
    finally:
        # Signal that the Flipkart scraping is done
        flipkart_done.set()

def scrape_amazon(product_name, driver, result_queue):
    url = urls["Amazon"].format(product_name=product_name)
    try:
        # Wait for the Flipkart scraping to complete before starting Amazon
        flipkart_done.wait()

        driver.get(url)
        wait = WebDriverWait(driver, 5)
        products = []
        product_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//*[@class= 'a-section']")))

        for product_element in product_elements:
            time.sleep(10)
            title_element = product_element.find_element(By.XPATH, ".//span[@class='a-size-medium a-color-base a-text-normal']")
            print(f"[TITLE ELEMENT] {title_element}")
            price_element = product_element.find_element(By.XPATH, ".//span[@class='a-price']")
            image_element = product_element.find_element(By.XPATH, ".//img[@class='s-image']")
            title = title_element.text
            price = price_element.text
            image_url = image_element.get_attribute('src')
            products.append({"title": title,  "price": price, "image_url": image_url})
        result_queue.put(products)
    except Exception as e:
        print(f"Error scraping data from Amazon: {e}")
        result_queue.put([])

# Create a queue to store the results
result_queue = Queue()

# Create and start threads
flipkart_thread = threading.Thread(target=scrape_flipkart, args=(product_name, driver, result_queue))
amazon_thread = threading.Thread(target=scrape_amazon, args=(product_name, driver, result_queue))

flipkart_thread.start()
amazon_thread.start()

# Wait for threads to complete
flipkart_thread.join()
amazon_thread.join()

# Get the results from the queue
flipkart_products = result_queue.get()
amazon_products = result_queue.get()

# Save the scraped data to a CSV file
with open(f"{product_name}_results.csv", "w", newline="", encoding="utf-8") as file:
    fieldnames = ["Website", "Product Title", "Product Price", "Image URL"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for product in flipkart_products:
        writer.writerow({"Website": "Flipkart", "Product Title": product["title"], "Product Price": product["price"], "Image URL": product["image_url"]})
    for product in amazon_products:
        writer.writerow({"Website": "Amazon", "Product Title": product["title"], "Product Price": product["price"], "Image URL": product["image_url"]})

# Close the webdriver
driver.quit()