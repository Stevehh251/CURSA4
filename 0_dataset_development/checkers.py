from bs4 import BeautifulSoup
import warnings
import json
'''
    This file contains checkers for HTML preprocessing.
'''


def bs_checker(path: str) -> bool:
    """
        This function checks warnings from the BS module
        :param path: Path to file contains HTML page
        :return: True - if no warning, False - if warning raised
    """
    with open(path, 'r') as input_file:
        page_html = json.load(input_file)["html"]
         
        with warnings.catch_warnings(record=True) as caught_warnings:
            BeautifulSoup(page_html, 'html.parser')
            for warn in caught_warnings:
                print(warn)
                return False
    return True


def length_check(path: str, min_length: int = 2000) -> bool:
    """
    This function checks the minimum HTML page size.
    :param path: Path to file contains HTML page
    :param min_length: Minimum allowed length
    :return: True – if not satisfied, False – otherwise
    """
    with open(path, "r") as file:
        data = file.read()

        if len(data) < min_length:
            return True
    return False
