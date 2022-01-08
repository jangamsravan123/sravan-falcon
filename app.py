from wsgiref.simple_server import make_server
import falcon
import json
import sqlite3
import uuid
import time
import bcrypt
from contextlib import closing

sql_hostname = "localhost"
sql_username = "root"
sql_password = "Sravan123@"
sql_dbname = "mydb"
#salt = "5325795$6579349&".encode("utf-8")

class User :
	def __init__(self, user_id, username, password, session_id, session_time) :
		self.user_id = user_id
		self.username = username
		self.password = password
		self.token = token
		self.token_time = token_time


class Register :
	def on_post(self, req, resp) :
		resp.status = falcon.HTTP_200
		credentials = req.media
		user_id = int(credentials["user_id"])
		username = credentials["username"]
		password = credentials["password"]
		valid_user_params(username, password)
		password = password.encode("utf-8")
		salt = bcrypt.gensalt(5)
		password = bcrypt.hashpw(password, salt).decode("utf-8")
		salt = salt.decode("utf-8")
		token = "55558058dggg2335215365"
		token_time = 4567373
		query = "insert into users values({}, '{}','{}', '{}', {}, '{}')".format(user_id, username, password, token, token_time, salt)
		mysql_action(query, "registration")
		resp.body = json.dumps({"registration" : "successfully registered"})


class Login :
	def on_post(self, req, resp) :
		resp.status = falcon.HTTP_200
		credentials = req.media
		username = credentials["username"]
		password = credentials["password"]
		valid_user_params(username, password)
		entered_password = password.encode("utf-8")
		query = "select * from users"
		cur = mysql_action(query, "login")
		global logged_in
		for user in cur :
			actual_password = user[2].encode("utf-8")
			salt = user[5].encode("utf-8")
			user_hash = bcrypt.hashpw(entered_password, salt)
			actual_hash = bcrypt.hashpw(actual_password, salt)
			valid_pwd = bcrypt.checkpw(user_hash, actual_hash)
			if(user[1] == username and valid_pwd) :
				token = uuid.uuid4().hex
				token_time = time.time()
				query = "update users set token = '{}' , token_time = {} where id = {} ".format(token, token_time, user[0])
				mysql_action(query, "login")
				resp.set_header("token", token)
				logged_in = True
				break
		else :
			raise falcon.HTTPUnauthorized(title='Login failed', description="Invalid username or password")
		resp.body = json.dumps({"login" : "logged in successfully"})


class Logout :
	def on_get(self, req, resp) :
		resp.status = falcon.HTTP_200
		global logged_in
		logged_in = False
		resp.body = json.dumps({"logout" : "logged out successfully"})


class Employee :
	def __init__(self, emp_id, emp_name, emp_salary, emp_address, emp_designation) :
		self.emp_id = emp_id
		self.emp_name = emp_name
		self.emp_salary = emp_salary
		self.emp_designation = emp_designation
		self.emp_address = emp_address


class EmployeeAction :
	def on_get(self, req, resp, id) :
		login(req, resp)
		resp.status = falcon.HTTP_200
		query = "select * from employees where id={};".format(id)
		cur = mysql_action(query, "fetch employee details")
		data = json.dumps({"employee" : {}})
		for emp in cur :
			e_dict = { 
			"emp_id" : emp[0],
			"emp_name" :  emp[1],
			"emp_salary" : emp[2],
			"emp_address" : emp[3],
			"emp_designation" : emp[4]
			}
			data = json.dumps({"employee" : e_dict})
			break
		else :
			raise falcon.HTTPBadRequest(title="Bad request", description = "Employee with {} does not exist".format(id))

		resp.body = data

	def on_put(self, req, resp, id) :
		login(req, resp)
		resp.status = falcon.HTTP_200 
		data = req.media
		emp_id = data["id"]
		emp_name = data["name"]
		emp_salary = data["salary"]
		emp_designation = data["designation"]
		emp_address = data["address"]
		query = "update employees set name = '{}', salary = {}, address = '{}', designation = '{}' where id = {};".format(emp_name, emp_salary, emp_address, emp_designation, emp_id)
		mysql_action(query, "update employee")
		resp.body = json.dumps(data)

	def on_delete(self, req, resp, id) :
		login(req, resp)
		resp.status = falcon.HTTP_200
		query = "select * from employees where id={};".format(id)
		cur = mysql_action(query, "delete employee")
		data = json.dumps({"employee" : {}})
		for emp in cur :
			e_dict = { 
			"emp_id" : emp[0],
			"emp_name" :  emp[1],
			"emp_salary" : emp[2],
			"emp_address" : emp[3],
			"emp_designation" : emp[4]
			}
			data = json.dumps({"employee" :e_dict})
			break
		else :
			raise falcon.HTTPBadRequest(title="Bad request", description = "Employee with id {} does not exist".format(id))
		query = "delete from employees where id={};".format(id)
		mysql_action(query, "delete employee")
		resp.body = data


