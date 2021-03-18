import logging
import os
import json
import requests
from urllib import request
import http
from urllib.parse import urljoin
from python_graphql_client import GraphqlClient
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from app.waitrose import constants
from app.log import app_exception
from app.log.status_bar import PROGRESS_LOG


class Session:
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self.client = GraphqlClient(endpoint=constants.SESSION_ENDPOINT_URL)

        chrome_options = webdriver.ChromeOptions()
        capabilities = DesiredCapabilities.CHROME.copy()

        if os.getenv('INSIDE_DOCKER_CONTAINER') == '1':
            self.driver = webdriver.Remote("http://selenium-hub:4444/wd/hub",
                                           desired_capabilities=capabilities,
                                           options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)

        # waitrose is canny and rewrite cookie after login,
        # so we need to get the initial value of _abck to be authorised successfully
        self._abck = None
        self.cookies = self._login()
        #self.token = self._get_cookie_value('accessToken')[9:]
        #self.customerId = self._get_cookie_value('customerId')

        session_data = self.post(constants.SESSION_QUERY,
                                 {"session": {"username": login, "password": password, "customerId": "-1", "clientId": "WEB_APP"}})

        self.token = session_data['data']['generateSession']['accessToken']
        self.headers = {'authorization': f"Bearer {self.token}"}
        self.customerId = int(session_data['data']['generateSession']['customerId'])
        self.customerOrderId = int(session_data['data']['generateSession']['customerOrderId'])

        address_list = self.get_address_list()
        self.default_address_id = address_list[0]['id']
        self.default_postcode = address_list[0]['postalCode']
        self.phone_number = address_list[0]['addressee']['contactNumber']
        postcode_branches = requests.get(constants.BRANCH_ID_BY_POSCODE_URL.format(self.default_postcode),
                                         headers=self.headers).json()
        if postcode_branches or postcode_branches['totalCount'] >= 1:
            self.default_branch_id = [branch['branch']['id'] for branch in postcode_branches['branches']
                                      if branch['defaultBranch']][0]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    def _load(self, url):
        self.driver.get(urljoin(constants.MAIN_PAGE_URL, url))

    def _login(self):
        PROGRESS_LOG.info('Loggining into Waitrose profile')
        self._load('ecom/login')
        allow_cookies = self.driver.find_element_by_xpath("//*[contains(text(), 'Yes, allow all')]")
        allow_cookies.click()

        # we need to get _abck cookie before login, after login server changes it to invalid value
        # server will accept only the initial value which we need to save before login
        temp_cookies = self.driver.get_cookies()
        for cookie in temp_cookies:
            if cookie['name'] == '_abck':
                self._abck = cookie['value']

        login = self.driver.find_element_by_id('email')
        login.send_keys(self.login)

        password = self.driver.find_element_by_id('password')
        password.send_keys(self.password)

        sign_in = self.driver.find_element_by_id('loginSubmit')
        sign_in.submit()

        incorrect_login_errors = self.driver.find_elements_by_xpath("//*[contains(text(), \"We didn't recognise your details\")]")
        if incorrect_login_errors:
            raise app_exception.LoginFailException

        account__locked_errors = self.driver.find_elements_by_xpath("//*[contains(text(), \"Your account has been locked due to several unsuccessful sign in attempts\")]")
        if account__locked_errors:
            raise app_exception.AccountLockedException

        _ = WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, "//*[contains(text(), \"My account\")]")))

        return self.driver.get_cookies()

    def _get_cookie_value(self, name):
        for cookie in self.cookies:
            if cookie['name'] == name:
                return cookie['value']
        raise app_exception.NoCookieException

    def _get_header_cookies(self):
        res = list()
        res.append('bm_sz=' + self._get_cookie_value('bm_sz'))
        res.append('mt.v=' + self._get_cookie_value('mt.v'))
        res.append('mt.sc=' + self._get_cookie_value('mt.sc'))
        res.append('ak_bmsc=' + self._get_cookie_value('ak_bmsc'))
        res.append('_abck=' + self._abck)
        res.append('wtr_cookie_consent=' + self._get_cookie_value('wtr_cookie_consent'))
        res.append('wtr_cookies_advertising=' + self._get_cookie_value('wtr_cookies_advertising'))
        res.append('wtr_cookies_analytics=' + self._get_cookie_value('wtr_cookies_analytics'))
        res.append('wtr_cookies_functional=' + self._get_cookie_value('wtr_cookies_functional'))
        res.append('IR_gbd=' + self._get_cookie_value('IR_gbd'))
        res.append('IR_12163=' + self._get_cookie_value('IR_12163'))
        res.append('_gcl_au=' + self._get_cookie_value('_gcl_au'))
        res.append('_fbp=' + self._get_cookie_value('_fbp'))
        res.append('_pin_unauth=' + self._get_cookie_value('_pin_unauth'))
        res.append('_ga=' + self._get_cookie_value('_ga'))
        res.append('_gid=' + self._get_cookie_value('_gid'))
        res.append('_gat_UA-34398547-2=' + self._get_cookie_value('_gat_UA-34398547-2'))
        res.append('ecos.dt=' + self._get_cookie_value('ecos.dt'))
        #res.append('loginAttempted=true')

        cookie_str = '; '.join(res)

        return cookie_str

    def post(self, query: str, variables: dict):
        logging.debug(variables)

        data_raw = json.dumps({"query": query, "variables": variables})
        req = request.Request(constants.SESSION_ENDPOINT_URL, method="POST")
        req.add_header('cookie', self._get_header_cookies())
        req.add_header('content-type', 'application/json')
        r = request.urlopen(req, data=data_raw.encode())
        content = json.loads(r.read().decode())

        logging.debug(content)

        if r.status != http.HTTPStatus.OK:
            raise app_exception.PostRequestException

        return content

    def execute(self, query: str, variables: dict):
        logging.debug(variables)

        logging.debug(variables)
        return self.client.execute(
            query=query,
            variables=variables,
            headers=self.headers if self.token else {})

    def get_address_list(self):
        r = requests.get(constants.LAST_ADDRESS_ID_URL, headers=self.headers).json()
        if not r:
            raise app_exception.NoAddressException
        return r

    def get_order_dict(self):
        r = requests.get(constants.ORDER_LIST_URL, headers=self.headers).json()
        return {order['customerOrderId']: order for order in r['content']}

    def _get_orders(self):
        r = requests.get(constants.ORDER_LIST_URL, headers=self.headers)
        if r.status_code != http.HTTPStatus.OK:
            raise app_exception.OrderListException
        res = r.json()
        if not res['content']:
            raise app_exception.NoOrdersException
        return res

    def get_last_order_date(self):
        orders = self._get_orders()
        return datetime.strptime(orders['content'][0]['slots'][0]['startDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ').date()

    def order_exists(self, slot_datetime):
        orders = self._get_orders()
        for order in orders['content']:
            order_datetime = datetime.strptime(order['slots'][0]['startDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ').date()
            if order_datetime == slot_datetime:
                logging.info(f'Order already exists {order_datetime}')
                return True
        return False

    def merge_last_order_to_trolley(self):
        try:
            order = next(iter(self.get_order_dict().values()))
        except StopIteration:
            logging.info('Orders not found1')
            raise app_exception.NoOrdersSlotBookedException

        logging.info('Getting products')
        line_num_qty_dict = {ol['lineNumber']: ol['quantity'] for ol in order['orderLines']}
        order_lines = '+'.join(ol for ol in line_num_qty_dict.keys())
        products = requests.get(constants.PRODUCT_LIST_URL.format(order_lines),
                                headers=self.headers).json() if order_lines else {}

        res = []
        for p in products['products']:
            if not p['markedForDelete']:
                pl = dict(canSubstitute='false',
                          lineNumber=str(p['lineNumber']),
                          productId=str(p['id']),
                          quantity=line_num_qty_dict[p['lineNumber']],
                          reservedQuantity=0,
                          trolleyItemId=-1)
                res.append(pl)

        logging.info('Getting items')
        items = requests.patch(constants.TROLLEY_ITEMS_URL.format(self.customerOrderId),
                               headers=self.headers, json=res).json() if res else {}

        # if there is no match the dict will contain 'message' key with the details what's wrong
        if 'message' in items:
            logging.exception(items['message'])
            raise ValueError(items['message'])

    def is_trolley_empty(self):
        variables = {"orderId": str(self.customerOrderId)}
        trolley = self.execute(constants.TROLLEY_QUERY, variables)
        failures = trolley['data']['getTrolley'].get('failures') or {}
        if failures.get('message'):
            raise app_exception.TrolleyException
        return not trolley['data']['getTrolley']['products']

    def get_payment_card_list(self):
        card_list = requests.get(constants.PAYMENTS_CARDS_URL, headers=self.headers).json()
        if not card_list:
            raise app_exception.NoPaymentCardException
        return card_list

    def get_card_id(self, card_num: int):
        cards = self.get_payment_card_list()
        for card in cards:
            if card['maskedCardNumber'].endswith(str(card_num)):
                return card['id']
        raise ValueError(f'Card number with last 4 digits "***{card_num}" is not found!')

    def checkout_trolley(self, card_id: int, cvv: int):
        # 1. CHECKOUT ORDER
        logging.info(f'Checkout: card_id {card_id}')
        checkout_param = {"addressId": str(self.default_address_id),
                          "cardSecurityCode": str(cvv)}
        checkout_resp = requests.put(constants.CHECKOUT_URL.format(str(self.customerOrderId), str(card_id)),
                                     headers=self.headers, json=checkout_param)
        logging.info(f'Checkout order response status code {checkout_resp.status_code}')
        if checkout_resp.status_code != http.HTTPStatus.CREATED:
            raise app_exception.PaymentException

        # 2. PLACE ORDER CONFIRMATION
        logging.info(f'Place order {self.customerOrderId}')
        place_param = {"contactNumber": self.phone_number,
                       "event": "PLACE",
                       "paperStatement": "false"}
        place_resp = requests.patch(constants.PLACE_ORDER_URL.format(str(self.customerOrderId)),
                                    headers=self.headers, json=place_param)
        logging.info(f'Place order response status code {place_resp.status_code}')
        if place_resp.status_code != http.HTTPStatus.OK:
            raise app_exception.PlaceOrderException


if __name__ == '__main__':
    s = Session('clrn@mail.ru', 'HSw=Lr%wHUM38JC')