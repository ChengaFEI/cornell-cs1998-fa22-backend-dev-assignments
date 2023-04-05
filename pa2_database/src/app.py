import json
from flask import Flask, request
import db
import hashlib
import os

# Initialize database connection.
DB = db.DatabaseDriver()

app = Flask(__name__)

"""
Support functions start here.
"""

"""
Simplify the success response output process.
Requires:
    body -- dict object with structured user info (id, name, username)
    code -- integer with the status code, default value is 200 (success request)
Returns:
    body contents -- json file
    code -- integer
"""
def success_response(body, code=200):
    return json.dumps(body), code

"""
Support function:
Simplify the failure response output process.
Requires:
    message -- string object with specific error
    code -- integer with the status code, default value is 404 (not found error)
Returns:
    error -- json file 
    code -- integer
"""
def failure_response(message, code=404):
    return json.dumps({"error": message}), code

"""
Support functions end here.
"""

"""
Routes start here.
"""
# Greet.
@app.route("/")
def hello_world():
    return "Hello world!"

# Get all users.
@app.route("/api/users/")
def get_users():
    return success_response({"users": DB.get_users()})

# Create a new user.
@app.route("/api/users/", methods=["POST"])
def create_user():
    # Get body info of the request.
    body = json.loads(request.data)
    # Check to ensure body is not None.
    if body is None:
        failure_response("Post not found!")
    # Get name, username, balance from the request.
    # If not specified, default balance as 0.
    name = body.get("name")
    username = body.get("username")
    balance = body.get("balance", 0)

    # name and username is required, if missing any of them, report 400 bad request error.
    if name is None or username is None:
        return failure_response("Requied information missing!", 400)
    # If type of name or username is not str, or if type of balance is not integer, report 400 bad request error.
    if type(name) is not str or type(username) is not str or type(balance) is not int:
        return failure_response("Incorrect input type!", 400)
    
    # Pass inputs into the database.
    user_id = DB.create_user(name, username, balance)

    # If the creation fails, report 500 error.
    user = DB.get_user(user_id)
    if user is None:
        return failure_response("Database error!", 500)
    # If everything is OK, report 201 success post.
    return success_response(user, 201)

# Get a specific user.
@app.route("/api/user/<int:user_id>/")
def get_user(user_id):
    # Get the user from database.
    user = DB.get_user(user_id)
    # Check the type of user, if None, report 404 not found error.
    if user is None:
        return failure_response("User not found!", 404)
    # If user is found, return user's info in a dict object with the status code of 200.
    return success_response(user, 200)

# Delete a specific user.
@app.route("/api/user/<int:user_id>/", methods=["DELETE"])
def delete_user(user_id):
    # Check whether database has the specific user. 
    user = DB.get_user(user_id)
    # If user exists, delete it.
    if user is not None:
        DB.delete_user(user_id)
        return success_response(user, 200)
    # If not found, return 404 not found error.
    return failure_response("User not found!")

# Send money from one user to another.
@app.route("/api/send/", methods=["POST"])
def transfer_money():
    # Get the body info of the request.
    body = json.loads(request.data)
    # Check to ensure body is not None.
    if body is None:
        failure_response("Post not found!")
    # Get specific request info.
    sender_id = body.get("sender_id")
    receiver_id = body.get("receiver_id")
    amount = body.get("amount")
    # Check all request info are not None.
    if sender_id is None or receiver_id is None or amount is None:
        return failure_response("Required Information missing!", 400)
    # Check the type of all request info. If any of them is not an integer, return 400 bad request error.
    if type(sender_id) is not int or type(receiver_id) is not int or type(amount) is not int:
        return failure_response("Incorrect information type! (integer required)", 400)
    # Get users by sender_id and receiver_id.
    sender = DB.get_user(sender_id)
    receiver = DB.get_user(receiver_id)
    # If any user doesn't exist, return 404 not found error.
    if sender is None or receiver is None:
        return failure_response("User not found!")
    # Check the amount is not larger than sender's balance. If amount exceeds sender's balance, return 400 bad request error.
    sender_balance = sender["balance"]
    receiver_balance = receiver["balance"]
    if amount > sender_balance:
        return failure_response("Sender overdraw balance!", 400)
    # Extra check:
    # If amount is negative, it is same as receiver send money to sender.
    if amount < -receiver_balance:
        return failure_response("Receiver overdraw balance!", 400)
    # If every check is passed, execute the transfer process.
    # Calculate new balance of sender and receiver.
    sender_balance_after = sender_balance - amount
    receiver_balance_after = receiver_balance + amount
    # Update user's balance in database.
    DB.update_user_balance(sender_id, sender_balance_after)
    DB.update_user_balance(receiver_id, receiver_balance_after)
    return success_response(body)

"""
Routes end here.
"""

"""
Extra routes start here.
"""

