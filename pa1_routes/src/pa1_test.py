import sys
import json
from threading import Thread
from time import sleep
import unittest

from requests.api import post

from app import app
import requests

unittest.TestLoader.sortTestMethodsUsing = None

# NOTE: Make sure you run 'pip3 install requests' in your virtualenv

# Flag to run extra credit tests (if applicable)
EXTRA_CREDIT = False

# URL pointing to your local dev host
LOCAL_URL = "http://localhost:5000"

# Sample testing data
SAMPLE_POST = {
    "title": "Hello, World!",
    "link": "cornellappdev.com",
    "username": "appdev",
}
SAMPLE_COMMENT = {"text": "First comment", "username": "appdev"}

POSTS_ROUTE = "/api/posts"

EXTRA_CREDIT_POSTS_ROUTE = "/api/extra/posts"

# Request endpoint generators
def gen_posts_route(post_id=None, extra=False, params={}):
    route = EXTRA_CREDIT_POSTS_ROUTE if extra else POSTS_ROUTE
    param_list = [f"{key}={val}" for key, val in params.items()]
    param_str = f"?{'&'.join(param_list)}" if len(param_list) != 0 else ""
    return (
        f"{route}/{param_str}"
        if post_id is None
        else f"{route}/{str(post_id)}/{param_str}"
    )


def gen_posts_path(post_id=None, extra=False, params={}):
    return f"{LOCAL_URL}{gen_posts_route(post_id, extra, params)}"


def gen_comments_route(post_id, comment_id=None, extra=False):
    route = EXTRA_CREDIT_POSTS_ROUTE if extra else POSTS_ROUTE
    base_path = f"{route}/{str(post_id)}/comments"
    return (
        base_path + "/"
        if comment_id is None
        else f"{base_path}/{str(comment_id)}/"
    )


