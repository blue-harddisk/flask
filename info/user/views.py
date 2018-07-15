from info import db, constants
from info.models import Category, News, User
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import profile_blue
from info.utils.common import user_login_data
from flask import render_template, g, request, jsonify, redirect


# 作者信息发布的新闻
@profile_blue.route('/other_news_list')
def other_news_list():
    page = request.args.get("p", 1)
    user_id = request.args.get("user_id")
    try:
        page = int(page)
    except Exception as e:
        page = 1

    user = User.query.get(user_id)
    paginate = News.query.filter(News.user_id == user.id).paginate(page, constants.OTHER_NEWS_PAGE_MAX_COUNT, False)
    # 获取当前页数据
    news_li = paginate.items
    # 获取当前页
    current_page = paginate.page
    # 获取总页数
    total_page = paginate.pages
    news_list = []
    for item in news_li:
        news_list.append(item.to_review_dict())

    data = {
        "news_list":news_list,
        "total_page":total_page,
        "current_page":current_page
    }

    return jsonify(errno=RET.OK, errmsg="OK", data=data)


# 新闻作者信息
@profile_blue.route('/other_info')
@user_login_data
def other_info():
    user = g.user

    # 获取其他用户id
    user_id = request.args.get("id")
    other = User.query.get(user_id)
    is_followed = False
    if other and user:

        # 当前新闻必须要有作者,并且当前新闻的作者,在我关注人的列表当中,说明,我是当前新闻作者的粉丝
        if other in user.followed:
            is_followed = True
    data = {
        "user_info": user.to_dict() if user else None,
        "other_info": other.to_dict(),
        "is_followed": is_followed
    }

    return render_template('news/other.html', data =data)


# 关注列表
@profile_blue.route('/user_follow')
@user_login_data
def user_follow():
    user = g.user
    page = request.args.get("p", 1)
    try:
        page = int(page)
    except Exception as e:
        page = 1

    paginate = user.followed.paginate(page, constants.USER_FOLLOWED_MAX_COUNT, False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    user_list = []
    for item in items:
        user_list.append(item.to_dict())

    date = {
        "users": user_list,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("news/user_follow.html", data=date)


# 新闻列表
@profile_blue.route("/news_list")
@user_login_data
def news_list():
    user = g.user
    page = request.args.get("p", 1)
    try:
        page = int(page)
    except Exception as e:
        page = 1

    """
        获取到用户发布的新闻列表
    """
    paginate = News.query.filter(News.user_id == user.id).paginate(page, 10, False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    news_list = []
    for news in items:
        news_list.append(news.to_review_dict())

    data = {
        "news_list": news_list,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("news/user_news_list.html", data=data)


# 发布新闻
@profile_blue.route("/news_release", methods=["GET", "POST"])
@user_login_data
def news_release():
    user = g.user
    if request.method == "GET":
        # 查询新闻分类
        categorys = Category.query.all()
        category_list = []
        for category in categorys:
            category_list.append(category.to_dict())
        # 删除第0个元素
        category_list.pop(0)

        data = {
            "categories": category_list
        }
        return render_template("news/user_news_release.html", data=data)

        # 1.获取要提交的数据
    title = request.form.get("title")
    source = "个人发布"
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image").read()
    category_id = request.form.get("category_id")
    # 1.1 判断数据是否有值
    if not all([title, source, digest, content, index_image, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
    # 1.2数据写入数据库
    key = storage(index_image)
    news = News()
    news.title = title
    news.source = source
    news.digest = digest
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
    news.category_id = category_id
    news.user_id = user.id
    news.status = 1
    db.session.add(news)
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="提交成功,等待审核..")


# 个人收藏
@profile_blue.route("/collection")
@user_login_data
def collection():
    user = g.user
    page = request.args.get("p", 1)

    try:
        page = int(page)
    except Exception as e:
        page = 1
    """
        我的收藏是展示当前登陆用户收藏的新闻
        1 判断当前登陆用户
    """
    paginate = user.collection_news.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    collection_list = []
    for collection in items:
        collection_list.append(collection.to_review_dict())

    data = {
        "collections": collection_list,
        "current_page": current_page,
        "total_page": total_page
    }
    return render_template("news/user_collection.html", data=data)


# 修改密码
@profile_blue.route("/pass_info", methods=["GET", "POST"])
@user_login_data
def pass_info():
    user = g.user
    if request.method == "GET":
        # 不需要返回用户数据
        return render_template("news/user_pass_info.html")

    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    if user.check_password(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="密码错误")

    user.password = new_password
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="密码修改成功")


# 更改头像
@profile_blue.route("/pic_info", methods=["GET", "POST"])
@user_login_data
def pic_info():
    user = g.user
    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else None
        }
        return render_template("news/user_pic_info.html", data=data)

    # 获取到用户上传的图片
    avatar = request.files.get("avatar").read()
    # 传图片, 获取返回的key
    key = storage(avatar)
    # 更新用户的头像，存储到数据库
    user.avatar_url = key
    db.session.commit()

    data = {
        "avatar_url": constants.QINIU_DOMIN_PREFIX + key
    }
    return jsonify(errno=RET.OK, errmsg="上传成功", data=data)


# 基本资料
@profile_blue.route("/base_info", methods=["GET", "POST"])
@user_login_data
def base_info():
    user = g.user
    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else None
        }
        return render_template("news/user_base_info.html", data=data)

    nick_name = request.json.get("nick_name")
    # 获取到用户修改的签名
    signature = request.json.get("signature")
    # 获取到用户的性别
    gender = request.json.get("gender")
    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender
    db.session.commit()
    return jsonify(errno=RET.OK, errmgs="修改成功")


# 个人中心页面
@profile_blue.route("/info")
@user_login_data
def get_user_info():
    user = g.user
    if not user:
        return redirect("/")
    data = {
        "user_info": user.to_dict() if user else None
    }
    return render_template("news/user.html", data=data)
