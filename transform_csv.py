import csv
from collections import OrderedDict
from pathlib import Path

import click

map_headers = OrderedDict({
    'Date': ['תאריך העסקה', 'תאריך'],
    'Payee': ['שם בית העסק', 'תיאור'],
    'Category': [],
    'Memo': ['פרטים', 'אסמכתא'],
    'Outflow': ['סכום החיוב', 'חובה', 'סכום החיוב בש"ח'],
    'Inflow': ['זכות']
})


def debit_transaction(row):
    return 'כרטיס דביט' in row


def transform(file):
    rows = get_rows(file)
    new_column_index = list(_get_fields_index(rows[0]))
    new_rows = list(_extract_rows_values(new_column_index, rows[1:]))
    new_table = [list(map_headers.keys())] + new_rows
    return new_table


def _extract_rows_values(new_column_index, rows):
    for row in rows:
        if debit_transaction(row):
            continue
        yield _extract_columns(new_column_index, row)


def _extract_columns(new_column_index, row):
    for index in new_column_index:
        if index is not None:
            yield row[index]
        else:
            yield ''


def _get_fields_index(header):
    for values in map_headers.values():
        for column_index, column_name in enumerate(header):
            if column_name in values:
                yield column_index
                break
        else:
            yield None


def get_rows(file):
    with file.open() as f:
        return list(csv.reader(f))


@click.command()
@click.argument('input_path')
@click.argument('output_path')
def transform_csv(input_path, output_path):
    input_path, output_path = Path(input_path), Path(output_path)
    new_table = transform(input_path)
    with output_path.open('w') as f:
        writer = csv.writer(f)
        writer.writerows(new_table)


if __name__ == "__main__":
    transform_csv()
