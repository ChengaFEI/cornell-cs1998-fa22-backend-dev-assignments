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
    Database driver for the Task app.
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
    
    # Create a new user with id (autoincremented), name, username and balance
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

    # Get a specific user's id, name, username and balance by id.
    def get_user(self, user_id):
        # cursor object with selected user's info.
        cursor = self.conn.execute(
            """
            SELECT * FROM user
            WHERE id = ?;
            """,
            (user_id, )
        ) 
        # Loop through users
        for row in cursor:
            # If specific user is found, return info in the dict object.
            return {
                "id": row[0],
                "name": row[1],
                "username": row[2],
                "balance": row[3]
            }
        # If no such user, return None.
        return None

    # Delete a specific user by id.
    # Requires: only call this function after checking user is in database.
    def delete_user(self, user_id):
        # cursor object with specific user (maybe not found) from the database by id.
        cursor = self.conn.execute(
            """
            DELETE FROM user WHERE id = ?;
            """,
            (user_id, )
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

    """
    Extra functions start here.
    For authorized request in optional challenges.
    """

    # Create a new user with password.
    def create_user_withpassword(self, name, username, balance, password):
        cursor = self.conn.execute(
            """
            INSERT INTO user (name, username, balance, password)
            VALUES (?, ?, ?, ?)
            """,
            (name, username, balance, password)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    # Get user by id with password.
    def get_user_withpassword(self, user_id):
        # cursor object with entries of the user's info from database.
        cursor = self.conn.execute(
            """
            SELECT * FROM user
            WHERE id = ?;
            """,
            (user_id, )
        )
        # Loop over entry of user with proper id.
        for row in cursor:
            # If user exists, return the dict object with id, name, username, balance and password.
            return {
                "id": row[0],
                "name": row[1],
                "username": row[2],
                "balance": row[3],
                "password": row[4]
            }
        # if no user is found, return None.
        return None

    """
    Extra functions end here.
    """