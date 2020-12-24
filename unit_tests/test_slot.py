"""
Tests for Session class
Command line: python -m pytest unit_tests/test_slot.py
"""
import pytest
import mock

from app import utils
from app import constants
from datetime import datetime

LAST_ADDRESS_ID_GV = '40407464'
LAST_ADDRESS_GV = [{'id': LAST_ADDRESS_ID_GV}]
CUSTOMER_ORDER_ID_GV = '109235634'
CUSTOMER_ID_GV = '558661841'

SLOTS_JSON = {
    'data': {
        'slotDays': {
            'content': [{
                'id': '753_DELIVERY_2020-12-19',
                'branchId': '753',
                'slotType': 'DELIVERY',
                'date': '2020-12-19',
                'slots': [{
                    'slotId': '2020-12-19_07:00_08:00',
                    'startDateTime': '2020-12-19T07:00:00Z',
                    'endDateTime': '2020-12-19T08:00:00Z',
                    'shopByDateTime': None,
                    'slotStatus': 'UNAVAILABLE'
                }, {
                    'slotId': '2020-12-19_08:00_09:00',
                    'startDateTime': '2020-12-19T08:00:00Z',
                    'endDateTime': '2020-12-19T09:00:00Z',
                    'shopByDateTime': None,
                    'slotStatus': 'UNAVAILABLE'
                }]
            }],
            'failures': None
        }
    }
}

SLOTS_LIST = [{
    'id': '753_DELIVERY_2020-12-19',
    'branchId': '753',
    'slotType': 'DELIVERY',
    'date': '2020-12-19',
    'slots': [{
        'slotId': '2020-12-19_07:00_08:00',
        'startDateTime': '2020-12-19T07:00:00Z',
        'endDateTime': '2020-12-19T08:00:00Z',
        'shopByDateTime': None,
        'slotStatus': 'UNAVAILABLE'
    }, {
        'slotId': '2020-12-19_08:00_09:00',
        'startDateTime': '2020-12-19T08:00:00Z',
        'endDateTime': '2020-12-19T09:00:00Z',
        'shopByDateTime': None,
        'slotStatus': 'UNAVAILABLE'
    }]
}]

BOOK_SLOT_JSON_OK = {
    "data": {
        "bookSlot": {
            "amendOrderCutoffDateTime": "2020-12-18T12:00:00+01:00",
            "orderCutoffDateTime": "2020-12-18T12:00:00+01:00",
            "shopByDateTime": "null",
            "slotExpiryDateTime": "2020-06-17T09:43:48+01:00",
            "failures": "null"
        }
    }
}

BOOK_SLOT_JSON_FAIL = {
    "data": {
        "bookSlot": {
            "amendOrderCutoffDateTime": "2020-12-18T12:00:00+01:00",
            "orderCutoffDateTime": "2020-12-18T12:00:00+01:00",
            "shopByDateTime": "null",
            "slotExpiryDateTime": "2020-06-17T09:43:48+01:00",
            "failures": "Slot is not available"
        }
    }
}

CONFIRM_SLOT_JSON_OK = {
    "data": {
        "currentSlot": {
            "slotType": "DELIVERY",
            "branchId": "753",
            "addressId": "40407464",
            "postcode": "E14 3TJ",
            "startDateTime": "2020-12-19T07:00:00+01:00",
            "endDateTime": "2020-12-19T08:00:00+01:00",
            "expiryDateTime": "2020-06-17T09:43:48+01:00",
            "orderCutoffDateTime": "2020-12-18T12:00:00+01:00",
            "amendOrderCutoffDateTime": "2020-12-18T12:00:00+01:00",
            "shopByDateTime": "null"
        }
    }
}

CONFIRM_SLOT_JSON_FAIL = {
    "data": {
        "currentSlot": {
        }
    }
}

@pytest.fixture
def session():
    return mock.MagicMock(token='fake', customerOrderId=CUSTOMER_ORDER_ID_GV, customerId=CUSTOMER_ID_GV)


@pytest.fixture
def slot_values(session):
    return {
        'session': session,
        'fulfilment_type': 'DELIVERY',
        'postcode': 'E14 3TJ'
    }


@pytest.fixture
def slot(slot_values):
    return utils.Slot(**slot_values)


def test_get_slot(slot_values, slot):
    for attr_name in slot_values:
        assert getattr(slot, attr_name) == slot_values.get(attr_name)


@mock.patch("requests.get",
            mock.MagicMock(return_value=mock.MagicMock(json=mock.MagicMock(return_value=LAST_ADDRESS_GV))))
def test_get_last_address_id(slot_values, slot):
    last_address_id = slot.get_last_address_id()
    assert LAST_ADDRESS_ID_GV == last_address_id


