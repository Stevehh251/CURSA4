from transformers import MarkupLMFeatureExtractor, MarkupLMProcessor, MarkupLMForTokenClassification
import torch
from metrics import generate_segmentation_str, path_contains
from collections import defaultdict
from urllib.request import Request, urlopen
from lxml.html.clean import Cleaner


import argostranslate.package
import argostranslate.translate
from argostranslate.translate import get_installed_languages
import re
import unicodedata
import lxml
import os

from lxml import etree

from xpath_analyzer import xpath_analyzer


def extract_items(url):
    classification_model_path = "title_date_tag.pth"
    segmentation_model_path = "segmentation_model.pth"


    class_label2id = {"OTHER" : 0,
                "title" : 1,
                "short_text" : 0,
                "date" : 2,
                "time" : 2,
                "tag" : 3,
                "short_title" : 0,
                "author" : 0}

    class_id2label = {0: "OTHER",
                1 : "title",
                2 : "date",
                3 : "tag"}


    block_label2id = {"BEGIN": 1, "OTHER": 0}

    block_id2label = {1: "BEGIN", 0: "OTHER"}

    classification_model = MarkupLMForTokenClassification.from_pretrained("microsoft/markuplm-base", id2label=class_id2label, label2id=class_label2id)
    segmentation_model = MarkupLMForTokenClassification.from_pretrained("microsoft/markuplm-base", id2label=block_id2label, label2id=block_label2id)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if os.path.exists(classification_model_path):
        classification_model.load_state_dict(torch.load(classification_model_path, map_location=device))
        print("Classification Model Loaded")
    else:
        raise Exception("No model found")


    if os.path.exists(segmentation_model_path):
        segmentation_model.load_state_dict(torch.load(segmentation_model_path, map_location=device))
        print("Segmentation Model Loaded")
    else:
        raise Exception("No model found")
    classification_model.to(device)
    segmentation_model.to(device)


    def clean_spaces(text):
        return " ".join(re.split(r"\s+", text.strip()))


    def clean_format_str(text):
        text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
        text = clean_spaces(text)
        return text


    def get_dom_tree(html, need_clean):
        if need_clean:
            cleaner = Cleaner()
            cleaner.scripts = True
            cleaner.javascript = True
            cleaner.comments = True
            cleaner.style = True
            cleaner.inline_style = False
            cleaner.links = False
            cleaner.meta = False
            cleaner.page_structure = False
            cleaner.processing_instructions = True
            cleaner.embedded = False
            cleaner.frames = False
            cleaner.forms = False
            cleaner.annoying_tags = True
            cleaner.remove_unknown_tags = False
            cleaner.safe_attrs_only = False
            cleaner.add_nofollow = False

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


    def translate_html(html_str, translator, need_clean=False, from_code='auto', to_code="en"):
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
    req = Request(
        url=url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    html_response = urlopen(req).read().decode()

    # classification_model.eval()
    # segmentation_model.eval()

    extractor = MarkupLMFeatureExtractor()
    valid_processor = MarkupLMProcessor.from_pretrained("microsoft/markuplm-base")
    valid_processor.parse_html = False

    tree = lxml.html.fromstring(html_response)
    item_ru = extractor(html_response)
    nodes_ru = item_ru['nodes']
    html_response = translate_html(html_response, translator)
    item = extractor(html_response)
    nodes, xpaths = item['nodes'], item['xpaths']

    block_encoding = valid_processor(nodes=nodes, xpaths=xpaths, stride=0,
                                     padding="max_length", truncation=True, return_tensors="pt",
                                     return_overflowing_tokens=True, return_offsets_mapping=True)

    inputs = {k: v.to(device) for k, v in block_encoding.items()}

    inputs.pop("overflow_to_sample_mapping")
    offset_mapping = inputs.pop("offset_mapping")

    with torch.no_grad():
        segmentation_output = segmentation_model(**inputs)
    segmentation_predictions = segmentation_output.logits.argmax(dim=-1)

    pred_block_xpaths = []

    statistic = {k: defaultdict(int) for k in block_id2label.keys()}

    for idx in range(len(segmentation_predictions)):
        for pred_id, word_id, offset in zip(segmentation_predictions[idx].tolist(), block_encoding.word_ids(idx),
                                            offset_mapping[idx].tolist()):
            if word_id is not None and offset[0] == 0:
                if pred_id == 1:
                    pred_block_xpaths += [xpaths[0][word_id]]


    pred_block_prefix = generate_segmentation_str(pred_block_xpaths)
    print(pred_block_prefix)
    print("Segmentation Done")
    
    
    # ^^^^^ Main result of segmentation

    # CLASSIFICATION
    nodes, xpaths = item['nodes'], item['xpaths']

    class_encoding = block_encoding

    inputs = {k: v.to(device) for k, v in class_encoding.items()}

    inputs.pop("overflow_to_sample_mapping")
    offset_mapping = inputs.pop("offset_mapping")

    with torch.no_grad():
        classification_output = classification_model(**inputs)
    classification_predictions = classification_output.logits.argmax(dim=-1)
    print("Classification Done")

    statistic = {k: defaultdict(int) for k in class_id2label.keys()}

    all_xpath = []
    X = []
    y = []
    for idx in range(len(classification_predictions)):
        for pred_id, word_id, offset in zip(classification_predictions[idx].tolist(), class_encoding.word_ids(idx),
                                            offset_mapping[idx].tolist()):
            if word_id is not None and offset[0] == 0:

                in_predicted_blocks = [path_contains(block_xpath.split('/'), xpaths[0][word_id].split('/')) for
                                       block_xpath in pred_block_prefix]

                if pred_id != 0 and any(in_predicted_blocks):
                    X.append(xpaths[0][word_id])
                    y.append(pred_id)
                
                if not any(in_predicted_blocks):
                    X.append(xpaths[0][word_id])
                    y.append(0)
                    
                all_xpath.append(xpaths[0][word_id])

        
    analyzer = xpath_analyzer()
    t = analyzer.predict_labels(X, y, all_xpath)
    print(t)
    item_dicts = [defaultdict(list) for _ in pred_block_prefix]
    
    for idx in range(len(classification_predictions)):
        for pred_id, word_id, offset, probability in zip(classification_predictions[idx].tolist(),
                                                         class_encoding.word_ids(idx), offset_mapping[idx].tolist(),
                                                         classification_output.logits[idx]):
            if word_id is not None and offset[0] == 0:

                in_predicted_blocks = [path_contains(block_xpath.split('/'), xpaths[0][word_id].split('/')) for
                                       block_xpath in pred_block_prefix]

                if t[xpaths[0][word_id]] != 0 and any(in_predicted_blocks):
                    item_dicts[in_predicted_blocks.index(True)][class_id2label[t[xpaths[0][word_id]]]] += [{
                        "xpath": xpaths[0][word_id],
                        "text": nodes_ru[0][word_id],
                        "prob": list(probability.tolist())
                    }]
                    # print(probability)
                    item_dicts[in_predicted_blocks.index(True)]["snippet"] = pred_block_prefix[in_predicted_blocks.index(True)]
                    
    return item_dicts

ans = extract_items("https://ren.tv/news/v-rossii")

import json
print(json.dumps(ans, indent=4, ensure_ascii=False))
