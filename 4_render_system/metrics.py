from lxml import html, etree
from bs4 import BeautifulSoup
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score



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


def generate_all_xpaths(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    elems = soup.find_all(True)
    xpaths = []
    for elem in elems:
        xpaths.append(xpath_soup(elem))

    return xpaths


def str_prefix(parsed_string: list, prefix_len: int):
    return "/".join(parsed_string[:prefix_len])


def generate_segmentation_str(xpaths: list):
    '''
        Эта функция берет список строк xpath и для каждого xpath находит такой минимальный префикс,
        что он не содержит других элементов списка
        Возвращает список уникальных префиксов
    '''
    xpaths = [xpath.split('/') for xpath in xpaths]
    unique_xpaths = []

    for xpath in xpaths:
        for prefix_len in range(1, len(xpath)):
            prefix = str_prefix(xpath, prefix_len)

            unique_prefix = True

            for other_xpath in xpaths:
                if other_xpath != xpath:
                    other_prefix = str_prefix(other_xpath, prefix_len)

                    if other_prefix == prefix:
                        unique_prefix = False
                        break

            if unique_prefix:
                unique_xpaths.append(prefix)
                break
        else:
            prefix = str_prefix(xpath, None)
            unique_xpaths.append(prefix)

    return unique_xpaths


def path_contains(x: list, y: list) -> bool:
    '''
        True if x contains y
    '''
    return x == y[:len(x)]
