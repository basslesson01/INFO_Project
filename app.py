#!/usr/bin/env python
import sys
from flask import Flask, jsonify, abort, request, make_response, session, render_template
from flask_restful import reqparse, Resource, Api
from flask_session import Session
from flask.ext.cors import CORS
import MySQLdb
import json
import ldap
import ssl
import settings # Our server and db settings, stored in settings.py

###########################################################################################
#
# GROUP MEMBERS:
# 	Leon Kim (3443426)
#	Mike Tanner (3321885)
#
###########################################################################################

reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__, static_url_path="")
CORS(app)

app.secret_key = settings.SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_NAME'] = 'Chocolate'
app.config['SESSION_COOKIE_DOMAIN'] = settings.APP_HOST
Session(app)

# Error handlers
@app.errorhandler(400) # decorators to add to 400 response
def not_found(error):
	return make_response(jsonify( { 'status': 'Bad request' } ), 400)

@app.errorhandler(404) # decorators to add to 404 response
def not_found(error):
	return make_response(jsonify( { 'status': 'Resource not found' } ), 404)

###########################################################################################
class Root(Resource):
	def get(self):
		return app.send_static_file('index.html')

class signIn(Resource):
	# POST: Log in with username and password
	# curl -i -H "Content-Type: application/json" -X POST -d '{"username": "user", "password": "password"}' -c cookie-jar -k https://info3103.cs.unb.ca:43426/signin
	def post(self):

		if not request.json:
			abort(400)

		parser = reqparse.RequestParser()
 		try:
	 		parser.add_argument('username', type=str, required=True)
			parser.add_argument('password', type=str, required=True)
			request_params = parser.parse_args()
		except:
			abort(400)

		if request_params['username'] in session:
			response = {'status': 'success'}
			responseCode = 200

		else:
			try:
				l = ldap.open(settings.LDAP_HOST)
				l.start_tls_s()
				l.simple_bind_s("uid="+request_params['username']+
					", ou=People,ou=fcs,o=unb", request_params['password'])

				session['username'] = request_params['username']
				tempUser = session['username']
				##############################################################################################################################################################################
				#connection = MySQLdb.connect(host=settings.MYSQL_HOST,user=settings.MYSQL_USER,passwd=settings.MYSQL_PASSWD,db=settings.MYSQL_DB, use_unicode=True, charset='utf8')
				#cursor = connection.cursor()
				#cursor.callproc('createSession', (cUserID, cSongTitle, cYouTubeURL)) # stored procedure, with arguments
				#connection.commit() # database was modified, commit the changes
				##############################################################################################################################################################################
				response = {'status': 'success'}
				responseCode = 201
			except ldap.LDAPError, error_message:
				response = {'status': 'Access denied'}
				responseCode = 403
			finally:
				l.unbind()

		return make_response(jsonify(response), responseCode)

	# GET: Grabs the current user (used for debugging purpose)
	# curl -i -H "Content-Type: application/json" -X GET -b cookie-jar -k https://info3103.cs.unb.ca:43426/signin
	def get(self):
		success = False
		if 'username' in session:
			# tempUser = session['username']
			response = {'status':'success'}
			responseCode = 200
		else:
			response = {'status': 'fail'}
			responseCode = 403

		return make_response(jsonify(response), responseCode)

	# DELETE: Logout of connection, terminate session
	# curl -i -H "Content-Type: application/json" -X DELETE -b cookie-jar -k https://info3103.cs.unb.ca:43426/signin
	def delete(self):
		if 'username' in session:
			response = {'status':'Logged out'}
			responseCode = 200
			session.clear()
		else:
			response = {'status':'Session not found'}
			responseCode = 404

		return make_response(jsonify(response), responseCode)

class songs(Resource):
	# GET: Return all songs
	# curl -i -H "Content-Type: application/json" -X GET -b cookie-jar -k https://info3103.cs.unb.ca:43426/signin/songs
	def get(self):
		working = False
		if 'username' in session:
			tempUser = session['username']
			response = {'status':'success'}
			responseCode = 200
			try:
				connection = MySQLdb.connect(host=settings.MYSQL_HOST,user=settings.MYSQL_USER,passwd=settings.MYSQL_PASSWD,db=settings.MYSQL_DB, use_unicode=True, charset='utf8')
				cursor = connection.cursor()
				cursor.callproc('getSongs') # stored procedure, no arguments
				rows = cursor.fetchall()# get all the results
				field_names = [i[0] for i in cursor.description]
				set = [
					{description: value for description, value in zip(field_names, row)}
					for row in rows]
				working = True
			except:
				abort(500) # Nondescript server error
		else:
			response = {'status': 'Not logged in'}
			responseCode = 403

		if working is True:		# If user is logged in
			cursor.close()
			connection.close()
			return make_response(jsonify({'songs': set,'user':tempUser}), 200) # turn set into json and return it
		else:	# If user is not logged in
			return make_response(jsonify(response), 403) # turn set into json and return it

	# POST: Create a new song resource and upload to the database
	# curl -i -H "Content-Type: application/json" -X POST -d '{"songTitle": "Deja vu", "youTubeURL": "https://www.youtube.com/watch?v=OIjPwzL_5Yk"}' -b cookie-jar -k https://info3103.cs.unb.ca:43426/signin/songs
	def post(self):
		working = False
		if not request.json or not 'songTitle' in request.json:
			abort(400)

		if 'username' in session:
			user = str(session['username'])
			cUserID = session['username']
			cSongTitle = request.json['songTitle'];
			cYouTubeURL = request.json['youTubeURL'];
			print 'User is: ' + user
			print 'Songtitle is: ' + cSongTitle
			print 'URL is: ' + cYouTubeURL
			try:
				connection = MySQLdb.connect(host=settings.MYSQL_HOST,user=settings.MYSQL_USER,passwd=settings.MYSQL_PASSWD,db=settings.MYSQL_DB, use_unicode=True, charset='utf8')
				cursor = connection.cursor()
				cursor.callproc('createSong', (cUserID, cSongTitle, cYouTubeURL))
				connection.commit()
				response = {'status': 'success'}
				responseCode = 201
				working = True
			except:
				abort(500)
		else:
			responseFail = {'status': 'Not logged inn'}
			responseCode = 403

		if working is True:
			cursor.close()
			connection.close()
			return make_response(jsonify(response), 201)
		else:
			return make_response(jsonify(responseFail))

