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
    base_url = 'https://www.ncbi.nlm.nih.gov/clinvar/'   
    download_path = f'{script_dir}/clinvar_download'
    download_rename_path = f'{script_dir}/rename_clinvar_download'
    screenshot_dir_path = f'./{log_time}_clinvar_screenshot' 

    os.makedirs(download_path, exist_ok=True)
    os.makedirs(download_rename_path, exist_ok=True)

    if not os.path.exists(screenshot_dir_path):
        os.makedirs(screenshot_dir_path)

    disease_list = []
    no_results_list = [] 
    download_failed_list = [] 
    
    with open('./input_data/ncbi-clinvar_example_list.txt', 'r') as file:
        for line in file:
            disease_list.append(line.strip())
    

    for disease in disease_list:
        logging.info("")
        driver = init_driver(driver_path, download_path)
        driver.get(base_url)           
        try:            
            search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "term")))
            search_box.clear()
            search_box.send_keys(disease)
            search_box.send_keys(Keys.RETURN)
            
            time.sleep(5)  # Give the page time to load

            driver.set_window_size(1920, 1920)
            file_name = next_step(f"{disease}_search_results.png")
            screenshot_path = f"{screenshot_dir_path}/{file_name}"
            driver.save_screenshot(screenshot_path)
            logging.info(f'Screenshot saved: {screenshot_path}')

            # Check for "No items found" message
            no_items_found = driver.find_elements(By.XPATH, "//*[contains(text(), 'No items found')]")
            if no_items_found:
                logging.info(f"No items found for {disease}. No download will be performed.")
                # no_results_list.append(disease)  # Store the disease with no results
                with open('./no_results_disease_list.txt', 'a') as f:
                    f.write(disease + '\n')
            else:
                # If results are found, look for the download link and click it
                download_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Download")))
                download_link.click()
                file_name = next_step(f"{disease}_click_download.png")
                screenshot_path = f"{screenshot_dir_path}/{file_name}"
                driver.save_screenshot(screenshot_path)
                logging.info(f'Screenshot saved: {screenshot_path}')

                time.sleep(5)

                # Wait for the file_sort element to be present
                file_sort_link = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "file_sort")))
                file_sort_link.click()
                file_name = next_step(f"{disease}_click_filesort.png")
                screenshot_path = f"{screenshot_dir_path}/{file_name}"
                driver.save_screenshot(screenshot_path)
                logging.info(f'Screenshot saved: {screenshot_path}')

                # Select the "Relevance" option from the dropdown
                select = Select(file_sort_link)
                select.select_by_visible_text("Relevance")
                file_name = next_step(f"{disease}_select_relevance.png")
                screenshot_path = f"{screenshot_dir_path}/{file_name}"
                driver.save_screenshot(screenshot_path)
                logging.info(f'Screenshot saved: {screenshot_path}')

                files_in_download_path = glob(os.path.join(download_path, "*"))
                if len(files_in_download_path) != 0:
                    for file_path in files_in_download_path:
                        os.remove(file_path)
                        logging.info(f'Removed file: {file_path}')

                # Now click the button to submit the request
                create_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "EntrezSystem2.PEntrez.clinVar.clinVar_Entrez_ResultsPanel.Entrez_DisplayBar.SendToSubmit")))
                create_button.click()
                file_name = next_step(f"{disease}_download_results.png")
                screenshot_path = f"{screenshot_dir_path}/{file_name}"
                driver.save_screenshot(screenshot_path)
                logging.info(f'Screenshot saved: {screenshot_path}')

                time.sleep(300)

                try:
                    ori_file_path = glob(os.path.join(download_path, "*.txt"))[0]
                    rename_disease = disease.replace(","," ").replace(" ","_").replace("/","_")
                    new_file_path = os.path.join(download_rename_path, f"{rename_disease}.txt")

                    with open(ori_file_path, 'r') as file:
                        lines = file.readlines()

                    header = lines[0].strip()
                    new_header = f"Disease Name\t{header}\n"  # Assuming columns are tab-separated

                    # Prepend the disease name to each row starting from the second line
                    new_content = [new_header]  # Start with the new header
                    for line in lines[1:]:
                        new_content.append(f"{disease}\t{line}")

                    # Write the updated content back to the file
                    with open(ori_file_path, 'w') as file:
                        file.writelines(new_content)

                    os.rename(ori_file_path, new_file_path)

                    logging.info(f'Renamed and updated file: {new_file_path}')
                
                except:
                    logging.warning(f'{disease} Renamed and updated file Failed!!!!')
                    with open('./download_failed_disease_list.txt', 'a') as f:
                        f.write(disease + '\n')
                    logging.info(f'{disease} saved to download_failed_disease_list.txt')
                
        except Exception as e:
            print(f"An error occurred: {e}")
            logging.warning(f'{disease} Something Failed when ckicking!!!!')
            with open('./download_failed_disease_list.txt', 'a') as f:
                        f.write(disease + '\n')
            logging.info(f'{disease} saved to download_failed_disease_list.txt')

        driver.quit()


if __name__ == "__main__":
        
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

    # Global step counter
    step_counter = 0
    
    main()