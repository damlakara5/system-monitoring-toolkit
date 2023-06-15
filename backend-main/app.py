from flask import Flask, jsonify
from flask import request
from flask_mysqldb import MySQL
from flask_cors import CORS
import jwt
import datetime
import json
import hashlib


app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'sammy'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'monitorProject'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
jwt_secret="mysupersecretsecretkey"
client_access_key = "second_public_key"

@app.route('/')
def hello_world():
    return 'Hello, World!'


def client_protected(accessKey):

    if accessKey == client_access_key:
        return True
    else:
        return False




def panel_protected(token):
    # Get the JWT token from the authorization header

    try:
        # Decode the JWT token using the secret key
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])

        # If the token is valid, return a success response
        return True
    except jwt.exceptions.DecodeError:
        # If the token is invalid, return an error response
        return False

def check_hostname(hostname):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT EXISTS(SELECT 1 FROM statistics WHERE hostname = %s)", [hostname])
    result = cursor.fetchone()
    cursor.close()

    if len(result) >= 1:
        return True
    else:
        return False



#test endpointi
@app.route('/test')
def test():
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    if panel_protected(token):
        return 'Hello, World!'
    else:
        return "Unauthorized"
    

@app.route("/showStatistics", methods=['GET'])
def show_statistics():
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    if panel_protected(token):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM statistics")
        rows = cursor.fetchall()
        print(rows)
        cursor.close()
         # Convert the data to a list of dictionaries
        data = []
        for row in rows:
            data.append(row)  # Assuming the dictionary is the first element in the tuple
            #data.append({'hostname': row[0], 'cpu_usage': row[1], 'ram_usage': row[2], 'storage_usage': row[3]})  # Adjust this according to your table structure
    # Return the data as JSON
        return json.dumps(data)
    return "Unauthorized", 401


@app.route("/showStatistics/<name>", methods=['GET'])
def showStats(name):
    print(type(name))
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    if panel_protected(token):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM statistics where hostname=%s", [name])
        rows = cursor.fetchall()
        cursor.close()
         # Convert the data to a list of dictionaries
        data = []
        for row in rows:
            data.append(row)  # Assuming the dictionary is the first element in the tuple
            #data.append({'hostname': row[0], 'cpu_usage': row[1], 'ram_usage': row[2], 'storage_usage': row[3]})  # Adjust this according to your table structure
    # Return the data as JSON
        return json.dumps(data)
    return "Unauthorized", 401


@app.route("/get/command/<name>", methods=['GET'])
def getCommand(name):
    accessKey = request.headers['x-access-key']

    if client_protected(accessKey):
        if check_hostname(name):
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT command FROM statistics where hostname=%s", [name])
            row = cursor.fetchone()
            cursor.close()
            return row
        else:
            print("I'm not an existed hosts")
            return "Unauthorized", 401
         # Convert the data to a list of dictionaries
        
    return "Unauthorized", 401


@app.route("/insertStatistics", methods=['POST'])
def register_client():
    accessKey = request.headers['x-access-key']
    if client_protected(accessKey):
        if request.method == 'POST':
            data = request.get_json()
            hostname = data['host_name']
            if check_hostname(hostname) == False:
                cpu_usage = data['cpu_usage']
                storage_usage = data['storage_usage']
                ram_usage = data['ram_usage']
                command_output = data['command_output']
                kernel_version = data['kernel_version']
                running_services = data['running_services']
                last_reboot_time = data['last_reboot_time']
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO statistics (hostname, cpu_usage, storage_usage, ram_usage,kernel_version, running_services, last_reboot_time, command_result) VALUES (%s, %s, %s, %s, %s, %s, %s,%s)", (hostname, cpu_usage, storage_usage, ram_usage, kernel_version, running_services,last_reboot_time, command_output))
                mysql.connection.commit()
                cur.close()
            else:
                cpu_usage = data['cpu_usage']
                storage_usage = data['storage_usage']
                ram_usage = data['ram_usage']
                command_output = data['command_output']
                kernel_version = data['kernel_version']
                running_services = data['running_services']
                last_reboot_time = data['last_reboot_time']
                cur = mysql.connection.cursor()
                cur.execute("UPDATE statistics set cpu_usage=%s, storage_usage=%s, ram_usage=%s, kernel_version=%s, running_services=%s,last_reboot_time=%s, command_result=%s where hostname=%s", ( cpu_usage, storage_usage, ram_usage, kernel_version, running_services, last_reboot_time, command_output, hostname))
                mysql.connection.commit()
                cur.close()
            return "OK",200
    else:
        return "Unauthorized",401
    


@app.route("/insertCommand", methods=['POST'])
def set_command():
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    if panel_protected(token):
        if request.method == 'POST':
            data = request.get_json()
            hostname = data['hostname']
            command = data['command']
            if check_hostname(hostname):
                cur = mysql.connection.cursor()
                cur.execute("UPDATE statistics set command=%s, command_result='' where hostname=%s", ( command, hostname))
                mysql.connection.commit()
                cur.close()
                return "OK",200
            else:
                return "Host does not exists",404
        else:
            return "Method not allowed", 401
    else:
        return "Unauthorized",401
    
@app.route('/reset_password', methods=['POST'])
def reset_password():
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    if panel_protected(token):
        if request.method == 'POST':
            username = request.json.get('username')
            old_password = request.json.get('old_password')
            new_password = request.json.get('new_password')

            cur = mysql.connection.cursor()
            cur.execute("SELECT password FROM users WHERE username = %s", (username,))
            user = cur.fetchone()

            if user:
                if user['password'] == hashlib.md5(old_password.encode()).hexdigest():
                    # Reset the password
                    cur.execute("UPDATE users SET password = MD5(%s) WHERE username = %s",
                                (new_password, username))
                    mysql.connection.commit()
                    cur.close()
                    return "Password reset successfully!"
                else:
                    return "Invalid old password."
            else:
                return "Invalid username."
    else:
        return "Unauthorized",401




@app.route('/login', methods=['POST'])
def login():
    # Get the username and password from the request body
    username = request.json.get('username')
    password = request.json.get('password')

    # Check if the username and password are correct
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s AND password = MD5(%s)", (username, password))
    user = cur.fetchone()

    if user:

        # Generate a JWT token with the user's username
        payload = {'username': username}
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
      

        return token
    else:
        return jsonify({'error': 'Invalid username or password'}), 401


if __name__ == '__main__':
    app.run()
