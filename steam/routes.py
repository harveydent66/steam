from steam import app
from flask import render_template, request, jsonify
import json
import ast
from .constants import *

import psycopg2
conn = psycopg2.connect(user = "postgres",password = "montyhanda",host = "127.0.0.1",port = "5432",database = "project")
cur = conn.cursor()

@app.route('/home')
@app.route('/')
def home():
	try:
		cur.execute("SELECT name,release_date,appid,price FROM games WHERE appid IS NOT NULL ORDER BY positive_ratings DESC, name ASC OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY ");
		rows = cur.fetchall()
		games = []
		if len(rows)>0:
			for tup in rows:
				D = {}
				D["name"] = tup[0]
				D["release_date"] = tup[1]
				D["appid"] = tup[2]
				D["price"] = str(round(float(tup[3])*93.13, 1))+" INR" if float(tup[3])!=0.0 else "FREE" #in inr
				games.append(D)
		cur.execute("SELECT count(*) from games")
		rows = cur.fetchall()
		if len(rows)>0:
			totalRows = rows[0][0]
		else:
			totalRows = 0
		conn.commit()
		return render_template('home.html', user="DEFAULT",games = games, totalRows=totalRows)
	except Exception as e:
		conn.rollback()
		print("home",e)
		return "Some error occured"


@app.route('/login')
def login():
	return ""


#return game description, website url, support url, tags and requirements using appid
@app.route('/game_details')
def game_details():
	appid = request.args.get('appid') ###
	if appid == None:
		return "No appid provided"
	try:
		variables = {}
		cur.execute("SELECT detailed_description FROM games_description WHERE appid="+str(appid))
		rows = cur.fetchall()
		if len(rows)>0:
			description = rows[0][0]
		else:
			description = None
		cur.execute("SELECT website,support_url FROM support WHERE appid="+str(appid))
		rows = cur.fetchall()
		if(len(rows)>0):
			website = rows[0][0]
			steam_page = rows[0][1]
		else:
			website = None
			steam_page = None
		cur.execute("SELECT pc_requirements,mac_requirements,linux_requirements FROM requirements WHERE appid="+str(appid))
		rows = cur.fetchall()
		if len(rows)>0:
			wr = ast.literal_eval(rows[0][0])
			mr = ast.literal_eval(rows[0][1])
			lr = ast.literal_eval(rows[0][2])
			if type(wr) == type({}):
				windows_requirements = wr['minimum']
			else:
				windows_requirements = None
			if type(mr) == type({}):
				mac_requirements = mr['minimum']
			else:
				mac_requirements = None
			if type(lr)==type({}):
				linux_requirements = lr['minimum']
			else:
				linux_requirements = None
		else:
			windows_requirements = None
			mac_requirements = None
			linux_requirements = None
		cur.execute("SELECT * FROM games WHERE appid="+str(appid))
		rows = cur.fetchall()
		if len(rows)>0:
			tup = rows[0]
			variables["name"] = tup[1]
			variables["release_date"] = tup[2]
			variables["is_english"] = tup[3]
			variables["developer"] = tup[4]
			variables["platforms"] = tup[6].split(";") #list
			variables["required_age"] = tup[7]
			variables["genres"] = tup[9]
			variables["tags"] = tup[10].split(";") #list
			variables["achievements "] = tup[11]
			variables["positive_ratings"] = tup[12]
			variables["negative_ratings"] = tup[13]
			variables["average_playtime"] = tup[14]
			variables["player_count"] = tup[16]
			variables["price"] = str(round(float(tup[17])*93.13, 1))+" INR" if float(tup[3])!=0.0 else "FREE" #in inr
		else:
			variables["name"] = None
			variables["release_date"] = None
			variables["is_english"] = None
			variables["developer"] = None
			variables["platforms"] = None
			variables["required_age"] = None
			variables["genres"] = None # ; seperated
			variables["tags"] = None # ; seperated
			variables["achievements "] =  None
			variables["positive_ratings"] =  None
			variables["negative_ratings"] =  None
			variables["average_playtime"] =  None
			variables["player_count"] =  None
			variables["price"] = None
		variables["description"] = description
		variables["website"] = website
		variables["steam_page"] = steam_page
		variables["windows_requirements"] = windows_requirements
		variables["linux_requirements"] = linux_requirements
		variables["mac_requirements"] = mac_requirements
		variables["appid"] = appid
		conn.commit()
		return render_template('game_details.html', user="DEFAULT",vars = variables)
	except Exception as e:
		conn.rollback()
		print("game_details",e)
		return "Some error occured"

