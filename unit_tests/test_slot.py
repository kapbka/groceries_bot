"""
Tests for Slot class
Command line: python -m pytest unit_tests/test_slot.py
"""
import pytest
import mock
import slot_constants

from app.slot import Slot
from app import constants
from datetime import datetime, time




@pytest.fixture
def session():
    return mock.MagicMock(
        token='fake',
        customerOrderId=slot_constants.CUSTOMER_ORDER_ID_GV,
        customerId=slot_constants.CUSTOMER_ID_GV,
        default_address_id=slot_constants.DEFAULT_ADDRESS_ID_GV
    )


@pytest.fixture
def slot_values(session):
    return {
        'session': session,
        'slot_type': slot_constants.SLOT_TYPE
    }


@pytest.fixture
def slot(slot_values):
    return Slot(**slot_values)


def test_get_slot(slot_values, slot):
    for attr_name in slot_values:
        assert getattr(slot, attr_name) == slot_values.get(attr_name)


def test_get_slots(slot_values, slot):
    slot.session.execute = mock.MagicMock(return_value=slot_constants.SLOTS_JSON)
    slots = slot.get_slots(slot_constants.BRANCH_ID, datetime.today())
    assert slots == slot_constants.SLOTS_LIST

    # check a call is done with the right variables
    variables = {"slotDaysInput": {
        "branchId": str(slot_constants.BRANCH_ID),
        "slotType": slot_constants.SLOT_TYPE,
        "customerOrderId": str(slot_constants.CUSTOMER_ORDER_ID_GV),
        "addressId": str(slot_constants.DEFAULT_ADDRESS_ID_GV),
        "fromDate": datetime.today().strftime('%Y-%m-%d'),
        "size": 5
    }}

    slot.session.execute.assert_called_with(constants.SLOT_QUERY, variables)


def test_get_available_slots_no_filter(slot_values, slot):
    slot.session.execute = mock.MagicMock(return_value=slot_constants.SLOTS_JSON)
    available_slots = slot.get_available_slots()
    assert slot_constants.AVAILABLE_SLOT_DICT == available_slots


def test_get_available_slots_with_filter(slot_values, slot):
    slot.session.execute = mock.MagicMock(return_value=slot_constants.SLOTS_JSON)
    slot_filter = {'sat': (time(7, 0, 0),),
                   'sun': (time(18, 0, 0), time(20, 0, 0))}
    available_slots = slot.get_available_slots(slot_filter)
    assert slot_constants.AVAILABLE_SLOT_DICT_FILTERED == available_slots


def test_book_slot_ok(slot_values, slot):
    slot.session.execute = mock.MagicMock(return_value=slot_constants.BOOK_SLOT_JSON_OK)
    book_slot = slot.book_slot(branch_id=slot_constants.BRANCH_ID, postcode=slot_constants.POSTCODE,
                               address_id=slot_constants.DEFAULT_ADDRESS_ID_GV, slot_type=slot_constants.SLOT_TYPE,
                               start_date_time=datetime.strptime('2020-12-19 07:00:00', '%Y-%m-%d %H:%M:%S'),
                               end_date_time=datetime.strptime('2020-12-19 08:00:00', '%Y-%m-%d %H:%M:%S'))
    assert book_slot

    # check a call is done with the right variables
    variables = {"bookSlotInput": {
        "branchId": str(slot_constants.BRANCH_ID),
        "slotType": slot_constants.SLOT_TYPE,
        "customerOrderId": str(slot_constants.CUSTOMER_ORDER_ID_GV),
        "customerId": str(slot_constants.CUSTOMER_ID_GV),
        "postcode": slot_constants.POSTCODE,
        "addressId": str(slot_constants.DEFAULT_ADDRESS_ID_GV),
        "startDateTime": "2020-12-19T07:00:00Z",
        "endDateTime": "2020-12-19T08:00:00Z"}
    }

    slot.session.execute.assert_called_with(constants.BOOK_SLOT_QUERY, variables)


def test_book_slot_failure(slot_values, slot):
    slot.session.execute = mock.MagicMock(return_value=slot_constants.BOOK_SLOT_JSON_FAIL)
    with pytest.raises(ValueError):
        book_slot = slot.book_slot(branch_id=slot_constants.BRANCH_ID, postcode=slot_constants.POSTCODE,
                                   address_id=slot_constants.DEFAULT_ADDRESS_ID_GV, slot_type=slot_constants.SLOT_TYPE,
                                   start_date_time=datetime.strptime('2020-12-19 07:00:00', '%Y-%m-%d %H:%M:%S'),
                                   end_date_time=datetime.strptime('2020-12-19 08:00:00', '%Y-%m-%d %H:%M:%S'))

    # check a call is done with the right variables
    variables = {"bookSlotInput": {
        "branchId": str(slot_constants.BRANCH_ID),
        "slotType": slot_constants.SLOT_TYPE,
        "customerOrderId": str(slot_constants.CUSTOMER_ORDER_ID_GV),
        "customerId": str(slot_constants.CUSTOMER_ID_GV),
        "postcode": slot_constants.POSTCODE,
        "addressId": str(slot_constants.DEFAULT_ADDRESS_ID_GV),
        "startDateTime": "2020-12-19T07:00:00Z",
        "endDateTime": "2020-12-19T08:00:00Z"}
    }

    slot.session.execute.assert_called_with(constants.BOOK_SLOT_QUERY, variables)


def test_get_current_slot_ok(slot_values, slot):
    slot.session.execute = mock.MagicMock(return_value=slot_constants.CURRENT_SLOT_JSON_OK)
    current_slot = slot.get_current_slot()
    assert current_slot == slot_constants.CURRENT_SLOT_OK

    # check a call is done with the right variables
    variables = {"currentSlotInput": {
        "customerOrderId": str(slot_constants.CUSTOMER_ORDER_ID_GV),
        "customerId": str(slot_constants.CUSTOMER_ID_GV)}
    }

    slot.session.execute.assert_called_with(constants.CURRENT_SLOT_QUERY, variables)


def test_get_current_slot_fail(slot_values, slot):
    slot.session.execute = mock.MagicMock(return_value=slot_constants.CURRENT_SLOT_JSON_FAIL)
    current_slot = slot.get_current_slot()
    assert current_slot == slot_constants.CURRENT_SLOT_FAIL

    # check a call is done with the right variables
    variables = {"currentSlotInput": {
        "customerOrderId": str(slot_constants.CUSTOMER_ORDER_ID_GV),
        "customerId": str(slot_constants.CUSTOMER_ID_GV)}
    }

    slot.session.execute.assert_called_with(constants.CURRENT_SLOT_QUERY, variables)
