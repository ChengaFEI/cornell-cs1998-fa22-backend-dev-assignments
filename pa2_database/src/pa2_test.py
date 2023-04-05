import sys
import json
from threading import Thread
from time import sleep
import unittest

from app import app
import requests

# NOTE: Make sure you run 'pip3 install requests' in your virtualenv

# Flag to run extra credit tests (if applicable)
EXTRA_CREDIT = False

# URL pointing to your local dev host
LOCAL_URL = "http://localhost:8000"

# Sample testing data
SAMPLE_USER = {"name": "Cornell AppDev", "username": "cornellappdev"}
EXTRA_SAMPLE_USER = {"name": "AppDev Premium", "username": "appdevpremium", "password": "abc123"}

# Request endpoint generators
USER_ROUTE = "/api/user"
EXTRA_CREDIT_USER_ROUTE = "/api/extra/user"
SEND_ROUTE = "/api/send"
EXTRA_CREDIT_SEND_ROUTE = "/api/extra/send"


def gen_users_route(user_id=None, extra=False):
    user_route = EXTRA_CREDIT_USER_ROUTE if extra else USER_ROUTE
    return (
        f"{user_route}s/"
        if user_id is None
        else f"{user_route}/{str(user_id)}/"
    )


def gen_users_path(user_id=None, extra=False):
    return f"{LOCAL_URL}{gen_users_route(user_id, extra)}"


def gen_send_route(extra=False):
    send_route = EXTRA_CREDIT_SEND_ROUTE if extra else SEND_ROUTE
    return f"{send_route}/"


def gen_send_path(extra=False):
    return f"{LOCAL_URL}{gen_send_route(extra)}"


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
            \nDid you remember to use jsonify on your response?\
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


class TestRoutes(unittest.TestCase):
    def jsonable_test(self, res, req_type, route, status_code, body=None):
        jsonable, error = is_jsonable(res, req_type, route, body)
        self.assertTrue(jsonable, error)
        self.assertEqual(
            res.status_code,
            status_code,
            status_code_error(req_type, route, res.status_code, status_code),
        )

    # -- USERS ---------------------------------------------

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

    def _create_user_and_assert_balance(self, balance, extra=False):
        dummy_user = EXTRA_SAMPLE_USER if extra else SAMPLE_USER
        user_with_balance = {**dummy_user, "balance": balance}
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

    def _get_user_and_assert_balance(self, user_id, balance, extra=False):
        dummy_user = EXTRA_SAMPLE_USER if extra else SAMPLE_USER
        req_type = "POST" if extra else "GET" 
        route = gen_users_path(user_id, extra=extra)
        print(dummy_user.get("password"))
        res = (requests.post(gen_users_path(user_id, extra=True), 
                            data=json.dumps({"password": dummy_user.get("password")}))
              ) if extra else requests.get(gen_users_path(user_id))
        print(f"printing res with extra={extra}")
        print(res)
        self.jsonable_test(res, req_type, route, 200)
        user = res.json()
        self.assertTrue(
            user.get("id") is not None,
            error_str(
                f"Returned user from {req_type} request to {route} does not have an 'id' field!"
            ),
        )
        for key in dummy_user.keys():
            self.assertEqual(
                user.get(key),
                dummy_user[key],
                wrong_value_error(
                    req_type, route, user.get(key), dummy_user[key], key
                ),
            )
        self.assertEqual(
            user.get("balance"),
            balance,
            wrong_value_error(
                req_type, route, user.get("balance"), balance, "balance"
            ),
        )

    def _send_money(self, user_id1, user_id2, amount, status_code, password=None, extra=False):
        req_type = "POST"
        route = gen_send_path(extra=extra)
        send_body = {
            "sender_id": user_id1,
            "receiver_id": user_id2,
            "amount": amount,
        }
        if extra:
            send_body["password"] = password
        res = requests.post(gen_send_path(extra=extra), data=json.dumps(send_body))
        if extra:
            del send_body["password"]
        self.jsonable_test(res, req_type, route, status_code)
        if status_code < 400:
            transaction = res.json()
            print(transaction)
            for key in send_body:
                self.assertEqual(
                    transaction.get(key),
                    send_body[key],
                    wrong_value_error(
                        req_type,
                        route,
                        transaction.get(key),
                        send_body[key],
                        key,
                        send_body,
                    ),
                )

    def test_send_money(self):
        user_id1 = self._create_user_and_assert_balance(10).get("id")
        user_id2 = self._create_user_and_assert_balance(10).get("id")
        self._send_money(user_id1, user_id2, 6, 200)
        self._get_user_and_assert_balance(user_id1, 4)
        self._get_user_and_assert_balance(user_id2, 16)
        # cannot overdraw user1's balance
        self._send_money(user_id1, user_id2, 6, 400)
        # balances remain the same
        self._get_user_and_assert_balance(user_id1, 4)
        self._get_user_and_assert_balance(user_id2, 16)

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

    def test_user_id_increments(self):
        user_id1 = self._create_user_and_assert_balance(0).get("id")
        user_id2 = self._create_user_and_assert_balance(0).get("id")
        self.assertEqual(
            user_id1 + 1, user_id2, error_str("User IDs do not increment!")
        )

    def test_extra_create_user(self):
        if not EXTRA_CREDIT:
            return
        self._create_user_and_assert_balance(5, extra=True)
    
    def test_extra_get_user(self):
        if not EXTRA_CREDIT:
            return
        user = self._create_user_and_assert_balance(5, extra=True)
        self._get_user_and_assert_balance(user["id"], 5, extra=True)

    def test_extra_get_user_unauthorized(self):
        if not EXTRA_CREDIT:
            print("test unauthorized?")
            return
        user = self._create_user_and_assert_balance(5, extra=True)

        req_type = "POST"
        route = gen_users_route(user["id"], extra=True)
        res = requests.post(gen_users_path(user["id"], extra=True), data=json.dumps({"password": "bad" + user.get('password')}))
        self.jsonable_test(res, req_type, route, 401)

    def test_extra_send_money(self):
        if not EXTRA_CREDIT:
            return
        user1 = self._create_user_and_assert_balance(10, extra=True)
        user_id1 = user1.get("id")
        user_id2 = self._create_user_and_assert_balance(10, extra=True).get("id")
        self._send_money(user_id1, user_id2, 6, 200, password=user1.get("password"), extra=True)
        self._get_user_and_assert_balance(user_id1, 4, extra=True)
        self._get_user_and_assert_balance(user_id2, 16, extra=True)
        # cannot overdraw user1's balance
        self._send_money(user_id1, user_id2, 6, 400, password=user1.get("password"), extra=True)
        # balances remain the same
        self._get_user_and_assert_balance(user_id1, 4, extra=True)
        self._get_user_and_assert_balance(user_id2, 16, extra=True)

    def test_extra_send_money_unauthorized(self):
        if not EXTRA_CREDIT:
            return
        user1 = self._create_user_and_assert_balance(10, extra=True)
        user_id1 = user1.get("id")
        user_id2 = self._create_user_and_assert_balance(10, extra=True).get("id")
        self._send_money(user_id1, user_id2, 6, 401, password="bad" + user1.get("password"), extra=True)
        

    


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