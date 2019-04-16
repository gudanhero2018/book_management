from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)

#开启csrf保护
CSRFProtect(app)

#设置数据库配置信息
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:mysql@127.0.0.1/library2"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #压制警告信息

#创建SQLAlchemy对象,关联app
db = SQLAlchemy(app)

#设置密码
app.config['SECRET_KEY'] = "jfkdjfkdkjf"

#编写模型类
#作者(一方)
class Author(db.Model):
    __tablename__ = 'authors'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64),unique=True)

    #关系属性和反向引用
    books = db.relationship('Book',backref='author')

#书籍(多方)
class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64),unique=True)

    #外键
    author_id = db.Column(db.Integer,db.ForeignKey('authors.id')) #或者是, Author.id

#自定义表单类
class AuthorForm(FlaskForm):
    author=StringField('作者',validators=[DataRequired()])
    book=StringField('书籍',validators=[DataRequired()])
    submit=SubmitField('提交')



db.drop_all()
db.create_all()


#添加测试数据库
# 生成数据
au1 = Author(name='金庸')
au2 = Author(name='古龙')
au3 = Author(name='鲁迅')
# 把数据提交给用户会话
db.session.add_all([au1, au2, au3])
# 提交会话
db.session.commit()

bk1 = Book(name='天龙八部', author_id=au1.id)
bk2 = Book(name='射雕英雄传', author_id=au1.id)
bk3 = Book(name='小李飞刀', author_id=au2.id)
bk4 = Book(name='药', author_id=au3.id)
bk5 = Book(name='阿Q正传', author_id=au3.id)
# 把数据提交给用户会话
db.session.add_all([bk1, bk2, bk3, bk4, bk5])
# 提交会话
db.session.commit()
#删除作者
@app.route('/delete_author/<author_id>')
def delete_author(author_id):
    #查询数据库，是否有该ID的作者，如果有就删除（先删除书、再删作者），没有就提示错误
    #1、查询数据库
    author=Author.query.get(author_id)
    if author:
        try:
            #查询之后直接删除
            Book.query.filter_by(author_id=author.id).delete()

            #删除作者
            db.session.delete(author)
            db.session.commit()
        except Exception as e:
            print(e)
            flash('删除作者错误')
            db.session.rollback()
    else:
        flash('作者找不到')

    return redirect(url_for('show_page'))



#删除书籍-》网页中删除---》点击需要发送书籍的ID给删除书籍的路由----》路由需要接收参数
@app.route('/delete_book/<book_id>')
def delete_book(book_id):

    #查询数据库，是否有该ID的书籍，有就删除
    book=Book.query.get(book_id)
    if book:
        try:
            db.session.delete(book)
            db.session.commit()
        except Exception as e:
            print(e)
            flash('删除该书籍')
            db.session.rollback()
    else:
        flash('书籍找不到')


    #如何返回当前网址--->重定向
    #redirect：重定向，需要传入网络/路由地址
    #url_for:需要传入视图函数名，返回该视图函数的对应的路由
    return redirect(url_for('show_page'))




@app.route('/',methods=['GET','POST'])
def show_page():
    author_form=AuthorForm()
    '''
    验证逻辑：
    1、调用WTF函数的实现验证
    2、验证通过获取数据
    3、判断作者是否存在
    4、如果作者存在，判断书籍是否存在，没有重复书籍就添加数据，如果重复就提示错误
    5、如果作者不存在，添加作者和书籍
    6、验证不通过就提示错误'''

    #调用WTF的函数实现验证
    if author_form.validate_on_submit():
        author_name=author_form.author.data
        book_name=author_form.book.data
        #3、判断作者是否存在
        author=Author.query.filter_by(name=author_name).first()
        if author:
            book=Book.query.filter_by(name=book_name).first()
            if book:
                flash('已存在同名书籍')
            else:
                try:
                    new_book=Book(name=book_name,author_id=author.id)
                    db.session.add(new_book)
                    db.session.commit()
                except Exception as e:
                    print(e)
                    flash('添加书籍失败')
                    db.session.rollback()

        else:
            #5、如果作者不存在，添加作者和书籍
            try:
                new_author=Author(name=author_name)
                db.session.add(new_author)
                db.session.commit()

                new_book=Book(name=book_name,author_id=new_author.id)
                db.session.add(new_book)
                db.session.commit()
            except Exception as e:
                print(e)
                flash('添加书籍失败')
                db.session.rollback()

    else:

        if request.method=='POST':
            flash('参数错误')


    #查询数据库
    authors = Author.query.all()

    # 渲染到页面
    return render_template('library.html',authors=authors,form=author_form)



if __name__ == '__main__':

    app.run(debug=True)

