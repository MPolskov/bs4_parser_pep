import logging
import re
from requests import RequestException
from exceptions import ParserFindTagException
from bs4 import BeautifulSoup


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


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag


def find_status(session, url):
    response = get_response(session, url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    table = soup.find('dl', {'class': 'rfc2822 field-list simple'})
    if table is None:
        error_msg = f'{url} - не найдена таблица с данными.'
        logging.error(error_msg)
        raise ParserFindTagException(error_msg)
    dt_tag_status = table.find(string=re.compile('Status')).parent
    if dt_tag_status is None:
        error_msg = f'{url} - не найдена строка со статусом.'
        logging.error(error_msg)
        raise ParserFindTagException(error_msg)
    status = dt_tag_status.find_next_sibling().string
    return status
