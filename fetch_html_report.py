# -*- coding: utf-8 -*-
import configparser
import logging
import os
import pathlib
import re
import shutil
from collections import namedtuple
from os.path import expanduser
from time import sleep

import click as click
from selenium import webdriver
from selenium.webdriver.support.select import Select

logging.basicConfig(level=logging.INFO)

CARDS_SELECTOR = '#ddlCard'
ACCOUNTS_CSS_SELECTOR = '#ddlAccounts_m_ddl'
FIRST_ACCOUNT_SELECTOR = '#ctlActivityTable > tbody > tr.item > td:nth-child(1) > a'
account_num_regex = re.compile('\d{3}-\d{6}/\d{2}')
credit_card_regex = re.compile('.* \d{4}')

Creds = namedtuple('Creds', 'id pswd')

d = None
processed_accounts = set()


def _move_report_to_output_path(output_path, account_name):
    downloads_path = pathlib.Path(expanduser("~")) / 'Downloads'
    newest = max(downloads_path.glob('*.html'), key=os.path.getctime)
    filename = output_path / (account_name + '.html')
    shutil.copy(newest, filename)


def is_new_window_open():
    return len(d.window_handles) > 1


def _save_report():
    d.find_element_by_css_selector("#btnDisplay").click()
    d.find_element_by_css_selector("#BTNSAVE").click()

    # Wait for new window to open
    sleep(0.5)

    # Sometimes there are no transactions so on pressing save nothing happens.
    if not is_new_window_open():
        return False

    d.switch_to_window(d.window_handles[1])
    d.find_element_by_css_selector("#ImgContinue").click()
    d.switch_to_window(d.window_handles[0])

    # Wait for download to finish
    sleep(1.5)
    return True


def _go_to_bank_account_view():
    d.find_element_by_css_selector("#navTopImgID_1").click()


def _go_to_credit_account_view():
    d.find_element_by_css_selector("#navTopImgID_2").click()
    d.find_element_by_css_selector(FIRST_ACCOUNT_SELECTOR).click()


def _traverse_all_dropdown_options(css_dropdown_selector, regex):
    # this weird pattern is used since switching windows cause to lose the select dropdown, hence
    # I'm re-selecting it all the time and keeping an index
    i = 0
    while True:
        try:
            account = Select(d.find_element_by_css_selector(css_dropdown_selector)).options[i]
        except IndexError:
            break

        account_name = account.text
        if regex.match(account_name):
            account.click()
            yield _extract_account_num(account_name)

        i += 1


def is_account_processed(account_name):
    is_processed = account_name in processed_accounts
    processed_accounts.add(account_name)
    return is_processed


def _save_accounts(output_path, selector, regex):
    for account_num in _traverse_all_dropdown_options(selector, regex):
        if not is_account_processed(account_num):
            logging.info("Processing account %s", account_num)
            success = _save_report()
            if success:
                _move_report_to_output_path(output_path, account_num)


def _extract_account_num(account_name):
    return ''.join(i for i in account_name if i.isdigit())


def _save_credit_cards(output_path):
    for _ in _traverse_all_dropdown_options(ACCOUNTS_CSS_SELECTOR, account_num_regex):
        _save_accounts(output_path, CARDS_SELECTOR, credit_card_regex)


def login(id_, pswd):

    d.find_element_by_css_selector(u"a[title=\"כניסה לחשבונך\"]").click()
    d.find_element_by_id("uid").send_keys(id_)
    d.find_element_by_id("password").send_keys(pswd)
    d.find_element_by_id("enter").click()


def _retrieve_info(output_path, creds):
    login(*creds)
    logging.info('Fetching checking account')
    _go_to_bank_account_view()
    _save_accounts(output_path, ACCOUNTS_CSS_SELECTOR, account_num_regex)

    logging.info('Fetching credit account')
    _go_to_credit_account_view()
    _save_credit_cards(output_path)


def _get_conf(conf_path):
    config = configparser.ConfigParser()
    config.read(conf_path)
    return config


def _create_driver():
    global d
    d = webdriver.Chrome()
    d.implicitly_wait(30)
    d.get("http://www.leumi.co.il/")


def get_creds(conf_path):
    conf = _get_conf(conf_path)
    for section, values in conf.items():
        if section in ['DEFAULT', 'ynab']:
            continue
        yield section, Creds(values['id'], values['pswd'])


@click.command()
@click.argument('conf_path')
@click.argument('output_path')
def fetch_accounts_data(conf_path, output_path):
    """A program to download Leumi bank accounts data"""
    output_path = pathlib.Path(output_path)
    for account, creds in get_creds(conf_path):
        logging.info('Fetching info for %s bank accounts', account.title())
        _create_driver()
        _retrieve_info(output_path, creds)
        d.quit()


if __name__ == "__main__":
    fetch_accounts_data()
