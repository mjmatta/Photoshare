import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64
from datetime import datetime

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'cs460'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='checkbox' name='guest' id='guest'>Sign in as guest</input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	try:
		isGuest = flask.request.form['guest']
		if isGuest == 'on':
			user = User()
			user.id = 'guest@guest.net'
			flask_login.login_user(user)
			return flask.redirect(flask.url_for('protected'))
	except:
		print("Guest error")
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	firstname=request.form.get('firstname')
	firstname=checkNullVal(firstname)
	lastname=request.form.get('lastname')
	lastname=checkNullVal(lastname)
	birthday=request.form.get('birthday')
	birthday=checkNullVal(birthday)
	hometown=request.form.get('hometown')
	hometown=checkNullVal(hometown)
	gender=request.form.get('gender')
	gender=checkNullVal(gender)
	if test and password != "" and (checkDate(birthday.replace("'", "")) or birthday == 'NULL'):
		print(cursor.execute("INSERT INTO Users (first_name, last_name, email, birth_date, hometown, gender, password) VALUES ({0}, {1}, '{2}', {3}, {4}, {5}, '{6}')".format(firstname, lastname, email, birthday, hometown, gender, password)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		return flask.redirect(flask.url_for('register'))

def checkDate(bday):
	try:
		datetime.strptime(bday, '%Y-%m-%d')
		return True
	except ValueError:
		return False

def checkNullVal(text):
	if text == '':
		return 'NULL'
	else:
		return "'" + text + "'"

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getAllAlbums():
	cursor = conn.cursor()
	cursor.execute("SELECT albums_id, name, date, user_id FROM Albums")
	return cursor.fetchall()

def getNumPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) FROM Pictures")
	return cursor.fetchone()[0]

def getPhotosFromAlbumId(aid):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption FROM Albums A, Pictures P WHERE A.albums_id = '{0}' AND P.albums_id = A.albums_id".format(aid))
	return cursor.fetchall()

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getAlbumIdFromName(album, uid):
	cursor = conn.cursor()
	cursor.execute("SELECT A.albums_id  FROM Albums A, Users U WHERE A.name = '{0}' AND A.user_id = '{1}'".format(album, uid))
	return cursor.fetchone()[0]

def getAllTags():
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) FROM Tags")
	return cursor.fetchone()[0]

def getTagId(tag):
	try:
		cursor = conn.cursor()
		cursor.execute("SELECT T.tag_id FROM Tags T WHERE T.name='{0}'".format(tag))
		res = cursor.fetchone()[0]
		return res
	except:
		return None

def getUserFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT U.email FROM Users U, Friends F WHERE F.user_id1 = '{0}' AND U.user_id = F.user_id2".format(uid))
	return [row[0] for row in cursor.fetchall()]

def getPhotoFromId(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id='{0}'".format(pid))
	return cursor.fetchone()

def getLikesFromPid(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) FROM Likes WHERE picture_id='{0}'".format(pid))
	return cursor.fetchone()[0]

def ifLike(uid, pid):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) FROM Likes WHERE picture_id='{0}' AND user_id='{1}'".format(pid, uid))
	return cursor.fetchone()[0]

def getRecFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT U.email FROM Users U, Friends F WHERE U.user_id = F.user_id2 AND F.user_id1 IN (SELECT U2.user_id FROM Users U2, Friends F WHERE F.user_id1 = '{0}' AND U2.user_id = F.user_id2)".format(uid))
	return [row[0] for row in cursor.fetchall()]

def getComments(pid):
	cursor=conn.cursor()
	cursor.execute("SELECT C.text FROM Comments C, Pictures P WHERE C.picture_id=P.picture_id AND P.picture_id='{0}'".format(pid))
	return [row[0] for row in cursor.fetchall()]

def getTags(pid):
	cursor=conn.cursor()
	cursor.execute("SELECT T.name FROM Tags T, Tagged D, Pictures P WHERE D.picture_id=P.picture_id AND T.tag_id = D.tag_id AND P.picture_id='{0}'".format(pid))
	return [row[0] for row in cursor.fetchall()]

