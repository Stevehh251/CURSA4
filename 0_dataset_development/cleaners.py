'''
    This module contains cleaners for HTML preprocessing.
'''

from lxml.html.clean import Cleaner

import re
import unicodedata
import lxml


def clean_pseudocontrol(text: str) -> str:
    """
    This function clean \n and \t as text from text nodes

    :param text: text from which should be deleted \n and \t
    :type text: str
    :return: modified string
    :rtype: str
    """
    return re.sub("(\\n|\\t)+", "", text)


def clean_spaces(text: str) -> str:
    """
    Clean extra spaces in a string.
    
    Example:
      input: " asd  qwe   " --> output: "asd qwe"
      input: " asd\t qwe   " --> output: "asd qwe"
      
    :param text: the input string with potentially extra spaces.
    :type text: str
    :return: a string containing only the necessary spaces.
    :rtype: str
    """
    return " ".join(re.split(r"\s+", text.strip()))


def clean_format_str(text: str) -> str:
    """Cleans unicode control symbols, non-ascii chars, and extra blanks."""
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    # text = "".join([c if ord(c) < 128 else "" for c in text])  # удаляет русский текст
    text = clean_spaces(text)
    # text = clean_pseudocontrol(text)
    return text


def clean_html(in_html: str) -> str:
    """
    This function clears the HTML page of unnecessary elements.

    :param in_html: html-code which needs cleaning
    :type in_html: str
    :return: cleaned html-code
    :rtype: str
    """
    cleaner = Cleaner()
    
    cleaner.javascript = True
    cleaner.style = False
    cleaner.inline_style = False
    cleaner.page_structure = False
    cleaner.annoying_tags = False
    cleaner.remove_unknown_tags = False
    cleaner.safe_attrs_only = False
    
    html = lxml.html.tostring(cleaner.clean_html(lxml.html.fromstring(in_html)))
    html = clean_format_str(html.decode('utf-8'))
    
    return html
