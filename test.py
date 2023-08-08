from flask import Flask, render_template,request, session,redirect
from pymongo import MongoClient
from flask_mail import Mail
import json
from datetime import datetime

with open('config.json','r') as f:
    params = json.load(f)['params']

if params['local_server'] == True:
    server = params['local_uri']
else:
    server = params['prod_uri']

app = Flask(__name__)
app.secret_key = 'my-key'  # Required for session
client = MongoClient(server) 
db = client['Sijan']
collection = db['Contacts']

collection_post = db['posts']

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']
)
mail = Mail(app)

def get_next_sno():
    with open('sno.txt','r') as file:
        current_sno = int(file.readline())
    next_sno = current_sno + 1
    with open('sno.txt','w') as file:
        file.write(str(next_sno))
    return next_sno

@app.route('/')
def home():
    posts = collection_post.find()[0:params['no_of_posts']]
    return render_template('index.html',params = params,posts = posts)

@app.route('/post/<string:post_slug>', methods =['GET'])
def post_route(post_slug):
    post = collection_post.find_one({"slug":post_slug})

    return render_template('/post.html', params = params, post = post)

@app.route('/about')
def about():
    return render_template('/about.html', params = params)

@app.route('/dashboard', methods= ['GET','POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = collection_post.find()
        return render_template('/dashboard.html', params=params, posts = posts)

    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_password']):
            #set the session variable
            session['user'] = username    
            posts = collection_post.find()
            return render_template('/dashboard.html', params=params,posts=posts)        
    
    return render_template('/login.html', params = params)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/edit/<string:_id>", methods = ['GET','POST'])
def edit(_id):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')

            if _id == '0':
                _id = int(get_next_sno())
                up = {
                    "_id":_id,
                    "title":box_title,
                    "slug":slug,
                    "content":content,
                    "img_file": img_file,
                    "tagline":tline
                }
                collection_post.insert_one(up)
                 
            else:
               
                up = {
                    "title":box_title,
                    "slug":slug,
                    "content":content,
                    "img_file": img_file,
                    "tagline":tline
                }
                update = {'$set':up}
                filt = {'_id':_id}
                collection_post.update_one(filt,update)
                return redirect('/edit/'+_id)

        post = collection_post.find_one({'_id':int(_id)})
        return render_template('/edit.html',params = params, post=post)


@app.route('/contact')
def contact():
    return render_template('/contact.html', params = params)

@app.route('/submit',methods=[ 'POST'])
def submit():
    name = request.form.get('MYName')
    email = request.form.get('myEmail')
    phone = request.form.get('myPhone')
    msg = request.form.get('myMessage')

    up = {
        "Name":name,
        "Email":email,
        "Phone":phone,
        "Message":msg,
        "Date":datetime.now()
    }
    collection.insert_one(up)
    mail.send_message('New message from '+ name,
                      sender = params['gmail_user'],
                      recipients = [params['gmail_user']],
                      body =msg +"\n"+phone)
    return "suceessfuly submitted"

if __name__ == '__main__':
    app.run(debug=True)