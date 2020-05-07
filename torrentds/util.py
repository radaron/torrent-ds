from datetime import datetime, timedelta


def check_time(start, **kwargs):
    now = datetime.now()
    if now - start >= timedelta(**kwargs):
        return True
    else:
        return False

def check_between_time(before, after):
    before = datetime.strptime(before, "%H:%M:%S").time()
    after = datetime.strptime(after, "%H:%M:%S").time()
    now = datetime.now().time()
    return before < now < after

