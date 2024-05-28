import argostranslate.package
import argostranslate.translate
from argostranslate.translate import get_installed_languages
from collections.abc import Iterable

import asyncio
import json
import re
import unicodedata
import lxml
import os
import sys
import time

from lxml import etree
from lxml.html.clean import Cleaner
from tqdm import tqdm
from glob import glob

def clean_spaces(text):
    return " ".join(re.split(r"\s+", text.strip()))


def clean_format_str(text):
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    text = clean_spaces(text)
    return text


def get_dom_tree(html, need_clean):
    if need_clean:
        cleaner = Cleaner()
        cleaner.javascript = True
        cleaner.style = True
        cleaner.page_structure = False
        html = html.replace("\0", "")  # Delete NULL bytes
        html = clean_format_str(html)
        x = lxml.html.fromstring(html)
        etree_root = cleaner.clean_html(x)
        dom_tree = etree.ElementTree(etree_root)
    else:
        dom_tree = lxml.html.fromstring(html).getroottree()
    return dom_tree

def ru2en(text, translator):

    translated_text = translator.translate(text)
    return translated_text

def translate_html(html_str, translator, need_clean=True, from_code='auto', to_code="en"):
    tree = get_dom_tree(html_str, need_clean)
    tasks = []
    for e in tree.iter():
        if e.text:
            node = unicodedata.normalize('NFKD', e.text)
            e.text = ru2en(node, translator)
        if e.tail:
            node = unicodedata.normalize('NFKD', e.tail)
            e.tail = ru2en(node, translator)
            
    return lxml.html.tostring(tree, doctype="<!DOCTYPE html>", encoding='unicode')


def translate_file(file_path, out_path, translator):
    print(file_path)
    start = time.time()
    # try:
    translated_node = {}
    with open(file_path) as file:
        info = json.load(file)
    for label, value in info.items():
        if label == "html":
            translated_node["html"] = translate_html(value, translator)
        elif label == "info":
            result = []
            for entity in value:
                translated_entity = {}
                for key, text in entity.items():
                    if isinstance(text, Iterable):
                        answer = []
                        for i in text:
                            trans = ru2en(i, translator)
                            answer.append(trans)
                        translated_entity[key] = answer
                    else:
                        translated_entity[key] = ru2en(text, translator)
                    
                    
                result.append(translated_entity)
            translated_node[label] = result
        else:
            translated_node[label] = value
                
    # except Exception:
    #     print("Cant translate\n")
    #     return
    
    filename = os.path.basename(file_path)
    with open(os.path.join(out_path, filename), "w", encoding="utf-8") as file:
        json.dump(translated_node, file, ensure_ascii=False, indent=4)
    print(time.time() - start)
        
        

def main():
    # python3 model_test/test_corpus_translate.py model_test/test_corpus model_test/translated_text_corpus/
    '''
        This script translate dataset into english language
        First param: initial folder
        Second param: aimed folder
    '''
    
    in_path = os.path.abspath(sys.argv[1])
    out_path = os.path.abspath(sys.argv[2])
    
    file_to_translate = glob(os.path.join(in_path, "*.json"))
    translated_files = glob(os.path.join(out_path, "*.json"))
    
    # BEGIN OF INITIALIZE
    
    from_code = "ru"
    to_code = "en"
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    package_to_install = next(
        filter(
            lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
        )
    )
    argostranslate.package.install_from_path(package_to_install.download())
   
    ru, en = get_installed_languages()
    translator = en.get_translation(ru)

    # END OF INITIALIZE
    
    tasks = []
    print(translated_files)
    for file_path in tqdm(file_to_translate):
        filename = os.path.basename(file_path)
        if os.path.join(out_path, filename) in translated_files:
            continue
        # task = asyncio.create_task(translate_file(file_path, out_path, translator))
        # tasks.append(task)        
        # break
        translate_file(file_path, out_path, translator)
    # await asyncio.gather(*tasks)
    
    
if __name__ == "__main__":
    # asyncio.run(main())
    main()