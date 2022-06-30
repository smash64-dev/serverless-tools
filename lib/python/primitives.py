ORDER = 'little'


def boolean(data: bool):
    return data.to_bytes(1, ORDER)


def string(data: str, null: bool = True):
    return data.rstrip('\0').encode() + (b'\0' if null else b'')


def stringz(data):
    return string(data, True)


def uint(data: int, size: int = 1, order: str = ORDER):
    return data.to_bytes(size, order)