@app.route('/reviews')
def reviews():
	appid = request.args.get('appid') ###
	page_num = request.args.get('page_num') ###
	if appid == None:
		return "No appid provided"
	if page_num == None:
		return "No offset provided"
	try:
		cur.execute("SELECT username,review,found_funny,hours,date FROM reviews WHERE appid="+str(appid)+" ORDER BY found_funny DESC, username ASC OFFSET "+ str((int(page_num)-1)*10) +" ROWS FETCH NEXT 10 ROWS ONLY ")
		#return a list of dictionary
		rev = []
		rows = cur.fetchall()
		if len(rows)>0:
			for tup in rows:
				D = {}
				D["username"] = tup[0]
				D["review"] = tup[1]
				D["found_funny"] = tup[2]
				D["hours"] = tup[3]
				D["date"] = tup[4]
				rev.append(D)
		conn.commit()
		return render_template('reviews.html', user="DEFAULT",reviews = rev, appid=appid)
	except Exception as e:
		print("reviews",e)
		conn.rollback()
		return "Some error occured"

@app.route('/screenshots')
def screenshots():
	appid = request.args.get('appid') ###
	if appid == None:
		return "No appid provided"
	try:
		cur.execute("SELECT screenshots FROM media_data WHERE appid="+str(appid))
		html = """""";
		rows = cur.fetchall()
		res = []
		conn.commit()
		if len(rows)>0:
			for ss in ast.literal_eval(rows[0][0]):
				D = {}
				D['path_full'] = ss['path_full']
				D['path_thumbnail'] = ss['path_thumbnail']
				res.append(D)
			return render_template('screenshots.html',user="DEFAULT",screenshots=res)
		else:
			return "ERROR"
	except Exception as e:
		print("screenshots",e)
		conn.rollback()
		return "Some error occured"

@app.route('/searchGames',methods=['POST'])
def searchGames():
	if request.method == 'POST':
		searchString = request.form.get('string')
		page_num = request.form.get('page_num')
		if searchString=="" or page_num=="" or int(page_num)<=0:
			return json.dumps("[]")
		page_num = int(page_num)
		searchString = searchString.lower() #to remove any caps problem
		try:
			cur.execute("SELECT name,release_date,appid,price FROM games WHERE appid IS NOT NULL AND LOWER(name) LIKE '%"+ searchString +"%' ORDER BY positive_ratings DESC, name ASC OFFSET "+ str((int(page_num)-1)*10) +" ROWS FETCH NEXT 10 ROWS ONLY ");
		except Exception as e:
			print("searchGames1",e)
			conn.rollback()
			return "Some error occured 1"
		rows = cur.fetchall()
		games = []
		if len(rows)>0:
			for tup in rows:
				D = {}
				D["name"] = tup[0]
				D["release_date"] = str(tup[1])
				D["appid"] = tup[2]
				D["price"] = str(round(float(tup[3])*93.13, 1))+" INR" if float(tup[3])!=0.0 else "FREE" #in inr
				games.append(D)
		#for counting total matching games
		try:
			cur.execute("SELECT count(*) from games WHERE appid IS NOT NULL AND LOWER(name) LIKE '%"+ searchString +"%'")
			conn.commit()
		except Exception as e:
			print("searchGames2",e)
			conn.rollback()
			return "Some error occured 2"
		rows = cur.fetchall()
		if len(rows)>0:
			totalRows = rows[0][0]
		else:
			totalRows = 0
		games.append({"totalRows": totalRows}) #last object becomes totalRows
		return json.dumps(games)
	else:
		return "Invalid Request"

@app.route('/getGames',methods=['POST'])
def getGames():
	if request.method == 'POST':
		page_num = request.form.get('page_num')
		if int(page_num)<=0:
			return json.dumps("[]")
		try:
			cur.execute("SELECT name,release_date,appid,price FROM games WHERE appid IS NOT NULL ORDER BY positive_ratings DESC, name ASC OFFSET "+ str((int(page_num)-1)*10) +" ROWS FETCH NEXT 10 ROWS ONLY ");
			rows = cur.fetchall()
			games = []
			if len(rows)>0:
				for tup in rows:
					D = {}
					D["name"] = tup[0]
					D["release_date"] = str(tup[1])
					D["appid"] = tup[2]
					D["price"] = str(round(float(tup[3])*93.13, 1))+" INR" if float(tup[3])!=0.0 else "FREE" #in inr
					games.append(D)
			conn.commit()
			return json.dumps(games)
		except Exception as e:
			print("getGames",e)
			conn.rollback()
			return "Some error occured"
	else:
		return "Invalid Request"

