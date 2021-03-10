import datetime
import logging
import os
import re
import sys
import time
from urllib.parse import urljoin

import dateutil.parser
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from app.constants import CHAIN_INTERVAL_HRS
from app.log.status_bar import PROGRESS_LOG
from app.timed_lru_cache import timed_lru_cache
from app.log import app_exception

from random import randint

MON, TUE, WED, THU, FRI, SAT, SUN = range(7)
SLOT_EXPIRY_SEC = 300


class Tesco:

    BASE_URL = 'https://www.tesco.com/'

    name = 'tesco'
    display_name = 'Tesco'

    session_expiry_sec = 300

    slot_start_time = datetime.time(8, 00, 00)
    slot_end_time = datetime.time(23, 00, 00)
    slot_interval_hrs = CHAIN_INTERVAL_HRS

    timeout_sec = 60

    def __init__(self, login, password):
        self._login = login
        self._password = password

        self._current_slot = None
        self._last_current_slot_update_time = None

        chrome_options = webdriver.ChromeOptions()
        capabilities = DesiredCapabilities.CHROME.copy()

        if os.getenv('INSIDE_DOCKER_CONTAINER') == '1':
            self.driver = webdriver.Remote("http://selenium-hub:4444/wd/hub",
                                           desired_capabilities=capabilities,
                                           options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)
        self.login()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    def _load(self, url):
        self.driver.get(urljoin(self.BASE_URL, url))

    def _wait_and_click(self, links_text):
        while True:
            success = False
            for link in links_text:
                try:
                    elem = self.driver.find_element_by_link_text(link)
                    elem.click()
                    success = True
                    break
                except:
                    continue

            if success:
                break
            else:
                time.sleep(1)

    def login(self):
        PROGRESS_LOG.info('Loggining into profile')
        self._load('account/en-GB/login')
        login = self.driver.find_element_by_id('username')
        login.send_keys(self._login)

        password = self.driver.find_element_by_id('password')
        password.send_keys(self._password)

        form = self.driver.find_element_by_xpath('//*[@id="sign-in-form"]/button')
        form.submit()

    def get_current_slot(self):
        PROGRESS_LOG.info('Fetching current slot')

        if self._current_slot and time.time() - self._last_current_slot_update_time < Tesco.session_expiry_sec:
            return self._current_slot

        self._load('groceries')
        slots = self.driver.find_elements_by_class_name("context-cards--slot-booked")
        if len(slots):
            _date = slots[0].find_element_by_class_name('context-card-date-tile')
            _time = slots[0].find_element_by_class_name('slot-time').get_attribute('innerHTML')
            _day = _date.find_element_by_class_name('date').get_attribute('innerHTML')
            _month = _date.find_element_by_class_name('month').get_attribute('innerHTML')

            res = datetime.datetime.strptime(f"{datetime.datetime.now().year}-{_month}-{_day} {_time.split(' - ')[0]}",
                                             '%Y-%b-%d %H:%M')
            if slots[0].get_attribute('class').find('expired') != -1:
                logging.warning(f"Current slot {res} has expired")
                return None
            self._current_slot = res
            self._last_current_slot_update_time = time.time()
            return res

    @timed_lru_cache(SLOT_EXPIRY_SEC)
    def get_slots(self, filters=None):
        PROGRESS_LOG.info(f'Fetching slots with filters "{filters or "no filters"}"')
        self._load('groceries/en-GB/slots/delivery')

        available_weeks = self.driver.find_elements_by_class_name("slot-selector--week-tabheader-link")
        weeks = []
        for week in available_weeks:
            weeks.append(week.get_attribute('href'))

        slots_data = list()

        for week_href in weeks:
            PROGRESS_LOG.info(f'Fetching slots for {week_href.replace("?slotGroup=1", "").split("/")[-1]}')
            self.driver.get(week_href)

            slots = self.driver.find_elements_by_class_name('slot-grid--item')

            for slot in slots:
                if slot.get_attribute('class').find('unavailable') != -1:
                    continue

                button = slot.find_element_by_tag_name('button')
                ref = button.find_element_by_tag_name('a')
                grid_time = ref.get_attribute('id')
                parts = grid_time.split('_')

                slot_time = dateutil.parser.isoparse(parts[1]).replace(tzinfo=None)

                if filters:
                    for day, time_begin, time_end in filters:
                        if day == slot_time.weekday() and time_begin <= slot_time.time() <= time_end:
                            slots_data.append(slot_time)
                else:
                    slots_data.append(slot_time)

        return [x for x in sorted(slots_data)]

    def _wait_for_slot(self, positive):
        started = time.time()
        while True:
            if time.time() - started > Tesco.timeout_sec:
                raise TimeoutError("Unable to book slot, timed out")

            found = len(self.driver.find_elements_by_class_name("slot-time")) > 0
            if positive == found:
                break
            else:
                logging.info(f"Waiting for book slot confirmation: {positive}")
                time.sleep(1)

    def _click_on_slot(self, slot_begin):
        # generate slot id
        time_format = "%Y-%m-%dT%H:%M:%S"
        slot_id = f"grid_{slot_begin.strftime(time_format)}"

        slot_elem = self.driver.find_element_by_xpath(f"//a[contains(@id, '{slot_id}')]")
        button = slot_elem.find_element_by_xpath('..')
        button.click()

    def book(self, slot_begin: datetime.datetime):
        PROGRESS_LOG.info(f'Booking slot: {slot_begin}')

        self._current_slot = self.get_current_slot()

        # load week page for this slot
        self._load(f"groceries/en-GB/slots/delivery/{slot_begin.date()}?slotGroup=1")

        if self._current_slot != slot_begin:

            if self.driver.find_elements_by_class_name("slot-time"):
                self._click_on_slot(self._current_slot)
                self._wait_for_slot(False)

                self._load(f"groceries/en-GB/slots/delivery/{slot_begin.date()}?slotGroup=1")

            self._click_on_slot(slot_begin)
            self._wait_for_slot(True)

            self._current_slot = slot_begin
            self._last_current_slot_update_time = time.time()

    def is_basket_empty(self):
        self._load('groceries/en-GB/trolley')
        return len(self.driver.find_elements_by_class_name('empty-section--empty-text')) > 0

    def add_last_order_to_basket(self):
        self._load('groceries/en-GB/orders')
        text = self.driver.find_element_by_xpath("//span[text()='Add all to basket']")
        button = text.find_element_by_xpath("../..")
        button.click()

    def checkout(self, cvv):
        PROGRESS_LOG.info('Checkout')

        if self.is_basket_empty():
            PROGRESS_LOG.info('Adding the last order to the basket')
            self.add_last_order_to_basket()

        self._load('groceries/en-GB/trolley')

        # TODO: add time check
        while not self.driver.current_url.endswith('review-trolley'):
            self._load('groceries/en-GB/checkout/review-trolley')
        while self.driver.current_url.find('payment?') == -1:
            self._wait_and_click(["Continue checkout", "Continue to payment"])

        self.driver.switch_to.frame('bounty-iframe')

        PROGRESS_LOG.info('Making payment')

        time.sleep(randint(0, 1))
        inp = self.driver.find_element_by_class_name('cvc-input')
        inp.send_keys(str(cvv))

        time.sleep(randint(0, 1))
        button = self.driver.find_element_by_class_name('confirm-button')
        button.click()

        start_time = time.time()
        PROGRESS_LOG.info('Waiting for payment confirmation')
        while True:
            if time.time() - start_time > Tesco.timeout_sec:
                raise app_exception.PaymentErrorException
            try:
                text = self.driver.find_element_by_xpath("//*[contains(text(), 'Your order number is')]")
                logging.info(f"Order text: '{text.text}'")
                return re.match(r"[^\d]+(\d+-\d+-\d+)", text.text).group(1)
            except:
                logging.info("Waiting for payment confirmation")
                time.sleep(1)

    def get_last_order_date(self):
        pass


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
    logging.getLogger().setLevel(getattr(logging, os.getenv('LOGGING_LEVEL', '') or 'INFO'))

    filters = [(FRI, datetime.time(16, 00, 00), datetime.time(17, 00, 00))]

    with Tesco(sys.argv[1], sys.argv[2]) as tesco:
        current = tesco.get_current_slot()
        logging.info(f"Current slot: {current}")
        if not current:
            slots = tesco.get_slots(filters)
            for slot in slots:
                logging.info(f"Available slot: {slot.strftime('%m/%d/%Y %H:%M:%S')}")
            if slots:
                tesco.book(slots[0])
            else:
                logging.error(f"No slots available with specified filters: '{filters}'")
                exit(1)

            logging.info("Booked")

        if tesco.is_basket_empty():
            tesco.add_last_order_to_basket()

        order_id = tesco.checkout(int(sys.argv[3]))
        logging.info(f"Checkout succeeded, order number: {order_id}")
