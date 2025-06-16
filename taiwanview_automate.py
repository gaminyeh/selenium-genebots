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
    base_url = 'https://taiwanview.twbiobank.org.tw/variant.php'   
    screenshot_dir_path = f'./{log_time}_taiwanview_screenshot' 

    if not os.path.exists(screenshot_dir_path):
        os.makedirs(screenshot_dir_path)
    
    df = pd.read_csv("./input_data/taiwanview_example.csv", header=0)

    output_file = './taiwanview_update.csv'

    # 若 CSV 檔案不存在，則寫入標題行
    if not os.path.exists(output_file):
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["#", "rs ID", "gene", "freq"])
    
    for index, row in df.iterrows():
        id = row['rs ID']
        # id = 'rs6683165'
        number = row['#']
        
        # 初始化 WebDriver 並訪問網站
        logging.info("")
        driver = init_driver(driver_path)
        driver.implicitly_wait(0)
        driver.get(base_url)

        # 選擇 "Whole genome sequence: Illumina (GRCh38)"
        database = Select(driver.find_element("id", "database"))
        database.select_by_visible_text("Whole genome sequence: Illumina (GRCh38)")

        # 選擇 "RS ID"
        searchby = Select(driver.find_element("id", "searchBy"))
        searchby.select_by_visible_text("RS ID")

        # 填入 RS ID
        search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "geneOrVariant")))
        search_box.clear()
        search_box.send_keys(id)

        # 儲存搜索頁面的截圖
        driver.set_window_size(1920, 1920)
        file_name = next_step(f"{id}_search.png")
        screenshot_path = f"{screenshot_dir_path}/{file_name}"
        driver.save_screenshot(screenshot_path)
        logging.info(f'Screenshot saved: {screenshot_path}')
                
        try:
            # 提交搜索
            submit = driver.find_element(By.XPATH, "//button[@type='submit']")
            submit.click()
            
            time.sleep(3)  # 給頁面加載時間
            
            # 儲存結果頁面的截圖
            file_name = next_step(f"{id}_result.png")
            screenshot_path = f"{screenshot_dir_path}/{file_name}"
            driver.save_screenshot(screenshot_path)
            logging.info(f'Screenshot saved: {screenshot_path}')
            
            # 檢查 `tbody` 是否為空
            rows = driver.find_elements("xpath", "//div[@id='datatable']/table/tbody/tr")
            
            if not rows:
                # 若 `tbody` 為空，設定 `gene` 和 `all_freq` 為 None
                gene = None
                all_freq = None
                logging.info(f"{id} | No data available.")
            else:
                # 提取 gene 資料
                gene = driver.find_element("xpath", "//div[@id='datatable']/table/tbody/tr[1]/td[3]").text
                gene = gene.replace("\n", " ")
                logging.info(f"{id} | GENE: {gene}")

                # 提取 freq 資料
                freq_cells = driver.find_elements("xpath", "//div[@id='datatable']/table/tbody/tr/td[6]")
                freqs = [cell.text.replace("\n", " ") for cell in freq_cells]
                
                all_freq = ",".join(freqs)
                logging.info(f"{id} | All FREQ: {all_freq}")

        except Exception as e:
            # 若發生錯誤，設定 `gene` 和 `all_freq` 為 None 並記錄錯誤
            gene = None
            all_freq = None
            logging.error(f"Error processing {id}: {e}")

        # 將 number, id, gene 和 all_freq 寫入 CSV
        with open('./combine_rs_ID_list_update.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([number, id, gene, all_freq])

        driver.quit()


if __name__ == "__main__":
        
    script_dir = os.path.dirname(os.path.abspath(__file__))

    os.makedirs(f'{script_dir}/logs', exist_ok=True)    
    log_time = datetime.now().strftime("%Y-%m-%d")
    logFileName = f'{script_dir}/logs/taiwanview_automator_{log_time}.log'
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