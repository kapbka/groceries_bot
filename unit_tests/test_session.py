"""
Tests for Session class
Command line: python -m pytest unit_tests/test_session.py
"""
import pytest
import requests
import mock

from app import utils
from app import constants


LAST_ADDRESS_ID_GV = 40407464


@pytest.fixture
def session_values():
    return {
        'login': 'clrn@mail.ru',
        'password': '3zbiWViHJuE&{Ns'
    }


@pytest.fixture
def session(session_values):
    return utils.Session(**session_values)


def test_create_session(session_values, session):
    for attr_name in session_values:
        assert getattr(session, attr_name) == session_values.get(attr_name)


def test_create_invalid_login(session_values):
    session_values['login'] = 'dfsdfsfs@gmail.com'
    with pytest.raises(requests.exceptions.HTTPError):
        utils.Session(**session_values)


def test_create_invalid_password(session_values):
    session_values['password'] = 'test'
    with pytest.raises(requests.exceptions.HTTPError):
        utils.Session(**session_values)


def test_get_last_address_id(session):
    session.get_last_address_id = mock.MagicMock(return_value=LAST_ADDRESS_ID_GV)
    last_address_id = session.get_last_address_id()
    assert LAST_ADDRESS_ID_GV == last_address_id
