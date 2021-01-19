# constants for Slot class tests


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
                    'slotId': '2020-12-20_14:00_15:00',
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
            'slotId': '2020-12-20_14:00_15:00',
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
    '2020-12-20_14:00_15:00': {
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
