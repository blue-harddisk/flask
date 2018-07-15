import functools

from flask import session, g

from info.models import User


def do_index_class(index):
    if index == 0:
        return "first"
    elif index == 1:
        return "second"
    elif index == 2:
        return "third"
    else:
        return ""


def user_login_data(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        user = None
        if user_id:
            user = User.query.get(user_id)
        g.user = user
        return f(*args, **kwargs)
    return wrapper