class TastyPieError(Exception):
    pass


class NotFound(TastyPieError):
    pass


class ApiFieldError(TastyPieError):
    pass


class UnsupportedFormat(TastyPieError):
    pass
