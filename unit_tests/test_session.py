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
LAST_ORDER_ID = 1001283128

ORDER_LIST = {
    "content": [{
        "customerOrderId": "1001283128",
        "status": "COMPLETED",
        "bagless": "true",
        "substitutionsAllowed": "false",
        "paperStatement": "false",
        "alerts": [],
        "alcoholPresent": "false",
        "contactNumber": "07588013493",
        "created": "2020-09-27T10:37:50.046Z",
        "lastUpdated": "2020-09-27T13:30:59.921Z",
        "totals": {
            "estimated": {},
            "actual": {
                "pickedPrice": {
                    "amount": 134.0,
                    "currencyCode": "GBP"
                },
                "carrierBagCharge": {
                    "amount": 0.0,
                    "currencyCode": "GBP"
                },
                "deliveryCharge": {
                    "amount": 0.0,
                    "currencyCode": "GBP"
                },
                "membershipSavings": {
                    "amount": 0.0,
                    "currencyCode": "GBP"
                },
                "paid": {
                    "amount": 132.6,
                    "currencyCode": "GBP"
                },
                "offerSavings": {
                    "amount": 1.4,
                    "currencyCode": "GBP"
                },
                "savings": {
                    "amount": 1.4,
                    "currencyCode": "GBP"
                },
                "partnerDiscountSavings": {
                    "amount": 0.0,
                    "currencyCode": "GBP"
                }
            }
        },
        "orderLines": [{
            "lineNumber": "883134",
            "adjustments": [],
            "salePrice": {
                "amount": 1.1,
                "currencyCode": "GBP"
            },
            "price": {
                "amount": 2.2,
                "currencyCode": "GBP"
            },
            "quantity": {
                "amount": 2.00,
                "uom": "C62"
            },
            "substitutionAllowed": "false",
            "supplierOrderRequired": "false",
            "sequenceNumber": 28,
            "orderLineStatus": "IN_STOCK",
            "orderLineType": "GROCERY"
        }, {
            "lineNumber": "859955",
            "adjustments": [],
            "salePrice": {
                "amount": 2.6,
                "currencyCode": "GBP"
            },
            "price": {
                "amount": 2.6,
                "currencyCode": "GBP"
            },
            "quantity": {
                "amount": 1.00,
                "uom": "C62"
            },
            "substitutionAllowed": "false",
            "supplierOrderRequired": "false",
            "sequenceNumber": 27,
            "orderLineStatus": "IN_STOCK",
            "orderLineType": "GROCERY"
        }]
    },
    {
        "customerOrderId": "1001283126",
        "status": "COMPLETED",
        "bagless": "true",
        "substitutionsAllowed": "false",
        "paperStatement": "false",
        "alerts": [],
        "alcoholPresent": "false",
        "contactNumber": "07588013493",
        "created": "2020-09-27T10:37:50.046Z",
        "lastUpdated": "2020-09-27T13:30:59.921Z",
        "totals": {
            "estimated": {},
            "actual": {
                "pickedPrice": {
                    "amount": 134.0,
                    "currencyCode": "GBP"
                },
                "carrierBagCharge": {
                    "amount": 0.0,
                    "currencyCode": "GBP"
                },
                "deliveryCharge": {
                    "amount": 0.0,
                    "currencyCode": "GBP"
                },
                "membershipSavings": {
                    "amount": 0.0,
                    "currencyCode": "GBP"
                },
                "paid": {
                    "amount": 132.6,
                    "currencyCode": "GBP"
                },
                "offerSavings": {
                    "amount": 1.4,
                    "currencyCode": "GBP"
                },
                "savings": {
                    "amount": 1.4,
                    "currencyCode": "GBP"
                },
                "partnerDiscountSavings": {
                    "amount": 0.0,
                    "currencyCode": "GBP"
                }
            }
        },
        "orderLines": [{
            "lineNumber": "883135",
            "adjustments": [],
            "salePrice": {
                "amount": 1.1,
                "currencyCode": "GBP"
            },
            "price": {
                "amount": 2.2,
                "currencyCode": "GBP"
            },
            "quantity": {
                "amount": 2.00,
                "uom": "C62"
            },
            "substitutionAllowed": "false",
            "supplierOrderRequired": "false",
            "sequenceNumber": 28,
            "orderLineStatus": "IN_STOCK",
            "orderLineType": "GROCERY"
        }, {
            "lineNumber": "859955",
            "adjustments": [],
            "salePrice": {
                "amount": 2.6,
                "currencyCode": "GBP"
            },
            "price": {
                "amount": 2.6,
                "currencyCode": "GBP"
            },
            "quantity": {
                "amount": 1.00,
                "uom": "C62"
            },
            "substitutionAllowed": "false",
            "supplierOrderRequired": "false",
            "sequenceNumber": 27,
            "orderLineStatus": "IN_STOCK",
            "orderLineType": "GROCERY"
        }]
    }]
}

