# constants for telegram

# emoji
ENABLED_EMOJI = '\u2705'
DISABLED_EMOJI = '\u25fb'
BACK_EMOJI = '\u21a9'
# some magic but makes 5 digit emoji work
HELP_EMOJI = '\uD83D\uDCD6'.encode('utf-16', 'surrogatepass').decode('utf-16')


# menu
M_AVAILABLE_SLOTS = 'All available slot days'
M_AUTOBOOKING = 'Autobooking'
M_BOOK_AND_CHECKOUT = 'Book slot and checkout'
M_BOOK = 'Book slot'
M_CHECKOUT = 'Checkout'
M_PASSWORD = 'Password'
M_LOGIN = 'Login'
M_CVV = 'Payment details'
M_SETTINGS = 'Settings'
M_MAIN = 'Main'
M_ENABLE_AUTOBOOKING = 'Enable autobooking'
M_MIN_ORDER_INTERVAL = 'Minimal order interval'
M_DECREASE = '<'
M_INCREASE = '>'
M_ENABLED = 'Enabled'

M_HELP = f'{HELP_EMOJI} Help'

# invitation strings
S_LOGIN = 'Please enter your login'
S_PASSWORD = 'Please enter your password'
S_CVV = 'Please enter the cvv of the card linked to your profile'

S_BACK_TO = 'Back to'

S_ORDER_NUMBER = 'Order number is'
S_BOOKED = 'booked'
S_CHECKED_OUT = 'checked out'

S_NO_MATCHING_SLOT = 'No matching slot found!'
S_SLOT_FOUND = 'Matching slot found'

# errors/exceptions
E_SLOT_EXPIRED = 'The booked slot has expired, please book a new slot.'
E_NO_ACTION = 'At least one action required: booking or checkout!'

# help
H_HELP = f'{HELP_EMOJI}\n\n' \
         'Groceries bot, provides auto or manual bookings/checkouts for popular supermarket chains. \n\n' \
         'Press /start to begin, then choose a supermarket chain where you would like to do shopping.'

H_MAIN = f'{HELP_EMOJI}\n\n' \
         'Autobooking - set up automatic book and checkout for a certain date/time. \n\n' \
         'Book slot and checkout - book slot and checkout manually using bot. \n\n' \
         'Book slot - book slot manually using bot. \n\n' \
         'Checkout - checkout previously booked slot manually using bot. \n\n' \
         'Settings - adjust login/password or payment details to login into your chain profile.'

H_AUTOBOOKING = f'{HELP_EMOJI}\n\n' \
                'Days of the week and time slots - a day of the week and time for delivery. \n\n' \
                'Minimal order interval - minimal interval in days between orders (for example, 7 is once a week). \n\n' \
                'Enabled - a checkbox to enable autobooking functionality. If no days/times are chosen then the first available slot will be booked.\n\n'

H_BOOK_CHECKOUT = f'{HELP_EMOJI}\n\n' \
                  'Choose a day of the week and time to book and check out a delivery slot.'

H_BOOK = f'{HELP_EMOJI}\n\n' \
         'Chose a day of the week and time to book a delivery slot.'

H_CHECKOUT = f'{HELP_EMOJI}\n\n' \
             'Press the booked slot to make a checkout.'

H_SETTINGS = f'{HELP_EMOJI}\n\n' \
             'Login - change/update your chain specific credentials.\n\n' \
             'Payment details - change/update the cvv for the payment card linked to your chain profile.'
