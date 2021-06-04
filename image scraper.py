# Hanny Long
# Scraping image off of imgur given a search keyword 

import requests
import os
import subprocess
from bs4 import BeautifulSoup
import tldextract

PATH = r'\Users\HLL\Desktop\CSS\Independent study\test folder\image'
PAGE = 'https://imgur.com/search?q='

# Take input that will be use as keyword for the img search
web_pages = [item for item in input("Enter the list items eg \"banana Stephen+Hawking\": ").split()]

# Add keyword to the page url
for n, term in enumerate(web_pages): 
    web_pages[n] = PAGE + term 
      
print(web_pages) 

url_dictionary = {}

for page in web_pages:
    # 1. Extracting the domain name of the web page:
    domain_name = tldextract.extract(page).registered_domain  
    # 2. Request the web page:
    r = requests.get(page)
    # 3. Check to see if the web page returned a status_200:
    if r.status_code == 200:

        # 4. Create a URL dictionary entry for future use:
        url_dictionary[page] = []

        # 5. Parse the HTML content with BeautifulSoup and look for image tags:
        soup = BeautifulSoup(r.content, 'html.parser')

        # 6. Find all of the images per web page:
        images = soup.find_all('img')

        # 7. Store all of the images 
        url_dictionary[page].extend(images)

    else:
        print('failed!')

print(url_dictionary)

for key, value in url_dictionary.items():
    if len(value) > 0:
        print(f"This domain: {key} has more than 1 image on the web page.")

cleaned_dictionary = {key: value for key, value in url_dictionary.items() if len(value) > 0}

for key, images in cleaned_dictionary.items():
    for image in images:
        print(image.attrs['src'])

all_images = []

for key, images in cleaned_dictionary.items():
    # 1. Creating a clean_urls and domain name for every page:
    clean_urls = []
    domain_name = tldextract.extract(key).registered_domain
    # 2. Looping over every image per url:
    for image in images:
        # 3. Extracting the source (src) with .attrs:
        source_image_url = image.attrs['src']
        # 4. Clean The Data
        if source_image_url.startswith("//"):
            url = 'https:' + source_image_url
            all_images.append(url)
        elif domain_name not in source_image_url and 'http' not in source_image_url:
            url = 'https://' + domain_name + source_image_url
            all_images.append(url)
        else:
            all_images.append(source_image_url)

def extract_images(image_urls_list:list, directory_path):

    # Changing directory into a specific folder:
    os.chdir(directory_path)

    # Downloading all of the images
    for img in image_urls_list:
        file_name = img.split('/')[-1]

        # Let's try both of these versions in a loop [https:// and https://www.]
        url_paths_to_try = [img, img.replace('https://', 'https://www.')]
        for url_image_path in url_paths_to_try:
            print(url_image_path)
            try:
                r = requests.get(img, stream=True)
                if r.status_code == 200:
                    with open(file_name, 'wb') as f:
                        for chunk in r:
                            f.write(chunk)
            except Exception as e:
                pass     


extract_images(image_urls_list=all_images, 
               directory_path=PATH)