# Create a user with authorization.
@app.route("/api/extra/users/", methods=["POST"])
def create_user_with_auth():
    # Get dict object with all request info from the request.
    body = json.loads(request.data)
    # Check to ensure body is not None.
    if body is None:
        failure_response("Post not found!")
    # Get specific request info.
    # If balance is not specified, default it to 0.
    name = body.get("name")
    username = body.get("username")
    balance = body.get("balance", 0)
    password = body.get("password")

    # name, username and password are required, if missing any of them, report 400 bad request error.
    if name is None or username is None or password is None:
        return failure_response("Requied information missing!", 400)
    # If type of name or username or password is not str, or if type of balance is not integer, report 400 bad request error.
    if type(name) is not str or type(username) is not str or type(balance) is not int or type(password) is not str:
        return failure_response("Incorrect input type!", 400)
    # If password is empty / length of password is 0.
    if len(password) < 1:
        return failure_response("Password can't be empty!", 400)
    
    # Hash password.
    sha512 = hashlib.sha512()
    # Password salting.
    salted_password = password + os.environ.get("PASSWORD_SALT")
    # Iterative hashing.
    iterations = os.environ.get("NUMBER_OF_ITERATIONS")
    for i in range(int(iterations)):
        sha512.update(salted_password.encode("utf-8"))
        salted_password = sha512.hexdigest()

    # Pass inputs into the database.
    user_id = DB.create_user_withpassword(name, username, balance, sha512.hexdigest())
    # If the creation fails, report 500 error.
    user = DB.get_user(user_id)
    if user is None:
        return failure_response("Database error!", 500)
    # If everything is OK, report 201 success post.
    user_withpassword = {
        "id": user["id"],
        "name": user["name"],
        "username": user["username"],
        "balance": user["balance"],
        "password": password
    }
    return success_response(user_withpassword, 201)

# Get a user by id with authorization.
@app.route("/api/extra/user/<int:user_id>/", methods=["POST"])
def get_user_with_auth(user_id):
    # Get dict object with all request info from request.
    body = json.loads(request.data)
    # Check to ensure body is not None.
    if body is None:
        failure_response("Post not found!")
    # Get specific request info: entered password.
    password = body.get("password")
    # Get user by id from database.
    user = DB.get_user_withpassword(user_id)

    # Check whether user exists, if not, report 404 not found error.
    if user is None:
        return failure_response("User not found!")

    # If user exists, check the authorization.
    # Case 0: user has no password / password not needed.
    user_password = user.get("password")
    if user_password is None:
        return success_response(user)
    # If user has password.
    # Case 1: no password sent.
    if password is None:
        return failure_response("Password missing!", 401)
    # Case 2: incorrect password type.
    if type(password) is not str:
        return failure_response("Incorrect password type! (string required)", 401)
    # Case 3: password sent is incorrect.
    # Encode sent password.
    sha512 = hashlib.sha512()
    # Password salting.
    salted_password = password + os.environ.get("PASSWORD_SALT") # string
    iterations = os.environ.get("NUMBER_OF_ITERATIONS")
    for i in range(int(iterations)):
        sha512.update(salted_password.encode("utf-8"))
        salted_password = sha512.hexdigest()
    if sha512.hexdigest() != user_password:
        return failure_response("Password incorrect!", 401)
    # If password is perfectly correct, return the requested user with password.
    user_with_original_password = {
        "id": user["id"],
        "name": user["name"],
        "username": user["username"],
        "balance": user["balance"],
        "password": password
    }
    return success_response(user_with_original_password)

# Transfer money with authorization.
@app.route("/api/extra/send/", methods=["POST"])
def transfer_money_with_auth():
    # Get the body info of the request.
    body = json.loads(request.data)
    # Check to ensure body is not None.
    if body is None:
        failure_response("Post not found!")
    # Get specific request info.
    sender_id = body.get("sender_id")
    receiver_id = body.get("receiver_id")
    amount = body.get("amount")
    password = body.get("password")

    # Check all request info are not None.
    if sender_id is None or receiver_id is None or amount is None:
        return failure_response("Required Information missing!", 400)
    # Check the type of all request info. If any of them is not an integer, return 400 bad request error.
    if type(sender_id) is not int or type(receiver_id) is not int or type(amount) is not int:
        return failure_response("Incorrect information type! (integer required)", 400)
    # Get users by sender_id and receiver_id.
    sender = DB.get_user_withpassword(sender_id)
    receiver = DB.get_user(receiver_id)
    # If any user doesn't exist, return 404 not found error.
    if sender is None or receiver is None:
        return failure_response("User not found!")
    
    # Check the authorization.
    user_password = sender.get("password")
    if user_password is not None:
        # If user has password.
        # Case 1: no password sent.
        if password is None:
            return failure_response("Password missing!", 401)
        # Case 2: incorrect password type.
        if type(password) is not str:
            return failure_response("Incorrect password type! (string required)", 401)
        # Case 3: password sent is incorrect.
        # Encode sent password
        sha512 = hashlib.sha512()
        # Password salting.
        salted_password = password + os.environ.get("PASSWORD_SALT") # string
        # Iterative hashing.
        iterations = os.environ.get("NUMBER_OF_ITERATIONS")
        for i in range(int(iterations)):
            sha512.update(salted_password.encode("utf-8"))
            salted_password = sha512.hexdigest()
        if sha512.hexdigest() != user_password:
            return failure_response("Password incorrect!", 401)
    
    # Check the amount is not larger than sender's balance. If amount exceeds sender's balance, return 400 bad request error.
    sender_balance = sender["balance"]
    receiver_balance = receiver["balance"]
    if amount > sender_balance:
        return failure_response("Sender overdraw balance!", 400)
    # Extra check:
    # If amount is negative, it is same as receiver send money to sender.
    if amount < -receiver_balance:
        return failure_response("Receiver overdraw balance!", 400)
    # If every check is passed, execute the transfer process.
    # Calculate new balance of sender and receiver.
    sender_balance_after = sender_balance - amount
    receiver_balance_after = receiver_balance + amount
    # Update user's balance in database.
    DB.update_user_balance(sender_id, sender_balance_after)
    DB.update_user_balance(receiver_id, receiver_balance_after)
    return success_response(body)

"""
Extra routes end here.
"""

"""
Main function.
"""
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)