class userSongs(Resource):
	# GET: Return identified song
	# curl -i -H "Content-Type: application/json" -X GET -b cookie-jar -k https://info3103.cs.unb.ca:43426/signin/songs/user
	def get(self, userID):
		working = False
		if 'username' in session:
			try:
				connection = MySQLdb.connect(host=settings.MYSQL_HOST,user=settings.MYSQL_USER,passwd=settings.MYSQL_PASSWD,db=settings.MYSQL_DB, use_unicode=True, charset='utf8')
				cursor = connection.cursor(MySQLdb.cursors.DictCursor)

				cursor.callproc('getSong',[userID])
				row = cursor.fetchall()
				working = True
			except:
				abort(404)
		else:
			responseDeny = {'status': 'Not logged in'}
			responseCode = 403

		if working is True:
			cursor.close()
			connection.close()
			return make_response(jsonify({'songs': row}), 200)
		else:
			return make_response(jsonify(responseFail), 400)

	###########################################
	# DELETE DOES NOT WORK
	###########################################
	# DELETE: Delete a song specified by the songTitle. User can only delete his own song
	# curl -i -H "Content-Type: application/json" -X DELETE -d '{"songTitle":"supper"}' -b cookie-jar -k https://info3103.cs.unb.ca:43426/signin/songs/user
	# def delete(self, userID):
	# 	working = False
	# 	print userID
	# 	if 'username' in session:
	# 		try:
	# 			connection = MySQLdb.connect(host=settings.MYSQL_HOST,user=settings.MYSQL_USER,passwd=settings.MYSQL_PASSWD,db=settings.MYSQL_DB, use_unicode=True, charset='utf8')
	# 			cursor = connection.cursor(MySQLdb.cursors.DictCursor)
	# 			cSongTitle = request.json['songTitle']
	# 			print cSongTitle
	# 			cursor.callproc('deleteSong',(userID, cSongTitle))
	# 			print 'YOU DID IT'
	# 			connection.commit()
	# 			working = True
	# 		except:
	# 			abort(404) # Resource not found
	# 	else:
	# 		responseDeny = {'status':'Not logged in'}
	# 		responseCode = 403
	#
	# 	if working is True:
	# 		cursor.close()
	# 		connection.close()
	# 		return make_response(jsonify("Resource deleted!"), 204)
	# 	else:
	# 		return make_response(jsonify("Didn't work :("))

	# PUT: User can update a song uploaded by them
	# curl -i -H "Content-Type: application/json" -X PUT -d '{"songTitle":"Deja vu", "youTubeURL":"https://www.youtube.com/watch?v=OIjPwzL_5Yk"}' -b cookie-jar -k https://info3103.cs.unb.ca:43426/signin/songs/user
	def put(self, userID):
		working = False
		responseFail = {'status':'Failed'}
		if 'username' in session:
			try:
				connection = MySQLdb.connect(host=settings.MYSQL_HOST,user=settings.MYSQL_USER,passwd=settings.MYSQL_PASSWD,db=settings.MYSQL_DB, use_unicode=True, charset='utf8')
				cursor = connection.cursor(MySQLdb.cursors.DictCursor)
				cSongTitle = request.json['songTitle']
				cYouTubeURL = request.json['youTubeURL']
				cursor.callproc('updateSong',(userID, cSongTitle, cYouTubeURL)) # stored procedure, with argument
				connection.commit()
				response = {'status':'success'}
				working = True
			except:
				# 	Things messed up
				abort(404) # Resource not found
		else:
			responseDeny = {'status': 'Not logged in'}
			responseCode = 403

		if working is True:
			cursor.close()
			connection.close()
			return make_response(jsonify(response), 200)
		else:
			return make_response(jsonify(responseFail), 400)

############################################################################################
# Identify/create endpoints and endpoint objects

api = Api(app)
api.add_resource(signIn, '/signin')
api.add_resource(songs, '/signin/songs')
api.add_resource(userSongs, '/signin/songs/<string:userID>')
api.add_resource(Root, '/')

if __name__ == "__main__":
	context = ('cert.pem', 'key.pem') # Identify the certificates you've generated.
    	app.run(host=settings.APP_HOST, port=settings.APP_PORT, debug=settings.APP_DEBUG, ssl_context=context)