@app.route('/manageUser', methods=['GET','POST'])
def manageUser():
	#when admin is user then only open this page
	if request.method == 'GET':
		page_num = 1
	else:
		page_num = request.form.get('page_num')
	page_num = int(page_num)
	if page_num <=0:
		return "Bad page number"
	try:
		cur.execute("SELECT username, isbanned FROM users WHERE isadmin=false ORDER BY username ASC OFFSET "+ str((int(page_num)-1)*10) +" ROWS FETCH NEXT 10 ROWS ONLY ")
		rows = cur.fetchall()
		userslist = []
		for tup in rows:
			userObj = {}
			userObj['username'] = tup[0]
			userObj['isbanned'] = str(tup[1])
			userslist.append(userObj)
		conn.commit()
		render_template('manage_user.html',user="DEFAULT", userslist = userslist)
	except Exception as e:
		conn.rollback()
		print("manageUser",e)
		return "Some error occured"


@app.route('/banUser', methods=['POST'])
def banUser():
	#only when the request is made by admin
	if request.method == 'POST':
		username = request.form.get('username')
		username = str(username)
		try:
			cur.execute("UPDATE users SET isbanned=true WHERE username='"+username+"'")
			conn.commit()
			return "successfully banned user "+ username
		except Exception as e:
			conn.rollback()
			print("banuser",e)
			return "Some error occured"
	else:
		return "Bad request"

@app.route('/unbanUser', methods=['POST'])
def unbanUser():
	#only when the request is made by admin
	if request.method == 'POST':
		username = request.form.get('username')
		username = str(username)
		try:
			cur.execute("UPDATE users SET isbanned=false WHERE username='"+username+"'")
			conn.commit()
			return "unbanned user "+ username
		except Exception as e:
			print("unbanuser", e)
			conn.rollback()
			return "Some error occured"
	else:
		return "Bad request"

@app.route('/addMoney', methods=['POST'])
def addMoney():
	#only admin can use this method
	if request.method == 'POST':
		username = request.form.get('username')
		amount = request.form.get('amount')
		username = str(username)
		amount = float(amount)
		try:
			cur.execute("UPDATE wallet SET money = money+"+str(amount)+" WHERE username="+username)
			conn.commit()
			return "added money to wallet of user "+ username
		except Exception as e:
			print("addMoney",e)
			conn.rollback()
			return "Some error occured!"
	else:
		return "Bad request"


@app.route('/addGame', methods=['POST'])
def addGame():
	#only admin can call this function
	if request.method == 'POST':
		name = request.form.get('name').replace("'","&#39")
		release_date = request.form.get('release_date')
		description = request.form.get('description').replace("'","&#39")
		developers = request.form.get('developers').replace("'","&#39")
		publishers = request.form.get('publishers').replace("'","&#39")
		platforms = request.form.get('platforms').replace("'","&#39")
		required_age = request.form.get('required_age')
		categories = request.form.get('categories').replace("'","&#39")
		genres = request.form.get('genres').replace("'","&#39")
		tags = request.form.get('tags').replace("'","&#39")
		achievements = request.form.get('achievements')
		price = request.form.get('price')
		price = float(price)
		price /=93.13 #to convert to gbp
		try:
			cur.execute("SELECT MAX(appid) from games");
			rows = cur.fetchall()
			appidmax = int(rows[0][0])
			newappid = appidmax+1
		except Exception as e:
			print("addGame1",e)
			conn.rollback()
			return "Some error occured1!"
		
		try:
			cur.execute(
						'''
						INSERT INTO games (appid, name,release_date,is_english,developer,publisher,platforms,required_age,categories,genres,steamspy_tags,achievements,positive_ratings,negative_ratings,average_playtime,median_playtime,owners_range,price)
						VALUES ({newappid},'{name}','{release_date}',1,'{developers}','{publishers}','{platforms}',{required_age},'{categories}','{genres}','{tags}',{achievements},0,0,0,0,'0-20000',{price})
						'''.format(newappid=newappid, name=name, release_date=release_date, developers=developers,publishers=publishers,platforms=platforms,required_age=required_age,categories=categories,
							genres=genres,tags=tags,achievements=achievements,price=str(price))
						)
			cur.execute('''
						INSERT INTO games_description (appid, detailed_description, about_game, short_description)
						VALUES ({newappid}, '{description}', '{description}', '{description}')
						'''.format(newappid=newappid, description=description))
			conn.commit()
			return "added game "+name
		except Exception as e:
			print("addGame2",e)
			conn.rollback()
			return "Some error occured2!"
	else:
		return "Bad request"


@app.route('/admin')
def admin():
	return render_template('admin_page.html',user="DEFAULT")