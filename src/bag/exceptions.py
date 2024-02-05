class BagIdException(Exception):
    pass


class IncorrectBagIdLengthException(BagIdException):
    pass


class IncorrectGemeenteCodeException(BagIdException):
    pass


class IncorrectObjectTypeException(BagIdException):
    pass
