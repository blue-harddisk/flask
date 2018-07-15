import time
from info import constants, db
from datetime import datetime, timedelta
from info.models import User, News, Category
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import admin_blue
from info.utils.common import user_login_data
from flask import render_template, request, session, redirect, url_for, g, jsonify


# 对新闻分类进行增加或者修改
@admin_blue.route('/add_category', methods=["POST"])
def add_category():
    # 获取到分类id
    cid = request.json.get("id")
    # 新闻分类的名字
    name = request.json.get("name")
    if cid:
        # 修改分类id的名称
        category = Category.query.get(cid)
        category.name = name
    else:
        # 增加分类
        category = Category()
        category.name = name
        db.session.add(category)

    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="保存数据成功")


# 新闻分类
@admin_blue.route("/news_type")
def news_type():
    categorys = Category.query.all()
    category_list = []
    for category in categorys:
        category_list.append(category.to_dict())

    category_list.pop(0)
    data = {
        "categories": category_list
    }
    return render_template("admin/news_type.html", data=data)


# 对新闻进行编辑
@admin_blue.route("/news_edit_detail", methods=["GET", "POST"])
def news_edit_detail():
    if request.method == "GET":
        news_id = request.args.get("news_id")
        news = News.query.get(news_id)
        categorys = Category.query.all()

        category_list = []
        for category in categorys:
            category_list.append(category.to_dict())

        category_list.pop(0)

        data = {
            "categories": category_list,
            "news": news.to_dict()
        }
        return render_template("admin/news_edit_detail.html", data=data)

    news_id = request.form.get("news_id")
    title = request.form.get("title")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")
    # 1.1 判断数据是否有值
    if not all([title, digest, content, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    news = News.query.get(news_id)
    news.title = title
    news.category_id = category_id
    news.digest = digest
    news.content = content
    # 上传图片逻辑,可传也可不传
    if index_image:
        index_image = index_image.read()
        key = storage(index_image)
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + key

    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="ok")


# 所有新闻列表
@admin_blue.route("/news_edit")
def news_edit():
    page = request.args.get("p", 1)

    try:
        page = int(page)
    except Exception as e:
        page = 1
    """
        新闻编辑:
        1 查询所有的新闻,按照新闻的创建时间进行排序,order_by(News.create_time.desc())
        2 分页查询
    """
    paginate = News.query.order_by(News.create_time.desc()).paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    news_list = []
    for item in items:
        news_list.append(item.to_review_dict())

    data = {
        "news_list": news_list,
        "current_page": current_page,
        "total_page": total_page
    }
    return render_template("admin/news_edit.html", data=data)


# 新闻审核详情
@admin_blue.route('/news_review_detail', methods=["GET", "POST"])
def news_review_detail():
    news_id = request.args.get("news_id")

    if request.method == "GET":
        news = News.query.get(news_id)
        data = {
            "news": news.to_dict()
        }
        return render_template("admin/news_review_detail.html", data=data)

    # 1.获取参数
    action = request.json.get("action")
    news_id = request.json.get("news_id")

    # 2.查询新闻
    news = News.query.get(news_id)

    # 3.通过还是不通过
    if action == "accept":
        news.status = 0
    else:
        # 拒绝通过，需要获取原因
        reason = request.json.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="请说明没有通过的原因")
        news.reason = reason
        news.status = -1

    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="操作成功")


# 新闻审核
@admin_blue.route("/news_review")
def news_review():
    page = request.args.get("p", 1)
    keywords = request.args.get("keywords", "")

    try:
        page = int(page)
    except Exception as e:
        page = 1

    filters = [News.status != 0]
    if keywords:
        # contains:包含-->新闻包含关键词
        filters.append(News.title.contains(keywords))
    paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,
                                                                                      constants.ADMIN_NEWS_PAGE_MAX_COUNT,
                                                                                      False)

    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    news_list = []
    for item in items:
        news_list.append(item.to_review_dict())

    data = {
        "news_list": news_list,
        "current_page": current_page,
        "total_page": total_page
    }
    return render_template("admin/news_review.html", data=data)


