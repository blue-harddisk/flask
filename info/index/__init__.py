"""
创建蓝图对象,并初始化
"""
from flask import Blueprint

index_blue = Blueprint("index", __name__)

from . import views