def test_get_slots(slot_values, slot):
    slot.get_last_address_id = mock.MagicMock(return_value=LAST_ADDRESS_ID_GV)
    slot.session.client = mock.MagicMock(execute=mock.MagicMock(return_value=SLOTS_JSON))
    slots = slot.get_slots(753, datetime.today())
    assert slots == SLOTS_LIST

    # check a call is done with the right variables
    variables = {"slotDaysInput": {
        "branchId": "753",
        "slotType": 'DELIVERY',
        "customerOrderId": slot.session.customerOrderId,
        "addressId": LAST_ADDRESS_ID_GV,
        "fromDate": datetime.today().strftime('%Y-%m-%d'),
        "size": 5
    }}

    slot.session.client.execute.assert_called_with(query=constants.SLOT_QUERY,
                                                   variables=variables,
                                                   headers={'authorization': f"Bearer {slot.session.token}"})


def test_book_slot_ok(slot_values, slot):
    slot.session.client = mock.MagicMock(execute=mock.MagicMock(return_value=BOOK_SLOT_JSON_OK))
    book_slot = slot.book_slot(branch_id=753, postcode='E14 3TJ', address_id=LAST_ADDRESS_ID_GV, slot_type='DELIVERY',
                               start_date_time=datetime.strptime('2020-12-19 07:00:00', '%Y-%m-%d %H:%M:%S'),
                               end_date_time=datetime.strptime('2020-12-19 08:00:00', '%Y-%m-%d %H:%M:%S'))
    assert book_slot

    # check a call is done with the right variables
    variables = {"bookSlotInput": {
        "branchId": "753",
        "slotType": "DELIVERY",
        "customerOrderId": CUSTOMER_ORDER_ID_GV,
        "customerId": CUSTOMER_ID_GV,
        "postcode": "E14 3TJ",
        "addressId": LAST_ADDRESS_ID_GV,
        "startDateTime": "2020-12-19T07:00:00Z",
        "endDateTime": "2020-12-19T08:00:00Z"}
    }

    slot.session.client.execute.assert_called_with(query=constants.BOOK_SLOT_QUERY,
                                                   variables=variables,
                                                   headers={'authorization': f"Bearer {slot.session.token}"})


def test_book_slot_failure(slot_values, slot):
    slot.session.client = mock.MagicMock(execute=mock.MagicMock(return_value=BOOK_SLOT_JSON_FAIL))
    book_slot = slot.book_slot(branch_id=753, postcode='E14 3TJ', address_id=LAST_ADDRESS_ID_GV, slot_type='DELIVERY',
                               start_date_time=datetime.strptime('2020-12-19 07:00:00', '%Y-%m-%d %H:%M:%S'),
                               end_date_time=datetime.strptime('2020-12-19 08:00:00', '%Y-%m-%d %H:%M:%S'))
    assert not book_slot

    # check a call is done with the right variables
    variables = {"bookSlotInput": {
        "branchId": "753",
        "slotType": "DELIVERY",
        "customerOrderId": CUSTOMER_ORDER_ID_GV,
        "customerId": CUSTOMER_ID_GV,
        "postcode": "E14 3TJ",
        "addressId": LAST_ADDRESS_ID_GV,
        "startDateTime": "2020-12-19T07:00:00Z",
        "endDateTime": "2020-12-19T08:00:00Z"}
    }

    slot.session.client.execute.assert_called_with(query=constants.BOOK_SLOT_QUERY,
                                                   variables=variables,
                                                   headers={'authorization': f"Bearer {slot.session.token}"})


def test_confirm_slot_ok(slot_values, slot):
    slot.session.client = mock.MagicMock(execute=mock.MagicMock(return_value=CONFIRM_SLOT_JSON_OK))
    confirm_slot = slot.confirm_slot()
    assert confirm_slot

    # check a call is done with the right variables
    variables = {"currentSlotInput": {
        "customerOrderId": CUSTOMER_ORDER_ID_GV,
        "customerId": CUSTOMER_ID_GV}
    }

    slot.session.client.execute.assert_called_with(query=constants.CONFIRM_SLOT_QUERY,
                                                   variables=variables,
                                                   headers={'authorization': f"Bearer {slot.session.token}"})


def test_confirm_slot_fail(slot_values, slot):
    slot.session.client = mock.MagicMock(execute=mock.MagicMock(return_value=CONFIRM_SLOT_JSON_FAIL))
    confirm_slot = slot.confirm_slot()
    assert not confirm_slot

    # check a call is done with the right variables
    variables = {"currentSlotInput": {
        "customerOrderId": CUSTOMER_ORDER_ID_GV,
        "customerId": CUSTOMER_ID_GV}
    }

    slot.session.client.execute.assert_called_with(query=constants.CONFIRM_SLOT_QUERY,
                                                   variables=variables,
                                                   headers={'authorization': f"Bearer {slot.session.token}"})
