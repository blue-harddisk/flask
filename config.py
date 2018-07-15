"""
配置文件
"""
import logging
import redis

class Config(object):

    # 数据库的配置信息
    SQLALCHEMY_DATABASE_URI = "mysql://root:Mysql@127.0.0.1:3306/information14"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis配置信息
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # session
    SECRET_KEY = "EjpNVSNQTyGi1VvWECj9TvC/+kq3oujee2kTfQUs8yCM6xX9Yjq52v54g+HVoknA"

    SESSION_TYPE = "redis"  # 指定 session 保存到 redis 中
    SESSION_USE_SIGNER = True  # 让 cookie 中的 session_id 被加密签名处理
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # 使用 redis 的实例
    PERMANENT_SESSION_LIFETIME = 7200  # session 的有效期，单位是秒

    # 默认日志等级
    LOG_LEVEL = logging.DEBUG


class DevelopmentConfig(Config):
    # 测试阶段,需要开启调试模式

    DEBUG = True


class ProductionConfig(Config):
    # 项目正式上线的时候,需要关闭调试模式

    DEBUG = True
    LOG_LEVEL = logging.ERROR

config_map = {
    "develop" : DevelopmentConfig,
    "production" : ProductionConfig
}