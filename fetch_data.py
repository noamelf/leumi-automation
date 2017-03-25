# -*- coding: utf-8 -*-
import configparser
import datetime
import logging
import os
import pathlib
import re
import shutil
from collections import namedtuple
from time import sleep

import click as click
from os.path import expanduser
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


def _move_report_to_output_path(output_path, filename):
    newest = max(output_path.glob('*.html'), key=os.path.getctime)
    report_path = output_path / 'leumi-automation' / str(datetime.date.today())
    report_path.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(newest), str(report_path / filename))


def _save_report():
    d.find_element_by_css_selector("#btnDisplay").click()
    d.find_element_by_css_selector("#BTNSAVE").click()

    # Wait for new window to open
    sleep(0.5)
    d.switch_to_window(d.window_handles[1])
    d.find_element_by_css_selector("#ImgContinue").click()
    d.switch_to_window(d.window_handles[0])

    # Wait for download to finish
    sleep(1.5)


def _go_to_bank_account_view():
    d.find_element_by_css_selector("#navTopImgID_1").click()


def _go_to_credit_account_view():
    d.find_element_by_css_selector("#navTopImgID_2").click()
    d.find_element_by_css_selector(FIRST_ACCOUNT_SELECTOR).click()


def _traverse_all_dropdown_options(css_dropdown_selector, regex):
    # this weird pattern is used since switching windows cause to loose the select dropdown, hence
    # I'm re-selecting it all the time and keeping an index
    i = 0
    while True:
        try:
            account = Select(d.find_element_by_css_selector(css_dropdown_selector)).options[i]
        except IndexError:
            break

        account_name = account.text
        if regex.match(account_name):
            logging.info("Processing account %s", account_name)
            account.click()
            yield account_name

        i += 1


def _save_accounts(output_path, selector, regex):
    for account_name in _traverse_all_dropdown_options(selector, regex):
        _save_report()
        _move_report_to_output_path(output_path, _create_filename(account_name))


def _create_filename(account_name):
    return ''.join(i for i in account_name if i.isdigit()) + '.html'


def _save_credit_cards(output_path):
    for _ in _traverse_all_dropdown_options(ACCOUNTS_CSS_SELECTOR, account_num_regex):
        _save_accounts(output_path, CARDS_SELECTOR, credit_card_regex)


def login(id_, pswd):
    d.find_element_by_css_selector(u"a[title=\"כניסה לחשבונך\"]").click()
    d.find_element_by_css_selector(u"#wtr_uid > strong:nth-child(1)").click()
    d.find_element_by_id("uid").send_keys(id_)
    d.find_element_by_css_selector("#wtr_password > strong").click()
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
        if section == 'DEFAULT':
            continue
        yield section, Creds(values['id'], values['pswd'])


@click.command()
@click.option('--conf_path', help='Path of config file')
def fetch_accounts_data(conf_path):
    downloads_path = pathlib.Path(expanduser("~")) / 'Downloads'
    """A program to download Leumi bank accounts data"""
    for account, creds in get_creds(conf_path):
        logging.info('Fetching info for %s bank accounts', account.title())
        _create_driver()
        _retrieve_info(downloads_path, creds)
        d.quit()


if __name__ == "__main__":
    fetch_accounts_data()