# 所有用户列表
@admin_blue.route("/user_list")
def user_list():
    page = request.args.get("p", 1)
    try:
        page = int(page)
    except Exception as e:
        page = 1

    # 查询所有用户,去除小编管理员,按最后登录事件降序
    paginate = User.query.filter(User.is_admin == False).order_by(User.last_login.desc()).paginate(page,
                                                                                                   constants.ADMIN_USER_PAGE_MAX_COUNT,
                                                                                                   False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages
    user_list = []
    for user in items:
        user_list.append(user.to_admin_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "users": user_list
    }
    return render_template("admin/user_list.html", data=data)


# 用户统计
@admin_blue.route("/user_count")
def user_count():
    # 总人数
    total_count = 0
    # 每个月新增人数
    mon_count = 0
    # 每天新增人数
    day_count = 0
    # 1.总用户
    # 获取到所有的人数,剔除小编,因为小编是员工,不是用户
    total_count = User.query.filter(User.is_admin == False).count()

    # 2.月新增用户
    # 获取到当前的时间
    t = time.localtime()
    # 2018-07-01
    mon_time = "%d-%02d-01" % (t.tm_year, t.tm_mon)
    # 传进去一个时间,返回一个格式化时间
    mon_time_begin = datetime.strptime(mon_time, "%Y-%m-%d")

    mon_count = User.query.filter(User.is_admin == False, User.create_time > mon_time_begin).count()

    # 3.日新增用户
    # 2018-07-11
    day_time = "%d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday)
    # 2018-07-01 00:00:00
    # 传进去一个时间,返回一个格式化时间
    day_time_begin = datetime.strptime(day_time, "%Y-%m-%d")

    day_count = User.query.filter(User.is_admin == False, User.create_time > day_time_begin).count()

    """
       需求:
       统计,这一个月每天新增用户量,往前面推30天

    """
    # 4.统计表(前30天的每天用户)
    # 2018-07-11
    # today_begin = "%d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday)
    # 2018-07-01 00:00:00
    # 传进去一个时间,返回一个格式化时间
    today_begin_date = datetime.strptime(day_time, "%Y-%m-%d")
    active_count = []
    active_time = []
    for i in range(0, 30):
        # timedelta:时间差,参数为天,正数则往前减,为负则往后加
        begin_date = today_begin_date - timedelta(days=i)
        end_date = today_begin_date - timedelta(days=(i - 1))
        # 30天的总人数
        count = User.query.filter(User.is_admin == False, User.create_time > begin_date,
                                  User.create_time < end_date).count()
        active_count.append(count)
        active_time.append(begin_date.strftime("%Y-%m-%d"))

    active_count.reverse()
    active_time.reverse()

    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_time": active_time,
        "active_count": active_count
    }
    return render_template("admin/user_count.html", data=data)


# 管理员主页
@admin_blue.route("/index")
@user_login_data
def admin_index():
    user = g.user
    return render_template("admin/index.html", user=user.to_dict())


# admin登录,登录过直接重定向index,没登录,请登录
@admin_blue.route("/login", methods=["GET", "POST"])
def login():
    # 已登录
    if request.method == "GET":
        user_id = session.get("user_id", None)
        is_admin = session.get("is_admin", None)
        if user_id and is_admin:
            return redirect(url_for("admin.admin_index"))
        return render_template("admin/login.html")
    # 未登录
    username = request.form.get("username")
    password = request.form.get("password")
    # User.is_admin == True:判断当前登陆用户是是否是管理员
    user = User.query.filter(User.mobile == username, User.is_admin == True).first()

    if not user:
        return render_template("admin/login.html", errmsg="没有这个用户")

    if not user.check_password(password):
        return render_template("admin/login.html", errmsg="密码错误")

    # 持久化操作
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    session["is_admin"] = user.is_admin

    return redirect(url_for("admin.admin_index"))
