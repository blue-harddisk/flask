"""
蓝图对象管理视图函数
"""
from info.models import User, News, Category
from info.utils.response_code import RET
from . import index_blue
from flask import render_template, current_app, session, request, jsonify, g
from info.utils.common import user_login_data


@index_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')


@index_blue.route('/')
@user_login_data
def index():
    user = g.user

    # 首页右边的热门新闻排行
    news_model = News.query.order_by(News.clicks.desc()).limit(10)
    news_list = []
    for new_dict in news_model:
        news_list.append(new_dict.to_dict())

    # 最上面的分类新闻数据,获取所有的新闻
    categorys = Category.query.all()
    categorys_list = []
    for category in categorys:
        categorys_list.append(category.to_dict())

    data = {
        "user_info": user.to_dict() if user else None,
        "click_news_list": news_list,
        "categories": categorys_list
    }
    return render_template("news/index.html", data=data)


@index_blue.route("/news_list")
def news_list():
    cid = request.args.get("cid", 1)
    page = request.args.get("page", 1)
    per_page = request.args.get("per_page", 10)

    # 校验前端传过来的数据
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        cid = 1
        page = 1
        per_page = 10

    filter = [News.status == 0]
    if cid != 1:
        filter.append(News.category_id == cid)
    paginate = News.query.filter(*filter).order_by(News.create_time.desc()).paginate(
        page, per_page, False)

    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    news_list = []
    for news in items:
        news_list.append(news.to_dict())
    data = {
        "news_dict_li": news_list,
        "current_page": current_page,
        "total_page": total_page
    }

    return jsonify(errno = RET.OK,errmsg = "ok",data = data)
