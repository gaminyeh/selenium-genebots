#!/usr/bin/env python
# coding: utf-8

import tempfile, json, logging, time, re, os, zipfile, sys, argparse, configparser
import smtplib
from email.mime.text import MIMEText
from threading import Thread
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
import csv

def next_step(tag_name):
    global step_counter
    step_counter += 1    
    
    return f'{step_counter:02d}-{tag_name}'


def init_driver(driverpath, download_dir=None, implicit_wait=30):
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
    base_url = 'https://genomes.vn/'   
    screenshot_dir_path = f'./{log_time}_vietnamese_screenshot' 

    if not os.path.exists(screenshot_dir_path):
        os.makedirs(screenshot_dir_path)
    
    df = pd.read_csv("./input_data/vietnamese_example.csv", header=0)
    output_file = './vietnamese_update.csv'

    # 若 CSV 檔案不存在，則寫入標題行
    if not os.path.exists(output_file):
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["#Uploaded_variation", "ALT", "KHV", "KHV-G", "Region", "Gene", "Impact", "AA Change"])
    
    for index, row in df.iterrows():
        id = row['#Uploaded_variation']
        
        try:
            # 初始化 WebDriver 並訪問網站
            logging.info("")
            driver = init_driver(driver_path)
            driver.implicitly_wait(5)
            driver.get(base_url)
            driver.set_window_size(1920, 1920)

        
            # 填入 RS ID
            search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "query")))
            search_box.clear()
            search_box.send_keys(id)

            # 選擇 "GRCh37"
            ref_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "ref")))
            ref_button.click()        

            # submit
            submit = driver.find_element(By.XPATH, "//button[@id='search-btn']/i")
            submit.click()
            
            # time.sleep(4)
            
            file_name = next_step(f"{id}_result.png")
            screenshot_path = f"{screenshot_dir_path}/{file_name}"
            driver.save_screenshot(screenshot_path)
            logging.info(f'Screenshot saved: {screenshot_path}')
            
            # 獲取所有行
            rows = driver.find_elements(By.XPATH, "//div[@id='result']/div/table/tbody/tr[5]/td/table/tbody/tr")
            
            if not rows:
                # 若 `tbody` 為空，設定為 None
                logging.warning(f"{id} | No data available.")
                alt, khv, khvg, region, gene, impact, aachange = None, None, None, None, None, None, None
                with open(output_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([id, alt, khv, khvg, region, gene, impact, aachange])
            else:
                for row in rows:
                    try:
                        alt = row.find_element(By.XPATH, ".//th").text
                        khv = row.find_element(By.XPATH, ".//td[1]").text
                        khvg = row.find_element(By.XPATH, ".//td[2]").text
                        region = row.find_element(By.XPATH, ".//td[3]").text
                        gene = row.find_element(By.XPATH, ".//td[4]").text
                        impact = row.find_element(By.XPATH, ".//td[5]").text
                        aachange = row.find_element(By.XPATH, ".//td[6]").text

                        logging.info(f"{id} | ALT: {alt} | KHV: {khv} | KHV-G: {khvg} | Region: {region} | Gene: {gene} | Impact: {impact} | AA Change: {aachange}")
                        
                        # 寫入 CSV
                        with open(output_file, 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([id, alt, khv, khvg, region, gene, impact, aachange])
                    except Exception as row_e:
                        logging.error(f"Error processing row for {id}: {row_e}")
                        alt, khv, khvg, region, gene, impact, aachange = 'error', 'error', 'error', 'error', 'error', 'error', 'error'
                        with open(output_file, 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([id, alt, khv, khvg, region, gene, impact, aachange])
                        continue
                
            driver.quit()

        except Exception as e:
            logging.error(f"Error processing {id}: {e}")
            alt, khv, khvg, region, gene, impact, aachange = 'error', 'error', 'error', 'error', 'error', 'error', 'error'
            with open(output_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([id, alt, khv, khvg, region, gene, impact, aachange])
            continue      
        


if __name__ == "__main__":
        
    script_dir = os.path.dirname(os.path.abspath(__file__))

    os.makedirs(f'{script_dir}/logs', exist_ok=True)    
    log_time = datetime.now().strftime("%Y-%m-%d")
    logFileName = f'{script_dir}/logs/vietnamese_automator_{log_time}.log'
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO,
                        handlers=[
                            logging.FileHandler(logFileName, mode='a'),
                            logging.StreamHandler()
                        ])

    # Global step counter
    step_counter = 0
    
    main()
