import datetime
import subprocess
from pathlib import Path

import click

from extract_csv import extract_csv
from fetch_html_report import fetch_accounts_data
from transform_csv import transform_csv


def _transform_csv(ctx, extracted_csv_file, report, transformed_csv_root):
    transformed_csv_file = _get_file_path(transformed_csv_root, report)
    ctx.invoke(transform_csv, input_path=extracted_csv_file, output_path=transformed_csv_file)


def _extract_csv(ctx, extracted_csv_root, report):
    extracted_csv_file = _get_file_path(extracted_csv_root, report)
    ctx.invoke(extract_csv, input_path=report, output_path=extracted_csv_file)
    return extracted_csv_file


def _get_file_path(root, report):
    return root / (report.stem + '.csv')


def _get_paths(root_path):
    run_root_path = _create_path_dir(root_path, str(datetime.date.today()))
    html_path = _create_path_dir(run_root_path, 'html')
    extracted_csv_root = _create_path_dir(run_root_path, 'extracted_csv')
    transformed_csv_root = _create_path_dir(run_root_path, 'transformed_csv')

    return extracted_csv_root, html_path, transformed_csv_root


def _create_path_dir(path, extension=None):
    new_path = Path(path) / extension if extension else path
    new_path.mkdir(exist_ok=True)
    return new_path


@click.command()
@click.argument('conf_path', type=click.Path(exists=True))
@click.argument('root_path')
@click.option('--fetch_data', default=True, type=bool)
@click.pass_context
def run(ctx, conf_path, root_path, fetch_data):
    extracted_csv_root, html_path, transformed_csv_root = _get_paths(root_path)

    if fetch_data:
        ctx.invoke(fetch_accounts_data, conf_path=conf_path, output_path=html_path)

    for report in html_path.glob('*.html'):
        extracted_csv_file = _extract_csv(ctx, extracted_csv_root, report)
        _transform_csv(ctx, extracted_csv_file, report, transformed_csv_root)

    subprocess.run(['bash', 'merge_csv.sh', str(transformed_csv_root)])


if __name__ == "__main__":
    run()
