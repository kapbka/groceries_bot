import time
import os
import datetime
import logging
import re
import sys
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from urllib.parse import urljoin
import dateutil.parser
from app.constants import CHAIN_INTERVAL_HRS
from app.timed_lru_cache import timed_lru_cache

MON, TUE, WED, THU, FRI, SAT, SUN = range(7)
SLOT_EXPIRY_SEC = 300


log = logging.getLogger('telegram')


class Tesco:

    BASE_URL = 'https://www.tesco.com/'

    name = 'tesco'
    display_name = 'Tesco'

    session_expiry_sec = 300

    slot_start_time = datetime.time(8, 00, 00)
    slot_end_time = datetime.time(23, 00, 00)
    slot_interval_hrs = CHAIN_INTERVAL_HRS

    def __init__(self, login, password):
        self._login = login
        self._password = password

        chrome_options = webdriver.ChromeOptions()
        capabilities = DesiredCapabilities.CHROME.copy()

        if os.getenv('container') == 'oci':
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
        self._load('account/en-GB/login')
        login = self.driver.find_element_by_id('username')
        login.send_keys(self._login)

        password = self.driver.find_element_by_id('password')
        password.send_keys(self._password)

        form = self.driver.find_element_by_xpath('//*[@id="sign-in-form"]/button')
        form.submit()

    def get_current_slot(self):
        self._load('groceries')
        slots = self.driver.find_elements_by_class_name("context-cards--slot-booked")
        if len(slots):
            date = slots[0].find_element_by_class_name('context-card-date-tile')
            time = slots[0].find_element_by_class_name('slot-time').get_attribute('innerHTML')
            day = date.find_element_by_class_name('date').get_attribute('innerHTML')
            month = date.find_element_by_class_name('month').get_attribute('innerHTML')

            res = datetime.datetime.strptime(f"{datetime.datetime.now().year}-{month}-{day} {time.split(' - ')[0]}",
                                             '%Y-%b-%d %H:%M')
            if slots[0].get_attribute('class').find('expired') != -1:
                logging.warning(f"Current slot {res} has expired")
                return None
            return res

    @timed_lru_cache(SLOT_EXPIRY_SEC)
    def get_slots(self, filters=None):
        logging.info(f'Getting slots with filters "{filters or "no filters"}"')
        self._load('groceries/en-GB/slots/delivery')

        available_weeks = self.driver.find_elements_by_class_name("slot-selector--week-tabheader-link")
        weeks = []
        for week in available_weeks:
            weeks.append(week.get_attribute('href'))

        slots_data = list()

        for week_href in weeks:
            logging.info(f'Fetching slots for {week_href.replace("?slotGroup=1", "").split("/")[-1]}')
            log.info(f'Fetching slots for {week_href.replace("?slotGroup=1", "").split("/")[-1]}')
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

    def book(self, slot_begin: datetime.datetime):
        # generate slot id
        slot_end = slot_begin + datetime.timedelta(hours=self.slot_interval_hrs)
        time_format = "%Y-%m-%dT%H:%M:%SZ"
        slot_id = f"grid_{slot_begin.strftime(time_format)}_{slot_end.strftime(time_format)}"

        # load week page for this slot
        self._load(f"groceries/en-GB/slots/delivery/{slot_begin.date()}?slotGroup=1")

        button = self.driver.find_element_by_id(slot_id).find_element_by_xpath('..')
        button.click()

    def is_basket_empty(self):
        self._load('groceries/en-GB/trolley')
        return len(self.driver.find_elements_by_class_name('empty-section--empty-text')) > 0

    def add_last_order_to_basket(self):
        self._load('groceries/en-GB/orders')
        text = self.driver.find_element_by_xpath("//span[text()='Add all to basket']")
        button = text.find_element_by_xpath("../..")
        button.click()

    def checkout(self, cvv):
        if self.is_basket_empty():
            self.add_last_order_to_basket()

        self._load('groceries/en-GB/trolley')

        while not self.driver.current_url.endswith('review-trolley'):
            self._load('groceries/en-GB/checkout/review-trolley')
        while self.driver.current_url.find('payment?') == -1:
            self._wait_and_click(["Continue checkout", "Continue to payment"])

        self.driver.switch_to.frame('bounty-iframe')

        inp = self.driver.find_element_by_class_name('cvc-input')
        inp.send_keys(str(cvv))

        button = self.driver.find_element_by_class_name('confirm-button')
        button.click()

        # TODO: add exit condition if wrong cvv for example
        while True:
            try:
                text = self.driver.find_element_by_xpath("//*[contains(text(), 'Your order number is')]")
                logging.info(f"Order text: '{text.text}'")
                return re.match(r"[^\d]+(\d{4}-\d{4}-\d{3})", text.text).group(1)
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
