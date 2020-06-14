import os
import secrets
import pytesseract
from io import BytesIO
import requests
from PIL import Image
from website import app,bcrypt,db, mail
from flask import render_template, url_for, flash, redirect,request,abort
from website.models import User,Post
from website.forms import SignUpForm, SignInForm,UpdateAccountForm,PostForm,OcrForm,RequestResetForm,ResetPasswordForm
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html',title='Home Page')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html',title='Muhammed Fahis')

@app.route('/contact')
def contact():
    return render_template('contact.html', title='Contact Me')
    
@app.route('/blogs')
def blog():
    page = request.args.get('page',1,type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page,per_page=5)
    return render_template('Blog.html', title='Blogs' ,post=posts)

@app.route('/user/<username>')
def user_posts(username):
    page = request.args.get('page',1,type=int)
    user = User.query.filter_by(username=username).filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page,per_page=5)
    return render_template('user_post.html', title='Blogs' ,post=posts ,user=user)


@app.route('/signup',methods=['GET','POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = SignUpForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Acoount is created succesfully for {form.username.data}! Now you Can Login', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html',title='Sign Up',form=form)

@app.route('/login',methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = SignInForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Login successfully", 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('blog'))
        else:
            flash("Login Unsuccessfully",'danger')
    return render_template('login.html', title='Sign in', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(16)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/img/profile_pic/', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@app.route('/account' ,methods=['GET','POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated', 'info')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static',filename='img/profile_pic/'+current_user.image_file)
    return render_template('account.html',title="Account",img=image_file , form=form)

@app.route("/blogs/new",methods=['GET','POST'])
@app.route("/blog/new",methods=['GET','POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your Post has been created!',"success")
        return redirect(url_for('new_post'))
    return render_template('create_post.html', title="Create Post", form=form, legend="Update Post")

@app.route("/blog/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

@app.route("/blog/<int:post_id>/update", methods=['GET','POST'])
@login_required
def postupdate(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)  #abort return a error message 
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been update!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':

        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update post', form=form ,legend='Update Form')


@app.route("/blog/<int:post_id>/delete", methods=['POST'])
@login_required
def postdelete(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash(f"Your post has been deleted !", "danger")
    return redirect(url_for('blog'))

def ocr_picture(form_picture):
    text = pytesseract.image_to_string(form_picture,lang="eng")
    return text

@app.route('/ocr', methods=['GET', 'POST'])
def ocr():
    form = OcrForm()
    form.content.data = " Upload a valid text image .\n If a image have unsupported character and small font\nThen this ocr will not work correctly"
    if form.validate_on_submit():
        if form.url.data:
            response = requests.get(form.url.data)
            img = Image.open(BytesIO(response.content))
            text = ocr_picture(img)
            if text == '':
                form.content.data = "No Text Found"
            else:
                form.content.data = text
                
            return render_template('ocr.html',title='OCR' ,form=form)
        else:
            img = Image.open(form.picture.data)
            text = ocr_picture(img)
            if text == '':
                form.content.data = "No Text Found"
            else:
                form.content.data = text
            return render_template('ocr.html',title='OCR',form=form)
    else:
        return render_template('ocr.html', title='OCR', form=form)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender="fahis.skazi@gmail.com", recipients=[user.email])
    msg.body = f'''To reset your password,visit the following link:
    {url_for('reset_token',token=token,_external=True)}
    If you did not make this request then simply ignore this message no changes will occur
    '''
    flash(f'{msg}',success)
    mail.send(msg)

@app.route("/reset_password",methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instruction to reset password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html',title='Reset Password',form=form)
    
@app.route("/reset_password/<token>",methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Password is Updated succesfully , Now you Can Login', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html',title="Reset Password",form=form)