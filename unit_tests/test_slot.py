"""
Tests for Slot class
Command line: python -m pytest unit_tests/test_slot.py
"""
import pytest
import mock

from app.slot import Slot
from app import constants
from datetime import datetime, time

DEFAULT_ADDRESS_ID_GV = 40407464
DEFAULT_ADDRESS_GV = [{'id': DEFAULT_ADDRESS_ID_GV}]
CUSTOMER_ORDER_ID_GV = 109235634
CUSTOMER_ID_GV = 558661841
BRANCH_ID = 753
POSTCODE = 'E14 3TJ'
SLOT_TYPE = 'DELIVERY'

SLOTS_JSON = {
    'data': {
        'slotDays': {
            'content': [{
                'id': str(BRANCH_ID) + '_' + SLOT_TYPE + '_2020-12-19',
                'branchId': BRANCH_ID,
                'slotType': SLOT_TYPE,
                'date': '2020-12-19',
                'slots': [{
                    'slotId': '2020-12-19_07:00_08:00',
                    'startDateTime': '2020-12-19T07:00:00Z',
                    'endDateTime': '2020-12-19T08:00:00Z',
                    'shopByDateTime': None,
                    'slotStatus': 'AVAILABLE'
                }, {
                    'slotId': '2020-12-19_08:00_09:00',
                    'startDateTime': '2020-12-19T08:00:00Z',
                    'endDateTime': '2020-12-19T09:00:00Z',
                    'shopByDateTime': None,
                    'slotStatus': 'UNAVAILABLE'
                }]
            },
            {
                'id': str(BRANCH_ID) + '_' + SLOT_TYPE + '_2020-12-20',
                'branchId': BRANCH_ID,
                'slotType': SLOT_TYPE,
                'date': '2020-12-20',
                'slots': [{
                    'slotId': '2020-12-20_14:00_08:00',
                    'startDateTime': '2020-12-20T14:00:00Z',
                    'endDateTime': '2020-12-20T15:00:00Z',
                    'shopByDateTime': None,
                    'slotStatus': 'AVAILABLE'
                }, {
                    'slotId': '2020-12-20_18:00_19:00',
                    'startDateTime': '2020-12-20T18:00:00Z',
                    'endDateTime': '2020-12-20T19:00:00Z',
                    'shopByDateTime': None,
                    'slotStatus': 'AVAILABLE'
                }]
            }
            ],
            'failures': None
        }
    }
}

SLOTS_LIST = [{
    'id': str(BRANCH_ID) + '_' + SLOT_TYPE + '_2020-12-19',
    'branchId': BRANCH_ID,
    'slotType': SLOT_TYPE,
    'date': '2020-12-19',
    'slots': [{
        'slotId': '2020-12-19_07:00_08:00',
        'startDateTime': '2020-12-19T07:00:00Z',
        'endDateTime': '2020-12-19T08:00:00Z',
        'shopByDateTime': None,
        'slotStatus': 'AVAILABLE'
    }, {
        'slotId': '2020-12-19_08:00_09:00',
        'startDateTime': '2020-12-19T08:00:00Z',
        'endDateTime': '2020-12-19T09:00:00Z',
        'shopByDateTime': None,
        'slotStatus': 'UNAVAILABLE'
    }]
},
    {
        'id': str(BRANCH_ID) + '_' + SLOT_TYPE + '_2020-12-20',
        'branchId': BRANCH_ID,
        'slotType': SLOT_TYPE,
        'date': '2020-12-20',
        'slots': [{
            'slotId': '2020-12-20_14:00_08:00',
            'startDateTime': '2020-12-20T14:00:00Z',
            'endDateTime': '2020-12-20T15:00:00Z',
            'shopByDateTime': None,
            'slotStatus': 'AVAILABLE'
        }, {
            'slotId': '2020-12-20_18:00_19:00',
            'startDateTime': '2020-12-20T18:00:00Z',
            'endDateTime': '2020-12-20T19:00:00Z',
            'shopByDateTime': None,
            'slotStatus': 'AVAILABLE'
        }]
    }
]

