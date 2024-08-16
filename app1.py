from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import json
import gradio as gr
from gradio_client import Client
import chromedriver_binary

def scrape_data(amazon_url):
    chrome_options = Options()
    chrome_options.add_argument('--headless')

    driver = webdriver.Chrome(options=chrome_options)

    driver.get(amazon_url)

    amazon_title_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, 'productTitle'))
    )
    amazon_title = amazon_title_element.text.strip()

    amazon_desc_element = driver.find_element(By.ID, 'feature-bullets')
    amazon_desc = amazon_desc_element.text.strip()

    driver.get(f'https://www.flipkart.com/search?q={"+".join(amazon_title.split()[:6])}')
    
    flipkart_url = ''
    elements = driver.find_elements(By.CLASS_NAME, '_2rpwqI')
    for element in elements:
        text_content = element.get_attribute('href')
        if amazon_title.split()[0].lower() in text_content:
            flipkart_url = text_content
            break

    if not flipkart_url:
        elements = driver.find_elements(By.CLASS_NAME, '_1fQZEK')
        for element in elements:
            text_content = element.get_attribute('href')
            if amazon_title.split()[0].lower() in text_content:
                flipkart_url = text_content
                break
    
    if(flipkart_url.find('flipkart.com') == -1):
        flipkart_url = 'https://www.flipkart.com' + flipkart_url

    driver.get(flipkart_url)
    final_elements = driver.find_elements(By.CLASS_NAME, '_2418kt')
    flipkart_desc = ''
    for element in final_elements:
        flipkart_desc = element.text

    driver.quit()

    return amazon_desc, flipkart_desc

def compare_descriptions(amazon_url):
    client = Client("https://atulit23-google-flan-t5.hf.space/")

    print(amazon_url)

    amazon_desc, flipkart_desc = scrape_data(amazon_url)

    description_to_compare = "First description: " + amazon_desc + " " + "Second Description: " + flipkart_desc + " As you can see I have provided you with two descriptions. Compare these two descriptions to see if for the same field some different information has been provided. Answer in yes or no."

    print(description_to_compare)

    result = client.predict(
        description_to_compare,
        api_name="/predict"
    )

    final_result = {"Amazon": amazon_desc, "Flipkart": flipkart_desc, "result": ""}
    if result.find("yes") != -1:
        final_result["result"] = "Mismatch Detected between the descriptions at Amazon & Flipkart."
    else:
        final_result["result"] = "No Mismatch Detected between the descriptions at Amazon & Flipkart."

    return json.dumps(final_result)


inputs_image_url = [
    gr.Textbox(type="text", label="Topic Name"),
]

outputs_result_dict = [
    gr.Textbox(type="text", label="Result"),
]

interface_image_url = gr.Interface(
    fn=compare_descriptions,
    inputs=inputs_image_url,
    outputs=outputs_result_dict,
    title="Text Generation",
    cache_examples=False,
)

gr.TabbedInterface(
    [interface_image_url],
    tab_names=['Some inference']
).launch()