def gen_comments_path(post_id, comment_id=None, extra=False):
    return f"{LOCAL_URL}{gen_comments_route(post_id, comment_id, extra)}"


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

    # -- POSTS ---------------------------------------------

    def test_get_initial_posts(self):
        req_type = "GET"
        route = gen_posts_route()
        res = requests.get(gen_posts_path())
        self.jsonable_test(res, req_type, route, 200)
        posts = res.json().get("posts")
        self.assertEqual(
            type(posts),
            list,
            wrong_value_error(
                req_type,
                route,
                posts,
                "a (potentially empty) list of posts",
                "posts",
            ),
        )

    def test_create_post(self):
        req_type = "POST"
        route = gen_posts_route()

        res = requests.post(gen_posts_path(), data=json.dumps(SAMPLE_POST))
        self.jsonable_test(res, req_type, route, 201, SAMPLE_POST)

        post = res.json()
        self.assertEqual(
            type(post),
            dict,
            wrong_value_error(
                req_type, route, post, "a post dictionary", "response"
            ),
        )
        for key in SAMPLE_POST.keys():
            self.assertEqual(
                post.get(key),
                SAMPLE_POST.get(key),
                wrong_value_error(
                    req_type,
                    route,
                    post.get(key),
                    SAMPLE_POST.get(key),
                    key,
                    SAMPLE_POST,
                ),
            )
        self.assertEqual(
            post.get("upvotes"),
            1,
            wrong_value_error(
                req_type, route, post.get("upvotes"), 1, "upvotes", SAMPLE_POST
            ),
        )

        req_type = "GET"
        route = gen_posts_route()

        res = requests.get(gen_posts_path())
        jsonable, error = is_jsonable(res, req_type, route)

        after_err = error_str("After creating a post,\n")
        self.assertTrue(jsonable, after_err + error)
        posts = res.json().get("posts")
        self.assertEqual(
            type(posts),
            list,
            after_err
            + wrong_value_error(
                req_type, route, posts, "a list of posts", "posts"
            ),
        )
        self.assertNotEqual(
            len(posts),
            0,
            after_err
            + wrong_value_error(
                req_type,
                route,
                posts,
                "a list of length greater than 0",
                "number of posts",
            ),
        )
        post = posts[-1]
        for key in SAMPLE_POST.keys():
            self.assertEqual(
                post.get(key),
                SAMPLE_POST.get(key),
                after_err
                + wrong_value_error(
                    req_type,
                    route,
                    post.get(key),
                    SAMPLE_POST.get(key),
                    key,
                    SAMPLE_POST,
                ),
            )
        self.assertEqual(
            post.get("upvotes"),
            1,
            after_err
            + wrong_value_error(
                req_type, route, post.get("upvotes"), 1, "upvotes", SAMPLE_POST
            ),
        )

    def test_delete_post(self):
        post_create_err = error_str(
            "\nCreation of a post failed. See `test_create_post` results."
        )
        res = requests.post(gen_posts_path(), data=json.dumps(SAMPLE_POST))
        jsonable, _ = is_jsonable(res, "POST", gen_posts_route(), SAMPLE_POST)
        self.assertTrue(jsonable, post_create_err)
        post_id = res.json().get("id")
        self.assertIsNotNone(post_id, post_create_err)

        req_type = "DELETE"
        route = gen_posts_route(post_id)
        res = requests.delete(gen_posts_path(post_id))

        jsonable, error = is_jsonable(res, req_type, route)
        self.assertTrue(jsonable, error)
        self.assertEqual(
            res.status_code,
            200,
            status_code_error(req_type, route, res.status_code, 200),
        )

    def test_post_id_increments(self):
        post_create_err = error_str(
            "\nCreation of a post failed. See `test_create_post` results."
        )
        req_type = "POST"
        route = gen_posts_route()
        res = requests.post(gen_posts_path(), data=json.dumps(SAMPLE_POST))
        jsonable, _ = is_jsonable(res, req_type, gen_posts_route(), SAMPLE_POST)
        self.assertTrue(jsonable, post_create_err)
        post_id = res.json().get("id")
        self.assertIsNotNone(post_id, post_create_err)

        res2 = requests.post(gen_posts_path(), data=json.dumps(SAMPLE_POST))
        post_id2 = res2.json().get("id")

        self.assertEqual(
            post_id2,
            post_id + 1,
            wrong_value_error(
                req_type,
                route,
                post_id2,
                f"one more than the previous post, which was {post_id}",
                "post_id",
            ),
        )

    def test_get_invalid_post(self):
        req_type = "GET"
        route = gen_posts_route(10000)
        res = requests.get(gen_posts_path(10000))
        jsonable, error = is_jsonable(res, req_type, route)
        self.assertTrue(
            jsonable, error_str("\nUsing an invalid post id of 10000,") + error
        )
        self.assertEqual(
            res.status_code,
            404,
            status_code_error(req_type, route, res.status_code, 404),
        )
        err_res = res.json()
        self.assertIsNotNone(
            err_res,
            wrong_value_error(
                req_type,
                route,
                err_res,
                'something of the form {"error": "Your error message here"}',
                "error response",
            ),
        )

    def test_delete_invalid_post(self):
        req_type = "DELETE"
        route = gen_posts_route(10000)
        res = requests.delete(gen_posts_path(10000))
        jsonable, error = is_jsonable(res, req_type, route)
        self.assertTrue(
            jsonable, error_str("\nUsing an invalid post id of 10000,") + error
        )
        self.assertEqual(
            res.status_code,
            404,
            status_code_error(req_type, route, res.status_code, 404),
        )
        err_res = res.json()
        self.assertIsNotNone(
            err_res,
            wrong_value_error(
                req_type,
                route,
                err_res,
                'something of the form {"error": "Your error message here"}',
                "error response",
            ),
        )

    # -- COMMENTS ------------------------------------------

    def test_post_comment(self):
        post_create_err = error_str(
            "\nCreation of a post failed. See `test_create_post` results."
        )
        req_type = "POST"
        res = requests.post(gen_posts_path(), data=json.dumps(SAMPLE_POST))
        jsonable, _ = is_jsonable(res, req_type, gen_posts_route(), SAMPLE_POST)
        self.assertTrue(jsonable, post_create_err)
        post_id = res.json().get("id")
        self.assertIsNotNone(post_id, post_create_err)

        route = gen_comments_route(post_id)
        res = requests.post(
            gen_comments_path(post_id), data=json.dumps(SAMPLE_COMMENT)
        )
        jsonable, error = is_jsonable(res, req_type, route, SAMPLE_COMMENT)
        self.assertTrue(jsonable, error)
        self.assertEqual(
            res.status_code,
            201,
            status_code_error(
                req_type, route, res.status_code, 201, SAMPLE_COMMENT
            ),
        )

        req_type = "GET"
        res = requests.get(gen_comments_path(post_id))
        jsonable, error = is_jsonable(res, req_type, route)
        self.assertTrue(jsonable, error)
        self.assertEqual(
            res.status_code,
            200,
            status_code_error(req_type, route, res.status_code, 200),
        )
        comments = res.json().get("comments")
        self.assertEqual(
            type(comments),
            list,
            wrong_value_error(
                req_type,
                route,
                comments,
                "a (potentially empty) list of comments",
                "comments",
            ),
        )
        self.assertEqual(
            len(comments),
            1,
            wrong_value_error(
                req_type,
                route,
                comments,
                [SAMPLE_COMMENT],
                "number of comments",
            ),
        )
        comment = comments[0]
        for key in SAMPLE_COMMENT.keys():
            self.assertEqual(
                comment.get(key),
                SAMPLE_COMMENT.get(key),
                wrong_value_error(
                    req_type,
                    route,
                    comment.get(key),
                    SAMPLE_COMMENT.get(key),
                    key,
                ),
            )

    def test_edit_comment(self):
        post_create_err = error_str(
            "\nCreation of a post failed. See `test_create_post` results."
        )
        req_type = "POST"
        res = requests.post(gen_posts_path(), data=json.dumps(SAMPLE_POST))
        jsonable, _ = is_jsonable(res, req_type, gen_posts_route(), SAMPLE_POST)
        self.assertTrue(jsonable, post_create_err)
        post_id = res.json().get("id")
        self.assertIsNotNone(post_id, post_create_err)

        comment_create_err = error_str(
            "\nCreation of a comment failed. See `test_post_comment` results."
        )
        res = requests.post(
            gen_comments_path(post_id), data=json.dumps(SAMPLE_COMMENT)
        )
        jsonable, _ = is_jsonable(
            res, req_type, gen_comments_route(post_id), SAMPLE_COMMENT
        )
        comment_id = res.json().get("id")
        self.assertIsNotNone(comment_id, comment_create_err)

        route = gen_comments_route(post_id, comment_id)
        body = {"text": "New text"}
        res = requests.post(
            gen_comments_path(post_id, comment_id),
            data=json.dumps(body),
        )
        jsonable, error = is_jsonable(res, req_type, route, body)
        self.assertTrue(jsonable, error)
        self.assertEqual(
            res.status_code,
            200,
            status_code_error(req_type, route, res.status_code, 200, body),
        )
        text = res.json().get("text")
        self.assertEqual(
            text,
            "New text",
            wrong_value_error(req_type, route, text, "New text", "text", body),
        )

    def test_get_comments_invalid_post(self):
        req_type = "GET"
        route = gen_comments_route(10000)
        res = requests.get(gen_comments_path(10000))
        jsonable, error = is_jsonable(res, req_type, route)
        self.assertTrue(
            jsonable, "\nUsing an invalid post id of 10000,\n" + error
        )
        self.assertEqual(
            res.status_code,
            404,
            status_code_error(req_type, route, res.status_code, 404),
        )
        res_error = res.json()
        self.assertIsNotNone(
            res_error,
            wrong_value_error(
                req_type,
                route,
                res_error,
                'something of the form {"error": "Your error response here."}',
                "error response",
            ),
        )

    def test_post_invalid_comment(self):
        req_type = "POST"
        route = gen_comments_route(10000)
        res = requests.post(
            gen_comments_path(10000), data=json.dumps(SAMPLE_COMMENT)
        )
        jsonable, error = is_jsonable(res, req_type, route)
        self.assertTrue(
            jsonable, "\nUsing an invalid post id of 10000,\n" + error
        )
        self.assertEqual(
            res.status_code,
            404,
            status_code_error(req_type, route, res.status_code, 404),
        )
        res_error = res.json()
        self.assertIsNotNone(
            res_error,
            wrong_value_error(
                req_type,
                route,
                res_error,
                'something of the form {"error": "Your error response here."}',
                "error response",
            ),
        )

    # -- EXTRA CREDIT ------------------------------------------

    def test_extra_create_post(self):
        if not EXTRA_CREDIT:
            return
        req_type = "POST"
        route = gen_posts_route(extra=True)

        for key in SAMPLE_POST.keys():
            SAMPLE_BAD_POST = SAMPLE_POST.copy()
            SAMPLE_BAD_POST[key] = 0  # values should all be string
            res = requests.post(
                gen_posts_path(extra=True), data=json.dumps(SAMPLE_BAD_POST)
            )
            jsonable, error = is_jsonable(res, req_type, route)
            self.assertTrue(jsonable, error)
            self.assertEqual(
                res.status_code,
                401,
                status_code_error(req_type, route, res.status_code, 401),
            )
            res_error = res.json()
            self.assertIsNotNone(
                res_error,
                wrong_value_error(
                    req_type,
                    route,
                    res_error,
                    'something of the form {"error": "Your error response here."}',
                    "error response",
                ),
            )

        res = requests.post(
            gen_posts_path(extra=True), data=json.dumps(SAMPLE_POST)
        )
        jsonable, error = is_jsonable(res, req_type, route, SAMPLE_POST)
        self.assertTrue(jsonable, error)

        post = res.json()
        self.assertEqual(
            res.status_code,
            201,
            status_code_error(res, route, res.status_code, 201),
        )
        self.assertEqual(
            type(post),
            dict,
            wrong_value_error(
                req_type, route, post, "a post dictionary", "response"
            ),
        )
        for key in SAMPLE_POST.keys():
            self.assertEqual(
                post.get(key),
                SAMPLE_POST.get(key),
                wrong_value_error(
                    req_type,
                    route,
                    post.get(key),
                    SAMPLE_POST.get(key),
                    key,
                    SAMPLE_POST,
                ),
            )
        self.assertEqual(
            post.get("upvotes"),
            1,
            wrong_value_error(
                req_type, route, post.get("upvotes"), 1, "upvotes", SAMPLE_POST
            ),
        )

        req_type = "GET"
        route = gen_posts_route()

        res = requests.get(gen_posts_path())
        jsonable, error = is_jsonable(res, req_type, route)

        after_err = error_str("After creating a post,\n")
        self.assertTrue(jsonable, after_err + error)
        posts = res.json().get("posts")
        self.assertEqual(
            type(posts),
            list,
            after_err
            + wrong_value_error(
                req_type, route, posts, "a list of posts", "posts"
            ),
        )
        self.assertNotEqual(
            len(posts),
            0,
            after_err
            + wrong_value_error(
                req_type,
                route,
                posts,
                "a list of length greater than 0",
                "number of posts",
            ),
        )
        post = posts[-1]
        for key in SAMPLE_POST.keys():
            self.assertEqual(
                post.get(key),
                SAMPLE_POST.get(key),
                after_err
                + wrong_value_error(
                    req_type,
                    route,
                    post.get(key),
                    SAMPLE_POST.get(key),
                    key,
                    SAMPLE_POST,
                ),
            )
        self.assertEqual(
            post.get("upvotes"),
            1,
            after_err
            + wrong_value_error(
                req_type, route, post.get("upvotes"), 1, "upvotes", SAMPLE_POST
            ),
        )

    def test_extra_post_comment(self):
        if not EXTRA_CREDIT:
            return
        post_create_err = error_str(
            "\nCreation of a post failed. See `test_extra_create_post` results."
        )
        req_type = "POST"
        res = requests.post(
            gen_posts_path(extra=True), data=json.dumps(SAMPLE_POST)
        )
        jsonable, _ = is_jsonable(
            res, req_type, gen_posts_route(extra=True), SAMPLE_POST
        )
        self.assertTrue(jsonable, post_create_err)
        post_id = res.json().get("id")
        self.assertIsNotNone(post_id, post_create_err)

        route = gen_comments_route(post_id, extra=True)
        for key in SAMPLE_COMMENT.keys():
            SAMPLE_BAD_COMMENT = SAMPLE_COMMENT.copy()
            SAMPLE_BAD_COMMENT[key] = 0  # values should all be string
            res = requests.post(
                gen_comments_path(post_id, extra=True),
                data=json.dumps(SAMPLE_BAD_COMMENT),
            )
            jsonable, error = is_jsonable(
                res, req_type, route, SAMPLE_BAD_COMMENT
            )
            self.assertTrue(jsonable, error)
            self.assertEqual(
                res.status_code,
                401,
                status_code_error(
                    req_type, route, res.status_code, 401, SAMPLE_BAD_COMMENT
                ),
            )
            res_error = res.json()
            self.assertIsNotNone(
                res_error,
                wrong_value_error(
                    req_type,
                    route,
                    res_error,
                    'something of the form {"error": "Your error response here."}',
                    "error response",
                ),
            )

        res = requests.post(
            gen_comments_path(post_id, extra=True),
            data=json.dumps(SAMPLE_COMMENT),
        )
        jsonable, error = is_jsonable(res, req_type, route, SAMPLE_COMMENT)
        self.assertTrue(jsonable, error)
        self.assertEqual(
            res.status_code,
            201,
            status_code_error(
                req_type, route, res.status_code, 201, SAMPLE_COMMENT
            ),
        )
        res_error = res.json()
        self.assertIsNotNone(
            res_error,
            wrong_value_error(
                req_type,
                route,
                res_error,
                'something of the form {"error": "Your error response here."}',
                "error response",
            ),
        )

        req_type = "GET"
        res = requests.get(gen_comments_path(post_id))
        jsonable, error = is_jsonable(res, req_type, route)
        self.assertTrue(jsonable, error)
        self.assertEqual(
            res.status_code,
            200,
            status_code_error(req_type, route, res.status_code, 200),
        )
        comments = res.json().get("comments")
        self.assertEqual(
            type(comments),
            list,
            wrong_value_error(
                req_type,
                route,
                comments,
                "a (potentially empty) list of comments",
                "comments",
            ),
        )
        self.assertEqual(
            len(comments),
            1,
            wrong_value_error(
                req_type,
                route,
                comments,
                [SAMPLE_COMMENT],
                "number of comments",
            ),
        )
        comment = comments[0]
        for key in SAMPLE_COMMENT.keys():
            self.assertEqual(
                comment.get(key),
                SAMPLE_COMMENT.get(key),
                wrong_value_error(
                    req_type,
                    route,
                    comment.get(key),
                    SAMPLE_COMMENT.get(key),
                    key,
                ),
            )

    def test_extra_edit_comment(self):
        if not EXTRA_CREDIT:
            return
        post_create_err = error_str(
            "\nCreation of a post failed. See `test_extra_create_post` results."
        )
        req_type = "POST"
        res = requests.post(
            gen_posts_path(extra=True), data=json.dumps(SAMPLE_POST)
        )
        jsonable, _ = is_jsonable(
            res, req_type, gen_posts_route(extra=True), SAMPLE_POST
        )
        self.assertTrue(jsonable, post_create_err)
        post_id = res.json().get("id")
        self.assertIsNotNone(post_id, post_create_err)

        comment_create_err = error_str(
            "\nCreation of a comment failed. See `test_extra_post_comment` results."
        )
        res = requests.post(
            gen_comments_path(post_id, extra=True),
            data=json.dumps(SAMPLE_COMMENT),
        )
        jsonable, _ = is_jsonable(
            res,
            req_type,
            gen_comments_route(post_id, extra=True),
            SAMPLE_COMMENT,
        )
        comment_id = res.json().get("id")
        self.assertIsNotNone(comment_id, comment_create_err)

        route = gen_comments_route(post_id, comment_id, extra=True)
        body = {"text": 0}
        res = requests.post(
            gen_comments_path(post_id, comment_id, extra=True),
            data=json.dumps(body),
        )
        jsonable, error = is_jsonable(res, req_type, route, body)
        self.assertTrue(jsonable, error)
        self.assertEqual(
            res.status_code,
            401,
            status_code_error(req_type, route, res.status_code, 401, body),
        )
        res_error = res.json()
        self.assertIsNotNone(
            res_error,
            wrong_value_error(
                req_type,
                route,
                res_error,
                'something of the form {"error": "Your error response here."}',
                "error response",
            ),
        )

        route = gen_comments_route(post_id, comment_id, extra=True)
        body = {"text": "New text"}
        res = requests.post(
            gen_comments_path(post_id, comment_id, extra=True),
            data=json.dumps(body),
        )
        jsonable, error = is_jsonable(res, req_type, route, body)
        self.assertTrue(jsonable, error)
        self.assertEqual(
            res.status_code,
            200,
            status_code_error(req_type, route, res.status_code, 200, body),
        )
        text = res.json().get("text")
        self.assertEqual(
            text,
            "New text",
            wrong_value_error(req_type, route, text, "New text", "text", body),
        )

    def test_extra_upvote_post(self):
        if not EXTRA_CREDIT:
            return
        post_create_err = error_str(
            "\nCreation of a post failed. See `test_extra_create_post` results."
        )
        req_type = "POST"
        res = requests.post(
            gen_posts_path(extra=True), data=json.dumps(SAMPLE_POST)
        )
        jsonable, _ = is_jsonable(
            res, req_type, gen_posts_route(extra=True), SAMPLE_POST
        )
        self.assertTrue(jsonable, post_create_err)
        post_id = res.json().get("id")
        self.assertIsNotNone(post_id, post_create_err)

        route = gen_posts_route(post_id, extra=True)
        upvotes_to_add = 3
        body = {"upvotes": upvotes_to_add}
        old_upvotes = res.json().get("upvotes")
        res = requests.post(
            gen_posts_path(post_id, extra=True),
            data=json.dumps(body),
        )
        jsonable, error = is_jsonable(res, req_type, route, body)
        self.assertTrue(jsonable, error)
        self.assertEqual(
            res.status_code,
            200,
            status_code_error(req_type, route, res.status_code, 200, body),
        )
        new_upvotes = res.json().get("upvotes")
        self.assertEqual(
            upvotes_to_add + old_upvotes,
            new_upvotes,
            wrong_value_error(
                req_type,
                route,
                upvotes_to_add + old_upvotes,
                new_upvotes,
                "upvotes",
                body,
            ),
        )

    def test_extra_sorting_posts(self):
        if not EXTRA_CREDIT:
            return
        post_create_err = error_str(
            "\nCreation of a post failed. See `test_extra_create_post` results."
        )
        req_type = "POST"
        res = requests.post(
            gen_posts_path(extra=True), data=json.dumps(SAMPLE_POST)
        )
        jsonable, _ = is_jsonable(
            res, req_type, gen_posts_route(extra=True), SAMPLE_POST
        )
        self.assertTrue(jsonable, post_create_err)
        post_id = res.json().get("id")
        self.assertIsNotNone(post_id, post_create_err)
        body = {"upvotes": 1}
        res = requests.post(
            gen_posts_path(post_id, extra=True),
            data=json.dumps(body),
        )

        res = requests.post(
            gen_posts_path(extra=True), data=json.dumps(SAMPLE_POST)
        )
        jsonable, _ = is_jsonable(
            res, req_type, gen_posts_route(extra=True), SAMPLE_POST
        )
        self.assertTrue(jsonable, post_create_err)
        post_id = res.json().get("id")
        self.assertIsNotNone(post_id, post_create_err)
        body = {"upvotes": 2}
        res = requests.post(
            gen_posts_path(post_id, extra=True),
            data=json.dumps(body),
        )

        req_type = "GET"
        params = {"sort": "increasing"}
        route = gen_posts_route(extra=True, params=params)
        res = requests.get(gen_posts_path(extra=True, params=params))
        jsonable, error = is_jsonable(res, req_type, route)
        self.assertTrue(jsonable, error)
        self.assertEqual(
            res.status_code,
            200,
            status_code_error(res, route, res.status_code, 200),
        )
        posts = res.json().get("posts")
        self.assertEqual(
            type(posts),
            list,
            wrong_value_error(
                req_type,
                route,
                posts,
                "a (potentially empty) list of posts",
                "posts",
            ),
        )
        sorted_posts = sorted(posts, key=lambda x: x["upvotes"])

        def pretty_print_dic_lst(dic_lst):
            return [
                f"Post #{dic['id']}: {dic['upvotes']} upvote(s)"
                for dic in dic_lst
            ]

        pp_posts, pp_sorted_posts = pretty_print_dic_lst(
            posts
        ), pretty_print_dic_lst(sorted_posts)
        self.assertEqual(
            pp_posts, pp_sorted_posts, "The list is not in increasing order."
        )

        params = {"sort": "decreasing"}
        route = gen_posts_route(extra=True, params=params)
        res = requests.get(gen_posts_path(extra=True, params=params))
        jsonable, error = is_jsonable(res, req_type, route)
        self.assertTrue(jsonable, error)
        self.assertEqual(
            res.status_code,
            200,
            status_code_error(res, route, res.status_code, 200),
        )
        posts = res.json().get("posts")
        self.assertEqual(
            type(posts),
            list,
            wrong_value_error(
                req_type,
                route,
                posts,
                "a (potentially empty) list of posts",
                "posts",
            ),
        )
        sorted_posts = sorted(posts, key=lambda x: -x["upvotes"])
        pp_posts, pp_sorted_posts = pretty_print_dic_lst(
            posts
        ), pretty_print_dic_lst(sorted_posts)
        self.assertEqual(
            pp_posts, pp_sorted_posts, "The list is not in decreasing order."
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
    app.run(host="0.0.0.0", port=5000, debug=False)