AVAILABLE_SLOT_DICT = {'2020-12-19_07:00_08:00': {
    'slotId': '2020-12-19_07:00_08:00',
    'startDateTime': '2020-12-19T07:00:00Z',
    'endDateTime': '2020-12-19T08:00:00Z',
    'shopByDateTime': None,
    'slotStatus': 'AVAILABLE'
    },
    '2020-12-20_14:00_08:00': {
        'slotId': '2020-12-20_14:00_15:00',
        'startDateTime': '2020-12-20T14:00:00Z',
        'endDateTime': '2020-12-20T15:00:00Z',
        'shopByDateTime': None,
        'slotStatus': 'AVAILABLE'
    },
    '2020-12-20_18:00_19:00': {
        'slotId': '2020-12-20_18:00_19:00',
        'startDateTime': '2020-12-20T18:00:00Z',
        'endDateTime': '2020-12-20T19:00:00Z',
        'shopByDateTime': None,
        'slotStatus': 'AVAILABLE'
    }
}

AVAILABLE_SLOT_DICT_FILTERED = {'2020-12-19_07:00_08:00': {
    'slotId': '2020-12-19_07:00_08:00',
    'startDateTime': '2020-12-19T07:00:00Z',
    'endDateTime': '2020-12-19T08:00:00Z',
    'shopByDateTime': None,
    'slotStatus': 'AVAILABLE'
    },
    '2020-12-20_18:00_19:00': {
        'slotId': '2020-12-20_18:00_19:00',
        'startDateTime': '2020-12-20T18:00:00Z',
        'endDateTime': '2020-12-20T19:00:00Z',
        'shopByDateTime': None,
        'slotStatus': 'AVAILABLE'
    }
}

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

CURRENT_SLOT_JSON_OK = {
    "data": {
        "currentSlot": {
            "slotType": SLOT_TYPE,
            "branchId": BRANCH_ID,
            "addressId": "40407464",
            "postcode": POSTCODE,
            "startDateTime": "2020-12-19T07:00:00+01:00",
            "endDateTime": "2020-12-19T08:00:00+01:00",
            "expiryDateTime": "2020-06-17T09:43:48+01:00",
            "orderCutoffDateTime": "2020-12-18T12:00:00+01:00",
            "amendOrderCutoffDateTime": "2020-12-18T12:00:00+01:00",
            "shopByDateTime": "null"
        }
    }
}

CURRENT_SLOT_OK = ('2020-12-19T07:00:00+01:00', '2020-12-19T08:00:00+01:00')

CURRENT_SLOT_JSON_FAIL = {
    "data": {
        "currentSlot": {
        }
    }
}

CURRENT_SLOT_FAIL = None, None


@pytest.fixture
def session():
    return mock.MagicMock(
        token='fake',
        customerOrderId=CUSTOMER_ORDER_ID_GV,
        customerId=CUSTOMER_ID_GV,
        default_address_id=DEFAULT_ADDRESS_ID_GV
    )


@pytest.fixture
def slot_values(session):
    return {
        'session': session,
        'slot_type': SLOT_TYPE
    }


@pytest.fixture
def slot(slot_values):
    return Slot(**slot_values)


def test_get_slot(slot_values, slot):
    for attr_name in slot_values:
        assert getattr(slot, attr_name) == slot_values.get(attr_name)


def test_get_slots(slot_values, slot):
    slot.session.execute = mock.MagicMock(return_value=SLOTS_JSON)
    slots = slot.get_slots(BRANCH_ID, datetime.today())
    assert slots == SLOTS_LIST

    # check a call is done with the right variables
    variables = {"slotDaysInput": {
        "branchId": str(BRANCH_ID),
        "slotType": SLOT_TYPE,
        "customerOrderId": str(CUSTOMER_ORDER_ID_GV),
        "addressId": str(DEFAULT_ADDRESS_ID_GV),
        "fromDate": datetime.today().strftime('%Y-%m-%d'),
        "size": 5
    }}

    slot.session.execute.assert_called_with(constants.SLOT_QUERY, variables)


def test_get_available_slots_no_filter(slot_values, slot):
    slot.session.execute = mock.MagicMock(return_value=SLOTS_JSON)
    available_slots = slot.get_available_slots()
    assert AVAILABLE_SLOT_DICT == available_slots


