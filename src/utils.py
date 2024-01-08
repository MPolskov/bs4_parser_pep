import logging
# import re
from exceptions import ParserFindTagException

from requests import RequestException
# from bs4 import BeautifulSoup


def get_response(session, url):
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}',
            stack_info=True
        )


def find_tag(soup, tag, attrs=None, exeption=True):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None and exeption:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag
