# -- Exceptions
class DoubleAssignmentException(Exception):
    pass


class NotLiteralNameException(Exception):
    pass


class NotLiteralEvaluable(Exception):
    pass


# -- Sentinels
class EmptyValue:
    pass