def test_get_available_slots_with_filter(slot_values, slot):
    slot.session.execute = mock.MagicMock(return_value=SLOTS_JSON)
    slot_filter = {'sat': (time(7, 0, 0),),
                   'sun': (time(18, 0, 0), time(20, 0, 0))}
    available_slots = slot.get_available_slots(slot_filter)
    assert AVAILABLE_SLOT_DICT_FILTERED == available_slots


def test_book_slot_ok(slot_values, slot):
    slot.session.execute = mock.MagicMock(return_value=BOOK_SLOT_JSON_OK)
    book_slot = slot.book_slot(branch_id=BRANCH_ID, postcode=POSTCODE, address_id=DEFAULT_ADDRESS_ID_GV, slot_type=SLOT_TYPE,
                               start_date_time=datetime.strptime('2020-12-19 07:00:00', '%Y-%m-%d %H:%M:%S'),
                               end_date_time=datetime.strptime('2020-12-19 08:00:00', '%Y-%m-%d %H:%M:%S'))
    assert book_slot

    # check a call is done with the right variables
    variables = {"bookSlotInput": {
        "branchId": str(BRANCH_ID),
        "slotType": SLOT_TYPE,
        "customerOrderId": str(CUSTOMER_ORDER_ID_GV),
        "customerId": str(CUSTOMER_ID_GV),
        "postcode": POSTCODE,
        "addressId": str(DEFAULT_ADDRESS_ID_GV),
        "startDateTime": "2020-12-19T07:00:00Z",
        "endDateTime": "2020-12-19T08:00:00Z"}
    }

    slot.session.execute.assert_called_with(constants.BOOK_SLOT_QUERY, variables)


def test_book_slot_failure(slot_values, slot):
    slot.session.execute = mock.MagicMock(return_value=BOOK_SLOT_JSON_FAIL)
    with pytest.raises(ValueError):
        book_slot = slot.book_slot(branch_id=BRANCH_ID, postcode=POSTCODE, address_id=DEFAULT_ADDRESS_ID_GV, slot_type=SLOT_TYPE,
                                   start_date_time=datetime.strptime('2020-12-19 07:00:00', '%Y-%m-%d %H:%M:%S'),
                                   end_date_time=datetime.strptime('2020-12-19 08:00:00', '%Y-%m-%d %H:%M:%S'))

    # check a call is done with the right variables
    variables = {"bookSlotInput": {
        "branchId": str(BRANCH_ID),
        "slotType": SLOT_TYPE,
        "customerOrderId": str(CUSTOMER_ORDER_ID_GV),
        "customerId": str(CUSTOMER_ID_GV),
        "postcode": POSTCODE,
        "addressId": str(DEFAULT_ADDRESS_ID_GV),
        "startDateTime": "2020-12-19T07:00:00Z",
        "endDateTime": "2020-12-19T08:00:00Z"}
    }

    slot.session.execute.assert_called_with(constants.BOOK_SLOT_QUERY, variables)


def test_get_current_slot_ok(slot_values, slot):
    slot.session.execute = mock.MagicMock(return_value=CURRENT_SLOT_JSON_OK)
    current_slot = slot.get_current_slot()
    assert current_slot == CURRENT_SLOT_OK

    # check a call is done with the right variables
    variables = {"currentSlotInput": {
        "customerOrderId": str(CUSTOMER_ORDER_ID_GV),
        "customerId": str(CUSTOMER_ID_GV)}
    }

    slot.session.execute.assert_called_with(constants.CURRENT_SLOT_QUERY, variables)


def test_get_current_slot_fail(slot_values, slot):
    slot.session.execute = mock.MagicMock(return_value=CURRENT_SLOT_JSON_FAIL)
    current_slot = slot.get_current_slot()
    assert current_slot == CURRENT_SLOT_FAIL

    # check a call is done with the right variables
    variables = {"currentSlotInput": {
        "customerOrderId": str(CUSTOMER_ORDER_ID_GV),
        "customerId": str(CUSTOMER_ID_GV)}
    }

    slot.session.execute.assert_called_with(constants.CURRENT_SLOT_QUERY, variables)