class EmployeesAction :
	def on_get(self, req, resp) :
		login(req, resp)
		resp.status = falcon.HTTP_200
		query = "select * from employees;"
		cur = mysql_action(query, "fetch employee details")
		emp_dict = []
		for emp in cur :
			e_dict = { 
			"emp_id" : emp[0],
			"emp_name" :  emp[1],
			"emp_salary" : emp[2],
			"emp_address" : emp[3],
			"emp_designation" : emp[4]
			}
			emp_dict.append(e_dict)
		resp.body = json.dumps({"employees" : emp_dict})

	def on_post(self, req, resp) :
		login(req, resp)
		resp.status = falcon.HTTP_200 
		data = req.media
		emp_id = data["id"]
		emp_name = data["name"]
		emp_salary = data["salary"]
		emp_designation = data["designation"]
		emp_address = data["address"]
		query = "insert into employees values ({},'{}',{},'{}','{}');".format(emp_id, emp_name, emp_salary, emp_address, emp_designation)
		mysql_action(query,"new employee creation")
		resp.body = json.dumps(data)


app = falcon.App()
app.add_route("/employees", EmployeesAction())
app.add_route("/employee/{id}", EmployeeAction())
app.add_route("/login", Login())
app.add_route("/register", Register())
app.add_route("/logout", Logout())

logged_in = False

def valid_user_params(username, password) :
	if(username == "" or password == "") :
		raise falcon.HTTPBadRequest(title="Invalid credentials", description = "username and password should not be empty")


def login(req, resp) :
	token = req.get_header("token")
	query = "select * from users;"
	cur = mysql_action(query, "Authorization")
	for user in cur :
		user_token = user[3]
		token_time = user[4]
		if(user_token == token) and int(token_time) + 60 > int(time.time()) :
			token_time = time.time()
			query = "update users set token_time = {} where id = {} ;".format(token_time, user[0])
			mysql_action(query, "Authorization")
			break
	else :
		raise falcon.HTTPUnauthorized(title='Login required', description="please do login")

query_users = """create table users (
		id INTEGER NOT NULL PRIMARY KEY, 
		username TEXT NOT NULL, 
		password TEXT NOT NULL, 
		token TEXT NULL, 
		token_time INTEGER NULL,
		salt TEXT NULL 
	)"""

query_employees = """create table employees (
		id INTEGER NOT NULL PRIMARY KEY, 
		name TEXT NOT NULL, 
		salary INTEGER NULL, 
		address TEXT NULL, 
		designation TEXT NULL 
	)"""

def mysql_action(query, msg) :
	try :
		connection = sqlite3.connect("test.db")
		cur = connection.cursor()
		cur.execute(query)
		data = []
		for user in cur :
			data.append(user)
		connection.commit()
		connection.close()
		return data
	except Exception as e :
		raise falcon.HTTPUnauthorized(title="Internal server error", description = msg + " failed")

mysql_action(query_users, "create users tables")
mysql_action(query_employees, "create employees table")

