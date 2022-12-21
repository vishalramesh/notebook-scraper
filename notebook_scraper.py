import os
import numpy as np
import pandas as pd
import time
import re
import ast
import cssselect
import pickle
from bs4 import BeautifulSoup as bsoup
from lxml import html
from selenium.webdriver import Chrome, ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.by import By 

chrome_options = Options()
chrome_options.add_argument('log-level=3')
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")

webdriver = 'chromedriver_win32/chromedriver.exe'

driver = Chrome(webdriver, options=chrome_options)

meta_df = pd.read_csv('covid-kernels.csv')

start = 0
notebooks = {'name': [], 'packages': []}
# if os.path.isfile("notebooks.p"):
#     notebooks = pickle.load(open("notebooks.p", "rb"))
#     start = meta_df.index[meta_df.notebook_name == notebooks['name'][-1]][0]+1

for i in range(start+1, len(meta_df['notebook_link'])):
    notebooks['name'].append(meta_df['notebook_name'][i])
    link = meta_df['notebook_link'][i]
    print (f'{i}/{len(meta_df)}')
    print (link)
    driver.get(link)
    tree = html.fromstring(driver.page_source)
    
    #get views before switching to iframe
    # views_ = ''
    # try: 
    #     views_=tree.xpath('//*[@id="kernel-header-wrapper"]/div[1]/span[1]/span[2]/span/span[2]/span')[0].text
    #     print(f'{views_} views')
    # except: 
    #     print("couldn't get views")
    # notebooks['views'].append(views_)
    
    packages_ = ['']
    try:
        #switch to iframe context
        driver.switch_to.frame(driver.find_element('xpath', '//*[@id="rendered-kernel-content"]'))
        tree = html.fromstring(driver.page_source)
        
        #unhide codeblocks
        codeblocks = driver.find_elements(By.CLASS_NAME, '_kg_hide-input-true')
        for to_unhide in codeblocks:
            driver.execute_script(f"arguments[0].className = '_kg_hide-input-false';", to_unhide)
        
        #scrape imports
        code = [each.text for each in driver.find_elements(By.CLASS_NAME, "input_area") if 'import' in each.text]
        modules = []
        for block in code:
            for each in block.split('\n'):
                tokens = each.split(' ')
                if tokens[0] == 'import':
                    for package in re.sub(' ', '', each.split(' as ')[0].split('import')[1]).split(','):
                        modules.append(package)
                elif tokens[0] == 'from':
                    submodules = each.split('import')[1]
                    for sub in re.sub(' ', '', submodules).split(','):
                        modules.append(tokens[1]+'.'+sub)
        packages_= list(dict.fromkeys(modules))
        notebooks['packages'].append(packages_)
        print(f'{len(packages_)} module(s)')
    except:
        print("couldn't get modules")
        notebooks['packages'].append(packages_)

    pickle.dump(notebooks, open('notebooks.p', 'wb'))
driver.quit()
notebook_features = pd.DataFrame.from_dict(notebooks)
notebook_features.to_csv("notebook_features3.csv", index = False)
print('done writing csv')