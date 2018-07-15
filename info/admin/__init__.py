from flask import Blueprint, session, redirect, request

admin_blue = Blueprint("admin", __name__, url_prefix="/admin")

from . import views

@admin_blue.before_request
def check_admin():
    # 判断当前登陆后台的用户是否是管理员
    # None:表示默认值
    is_admin = session.get("is_admin",None)
    # 如果你不是管理员,那么就不让你请求后台管理员的界面
    if not is_admin and not request.url.endswith("/admin/login"):
        return redirect("/")