import json
from re import A
import db
from flask import Flask
from flask import request
from datetime import datetime

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
@app.route("/api/users/<int:user_id>/")
def get_user(user_id):
    # Get the user from database.
    user = DB.get_user(user_id)
    # Check the type of user, if None, report 404 not found error.
    if user is None:
        return failure_response("User not found!", 404)
    # If user is found, return user's info in a dict object with the status code of 200.
    return success_response(user, 200)

# Delete a specific user.
@app.route("/api/users/<int:user_id>/", methods=["DELETE"])
def delete_user(user_id):
    # Check whether database has the specific user. 
    user = DB.get_user(user_id)
    # If user exists, delete it.
    if user is not None:
        DB.delete_user(user_id)
        return success_response(user, 200)
    # If not found, return 404 not found error.
    return failure_response("User not found!")

# Create a transaction by sending or requesting money.
@app.route("/api/transactions/", methods=["POST"])
def create_transaction():
    # Get body info of the request.
    body = json.loads(request.data)
    # Check to ensure body is not None.
    if body is None:
        failure_response("Post not found!")
    # Get sender_id, receiver_id, amount, message and accepted field from the request.
    sender_id = body.get("sender_id")
    receiver_id = body.get("receiver_id")
    amount = body.get("amount")
    message = body.get("message")
    accepted = body.get("accepted")

    # all of the above info are required, if missing any of them, report 400 bad request error.
    if sender_id is None or receiver_id is None or amount is None or message is None:
        return failure_response("Requied information missing!", 400)
    # If type of name or username is not str, or if type of balance is not integer, report 400 bad request error.
    if type(sender_id) is not int or type(receiver_id) is not int or type(amount) is not int or type(message) is not str or (accepted is not None and type(accepted) is not bool):
        return failure_response("Incorrect input type!", 400)
    # Get users by sender_id and receiver_id.
    sender = DB.get_user(sender_id)
    receiver = DB.get_user(receiver_id)
    # If any user doesn't exist, return 404 not found error.
    if sender is None or receiver is None:
        return failure_response("User not found!")
    
    # If accepted field is true, carry out transaction process.
    if accepted:
        # Check the amount is not larger than sender's balance. If amount exceeds sender's balance, return 403 request forbidden error.
        sender_balance = sender["balance"]
        receiver_balance = receiver["balance"]
        if amount > sender_balance:
            return failure_response("Sender overdraw balance!", 403)
        # Extra check:
        # If amount is negative, it is same as receiver send money to sender.
        if amount < -receiver_balance:
            return failure_response("Receiver overdraw balance!", 403)
        # If every check is passed, execute the transfer process.
        # Calculate new balance of sender and receiver.
        sender_balance_after = sender_balance - amount
        receiver_balance_after = receiver_balance + amount
        # Update user's balance in database.
        DB.update_user_balance(sender_id, sender_balance_after)
        DB.update_user_balance(receiver_id, receiver_balance_after)

    # Get current time.
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    # Pass inputs into the database.
    transaction_id = DB.create_transaction(timestamp, sender_id, receiver_id, amount, message, accepted)
    # If the creation fails, report 500 error.
    transaction = DB.get_transaction(transaction_id)
    if transaction is None:
        return failure_response("Database error!", 500)
    # If everything is OK, report 201 success post.
    return success_response(transaction, 201)

# Accept or deny a payment request.
@app.route("/api/transactions/<int:transaction_id>/", methods=["POST"])
def process_transaction(transaction_id):
    # Get body info of the request.
    body = json.loads(request.data)
    # Check to ensure body is not None.
    if body is None:
        failure_response("Post not found!")
    # Get accepted field from the request.
    accepted = body.get("accepted")
    # accepted field is required, if it's missing, report 400 bad request error.
    if accepted is None:
        return failure_response("Requied information missing!", 400)
    # If type of accepted field is not bool, report 400 bad request error.
    if type(accepted) is not bool:
        return failure_response("Incorrect input type!", 400)

    # Get transaction info by transaction_id.
    transaction = DB.get_transaction(transaction_id)
    # If transaction is None, report 404 not found error.
    if transaction is None:
        return failure_response("Transaction not found!")
    # If accepted field of original transaction is true or false, report 403 forbidden error.
    if transaction["accepted"] is not None:
        return failure_response("Transaction has been accepted/denied!", 403)
    # If transaction has not been processed (its accepted field is neither true nor false), process the transaction based on user's input.
    if accepted:
        # If user accepts the transaction request,
        # check the amount is not larger than sender's balance. If amount exceeds sender's balance, return 400 bad request error.
        sender_id = transaction["sender_id"]
        sender = DB.get_user(sender_id)
        receiver_id = transaction["receiver_id"]
        receiver = DB.get_user(receiver_id)
        # If either user is not found, report 404 not found error.
        if sender is None or receiver is None:
            return failure_response("User not found!")
        sender_balance = sender["balance"]
        receiver_balance = receiver["balance"]
        # Get the transaction amount.
        amount = transaction["amount"]
        if amount > sender_balance:
            return failure_response("Sender overdraw balance!", 403)
        # Extra check:
        # If amount is negative, it is same as receiver send money to sender.
        if amount < -receiver_balance:
            return failure_response("Receiver overdraw balance!", 403)
        # If every check is passed, execute the transfer process.
        # Calculate new balance of sender and receiver.
        sender_balance_after = sender_balance - amount
        receiver_balance_after = receiver_balance + amount
        # Update user's balance in database.
        DB.update_user_balance(sender_id, sender_balance_after)
        DB.update_user_balance(receiver_id, receiver_balance_after)

    # Get current time.
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    # Update transaction's accepted field.
    DB.update_transaction_accepted(transaction_id, timestamp, accepted)
    # Get updated transaction info.
    transaction = DB.get_transaction(transaction_id)
    # If transaction is not found, report 500 server error.
    if transaction is None:
        return failure_response("Database error!", 500)
    # If everything is OK, return 200 success post.
    return success_response(transaction)

    
"""
Routes end here.
"""

"""
Extra routes start here.
"""

"""
Extra routes end here.
"""

"""
Main function.
"""
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
