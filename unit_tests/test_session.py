"""
Tests for Session class
Command line: python -m pytest unit_tests/test_session.py
"""
import pytest
import requests
import mock
from app.session import Session
import session_constants


@pytest.fixture
def session_values():
    return {
        'login': 'clrn@mail.ru',
        'password': '3zbiWViHJuE&{Ns'
    }


@pytest.fixture
def session(session_values):
    return Session(**session_values)


def test_create_session(session_values, session):
    for attr_name in session_values:
        assert getattr(session, attr_name) == session_values.get(attr_name)


def test_create_invalid_login(session_values):
    session_values['login'] = 'dfsdfsfs@gmail.com'
    with pytest.raises(requests.exceptions.HTTPError):
        Session(**session_values)


def test_create_invalid_password(session_values):
    session_values['password'] = 'test'
    with pytest.raises(requests.exceptions.HTTPError):
        Session(**session_values)


def test_get_last_address_id(session):
    session._get_last_address_id = mock.MagicMock(return_value=session_constants.DEFAULT_ADDRESS_ID_GV)
    last_address_id = session._get_last_address_id()
    assert session_constants.DEFAULT_ADDRESS_ID_GV == last_address_id


@mock.patch("requests.get",
            mock.MagicMock(return_value=mock.MagicMock(json=mock.MagicMock(return_value=session_constants.PRODUCT_LIST))))
@mock.patch("requests.patch",
            mock.MagicMock(return_value=mock.MagicMock(json=mock.MagicMock(return_value=session_constants.TROLLEY_ITEMS_DICT_OK))))
def test_merge_last_order_to_trolley_ok(session):
    session.get_order_dict = mock.MagicMock(return_value=session_constants.ORDER_DICT)
    session.merge_last_order_to_trolley()


@mock.patch("requests.get",
            mock.MagicMock(return_value=mock.MagicMock(json=mock.MagicMock(return_value=session_constants.PRODUCT_LIST))))
@mock.patch("requests.patch",
            mock.MagicMock(return_value=mock.MagicMock(json=mock.MagicMock(return_value=session_constants.TROLLEY_ITEMS_DICT_FAIL))))
def test_merge_last_order_to_trolley_fail(session):
    session.get_order_dict = mock.MagicMock(return_value=session_constants.ORDER_DICT)
    with pytest.raises(ValueError):
        session.merge_last_order_to_trolley()


def test_get_card_id_ok(session):
    session.get_payment_card_list = mock.MagicMock(return_value=session_constants.PAYMENT_CARD_LIST_OK)
    card_id = session.get_card_id(1234)
    assert card_id == session_constants.PAYMENT_CARD_LIST_OK[0]['id']


def test_get_card_id_fail(session):
    session.get_payment_card_list = mock.MagicMock(return_value=session_constants.PAYMENT_CARD_LIST_FAIL)
    with pytest.raises(ValueError):
        card_id = session.get_card_id(1234)


@mock.patch("requests.put",
            mock.MagicMock(return_value=mock.MagicMock(json=mock.MagicMock(return_value=session_constants.TROLLEY_CHECKOUT_OK))))
def test_checkout_trolley_ok(session):
    session.get_payment_card_list = mock.MagicMock(return_value=session_constants.PAYMENT_CARD_LIST_OK)
    card_id = session.get_card_id(1234)
    res = session.checkout_trolley(card_id, 123)
    assert res == 'OK'


@mock.patch("requests.put",
            mock.MagicMock(return_value=mock.MagicMock(json=mock.MagicMock(return_value=session_constants.TROLLEY_CHECKOUT_FAIL))))
def test_checkout_trolley_fail(session):
    session.get_payment_card_list = mock.MagicMock(return_value=session_constants.PAYMENT_CARD_LIST_OK)
    card_id = session.get_card_id(1234)
    res = session.checkout_trolley(card_id, 123)
    assert res == 'FAIL'
