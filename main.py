from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "API de Web Scraping"

@app.route('/searchWorldBank', methods=['POST'])
def searchWorldBank():
    company_name = request.json.get('company_name')

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    results = []
    try:
        url = "https://projects.worldbank.org/en/projects-operations/procurement/debarred-firms"
        driver.get(url)
        
        time.sleep(10)

        search_box = driver.find_element(By.ID, 'category')
        search_box.send_keys(company_name)
        search_box.send_keys('\n')

        time.sleep(5)

        table = driver.find_element(By.ID, 'k-debarred-firms')
        rows = table.find_elements(By.TAG_NAME, 'tr')
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if len(cells) > 0 and company_name.lower() in cells[0].text.lower():
                firm_name = cells[0].text.strip()
                address = cells[2].text.strip()
                country = cells[3].text.strip()
                from_date = cells[4].text.strip()
                to_date = cells[5].text.strip()
                grounds = cells[6].text.strip()
                results.append({
                    'firm_name': firm_name,
                    'address': address,
                    'country': country,
                    'from_date': from_date,
                    'to_date': to_date,
                    'grounds': grounds
                })
    
    finally:
        driver.quit()

    searchResult = {
        "hits": len(results),
        "results": results
    }
    
    return jsonify(searchResult)

@app.route('/searchSanctionsList', methods=['POST'])
def searchSanctionsList():
    data = request.get_json()

    company_name = data.get('company_name', '')
    country = data.get('country', '')

    if not company_name:
        return jsonify({'error': 'Company name is required'}), 400

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get('https://sanctionssearch.ofac.treas.gov/')

        search_input = driver.find_element(By.ID, 'ctl00_MainContent_txtLastName')
        search_input.send_keys(company_name)

        if country:
            country_select = Select(driver.find_element(By.ID, 'ctl00_MainContent_ddlCountry'))
            country_select.select_by_visible_text(country)

        search_button = driver.find_element(By.ID, 'ctl00_MainContent_btnSearch')
        search_button.click()

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'gvSearchResults'))
        )

        results = []
        rows = driver.find_elements(By.XPATH, '//table[@id="gvSearchResults"]/tbody/tr')
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, 'td')
            if len(cols) > 0:
                result = {
                    'name': cols[0].text.strip(),
                    'address': cols[1].text.strip(),
                    'type': cols[2].text.strip(),
                    'programs': cols[3].text.strip(),
                    'list': cols[4].text.strip(),
                    'score': cols[5].text.strip()
                }
                results.append(result)
        
        searchResult = {
            "hits": len(results),
            "results": results
        }

        return jsonify(searchResult)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(debug=True)