PRODUCT_LIST = {
    "products": [{
        "lineNumber": "883134",
        "id": "796466-143216-143217",
        "name": "Essential Unsmoked British Bacon 10 Rashers",
        "reviews": {
            "averageRating": 4.2629,
            "total": 369
        },
        "pricing": {
            "displayPrice": "£2.25",
            "displayPriceEstimated": 'false',
            "displayPriceQualifier": "(£7.50/kg)",
            "promotions": [],
            "displayUOMPrice": "(£7.50 per kg)"
        },
        "leadTime": 0,
        "categories": [{
            "id": "10051",
            "name": "Groceries"
        }, {
            "id": "301134",
            "name": "Fresh & Chilled"
        }, {
            "id": "301138",
            "name": "Fresh Meat"
        }, {
            "id": "301208",
            "name": "Pork"
        }, {
            "id": "301523",
            "name": "Bacon & Gammon"
        }, {
            "id": "301884",
            "name": "Bacon"
        }],
        "weights": {
            "uoms": ["C62"],
            "sizeDescription": "300g",
            "defaultQuantity": {
                "amount": 1,
                "uom": "C62"
            }
        },
        "brand": "Waitrose Ltd",
        "summary": "British unsmoked back bacon with added water",
        "images": {
            "small": "https://ecom-su-static-prod.wtrecom.com/images/products/9/LN_796466_BP_9.jpg",
            "medium": "https://ecom-su-static-prod.wtrecom.com/images/products/3/LN_796466_BP_3.jpg",
            "large": "https://ecom-su-static-prod.wtrecom.com/images/products/11/LN_796466_BP_11.jpg",
            "extraLarge": "https://ecom-su-static-prod.wtrecom.com/images/products/4/LN_796466_BP_4.jpg"
        },
        "productType": "G",
        "maxPersonalisedMessageLength": 0,
        "restriction": {},
        "barcode": "05000169170755.",
        "supplierOrder": 'false',
        "productShelfLife": 16,
        "availableDays": "NYYYYYY",
        "substitutionsProhibited": 'false',
        "containsAlcohol": 'false',
        "conflicts": []
    }, {
        "lineNumber": "883135",
        "id": "867143-373749-373750",
        "name": "Waitrose Duchy British Free Range Eggs",
        "reviews": {
            "averageRating": 4.3594,
            "total": 64
        },
        "pricing": {
            "displayPrice": "£4.50",
            "displayPriceEstimated": 'false',
            "displayPriceQualifier": "(37.5p each)",
            "promotions": [],
            "displayUOMPrice": "(37.5p each)"
        },
        "leadTime": 0,
        "categories": [{
            "id": "10051",
            "name": "Groceries"
        }, {
            "id": "301134",
            "name": "Fresh & Chilled"
        }, {
            "id": "301141",
            "name": "Milk, Butter & Eggs"
        }, {
            "id": "301245",
            "name": "Free Range Eggs"
        }, {
            "id": "301646",
            "name": "Mixed Weight Eggs"
        }],
        "weights": {
            "uoms": ["C62"],
            "sizeDescription": "12s",
            "defaultQuantity": {
                "amount": 1,
                "uom": "C62"
            }
        },
        "brand": "Waitrose Ltd",
        "summary": "12 British Free Range Eggs",
        "images": {
            "small": "https://ecom-su-static-prod.wtrecom.com/images/products/9/LN_867143_BP_9.jpg",
            "medium": "https://ecom-su-static-prod.wtrecom.com/images/products/3/LN_867143_BP_3.jpg",
            "large": "https://ecom-su-static-prod.wtrecom.com/images/products/11/LN_867143_BP_11.jpg",
            "extraLarge": "https://ecom-su-static-prod.wtrecom.com/images/products/4/LN_867143_BP_4.jpg"
        },
        "productType": "G",
        "maxPersonalisedMessageLength": 0,
        "restriction": {},
        "barcode": "05000169310335.",
        "supplierOrder": 'false',
        "productShelfLife": 18,
        "availableDays": "NYYYYYY",
        "substitutionsProhibited": 'false',
        "containsAlcohol": 'false',
        "conflicts": []
    }]
}

LAST_ORDER = ORDER_LIST['content'][0]


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
    session._get_last_address_id = mock.MagicMock(return_value=LAST_ADDRESS_ID_GV)
    last_address_id = session._get_last_address_id()
    assert LAST_ADDRESS_ID_GV == last_address_id


def test_merge_last_order_to_basket(session):
    session._get_order_list = mock.MagicMock(return_value=ORDER_LIST)
    session._get_last_order = mock.MagicMock(return_value=LAST_ORDER)
    session._get_last_order_id = mock.MagicMock(return_value=LAST_ORDER_ID)
    session._get_products = mock.MagicMock(return_value=LAST_ORDER_ID)

