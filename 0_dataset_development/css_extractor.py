'''
    This script will extract records from html page using folder with css selectors
'''
import json
import os
import sys

from glob import glob
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from tqdm import tqdm


def xpath_soup(element):
    '''
        This function generate xpath from BeautifulSoup4 element.
        This was adapted from a gist from Felipe A. Hernandez to a GitHub:
        https://gist.github.com/ergoithz/6cf043e3fdedd1b94fcf
    '''
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
    '''
        This function generate list of xpaths for first node with text into each block
    '''

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
        print(f"Broken css : > {block_selector} <")
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


def extract(filenames: list, css_folder: str) -> dict:
    """
    This function extract information from html using corresponding css-selectors.

    Args:
        filenames (list): The list with paths of filenames. Each file must contain dict with "html" key, which contains its html-code.
        css_folder (_type_): Path to the folder with sitemaps, which would use to extract items.

    Returns:
        dict: For each file dictionary contains: 
            * All previous items
            * Xpaths for extracted items by css selectors

    TODO: Parallelize
    """
    answer = dict()

    selectors_folder = os.path.abspath(css_folder)

    selectors = load_selectors(selectors_folder)

    for file_path in tqdm(filenames, desc='CSS extracting'):
        with open(file_path) as file:
            info = json.load(file)

        netloc = urlparse(info["url"]).netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]

        block_xpaths = generate_block_xpaths(json.loads(info["html"]), selectors[netloc]["block"])
        info["xpaths"] = block_xpaths

        allowed_labels = ["block", "title", "short_text",
                          "date", "time", "tag", "short_title", "author"]
        labeled_xpaths = {}

        exist_labels = selectors[netloc].keys()
        info["exist_labels"] = list(exist_labels)

        for name in selectors[netloc].keys():
            if not (name in allowed_labels):
                continue
                # raise Exception(f"Label {name} doesnt allowed in {file_path}")

            if name != "block":
                labeled_xpaths |= generate_labeled_xpaths(json.loads(info["html"]), selectors[netloc][name], name)

        info["labeled_xpaths"] = labeled_xpaths

        if (len(info["labeled_xpaths"]) == 0):
            print(f"No labels found in {file_path}")
            continue

        if (len(info["xpaths"]) == 0):
            print(f"No blocks found in {file_path}")
            continue

        answer[file_path] = info

        # with open(os.path.join(out_path, filename), "w", encoding="utf-8") as file:
        #     json.dump(info, file, ensure_ascii=False, indent=4)

    return answer
