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

