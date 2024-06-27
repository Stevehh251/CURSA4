'''
    This module will extract records from html page using folder with css selectors
'''

import json
import os

from glob import glob
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from cleaners import clean_html


def xpath_soup(element):
    """
        This function generate xpath from BeautifulSoup4 element.
        This was adapted from a gist from Felipe A. Hernandez to a GitHub:
        https://gist.github.com/ergoithz/6cf043e3fdedd1b94fcf

        :param element: BeautifulSoup element
        :return: xpath of corresponding element
    """
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name if 1 == len(siblings) else '%s[%d]' % (
                child.name,
                next(i for i, s in enumerate(siblings, 1) if s is child)
            )
        )
        child = parent
    components.reverse()
    return '/%s' % '/'.join(components)


def generate_block_xpaths(html: str, block_selector: str) -> list:
    """
    This function generates list of xpaths for first node with text into each block

    :param html: html-code
    :type html: str
    :param block_selector: CSS selector which describes each record's boundaries
    :type block_selector: str
    :return: List of xpaths
    :rtype: list
    """

    soup = BeautifulSoup(html, 'html5lib')
    blocks = soup.select(block_selector)

    xpaths = []

    for entity in blocks:

        text = ''.join(entity.find_all(text=True, recursive=False))

        if len(text) > 2:
            xpaths += [xpath_soup(entity)]
            continue

        text_elements = entity.find_all(True)
        for element in text_elements:
            text = ''.join(element.find_all(text=True, recursive=False))
            if len(text) > 2:
                xpaths += [xpath_soup(element)]
                # print(element.string)
                break
    if (len(blocks) == 0):
        print(f"Broken css : # {block_selector} #")
        
    return xpaths


def generate_labeled_xpaths(html: str, selector: str, label: str) -> dict:
    '''
        return
        xpath -> label
    '''

    soup = BeautifulSoup(html, 'html5lib')

    elements = soup.select(selector)

    result = {}

    for entity in elements:

        text = ''.join(entity.find_all(text=True, recursive=False))

        if len(text) > 2:
            result[xpath_soup(entity)] = label
            continue

        text_elements = entity.find_all(True)
        for element in text_elements:
            text = ''.join(element.find_all(text=True, recursive=False))
            if len(text) > 2:
                result[xpath_soup(element)] = label
                break

    return result


def load_selectors(selectors_folder: str) -> dict:
    '''
        This function returns dict of css_selectors
        netloc:str -> selectors:dict
    '''
    if not os.path.exists(selectors_folder):
        raise Exception("Invalid css selectors directory")

    selectors_folder = os.path.abspath(selectors_folder)

    files_path = glob(os.path.join(selectors_folder, "*.json"))

    selectors = dict()

    for file_path in files_path:
        with open(file_path) as file:
            record = json.load(file)

        # print(record)

        url = urlparse(record["startUrls"][0]).netloc
        if url.startswith("www."):
            url = url[4:]

        selectors[url] = {selector["id"]: selector["selector"]
                          for selector in record["selectors"]}

    return selectors


def process_file(file_path, selectors_folder):
    with open(file_path) as file:
        info = json.load(file)

    netloc = urlparse(info["url"]).netloc
    
    if netloc.startswith("www."):
        netloc = netloc[4:]
        
    if (selectors := load_selectors(selectors_folder)).get(netloc):
        selectors = selectors[netloc]
    else:
        print(f"No css selectors found for {file_path}")
        return None

    html = clean_html(info["html"])
    
    block_xpaths = generate_block_xpaths(html, selectors["block"])
    info["xpaths"] = block_xpaths

    allowed_labels = ["block", "title", "short_text", "date", "time", "tag", "short_title", "author"]
    labeled_xpaths = {}
    
    for name in selectors.keys():
        if not (name in allowed_labels):
            continue

        if name != "block":
            labeled_xpaths |= generate_labeled_xpaths(html, selectors[name], name)

    labels_on_page = set(labeled_xpaths.values())
    
    info["exist_labels"] = list(labels_on_page)
    info["labeled_xpaths"] = labeled_xpaths

    if len(info["labeled_xpaths"]) == 0:
        print(f"No labels found in {file_path}")
        return None

    if len(info["xpaths"]) == 0:
        print(f"No blocks found in {file_path}")
        return None

    return file_path, info


def extract(filenames: list, css_folder: str) -> dict:
    answer = dict()
    selectors_folder = os.path.abspath(css_folder)

    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_file, file, selectors_folder): file for file in filenames}
        for future in tqdm(as_completed(futures), total=len(filenames), desc='CSS extracting'):
            result = future.result()
            if result is not None:
                file_path, info = result
                answer[file_path] = info

    return answer
