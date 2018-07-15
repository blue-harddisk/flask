"""
创建,初始化app实例对象,
"""
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, g
from flask_session import Session
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_sqlalchemy import SQLAlchemy
from config import Config, DevelopmentConfig, ProductionConfig, config_map
import redis


# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG)  # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
# 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)

db = SQLAlchemy()

redis_store = None # type:redis.StrictRedis
def create_app(config_name):
    app = Flask(__name__)

    # 根据参数选择配置
    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    # 初始化redis,帮助我们存储数据(存验证码,图片验证码,短信验证码)
    global redis_store
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, decode_responses=True)

    # db = SQLAlchemy(app)
    db.init_app(app)

    # 初始化flask_session
    Session(app)

    # CSRF,只会校验['POST', 'PUT', 'PATCH', 'DELETE'],不会校验get请求,手动往cookie里面设置csrf_token,往服务器的表单设置token
    CSRFProtect(app)

    @app.after_request
    def after_request(response):
        csrf_token = generate_csrf()
        response.set_cookie("csrf_token", csrf_token)
        return response

    from info.utils.common import user_login_data
    @app.errorhandler(404)
    @user_login_data
    def error_404_handler(error):
        user = g.user
        data = {
            "user_info": user.to_dict() if user else None
        }
        return render_template("news/404.html", data=data)

    # 自定义过滤器
    from info.utils.common import do_index_class
    app.add_template_filter(do_index_class, "indexClass")

    # 首页注册蓝图
    from info.index import index_blue
    app.register_blueprint(index_blue)

    # 登录注册蓝图
    from info.passport import passport_blue
    app.register_blueprint(passport_blue)

    # 新闻详情注册蓝图
    from info.news import news_blue
    app.register_blueprint(news_blue)

    # 个人中心注册蓝图
    from info.user import profile_blue
    app.register_blueprint(profile_blue)

    # 后台admin注册蓝图
    from info.admin import admin_blue
    app.register_blueprint(admin_blue)



    # 返回app实例对象
    return app

