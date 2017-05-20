import csv
from pathlib import Path

import click
from bs4 import BeautifulSoup


def element_has_class(elem, elem_class):
    c = elem.get('class', [])
    return elem_class in c


def not_hidden_column(elem):
    return not element_has_class(elem, 'HiddenColumn')


def not_total_row(elem):
    return not element_has_class(elem, 'footer')


def not_inner_div(elem):
    # Some columns has hidden inner div, this removes them
    return not elem.div


def extract_column(tds):
    for elem in tds:
        if not_hidden_column(elem) and not_inner_div(elem):
            yield elem.text.strip()


def _find_table(html_path):
    with open(html_path) as f:
        soup = BeautifulSoup(f, 'html.parser')
    table_id_types = ['ctlActivityTable', 'ctlRegularTransactions']
    tables_found = (soup.find('table', id=table_id) for table_id in table_id_types)
    return list(filter(None, tables_found))[0]


def extract_content(html):
    table = _find_table(html)
    rows = table.find_all('tr')

    header = [c for c in rows[0].find_all(text=True, recursive=True) if c.strip()]

    yield header

    for tr in filter(not_total_row, rows[1:]):
        tds = tr.find_all('td')
        yield list(extract_column(tds))


def write_to_csv(rows, csv_path):
    with open(csv_path, 'w+') as f:
        writer = csv.writer(f)
        writer.writerows(rows)


@click.command()
@click.argument('input_path')
@click.argument('output_path')
def extract_csv(input_path, output_path):
    html_path = Path(input_path)
    rows = list(extract_content(html_path))
    write_to_csv(rows, output_path)


if __name__ == "__main__":
    extract_csv()
