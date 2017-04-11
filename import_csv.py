import configparser
import logging
import re
import time
from pathlib import Path

import click
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException

TIMEOUT = 20

logging.basicConfig(level=logging.INFO)
d = None


def _get_file_path(input_path, account_num):
    files = input_path.glob('*.csv')
    for file in files:
        if account_num in file.name:
            return file

    logging.info('No CSV file found for account %s (probably no transactions)', account_num)


def get_accounts():
    i = 0
    while True:
        try:
            account = _get_account(i)
        except IndexError:
            break
        except WebDriverException:
            # try to recover if there is an open window
            d.find_element_by_class_name('button-cancel').click()
            account = _get_account(i)

        match = re.search('(\d{4})', account.text)
        if match:
            account_num = match.group(0)
            account.click()
            logging.info('Processing account: %s', account_num)

            yield account_num

        time.sleep(0.5)
        i += 1


def _get_account(i):
    return d.find_element_by_class_name('onBudget').find_elements_by_class_name(
        'nav-account-row')[i]


def get_budget(input_path):
    for account_num in get_accounts():
        file = _get_file_path(input_path, account_num)
        if file:
            d.find_element_by_class_name('accounts-toolbar-file-import-transactions').click()
            e = d.find_element_by_css_selector('body > input[type="file"]')
            e.send_keys(str(file))
            _check_previous_transactions()
            _import_or_cancel()
            time.sleep(0.3)
            d.find_element_by_class_name('button-primary').click()


def _import_or_cancel():
    d.find_element_by_class_name('button-primary').click()


def _check_previous_transactions():
    # Check "import previous transactions" only if exists
    try:
        d.implicitly_wait(1)
        d.find_element_by_class_name('import-preview-warning').find_element_by_class_name(
            'ynab-checkbox-button-square').click()
    except NoSuchElementException:
        pass
    except WebDriverException as e:
        print(e)
    finally:
        d.implicitly_wait(TIMEOUT)


def _login(_id, pswd):
    logging.info('Logging in')
    d.find_element_by_class_name('login-username').send_keys(_id)
    d.find_element_by_class_name('login-password').send_keys(pswd)
    time.sleep(0.5)
    d.find_element_by_class_name('button-primary').click()


def _create_driver():
    global d
    d = webdriver.Chrome()
    d.implicitly_wait(TIMEOUT)
    d.get('https://app.youneedabudget.com')


def get_creds(conf_path):
    config = configparser.ConfigParser()
    config.read(conf_path)
    ynab_config = config['ynab']
    return ynab_config['id'], ynab_config['pswd']


@click.command()
@click.argument('conf_path')
@click.argument('input_path')
def import_to_ynab(conf_path, input_path):
    input_path = Path(input_path)
    _create_driver()
    _login(*get_creds(conf_path))
    get_budget(input_path)
    d.quit()


if __name__ == "__main__":
    import_to_ynab()