def getPhotosFromTag(tid):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption FROM Pictures P, Tagged D WHERE D.tag_id='{0}' AND D.picture_id=P.picture_id".format(tid))
	return cursor.fetchall()

def getPhotosFromTagAndUser(tid, uid):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption FROM Pictures P, Tagged D WHERE D.tag_id='{0}' AND D.picture_id=P.picture_id AND P.user_id='{1}'".format(tid, uid))
	return cursor.fetchall()

def getTagNameFromId(tid):
	cursor = conn.cursor()
	cursor.execute("SELECT name FROM Tags WHERE tag_id='{0}'".format(tid))
	return cursor.fetchone()[0]

def getTopTags():
	cursor = conn.cursor()
	cursor.execute("SELECT t.name, t.tag_id FROM Tags t JOIN Tagged d ON t.tag_id = d.tag_id GROUP BY t.tag_id ORDER BY COUNT(t.tag_id) DESC LIMIT 10")
	return cursor.fetchall()

def getTagIdFromName(name):
	cursor = conn.cursor()
	cursor.execute("SELECT tag_id FROM Tags WHERE name='{0}'".format(name))
	return cursor.fetchone()[0]

def getUidFromPid(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Pictures WHERE picture_id='{0}'".format(pid))
	return cursor.fetchone()[0]

def getCommentsFromText(text):
	cursor=conn.cursor()
	cursor.execute("SELECT U.email,COUNT(*) AS ccount FROM Comments C, Users U WHERE C.text='{0}' AND C.user_id=U.user_id GROUP BY C.user_id ORDER BY ccount DESC".format(text))
	return cursor.fetchall()

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def getTopUsers():
	cursor=conn.cursor()
	cursor.execute("SELECT U.email, COUNT(*) FROM Comments C, Users U WHERE U.user_id=C.user_id GROUP BY U.email ORDER BY COUNT(*) DESC")
	comments=cursor.fetchall()
	cursor.execute("SELECT U.email, COUNT(*) FROM Pictures P, Users U WHERE U.user_id=P.user_id GROUP BY U.email ORDER BY COUNT(*) DESC")
	pictures=cursor.fetchall()
	total=comments+pictures
	users = {}
	for (i, j) in total:
		if i in users.keys():
			users[i] += int(j)
		else:
			users[i] = int(j)
	return list(users.items())

	return cursor.fetchall()
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

@app.route('/friends', methods=['GET', 'POST'])
@flask_login.login_required
def friend_add():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'GET':
		return render_template('friends.html', friends=getUserFriends(uid), recFriends=getRecFriends(uid))
	else:
		newFriend=request.form.get('email')
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Friends (user_id1, user_id2) VALUES ('{0}', '{1}')".format(uid, getUserIdFromEmail(newFriend)))
		conn.commit()
		return render_template('friends.html', friends=getUserFriends(uid), recFriends=getRecFriends(uid))


#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		album_name = request.form.get('album')
		tags = (request.form.get('tags')).split(" ")
		print(tags)
		photo_data =imgfile.read()
		cursor = conn.cursor()
		try:
			album = getAlbumIdFromName(album_name, uid)
		except:
			cursor.execute('''INSERT INTO Albums (name, date, user_id) VALUES (%s, %s, %s)''', (album_name, datetime.today().strftime('%Y-%m-%d'), uid))
			album = getAlbumIdFromName(album_name, uid)
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption, albums_id) VALUES (%s, %s, %s, %s )''' ,(photo_data,uid, caption, album))
		conn.commit()
		if tags != "" and tags != None:
			for tag in tags:
				tagId = getTagId(tag)
				if tagId == None:
					cursor.execute('''INSERT INTO Tags (name) VALUES (%s)''', (tag))
					conn.commit()
					tagId = getTagId(tag)
				print(getNumPhotos(), tagId)
				cursor.execute('''INSERT INTO Tagged (picture_id, tag_id) VALUES (%s, %s)''', (getNumPhotos(),tagId))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid),base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code

# @app.route('/topusers')
# @flask_login.login_required
# def display_users():


@app.route('/gallery', methods=['GET', 'POST'])
@flask_login.login_required
def display_gallery():
	all_albums=list(getAllAlbums())
	for i in range(len(all_albums)):
		aid=all_albums[i][0]
		all_albums[i] = list(all_albums[i])
		all_albums[i].append(list(getPhotosFromAlbumId(aid)))
		all_albums[i] = tuple(all_albums[i])
	return render_template('albums.html', albums=tuple(all_albums), base64=base64)


@app.route('/photos/<int:Number>', methods=['GET', 'POST'])
@flask_login.login_required
def add_like(Number):
	if request.method == 'GET':
		return render_template('photos.html', photo=getPhotoFromId(Number), base64=base64, likes=getLikesFromPid(Number), number=Number, comments=getComments(Number), tags=getTags(Number))
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		print(ifLike(uid, Number))
		if request.form['action'] == 'Like':
			if(ifLike(uid, Number) == 0):
				cursor.execute('''INSERT INTO Likes (picture_id, user_id) VALUES (%s, %s)''', (Number, getUserIdFromEmail(flask_login.current_user.id)))
			else:
				cursor.execute('''DELETE FROM Likes WHERE picture_id=%s AND user_id=%s''', (Number, getUserIdFromEmail(flask_login.current_user.id)))
		elif request.form['action'] == 'Comment':
			print(request.form.get('comment'))
			if request.form.get('comment') != '' and uid != getUidFromPid(Number):
				cursor.execute('''INSERT INTO Comments (user_id, picture_id, text, date) VALUES (%s, %s, %s, %s)''', (uid, Number, request.form.get('comment'), datetime.today().strftime('%Y-%m-%d')))
		elif request.form['action'] == 'DeletePhoto':
			cursor.execute('''DELETE FROM Pictures WHERE picture_id=%s''', (Number))
			return flask.redirect(flask.url_for('hello'))
			conn.commit()
		elif request.form['action'] == 'DeleteAlbum':
			cursor.execute('''DELETE A FROM Albums A JOIN Pictures P ON P.picture_id=%s''', (Number))
			conn.commit()
			return flask.redirect(flask.url_for('hello'))
		conn.commit()
		print(getComments(Number))
		conn.commit()
		return render_template('photos.html', photo=getPhotoFromId(Number), base64=base64, likes=getLikesFromPid(Number), number=Number, comments=getComments(Number), tags=getTags(Number))

@app.route('/tags/<int:Number>', methods=['GET', 'POST'])
@flask_login.login_required
def get_tags(Number):
	if request.method=='GET':
		return render_template('tags.html', photos=getPhotosFromTag(Number), tagName=getTagNameFromId(Number), base64=base64, number=Number)
	else:
		if request.form['action'] == 'All':
			return render_template('tags.html', photos=getPhotosFromTag(Number), tagName=getTagNameFromId(Number), base64=base64, number=Number)
		else:
			return render_template('tags.html', photos=getPhotosFromTagAndUser(Number, getUserIdFromEmail(flask_login.current_user.id)), tagName=getTagNameFromId(Number), base64=base64, number=Number)

@app.route('/searchtags/', methods=['GET', 'POST'])
@flask_login.login_required
def search_tags():
	if request.method=='GET':
		return render_template('searchtags.html')
	else:
		tl = (request.form.get('tags')).split(" ")
		ps=[]
		for t in tl:
			ps.append(getPhotosFromTag(getTagIdFromName(t)))
		return render_template('searchtags.html', photos=ps, tagNames=tl, base64=base64)

@app.route('/searchcomments/', methods=['GET', 'POST'])
@flask_login.login_required
def search_comments():
	if request.method=='GET':
		return render_template('searchcomments.html')
	else:
		search=request.form.get('search')
		return render_template('searchcomments.html', comments=getCommentsFromName(search))


@app.route('/populartags/', methods=['GET'])
@flask_login.login_required
def get_pop_tags():
	return render_template('poptags.html', tags=getTopTags())

@app.route('/topusers/', methods=['GET'])
@flask_login.login_required
def get_top_users():
	return render_template('topusers.html', users=getTopUsers())

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
