from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from gradio_client import Client
import gradio as gr
import json
import pandas as pd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# client = Client("https://atulit23-google-flan-t5.hf.space/")

@app.route('/compare_descriptions', methods=['GET'])
def compare_descriptions():
    product = request.args.get('product')
    amazon_url = f'https://www.amazon.in/s?k={product}'

    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options, service=Service(ChromeDriverManager().install()))

    driver.get(amazon_url)

    amazon_price_elements = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'a-price-whole'))
    )

    amazon_prices = [element.text.strip() for element in amazon_price_elements] # Extract the price text

    print('------------')
    print(f'Amazon Price: {amazon_prices}')

    amazon_title_elements = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'a-size-medium.a-color-base.a-text-normal'))
    )
    amazon_titles = [element.text.strip() for element in amazon_title_elements]

    amazon_review_elements = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'a-row'))
    )

    aria_labels = []
    for element in amazon_review_elements:
        try:
            span_element = element.find_element(By.TAG_NAME, 'span')
            aria_label = span_element.get_attribute('aria-label')
            aria_labels.append(aria_label)
        except Exception as e:
            aria_labels.append(None)  
    new_aria_labels = []

    for label in aria_labels:
        if label is not None: 
            if label.lower().find('out of') != -1:
                new_aria_labels.append(label)

    products_and_prices = list(zip(amazon_titles, amazon_prices, new_aria_labels))
    products_and_prices_new = []

    df = pd.DataFrame(products_and_prices, columns=['Product', 'Price', 'Review'])

    df.to_excel('amazon_products_and_reviews.xlsx', index=False)

    print('------------')
    for title, price, review in products_and_prices:
        print(f'Product: {title}, Price: {price}, Review: {review}')
        obj = {"title": title, "price": price, "review": review}
        products_and_prices_new.append(obj)

    driver.quit()

    final_result = products_and_prices_new

    return jsonify(final_result)

if __name__ == '__main__':
    app.run(debug=True)