import json
from re import L
import sys
from threading import Thread
from time import sleep
import unittest
from datetime import datetime

from app import app
import requests

# NOTE: Make sure you run 'pip3 install requests' in your virtualenv

# Flag to run extra credit tests (if applicable)
EXTRA_CREDIT = False

# URL pointing to your local dev host
LOCAL_URL = "http://localhost:8000"

# Sample testing data
SAMPLE_USER = {"name": "Cornell AppDev", "username": "cornellappdev"}
SAMPLE_TRANSACTION = {"amount": 5, "message": "boba"}

# Request endpoint generators
USER_ROUTE = "/api/users"
TRANSACTION_ROUTE = "/api/transactions"
EXTRA_CREDIT_USER_ROUTE = "/api/extra/users"


# Request endpoint generators
def gen_users_route(user_id=None, extra=False):
    user_route = EXTRA_CREDIT_USER_ROUTE if extra else USER_ROUTE
    return (
        f"{user_route}/"
        if user_id is None
        else f"{user_route}/{str(user_id)}/"
    )


def gen_users_path(user_id=None, extra=False):
    return f"{LOCAL_URL}{gen_users_route(user_id, extra)}"


def gen_transactions_route(transaction_id=None):
    return (
        f"{TRANSACTION_ROUTE}/"
        if transaction_id is None
        else f"{TRANSACTION_ROUTE}/{str(transaction_id)}/"
    )


def gen_transactions_path(transaction_id=None):
    return f"{LOCAL_URL}{gen_transactions_route(transaction_id)}"


# Error Handlers
def error_str(str):
    return f"\033[91m{str}\033[0m"


def is_jsonable(res, req_type, route, body=None):
    postfix = "" if body is None else f"\n\nRequest Body:\n{body}"
    try:
        res.json().get("test")
        return True, ""
    except json.decoder.JSONDecodeError:
        err = f"\n{req_type} request to route '{route}' did not return a JSON response.\
            \nAre you sure you spelled the route correctly?\
            \nIs there an error in the route handling?\
            \nDid you remember to use json.dumps() on your response?\
            \nAre you accidentally returning a list/tuple instead of a dictionary?"
        err += postfix
        return False, error_str(err)
    except AttributeError:
        err = f"\n{req_type} request to route '{route}' did not return a dictionary response.\
            \nAre you accidentally returning a tuple or a list?\
            \nAre you accidentally returning nothing?"
        err += postfix
        return False, error_str(err)


def status_code_error(req_type, route, res_code, expected_code, body=None):
    err = f"\n{req_type} request to route '{route}' returned a status code of {res_code}, but {expected_code} was expected."
    return error_str(err)


def wrong_value_error(
    req_type, route, res_val, expected_val, value_name, body=None
):
    err = f"\n{req_type} request to route '{route}' returned an incorrect response of:\n{res_val}\nwhen we expected\n{expected_val}\nfor {value_name} value."
    return error_str(err)


# Transaction body generator
def gen_transaction_body(sender_id, receiver_id, accepted):
    return {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        **SAMPLE_TRANSACTION,
        "accepted": accepted,
    }


