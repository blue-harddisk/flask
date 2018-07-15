import random
import re
from datetime import datetime

from flask import request, make_response, jsonify, session

from info.lib.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from . import passport_blue
from info import redis_store, db
from info import constants
from info.utils.response_code import RET


# 图片验证码
@passport_blue.route("/image_code")
def get_image_code():
    code_id = request.args.get("code_id")
    name, text, image = captcha.generate_captcha()
    redis_store.set("image_code_" + code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    resp = make_response(image)
    resp.headers['Content-Type'] = 'image/jpg'
    return resp


# 短信验证码
@passport_blue.route("/sms_code", methods=["POST"])
def sms_code():
    mobile = request.json.get("mobile")
    image_code = request.json.get("image_code")
    image_code_id = request.json.get("image_code_id")

    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="请输入参数")

    if not re.match("1[356789]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="请输入手机号码")

    real_image_code = redis_store.get("image_code_" + image_code_id)
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码已过期")

    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.PARAMERR, errmsg="请输入正确的验证码")

    result = random.randint(0, 999999)
    sms_code = "%06d" % result
    print("短信验证码　= " + sms_code)
    redis_store.set("sms_code_" + mobile, sms_code, constants.SMS_CODE_REDIS_EXPIRES)

    statusCode = CCP().send_template_sms(mobile, [sms_code, 5], 1)
    if statusCode != 0:
        return jsonify(errno=RET.THIRDERR, errmsg="短信发送失败")

    return jsonify(errno=RET.OK, errmsg="发送短信成功")


# 注册账号
@passport_blue.route("/register", methods=["POST"])
def register():
    mobile = request.json.get("mobile")
    smscode = request.json.get("smscode")
    password = request.json.get("password")

    if not all([mobile, smscode, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="请输入参数")

    real_sms_code = redis_store.get("sms_code_" + mobile)
    if not real_sms_code:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码已过期")

    if real_sms_code != smscode:
        return jsonify(errno=RET.PARAMERR, errmsg="请输入正确的短信验证码")

    user = User()
    user.nick_name = mobile
    user.password = password
    user.mobile = mobile

    db.session.add(user)
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="注册成功")


# 登录账号
@passport_blue.route("/login", methods=["POST"])
def login():
    mobile = request.json.get("mobile")
    password = request.json.get("password")

    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="请输入参数")

    user = User.query.filter_by(mobile=mobile).first()
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="请注册")

    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR, errmsg="密码错误")

    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile

    user.last_login = datetime.now()
    db.session.commit()

    return jsonify(errno=RET.OK, errmsg="登录成功")


# 登出
@passport_blue.route("/logout", methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('nick_name', None)
    session.pop('mobile', None)
    session.pop("is_admin", None)

    return jsonify(errno=RET.OK, errmsg="退出成功")
