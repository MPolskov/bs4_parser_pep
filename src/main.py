import re
import logging
from collections import defaultdict

from urllib.parse import urljoin
import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm


from configs import configure_argument_parser, configure_logging
from constants import (
    BASE_DIR,
    MAIN_DOC_URL,
    PEP_URL,
    EXPECTED_STATUS
)
from outputs import control_output
from utils import get_response, find_tag


def whats_new(session):
    """Парсер страницы с новостями Python.
    Вывод: Ссылка на статью, заголовок статьи, автор.
    """
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')

    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})

    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})

    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        version_link = urljoin(whats_new_url, version_a_tag['href'])
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append(
            (version_link, h1.text, dl_text)
        )

    return results


def latest_versions(session):
    """Парсер информации о версиях python.
    Вывод: Ссылка на документацию, версия python, статус.
    """
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')

    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')
    for a_tag in a_tags:
        link = urljoin(MAIN_DOC_URL, a_tag['href'])
        search = re.search(pattern, a_tag.text)
        if search is not None:
            version, status = search.groups()
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))

    return results


def download(session):
    """Парсер для скачивания документации python.
    Вывод: zip-архив с PDF файлом.
    """
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')

    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag,
        'a',
        {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = get_response(session, archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    """Парсер страницы с перечнем всех PEP.
    Вывод: количество PEP в каждом статусе и общее количество PEP.
    """
    response = get_response(session, PEP_URL)
    if response is None:
        return
    status_count = defaultdict(int)
    results = [('Статус', 'Количество')]
    soup = BeautifulSoup(response.text, 'lxml')
    section_tag = find_tag(soup, 'section', {'id': 'index-by-category'})
    tr_tag_list = section_tag.find_all('tr')
    errors = []
    for tag in tqdm(tr_tag_list):
        short_type_status = find_tag(tag, 'td', exeption=False)
        if short_type_status is None:
            continue
        short_status = short_type_status.text[1:]
        short_link = find_tag(tag, 'a')['href']
        full_link = urljoin(PEP_URL, short_link)
        response = get_response(session, full_link)
        if response is None:
            errors.append(f'Не удалось загрузить страницу {full_link}')
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        table = find_tag(soup, 'dl', {'class': 'rfc2822 field-list simple'})
        if table is None:
            errors.append(f'{full_link} - не найдена таблица с данными.')
        dt_tag_status = table.find(string=re.compile('Status')).parent
        if dt_tag_status is None:
            errors.append(f'{full_link} - не найдена строка со статусом.')
        status = dt_tag_status.find_next_sibling().string
        if status not in EXPECTED_STATUS[short_status]:
            errors.append(
                (
                    'Несовподающие статусы:\n'
                    f'{full_link}\n'
                    f'Статус в карточке: {status}\n'
                    f'Ожижаемый статус: {EXPECTED_STATUS[short_status]}'
                )
            )
        status_count[status] += 1

    logging.error('\n'.join(errors))

    # results.extend(status_count.items()) - так пробовал, но
    # при вызове с агруменом --output pretty парсер падает с исключением:
    # "RecursionError: maximum recursion depth exceeded while
    # calling a Python object".
    results.extend([(str(k), int(v)) for k, v in status_count.items()])
    pep_count = sum(status_count.values())
    results.append(('Total', str(pep_count)))

    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