class TestRoutes(unittest.TestCase):
    def jsonable_test(self, res, req_type, route, status_code, body=None):
        jsonable, error = is_jsonable(res, req_type, route, body)
        self.assertTrue(jsonable, error)
        self.assertEqual(
            res.status_code,
            status_code,
            status_code_error(req_type, route, res.status_code, status_code),
        )

    # ---- USERS -----------------------------------------------------------

    def test_get_initial_users(self):
        req_type = "GET"
        route = gen_users_route()
        res = requests.get(gen_users_path())
        self.jsonable_test(res, req_type, route, 200)

        users = res.json().get("users")
        self.assertEqual(
            type(users),
            list,
            wrong_value_error(
                req_type, route, type(users), list, "type of users field"
            ),
        )

    def test_create_user(self):
        req_type = "POST"
        route = gen_users_route()
        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        self.jsonable_test(res, req_type, route, 201, SAMPLE_USER)
        user = res.json()
        for key in SAMPLE_USER.keys():
            self.assertEqual(
                user.get(key),
                SAMPLE_USER[key],
                wrong_value_error(
                    req_type,
                    route,
                    user.get(key),
                    SAMPLE_USER[key],
                    key,
                    SAMPLE_USER,
                ),
            )
        self.assertEqual(
            user.get("balance"),
            0,
            wrong_value_error(
                req_type, route, user.get("balance"), 0, "balance", SAMPLE_USER
            ),
        )
        self.assertEqual(
            type(user.get("transactions")),
            list,
            wrong_value_error(
                req_type, route, type(
                    user.get("transactions")), list, "type of transactions field"
            ),
        )

    def test_get_user(self):
        req_type = "POST"
        route = gen_users_route()
        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        jsonable, error = is_jsonable(res, req_type, route, SAMPLE_USER)
        self.assertTrue(
            jsonable,
            error_str(
                "Creating a user did not return a json response. See test_create_user for details."
            ),
        )
        user = res.json()
        self.assertTrue(
            user.get("id") is not None,
            error_str(
                "Returned user from POST to /api/users/ has no 'id' field!"
            ),
        )

        req_type = "GET"
        route = gen_users_route(user["id"])
        res = requests.get(gen_users_path(user["id"]))
        self.jsonable_test(res, req_type, route, 200)
        user = res.json()
        self.assertTrue(
            user.get("id") is not None,
            error_str(
                f"Returned user from GET request to {route} does not have an 'id' field!"
            ),
        )
        for key in SAMPLE_USER.keys():
            self.assertEqual(
                user.get(key),
                SAMPLE_USER[key],
                wrong_value_error(
                    req_type, route, user.get(key), SAMPLE_USER[key], key
                ),
            )
        self.assertEqual(
            user.get("balance"),
            0,
            wrong_value_error(
                req_type, route, user.get("balance"), 0, "balance"
            ),
        )

        self.assertEqual(
            type(user.get("transactions")),
            list,
            wrong_value_error(
                req_type, route, type(
                    user.get("transactions")), list, "type of transactions field"
            ),
        )

    def test_delete_user(self):
        req_type = "POST"
        route = gen_users_route()
        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        jsonable, error = is_jsonable(res, req_type, route, SAMPLE_USER)
        self.assertTrue(
            jsonable,
            error_str(
                "Creating a user did not return a json response. See test_create_user for details."
            ),
        )
        user = res.json()
        self.assertTrue(
            user.get("id") is not None,
            error_str(
                "Returned user from POST to /api/users/ has no 'id' field!"
            ),
        )

        user_id = user["id"]
        req_type = "DELETE"
        route = gen_users_path(user_id)
        res = requests.delete(gen_users_path(user_id))
        self.jsonable_test(res, req_type, route, 200)
        user = res.json()
        for key in SAMPLE_USER:
            self.assertEqual(
                user.get(key),
                SAMPLE_USER[key],
                wrong_value_error(
                    req_type, route, user.get(key), SAMPLE_USER[key], key
                ),
            )
        self.assertIsNotNone(
            user.get("balance")
        )
        self.assertEqual(
            type(user.get("transactions")),
            list,
            wrong_value_error(
                req_type, route, type(
                    user.get("transactions")), list, "type of transactions field"
            ),
        )

        req_type = "GET"
        route = gen_users_path(user_id)
        res = requests.get(gen_users_path(user_id))
        jsonable, error = is_jsonable(res, req_type, route)
        self.assertTrue(
            jsonable,
            error_str(
                "Getting a user by ID did not return a json response. See test_get_user for details."
            ),
        )
        self.assertEqual(
            res.status_code,
            404,
            error_str(
                "Trying to get a deleted user did not return a 404 status code."
            ),
        )

    def test_get_invalid_user(self):
        req_type = "GET"
        route = gen_users_path(1000)
        res = requests.get(gen_users_path(1000))
        self.jsonable_test(res, req_type, route, 404)

    def test_delete_invalid_user(self):
        req_type = "DELETE"
        route = gen_users_path(1000)
        res = requests.delete(gen_users_path(1000))
        self.jsonable_test(res, req_type, route, 404)

    # ---- TRANSACTIONS  ---------------------------------------------------

    def create_user_and_assert_balance(self, balance, extra=False):
        user_with_balance = {**SAMPLE_USER, "balance": balance}
        req_type = "POST"
        route = gen_users_route(extra=extra)
        res = requests.post(
            gen_users_path(extra=extra), data=json.dumps(user_with_balance)
        )
        self.jsonable_test(res, req_type, route, 201, user_with_balance)
        user_response = res.json()
        for key in user_with_balance.keys():
            self.assertEqual(
                user_response.get(key),
                user_with_balance[key],
                wrong_value_error(
                    req_type,
                    route,
                    user_response.get(key),
                    user_with_balance[key],
                    key,
                    user_with_balance,
                ),
            )
        self.assertEqual(
            user_response.get("balance"),
            balance,
            wrong_value_error(
                req_type,
                route,
                user_response.get("balance"),
                balance,
                "balance",
                user_with_balance,
            ),
        )
        return user_response

    def test_send_money(self):
        req_type = "POST"
        route = gen_transactions_route()

        user1 = self.create_user_and_assert_balance(10).get("id")
        user2 = self.create_user_and_assert_balance(10).get("id")
        transaction_body = gen_transaction_body(user1, user2, True)

        # Test if transaction body is right
        res = requests.post(gen_transactions_path(),
                            data=json.dumps(transaction_body))
        self.jsonable_test(res, req_type, route, 201, transaction_body)
        transaction = res.json()
        for key in transaction_body.keys():
            self.assertEqual(
                transaction.get(key),
                transaction_body[key],
                wrong_value_error(
                    req_type,
                    route,
                    transaction.get(key),
                    transaction_body[key],
                    key,
                    transaction_body[key]
                ),
            )
        self.assertEqual(
            type(transaction.get("timestamp")),
            str,
            wrong_value_error(
                req_type, route, type(transaction.get(
                    "timestamp")), str, "type of timestamp field"
            ),
        )

        # Test if sender balance is updated and if transaction outputs correctly in get_user
        res1 = requests.get(gen_users_path(user1)).json()
        balance = 10 - transaction_body.get("amount")
        self.assertEqual(
            res1.get("balance"),
            balance,
            wrong_value_error(
                req_type, route, res1.get("balance"), balance, "balance"
            )
        )
        self.assertEqual(
            len(res1.get("transactions")),
            1,
            wrong_value_error(
                req_type, route, len(
                    res1.get("transactions")), 1, "length of transactions"
            )
        )
        for t in res1.get("transactions"):
            for key in transaction_body.keys():
                self.assertEqual(
                    t.get(key),
                    transaction_body[key],
                    wrong_value_error(
                        req_type,
                        route,
                        t.get(key),
                        transaction_body[key],
                        key,
                        transaction_body[key]
                    ),
                )
            self.assertEqual(
                type(t.get("timestamp")),
                str,
                wrong_value_error(
                    req_type, route, type(
                        t.get("timestamp")), str, "type of timestamp field"
                ),
            )

        # Test if receiver balance is updated and if transaction outputs correctly in get_user
        res2 = requests.get(gen_users_path(user2)).json()
        balance = 10 + transaction_body.get("amount")
        self.assertEqual(
            res2.get("balance"),
            balance,
            wrong_value_error(
                req_type, route, res2.get("balance"), balance, "balance"
            )
        )
        self.assertEqual(
            len(res2.get("transactions")),
            1,
            wrong_value_error(
                req_type, route, len(
                    res2.get("transactions")), 1, "length of transactions"
            )
        )
        for t in res2.get("transactions"):
            for key in transaction_body.keys():
                self.assertEqual(
                    t.get(key),
                    transaction_body[key],
                    wrong_value_error(
                        req_type,
                        route,
                        t.get(key),
                        transaction_body[key],
                        key,
                        transaction_body[key]
                    ),
                )
            self.assertEqual(
                type(t.get("timestamp")),
                str,
                wrong_value_error(
                    req_type, route, type(
                        t.get("timestamp")), str, "type of timestamp field"
                ),
            )

    def test_request_payment(self):
        req_type = "POST"
        route = gen_transactions_route()

        user1 = self.create_user_and_assert_balance(10).get("id")
        user2 = self.create_user_and_assert_balance(10).get("id")
        transaction_body = gen_transaction_body(user1, user2, None)

        res = requests.post(gen_transactions_path(),
                            data=json.dumps(transaction_body))
        self.jsonable_test(res, req_type, route, 201, transaction_body)
        transaction = res.json()
        # Tests if transaction body is correct
        for key in transaction_body.keys():
            self.assertEqual(
                transaction.get(key),
                transaction_body[key],
                wrong_value_error(
                    req_type,
                    route,
                    transaction.get(key),
                    transaction_body[key],
                    key,
                    transaction_body[key]
                ),
            )
        self.assertEqual(
            type(transaction.get("timestamp")),
            str,
            wrong_value_error(
                req_type, route, type(transaction.get(
                    "timestamp")), str, "type of timestamp field"
            ),
        )

        # Tests if requester balance stays the same and get user outputs correctly
        res1 = requests.get(gen_users_path(user1)).json()
        self.assertEqual(
            res1.get("balance"),
            10,
            wrong_value_error(
                req_type, route, res1.get("balance"), 10, "balance"
            )
        )
        self.assertEqual(
            len(res1.get("transactions")),
            1,
            wrong_value_error(
                req_type, route, len(
                    res1.get("transactions")), 1, "length of transactions"
            )
        )
        for t in res1.get("transactions"):
            for key in transaction_body.keys():
                self.assertEqual(
                    t.get(key),
                    transaction_body[key],
                    wrong_value_error(
                        req_type,
                        route,
                        t.get(key),
                        transaction_body[key],
                        key,
                        transaction_body[key]
                    ),
                )
            self.assertEqual(
                type(t.get("timestamp")),
                str,
                wrong_value_error(
                    req_type, route, type(
                        t.get("timestamp")), str, "type of timestamp field"
                ),
            )

        # Tests if requestee balance is correct and if get user outputs correctly
        res2 = requests.get(gen_users_path(user2)).json()
        self.assertEqual(
            res2.get("balance"),
            10,
            wrong_value_error(
                req_type, route, res2.get("balance"), 10, "balance"
            )
        )
        self.assertEqual(
            len(res2.get("transactions")),
            1,
            wrong_value_error(
                req_type, route, len(
                    res2.get("transactions")), 1, "length of transactions"
            )
        )
        for t in res2.get("transactions"):
            for key in transaction_body.keys():
                self.assertEqual(
                    t.get(key),
                    transaction_body[key],
                    wrong_value_error(
                        req_type,
                        route,
                        t.get(key),
                        transaction_body[key],
                        key,
                        transaction_body[key]
                    ),
                )
            self.assertEqual(
                type(t.get("timestamp")),
                str,
                wrong_value_error(
                    req_type, route, type(
                        t.get("timestamp")), str, "type of timestamp field"
                ),
            )

    def test_accept_request(self):
        req_type = "POST"
        user1 = self.create_user_and_assert_balance(10).get("id")
        user2 = self.create_user_and_assert_balance(10).get("id")
        transaction_body = gen_transaction_body(user1, user2, None)

        create_res = requests.post(
            gen_transactions_path(), data=json.dumps(transaction_body))
        self.assertEqual(create_res.status_code, 201)

        tr = create_res.json().get("id")
        route = gen_transactions_route(tr)
        transaction_body["accepted"] = True

        res = requests.post(gen_transactions_path(
            tr), data=json.dumps({"accepted": True}))
        self.jsonable_test(res, req_type, route, 200, transaction_body)
        transaction = res.json()
        for key in transaction_body.keys():
            self.assertEqual(
                transaction.get(key),
                transaction_body[key],
                wrong_value_error(
                    req_type,
                    route,
                    transaction.get(key),
                    transaction_body[key],
                    key,
                    transaction_body[key]
                ),
            )
        self.assertEqual(
            type(transaction.get("timestamp")),
            str,
            wrong_value_error(
                req_type, route, type(transaction.get(
                    "timestamp")), str, "type of timestamp field"
            ),
        )

        res1 = requests.get(gen_users_path(user1)).json()
        balance = 10 - transaction_body.get("amount")
        self.assertEqual(
            res1.get("balance"),
            balance,
            wrong_value_error(
                req_type, route, res1.get("balance"), balance, "balance"
            )
        )
        self.assertEqual(
            len(res1.get("transactions")),
            1,
            wrong_value_error(
                req_type, route, len(
                    res1.get("transactions")), 1, "length of transactions"
            )
        )
        for t in res1.get("transactions"):
            for key in transaction_body.keys():
                self.assertEqual(
                    t.get(key),
                    transaction_body[key],
                    wrong_value_error(
                        req_type,
                        route,
                        t.get(key),
                        transaction_body[key],
                        key,
                        transaction_body[key]
                    ),
                )
            self.assertEqual(
                type(t.get("timestamp")),
                str,
                wrong_value_error(
                    req_type, route, type(
                        t.get("timestamp")), str, "type of timestamp field"
                ),
            )

        res2 = requests.get(gen_users_path(user2)).json()
        balance = 10 + transaction_body.get("amount")
        self.assertEqual(
            res2.get("balance"),
            balance,
            wrong_value_error(
                req_type, route, res2.get("balance"), balance, "balance"
            )
        )
        self.assertEqual(
            len(res2.get("transactions")),
            1,
            wrong_value_error(
                req_type, route, len(
                    res2.get("transactions")), 1, "length of transactions"
            )
        )
        for t in res2.get("transactions"):
            for key in transaction_body.keys():
                self.assertEqual(
                    t.get(key),
                    transaction_body[key],
                    wrong_value_error(
                        req_type,
                        route,
                        t.get(key),
                        transaction_body[key],
                        key,
                        transaction_body[key]
                    ),
                )
            self.assertEqual(
                type(t.get("timestamp")),
                str,
                wrong_value_error(
                    req_type, route, type(
                        t.get("timestamp")), str, "type of timestamp field"
                ),
            )

    def test_deny_request(self):
        req_type = "POST"
        user1 = self.create_user_and_assert_balance(10).get("id")
        user2 = self.create_user_and_assert_balance(10).get("id")
        transaction_body = gen_transaction_body(user1, user2, None)

        create_res = requests.post(
            gen_transactions_path(), data=json.dumps(transaction_body))
        self.assertEqual(create_res.status_code, 201)

        tr = create_res.json().get("id")
        route = gen_transactions_route(tr)
        transaction_body["accepted"] = False

        res = requests.post(gen_transactions_path(
            tr), data=json.dumps({"accepted": False}))
        self.jsonable_test(res, req_type, route, 200, transaction_body)
        transaction = res.json()
        for key in transaction_body.keys():
            self.assertEqual(
                transaction.get(key),
                transaction_body[key],
                wrong_value_error(
                    req_type,
                    route,
                    transaction.get(key),
                    transaction_body[key],
                    key,
                    transaction_body[key]
                ),
            )
        self.assertEqual(
            type(transaction.get("timestamp")),
            str,
            wrong_value_error(
                req_type, route, type(transaction.get(
                    "timestamp")), str, "type of timestamp field"
            ),
        )

        res1 = requests.get(gen_users_path(user1)).json()
        self.assertEqual(
            res1.get("balance"),
            10,
            wrong_value_error(
                req_type, route, res1.get("balance"), 10, "balance"
            )
        )
        self.assertEqual(
            len(res1.get("transactions")),
            1,
            wrong_value_error(
                req_type, route, len(
                    res1.get("transactions")), 1, "length of transactions"
            )
        )
        for t in res1.get("transactions"):
            for key in transaction_body.keys():
                self.assertEqual(
                    t.get(key),
                    transaction_body[key],
                    wrong_value_error(
                        req_type,
                        route,
                        t.get(key),
                        transaction_body[key],
                        key,
                        transaction_body[key]
                    ),
                )
            self.assertEqual(
                type(t.get("timestamp")),
                str,
                wrong_value_error(
                    req_type, route, type(
                        t.get("timestamp")), str, "type of timestamp field"
                ),
            )

        res2 = requests.get(gen_users_path(user2)).json()
        self.assertEqual(
            res2.get("balance"),
            10,
            wrong_value_error(
                req_type, route, res2.get("balance"), 10, "balance"
            )
        )
        self.assertEqual(
            len(res2.get("transactions")),
            1,
            wrong_value_error(
                req_type, route, len(
                    res2.get("transactions")), 1, "length of transactions"
            )
        )
        for t in res2.get("transactions"):
            for key in transaction_body.keys():
                self.assertEqual(
                    t.get(key),
                    transaction_body[key],
                    wrong_value_error(
                        req_type,
                        route,
                        t.get(key),
                        transaction_body[key],
                        key,
                        transaction_body[key]
                    ),
                )
            self.assertEqual(
                type(t.get("timestamp")),
                str,
                wrong_value_error(
                    req_type, route, type(
                        t.get("timestamp")), str, "type of timestamp field"
                ),
            )

    def test_get_user_transactions(self):
        """Testing get transaction by id gets transactions where user is both sender or receiver"""
        req_type = "POST"
        user1 = self.create_user_and_assert_balance(10).get("id")
        user2 = self.create_user_and_assert_balance(10).get("id")
        transaction_body = gen_transaction_body(user1, user2, None)

        create_res1 = requests.post(
            gen_transactions_path(), data=json.dumps(transaction_body))
        self.assertEqual(create_res1.status_code, 201)

        transaction_body2 = gen_transaction_body(user2, user1, True)
        create_res2 = requests.post(
            gen_transactions_path(), data=json.dumps(transaction_body2))
        self.assertEqual(create_res2.status_code, 201)

        transaction_body3 = gen_transaction_body(user1, user2, None)
        create_res3 = requests.post(
            gen_transactions_path(), data=json.dumps(transaction_body3))
        self.assertEqual(create_res3.status_code, 201)
        create_res3 = requests.post(gen_transactions_path(
            create_res3.json()["id"]), data=json.dumps({"accepted": False})).json()

        expected = [create_res1.json(), create_res2.json(), create_res3]

        route = gen_users_route(user2)
        res = requests.get(gen_users_path(user2))
        self.jsonable_test(res, req_type, route, 200)
        res = res.json()
        self.assertEqual(
            res.get("balance"),
            5,
            wrong_value_error(
                req_type, route, res.get("balance"), 5, "balance"
            )
        )
        self.assertEqual(
            len(res.get("transactions")),
            3,
            wrong_value_error(
                req_type, route, len(res.get("transactions")
                                     ), 3, "length of transactions"
            )
        )
        txns = sorted(res.get("transactions"), key=lambda d: d['id'])

        for te, tr in zip(txns, expected):
            for key in te.keys():
                self.assertEqual(
                    tr.get(key),
                    te.get(key),
                    wrong_value_error(req_type, route, tr.get(
                        key), te.get(key), te.get(key))
                )
                self.assertEqual(
                    type(tr.get("timestamp")),
                    str,
                    wrong_value_error(req_type, route, type(
                        tr.get("timestamp")), str, "type of timestamp field")
                )

    def test_overdraw_send(self):
        req_type = "POST"
        user1 = self.create_user_and_assert_balance(5).get("id")
        user2 = self.create_user_and_assert_balance(5).get("id")
        transaction_body = gen_transaction_body(user1, user2, True)
        route = gen_transactions_route()

        res = requests.post(gen_transactions_path(),
                            data=json.dumps(transaction_body))
        self.assertEqual(
            res.status_code,
            201
        )

        transaction_body = gen_transaction_body(user1, user2, True)
        route = gen_transactions_route()

        res = requests.post(gen_transactions_path(),
                            data=json.dumps(transaction_body))
        self.jsonable_test(res, req_type, route, 403, transaction_body)

        res1 = requests.get(gen_users_path(user1)).json()
        self.assertEqual(
            res1.get("balance"),
            0,
            wrong_value_error(
                req_type, route, res1.get("balance"), 0, "balance"
            )
        )
        self.assertEqual(
            len(res1.get("transactions")),
            1,
            wrong_value_error(
                req_type, route, len(
                    res1.get("transactions")), 1, "length of transactions"
            )
        )

        res2 = requests.get(gen_users_path(user2)).json()
        self.assertEqual(
            res2.get("balance"),
            10,
            wrong_value_error(
                req_type, route, res2.get("balance"), 20, "balance"
            )
        )
        self.assertEqual(
            len(res2.get("transactions")),
            1,
            wrong_value_error(
                req_type, route, len(
                    res2.get("transactions")), 1, "length of transactions"
            )
        )

    def test_overdraw_accept(self):
        req_type = "POST"
        user1 = self.create_user_and_assert_balance(0).get("id")
        user2 = self.create_user_and_assert_balance(20).get("id")
        transaction_body = gen_transaction_body(user1, user2, None)

        create_res = requests.post(
            gen_transactions_path(), data=json.dumps(transaction_body))
        self.assertEqual(create_res.status_code, 201)

        tr = create_res.json().get("id")
        route = gen_transactions_route(tr)
        transaction_body["accepted"] = True

        res = requests.post(gen_transactions_path(
            tr), data=json.dumps({"accepted": True}))
        self.jsonable_test(res, req_type, route, 403, transaction_body)

        res1 = requests.get(gen_users_path(user1)).json()
        self.assertEqual(
            res1.get("balance"),
            0,
            wrong_value_error(
                req_type, route, res1.get("balance"), 0, "balance"
            )
        )
        self.assertEqual(
            len(res1.get("transactions")),
            1,
            wrong_value_error(
                req_type, route, len(
                    res1.get("transactions")), 1, "length of transactions"
            )
        )

        res2 = requests.get(gen_users_path(user2)).json()
        self.assertEqual(
            res2.get("balance"),
            20,
            wrong_value_error(
                req_type, route, res2.get("balance"), 20, "balance"
            )
        )
        self.assertEqual(
            len(res2.get("transactions")),
            1,
            wrong_value_error(
                req_type, route, len(
                    res2.get("transactions")), 1, "length of transactions"
            )
        )

    def test_change_accepted_transaction(self):
        req_type = "POST"
        user1 = self.create_user_and_assert_balance(10).get("id")
        user2 = self.create_user_and_assert_balance(20).get("id")
        transaction_body = gen_transaction_body(user1, user2, True)

        create_res = requests.post(
            gen_transactions_path(), data=json.dumps(transaction_body))
        self.assertEqual(create_res.status_code, 201)

        tr = create_res.json().get("id")
        route = gen_transactions_route(tr)

        res = requests.post(gen_transactions_path(
            tr), data=json.dumps({"accepted": False}))
        self.jsonable_test(res, req_type, route, 403, transaction_body)

    def test_change_denied_transaction(self):
        req_type = "POST"
        user1 = self.create_user_and_assert_balance(0).get("id")
        user2 = self.create_user_and_assert_balance(20).get("id")
        transaction_body = gen_transaction_body(user1, user2, None)

        create_res = requests.post(
            gen_transactions_path(), data=json.dumps(transaction_body))
        self.assertEqual(create_res.status_code, 201)

        tr = create_res.json().get("id")
        route = gen_transactions_route(tr)
        res = requests.post(gen_transactions_path(
            tr), data=json.dumps({"accepted": False}))
        self.assertEqual(
            res.status_code,
            200
        )

        res = requests.post(gen_transactions_path(
            tr), data=json.dumps({"accepted": True}))
        self.jsonable_test(res, req_type, route, 403, transaction_body)

        transaction_body["accepted"] = False

        res1 = requests.get(gen_users_path(user1)).json()
        self.assertEqual(
            res1.get("balance"),
            0,
            wrong_value_error(
                req_type, route, res1.get("balance"), 10, "balance"
            )
        )
        for t in res1.get("transactions"):
            for key in transaction_body.keys():
                self.assertEqual(
                    t.get(key),
                    transaction_body[key],
                    wrong_value_error(
                        req_type,
                        route,
                        t.get(key),
                        transaction_body[key],
                        key,
                        transaction_body[key]
                    ),
                )
        self.assertEqual(
            len(res1.get("transactions")),
            1,
            wrong_value_error(
                req_type, route, len(
                    res1.get("transactions")), 1, "length of transactions"
            )
        )

        res2 = requests.get(gen_users_path(user2)).json()
        self.assertEqual(
            res2.get("balance"),
            20,
            wrong_value_error(
                req_type, route, res2.get("balance"), 10, "balance"
            )
        )
        for t in res2.get("transactions"):
            for key in transaction_body.keys():
                self.assertEqual(
                    t.get(key),
                    transaction_body[key],
                    wrong_value_error(
                        req_type,
                        route,
                        t.get(key),
                        transaction_body[key],
                        key,
                        transaction_body[key]
                    ),
                )
        self.assertEqual(
            len(res2.get("transactions")),
            1,
            wrong_value_error(
                req_type, route, len(
                    res2.get("transactions")), 1, "length of transactions"
            )
        )

    def test_extra_create_friends(self):
        if not EXTRA_CREDIT:
            return
        user1 = requests.post(gen_users_path(), data=json.dumps(
            SAMPLE_USER)).json().get("id")
        user2 = requests.post(gen_users_path(), data=json.dumps(
            SAMPLE_USER)).json().get("id")
        route = gen_users_route(user1, True) + f"friends/{user2}/"
        req_type = "POST"
        path = gen_users_path(user1, True) + f"friends/{user2}/"
        res = requests.post(path, data=None)
        self.assertEqual(res.status_code, 201)
        res2 = requests.get(gen_users_path(user1, True) +
                            "friends/").json().get("friends")
        for f in res2:
            self.assertEqual(
                f.get("id"),
                user2
            )
        self.assertEqual(len(res2), 1, wrong_value_error(
            req_type, route, len(res2), 1, "length of friends"))
        res3 = requests.get(gen_users_path(user2, True) +
                            "friends/").json().get("friends")
        for f in res3:
            self.assertEqual(
                f.get("id"),
                user1
            )
        self.assertEqual(len(res3), 1, wrong_value_error(
            req_type, route, len(res3), 1, "length of friends"))

    def test_extra_get_friends(self):
        if not EXTRA_CREDIT:
            return
        user1 = requests.post(gen_users_path(), data=json.dumps(
            SAMPLE_USER)).json().get("id")
        route = gen_users_route(user1, True) + f"friends/"
        req_type = "GET"
        res = requests.get(gen_users_path(user1, True) + "friends/")
        self.jsonable_test(res, req_type, route, 200)
        res = res.json()
        self.assertEqual(type(res.get("friends")), list, wrong_value_error(
            req_type, route, type(res.get("friends")), list, "type of friends field"))

    def test_join(self):
        if not EXTRA_CREDIT:
            return
        user1 = self.create_user_and_assert_balance(10).get("id")
        user2 = self.create_user_and_assert_balance(10).get("id")
        txn1 = gen_transaction_body(user1, user2, True)
        txn1_response = requests.post(
            gen_transactions_path(), data=json.dumps(txn1)).json()
        txn2 = gen_transaction_body(user1, user2, None)
        txn2_response = requests.post(
            gen_transactions_path(), data=json.dumps(txn2)).json()
        txn3 = gen_transaction_body(user1, user2, None)
        txn3_response = requests.post(
            gen_transactions_path(), data=json.dumps(txn3)).json()
        requests.post(gen_transactions_path(
            txn3_response["id"]), data=json.dumps({"accepted": False}))
        txn3["accepted"] = False
        expected = [{
            "sender_name": "Cornell AppDev",
            "receiver_name": "Cornell AppDev",
            **SAMPLE_TRANSACTION,
            "accepted": True
        }, {
            "sender_name": "Cornell AppDev",
            "receiver_name": "Cornell AppDev",
            **SAMPLE_TRANSACTION,
            "accepted": None
        }, {
            "sender_name": "Cornell AppDev",
            "receiver_name": "Cornell AppDev",
            **SAMPLE_TRANSACTION,
            "accepted": False
        }
        ]

        route = gen_users_route(user1, True) + "join/"
        req_type = "GET"
        res = requests.get(gen_users_path(user1, True) + "join/")
        self.jsonable_test(res, req_type, route, 200)
        res = res.json().get("transactions")
        self.assertEqual(len(res), 3, wrong_value_error(
            req_type, route, len(res), 3, "length of result"))
        for te, tr in zip(expected, res):
            for key in te.keys():
                self.assertEqual(
                    tr.get(key),
                    te.get(key),
                    wrong_value_error(req_type, route, tr.get(
                        key), te.get(key), te.get(key))
                )
                self.assertEqual(
                    type(tr.get("timestamp")),
                    str,
                    wrong_value_error(req_type, route, type(
                        tr.get("timestamp")), str, "type of timestamp field")
                )


def run_tests():
    sleep(1.5)
    sys.argv = sys.argv[:1]
    unittest.main()


if __name__ == "__main__":
    argv = sys.argv[1:]
    EXTRA_CREDIT = len(argv) > 0 and argv[0] == "--extra"
    thread = Thread(target=run_tests)
    thread.start()
    app.run(host="0.0.0.0", port=8000, debug=False)