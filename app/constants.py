# constants for the utils
from enum import IntEnum


WEEKDAYS = IntEnum('Weekdays', 'mon tue wed thu fri sat sun', start=0)

CHAIN_INTERVAL_HRS = 1

# Fernet.generate_key()
APP_BASE64_KEY = b'MXueuoA52O4a8DL8GjTNMDmtny8Wdc_rc3S_7bHSA6Y='
