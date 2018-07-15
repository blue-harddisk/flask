from info.models import News, Comment, CommentLike, User
from info.utils.response_code import RET
from . import news_blue
from flask import render_template, g, request, jsonify
from info.utils.common import user_login_data
from info import constants, db


# 关注
@news_blue.route('/followed_user', methods=["POST"])
@user_login_data
def followed_user():
    if not g.user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    user_id = request.json.get("user_id")
    action = request.json.get("action")

    other = User.query.get(user_id)
    if action == "follow":
        # 关注
        if other.followers.filter(User.id == g.user.id).count() > 0:
            return jsonify(errno=RET.DATAEXIST, errmsg="当前已关注")
        other.followers.append(g.user)

    else:
        # 取消关注
        if other.followers.filter(User.id == g.user.id).count() > 0:
            other.followers.remove(g.user)

    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="操作成功")


# 点赞
@news_blue.route("/comment_like", methods=["POST"])
@user_login_data
def comment_like():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="请登陆")

    comment_id = request.json.get("comment_id")
    news_id = request.json.get("news_id")
    # 判断当前用户的动作，到底是想点赞，还是想取消点赞
    action = request.json.get("action")

    comment = Comment.query.get(comment_id)

    if action == "add":
        # 用户想点赞
        comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                                CommentLike.user_id == user.id).first()
        # 查询出来之后，需要判断当前这条评论用户是否已经点赞，如果查询出来为空，说明之前没有点赞，那么就可以点赞
        if not comment_like:
            comment_like = CommentLike()
            comment_like.comment_id = comment_id
            comment_like.user_id = user.id
            db.session.add(comment_like)
            # 因为点赞了，所以需要把当前的评论进行加１
            comment.like_count += 1

    else:
        # 取消点赞的动作
        comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                                CommentLike.user_id == user.id).first()
        if comment_like:
            db.session.delete(comment_like)
            comment.like_count -= 1

    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="点赞成功")

# 评论
@news_blue.route("/news_comment", methods=["POST"])
@user_login_data
def news_comment():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="请登陆")
    news_id = request.json.get("news_id")
    # 评论的内容
    comment_str = request.json.get("comment")
    # 评论的父id
    parent_id = request.json.get("parent_id")
    """
       用户评论：
           用户如果在登录的情况下，可以进行评论，未登录，点击评论弹出登录框
           用户可以直接评论当前新闻，也可以回复别人发的评论
           1:用户必须先登陆才能进行评论，如果不登陆，直接返回
           2:如果需要评论，那么就需要知道当前评论的是哪条新闻，如果想知道是哪条新闻，那么就可以通过news_id 查询出来新闻
           3:如果评论成功之后，那么我们需要把用户的评论信息存储到数据库，为了方便下次用户在进来的时候可以看到评论
    """
    news = News.query.get(news_id)
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news.id
    comment.content = comment_str
    # 不是所有的新闻都有评论
    if parent_id:
        comment.parent_id = parent_id

    db.session.add(comment)
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="评论成功", data=comment.to_dict())

# 收藏
@news_blue.route("/news_collect", methods=["POST"])
@user_login_data
def news_collect():
    user = g.user
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    """
    新闻收藏：
        １：我们必须得知道，当前用户收藏的是哪条新闻，如果想知道用户收藏的是哪条新闻，那么直接通过news_id进行查询
        2:如果想收藏新闻，那么用户必须登陆，所以判断用户是否已经登陆就可以
        3:判断用户的动作，到底是想收藏，还是想取消收藏
        4:如果用户是收藏新闻的动作，那么直接把新闻丢到用户的收藏列表当中
    """
    news = News.query.get(news_id)
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    if action == "collect":
        user.collection_news.append(news)
    else:
        user.collection_news.remove(news)

    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="收藏成功")

# 详情页
@news_blue.route("/<int:news_id>")
@user_login_data
def news_detail(news_id):
    user = g.user
    # 首页右边的热门新闻排行
    news_model = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    news_list = []
    for new_dict in news_model:
        news_list.append(new_dict.to_dict())

    # 获取新闻详情的数据
    news = News.query.get(news_id)
    # 请求一次增加一次点击
    news.clicks += 1

    """
    新闻收藏
    1:进入到新闻详情页之后，如果用户已收藏该新闻，则显示已收藏，
    is_collected = true
    2:点击则为取消收藏，反之点击收藏该新闻 is_collected = false
    3:如果要收藏新闻，那么收藏的动作是用户的行为，所以收藏这个地方用户必
    须user要登陆有值
    4:因为我们需要收藏的是新闻，新闻必须也要存在,所以news必须有值
    5:要收藏的新闻必须在我收藏的列表当中，这样就可以把is_collected =
    true
    """

    # 当前登录用户是否关注当前新闻作者
    is_followed = False
    # 判断用户是否收藏过该新闻
    is_collected = False
    # 有的新闻是爬虫过来的,所以没有作者,会报167行,空对象无followers属性
    if user and news.user:
        if news.user.followers.filter(User.id == user.id).count() > 0:
            is_followed = True
        if news in user.collection_news:
            is_collected = True

    """
        获取到新闻评论列表
        1 :我们需要查询新闻评论表，在查询的时候，直接通过新闻id就可以查询，因为所有的评论都是针对新闻产生的
    """
    comments = Comment.query.filter(Comment.news_id ==
                                    news_id).order_by(Comment.create_time.desc()).all()
    comments_list = []
    # 获取到新闻详情页面评论点赞的数据
    # TODO
    commentLike_list = []
    comment_like_ids = []

    if user:
        # 根据user.id,查出用户点赞过的CommentLike对象
        commentLike_list = CommentLike.query.filter(CommentLike.user_id == user.id).all()
        # 遍历CommentLike所有对象,查出点赞评论的id
        comment_like_ids = [comment_like.comment_id for comment_like in commentLike_list]

    for comment in comments:

        comment_dict = comment.to_dict()
        comment_dict["is_like"] = False
        # comment_like_ids：所有的评论点赞id
        if comment.id in comment_like_ids:
            comment_dict["is_like"] = True
        comments_list.append(comment_dict)

    data = {
        "user_info": user.to_dict() if user else None,
        "click_news_list": news_list,
        "news": news.to_dict(),
        "is_collected": is_collected,
        "comments": comments_list,
        "is_followed": is_followed
    }

    return render_template("news/detail.html", data=data)
