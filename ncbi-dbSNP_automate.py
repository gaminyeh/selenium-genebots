#!/usr/bin/env python
# coding: utf-8

import tempfile, json, logging, time, re, os, zipfile, sys, argparse, configparser
from datetime import datetime, timedelta
from glob import glob
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
import pandas as pd


def init_driver(driverpath, download_dir=None, implicit_wait=10):
    logging.info('Initializing driver')
    
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless') # 瀏覽器在沒有 GUI 的情況下運行
    options.add_argument('--disable-dev-shm-usage')

    if download_dir is None:
        download_dir = tempfile.gettempdir()
        
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    
    service = Service(driverpath)
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(implicit_wait)
    logging.info('Driver initialized successfully')
    
    return driver


def main():
    driver_path = './chromedriver-linux64/chromedriver'
    base_url = 'https://www.ncbi.nlm.nih.gov/snp/'   
    screenshot_dir_path = f'{script_dir}/screenshots/{log_time}_dbsnp_screenshot' 
    os.makedirs(screenshot_dir_path, exist_ok=True)

    disease_list = []
    no_results_list = [] 
    download_failed_list = []

    df =  pd.read_csv(args.input, header=0)
    
    csv_filename = args.output
    if not os.path.exists(csv_filename) or os.path.getsize(csv_filename) == 0: # 檔案不存在或為空寫入column name
        with open(csv_filename, 'w', newline='') as f:
            f.write("Unnamed: 0,#Uploaded_variation,GRCh38,GRCh37\n")

    df['GRCh38'] = None
    df['GRCh37'] = None
    
    for index, snp in enumerate(df['#Uploaded_variation']):
        logging.info("")
        num = df.iloc[index]['Unnamed: 0']

        driver = None   
        try: 
            driver = init_driver(driver_path)
            driver.get(base_url)

            search_box = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "term")))
            search_box.clear()
            search_box.send_keys(snp)
            search_box.send_keys(Keys.RETURN)
            
            # time.sleep(2)  # Give the page time to load

            driver.set_window_size(1920, 1920)
            file_name = f"{num}-{snp}_search_results.png"
            screenshot_path = f"{screenshot_dir_path}/{file_name}"
            driver.save_screenshot(screenshot_path)
            logging.info(f'Screenshot saved: {screenshot_path}')

            grch38, grch37 = None, None

            try:
                chromosome_label = driver.find_element(By.XPATH, "//dt[contains(text(), 'Chromosome:')]")
                chromosome_values = chromosome_label.find_element(By.XPATH, "following-sibling::dd").text
                chromosome_list = chromosome_values.split("\n")

                if len(chromosome_list) >= 2:
                    grch38 = chromosome_list[0].strip()
                    grch37 = chromosome_list[1].strip()
                else:
                    logging.warning(f"No Chromosome results found for SNP {snp}.")

            except Exception as e:
                logging.error(f'Error: {e}')
        
        except Exception as e:
            grch38, grch37 = None, None

        finally:
            if driver:                   
                driver.quit()
        
        # 逐行寫入 CSV
        with open(csv_filename, 'a', newline='') as f:
            pd.DataFrame([[num, snp, grch38, grch37]], columns=['Unnamed: 0','#Uploaded_variation', 'GRCh38', 'GRCh37']).to_csv(f, index=False, header=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get SNP GRCh38 GRCh37 position from NCBI-dbSNP.')
    parser.add_argument('--input', help='Input file path. Default="./inputs/ncbi-dbSNP_example.csv"', default="./inputs/ncbi-dbSNP_example.csv")
    parser.add_argument('--output', help='Output file path. Default="./outputs/ncbi-dbSNP_example_output.csv"', default="./outputs/ncbi-dbSNP_example_output.csv")
    args = parser.parse_args()    
    script_dir = os.path.dirname(os.path.abspath(__file__))

    os.makedirs(f'{script_dir}/logs', exist_ok=True)    
    log_time = datetime.now().strftime("%Y-%m-%d")
    logFileName = f'{script_dir}/logs/clinvar_automator_{log_time}.log'
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO,
                        handlers=[
                            logging.FileHandler(logFileName, mode='a'),
                            logging.StreamHandler()
                        ])
    
    main()