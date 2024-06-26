from lxml.html.clean import Cleaner

import re
import unicodedata
import lxml

'''
    This file contains cleaners for HTML preprocessing.
'''

def clean_pseudocontrol(text: str) -> str:
    '''
      This function clean \n and \t as text from text nodes
    '''
    return re.sub("(\\n|\\t)+", "", text)
    
def clean_spaces(text: str) -> str:
    """Clean extra spaces in a string.
    Example:
      input: " asd  qwe   " --> output: "asd qwe"
      input: " asd\t qwe   " --> output: "asd qwe"
    Args:
      text: the input string with potentially extra spaces.
    Returns:
      a string containing only the necessary spaces.
    """
    return " ".join(re.split(r"\s+", text.strip()))


def clean_format_str(text: str) -> str:
    """Cleans unicode control symbols, non-ascii chars, and extra blanks."""
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    # text = "".join([c if ord(c) < 128 else "" for c in text])  # удаляет русский текст
    text = clean_spaces(text)
    text = clean_pseudocontrol(text)
    return text


def clean_html(in_html: str) -> str:
    """
    This function clears the HTML page of unnecessary elements.
    :param in_path: Path to the file containing the HTML page.
    :param out_path: Path to the file in which to place the cleaned page.
    :return: True - if the page is successfully cleaned, False otherwise
    """
    cleaner = Cleaner()
    cleaner.javascript = True
    cleaner.style = True

    html = lxml.html.tostring(cleaner.clean_html(lxml.html.fragment_fromstring(in_html)))
    html = clean_format_str(html.decode('latin'))
    
    return html
