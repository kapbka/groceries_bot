import traceback
from datetime import datetime


class AppException(Exception):
    """A custom exception used for groceries bot"""
    internal_err_msg = 'Unhandled exception occurred'
    user_err_msg = 'Unexpected error occurred on our side, please try later or contact support @kapbka'

    def __init__(self, *args, user_err_msg=None):
        if args:
            self.internal_err_msg = args[0]
            super().__init__(args)
        else:
            super().__init__(self.internal_err_msg)

        if user_err_msg:
            self.user_err_msg = user_err_msg

    @property
    def traceback(self):
        return ''.join(traceback.TracebackException.from_exception(self).format())

    def log_exception(self):
        exception = {
            'type': type(self).__name__,
            'internal _msg': self.args[0] if self.args else self.internal_err_msg,
            'args': self.args[1:],
            'user_msg': self.user_err_msg,
            'traceback': self.traceback
        }
        return f'EXCEPTION: {datetime.utcnow().isoformat()}: {exception}'


class LoginFailException(AppException):
    internal_err_msg = 'Failed to login into profile'
    user_err_msg = 'Failed to login into your profile, please check if your login/password is correct'


class ShopProviderUnavailableException(AppException):
    internal_err_msg = 'Internal error on shop provider side'
    user_err_msg = 'Internal error on shop provider side, please try later'


class ConnectionException(AppException):
    internal_err_msg = 'Connection error'
    user_err_msg = 'Connection problem, please try later'


class TimeoutException(AppException):
    internal_err_msg = 'Connection timeout'
    user_err_msg = 'Connection timeout occured, please /start again'


class NoOrdersException(AppException):
    internal_err_msg = 'No orders for this profile'
    user_err_msg = 'No completed orders found in your profile to fill in your basket basket. ' \
                   'Please fill in the basket manually via mobile application or website'


class NoOrdersSlotBookedException(AppException):
    internal_err_msg = 'No orders for the profile'
    user_err_msg = 'No completed orders found to fill in your basket, but the slot has been booked. ' \
                   'Please fill in the basket manually via mobile application/website'


class NoAddressException(AppException):
    internal_err_msg = 'No address linked to the profile'
    user_err_msg = 'No address linked to your profile. ' \
                   'Please link the necessary address to your profile manually via mobile application/website'


class NoPaymentCardException(AppException):
    internal_err_msg = 'No linked payment card to the profile'
    user_err_msg = 'No cards added to your profile. Please, add a payment card via mobile application/website'


class TrolleyException(AppException):
    internal_err_msg = 'Error during query the trolley'
    user_err_msg = 'There are some problems with trolley loading. Please try later'


class PaymentException(AppException):
    internal_err_msg = 'Error during payment'
    user_err_msg = 'There are some problems with payment. Please try later'


class PlaceOrderException(AppException):
    internal_err_msg = 'Error during placing order'
    user_err_msg = 'There are some problems with placing your order. Please try later or contact support @kapbka'


class OrderListException(AppException):
    internal_err_msg = 'Error during getting order list'
    user_err_msg = 'There are some problems with getting order list. Please try later or contact support @kapbka'


# for some reasons Waitrose doesn't have this check
class OrderExistsException(AppException):
    internal_err_msg = 'Order already exists'
    user_err_msg = 'Order already exists'
