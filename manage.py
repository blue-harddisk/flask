"""
主函数入口
"""

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from info import db, create_app
from info import models
from info.models import User

app = create_app("develop")
manager = Manager(app)
Migrate(app, db)
manager.add_command('mysql', MigrateCommand)

# 脚本创建admin账号:
# @manager.option('-n', '--name', dest='name')
# @manager.option('-p', '--password', dest='password')
# def create_super_user(name,password):
#     user = User()
#     user.nick_name = name
#     user.password = password
#     user.mobile = name
#     user.is_admin = True
#     db.session.add(user)
#     db.session.commit()


if __name__ == '__main__':
    manager.run()
