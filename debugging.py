from datetime import datetime
from icecream import ic


def now():
    return f'[{datetime.now()}] '

ic.configureOutput(prefix=now)
ic.disable()