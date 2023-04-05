import os
import sqlite3

# From: https://goo.gl/YzypOI
def singleton(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


class DatabaseDriver(object):
    """
    Database driver for the Venmo (Full) app.
    Handles with reading and writing data with the database.
    """

    # Constructor.
    def __init__(self):
        # Initialize the connection.
        self.conn = sqlite3.connect("venmo.db", check_same_thread=False)
        # Initialize the user table.
        self.create_user_table()
        # self.preload_user()
    
    # Create the table with user's id, name and username.
    def create_user_table(self):
        try:
            self.conn.execute(
                """
                CREATE TABLE user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    username TEXT NOT NULL,
                    balance INTEGER,
                    password CHAR(50)
                );
                """
            )
            self.conn.execute(
                """
                CREATE TABLE transfer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sender_id INTEGER SECONDARY KEY NOT NULL,
                    receiver_id INTEGER SECONDARY KEY NOT NULL,
                    amount INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    accepted BOOLEAN
                );
                """
            )
        except Exception as e:
            print(e)
    
    # Preload some test user info.
    def preload_user(self):
        self.conn.execute(
            """
            INSERT INTO user (name, username, balance, password)
            VALUES ("Raahi Menon", "raahi014", 100, "asdig423mkl/.");
            """
        )
    
    # Get users' id, name and username, don't get users' balance.
    def get_users(self):
        # list object with users' id, name and username.
        users = []
        # cursor object with all entries of user info.
        cursor = self.conn.execute(
            """
            SELECT id, name, username FROM user;
            """
        )
        # Loop through entries of user info and append user info in "users".
        for row in cursor:
            users.append({
                "id": row[0],
                "name": row[1],
                "username": row[2]
            })
        return users
    
    # Create a new user with id (autoincremented), name, username and balance.
    def create_user(self, name, username, balance):
        cursor = self.conn.execute(
            """
            INSERT INTO user (name, username, balance)
            VALUES (?, ?, ?);
            """,
            (name, username, balance)
        )
        self.conn.commit()
        # Return the new user's id.
        return cursor.lastrowid

    # Get a specific user's id, name, username, balance and transactions by id.
    def get_user(self, user_id):
        # cursor object with selected user's info.
        cursor_user = self.conn.execute(
            """
            SELECT * FROM user
            WHERE id = ?;
            """,
            (user_id, )
        ) 
        # cursor object with selected user's transaction info.
        cursor_transfer = self.conn.execute(
            """
            SELECT * FROM transfer
            WHERE sender_id = ? OR receiver_id = ?;
            """,
            (user_id, user_id)
        )
        # Loop through users
        for row_user in cursor_user:
            # If specific user is found,
            # first extract user's transactions records in a list object,
            transactions = []
            for row_transfer in cursor_transfer:
                transactions.append(
                    {
                        "id": row_transfer[0],
                        "timestamp": row_transfer[1],
                        "sender_id": row_transfer[2],
                        "receiver_id": row_transfer[3],
                        "amount": row_transfer[4],
                        "message": row_transfer[5],
                        "accepted": row_transfer[6]
                    }
                )
            # then return user info in a dict object.
            return {
                "id": row_user[0],
                "name": row_user[1],
                "username": row_user[2],
                "balance": row_user[3],
                "transactions": transactions
            }
        # If no such user, return None.
        return None

    # Delete a specific user by id.
    # Requires: only call this function after checking user is in database.
    def delete_user(self, user_id):
        # cursor object with specific user's info (maybe not found) by id.
        cursor_user = self.conn.execute(
            """
            DELETE FROM user WHERE id = ?;
            """,
            (user_id, )
        )
        # cursor object with specific user's transaction info (maybe not found) by id.
        cursor_transfer = self.conn.execute(
            """
            DELETE FROM transfer WHERE sender_id = ? OR receiver_id = ?;
            """,
            (user_id, user_id)
        )
        self.conn.commit()

    # Update a specific user's balance.
    # Requires: only call this function after checking user is in database.
    def update_user_balance(self, user_id, balance):
        self.conn.execute(
            """
            UPDATE user SET balance = ?
            WHERE id = ?;
            """,
            (balance, user_id)
        )
        self.conn.commit()
    
    # Create a transaction with sender_id, receiver_id, amount, message and accepted field.
    def create_transaction(self, timestamp, sender_id, receiver_id, amount, message, accepted):
        cursor = self.conn.execute(
            """
            INSERT INTO transfer (timestamp, sender_id, receiver_id, amount, message, accepted)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (timestamp, sender_id, receiver_id, amount, message, accepted)
        )
        self.conn.commit()
        # Return the new transaction's id.
        return cursor.lastrowid

    # Get a specific transaction's id, timestamp, sender_id, receiver_id, amount, message and accepted field by id.
    def get_transaction(self, transaction_id):
        # cursor object with selected transaction's info.
        cursor = self.conn.execute(
            """
            SELECT * FROM transfer 
            WHERE id = ?;
            """,
            (transaction_id, )
        )
        # Loop over selected transaction.
        for row in cursor:
            # If specific transaction is found, return transaction info in a dict object.
            return {
                "id": row[0],
                "timestamp": row[1],
                "sender_id": row[2],
                "receiver_id": row[3],
                "amount": row[4],
                "message": row[5],
                "accepted": row[6]
            }
        # If no such transaction, return None.
        return None

    # Update a specific transaction's accepted field.
    # Requires: only call this function after checking transaction is in database.
    def update_transaction_accepted(self, transaction_id, timestamp, accepted):
        self.conn.execute(
            """
            UPDATE transfer SET timestamp = ?, accepted = ?
            WHERE id = ?;
            """,
            (timestamp, accepted, transaction_id)
        )
        self.conn.commit()

    """
    Extra functions start here.
    For authorized request in optional challenges.
    """
    
    """
    Extra functions end here.
    """

# Only <=1 instance of the database driver
# exists within the app at all times
DatabaseDriver = singleton(DatabaseDriver)