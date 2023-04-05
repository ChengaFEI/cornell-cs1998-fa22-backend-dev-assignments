import json
import re

from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)

# all stored posts.
posts = {
    0: {
        "id": 0,
        "upvotes": 1,
        "title": "My cat is the cutest!",
        "link": "https://i.imgur.com/jseZqNK.jpg",
        "username": "alicia98",
    },
    1: {
        "id": 1,
        "upvotes": 3,
        "title": "Cat loaf",
        "link": "https://i.imgur.com/TJ46wX4.jpg",
        "username": "alicia98",
    }
}
# all stored comments.
"""
structure:
comments_allposts = {
    0 (post_id): {
        0 (comment_id): {
            "id": 0 (comment_id),
            "upvotes": 8,
            "text": "Wow, my first Reddit gold!",
            "username": "alicia98",
        },
        1: {
            ...
        }
    },
    1: {
        ...
    }
}
"""
comments_allposts = {}

# record next post's id.
post_id_count = 2
# record next comment's id.
comment_id_count = 0

"""
greeting.
"""
@app.route("/")
def hello_world():
    return "Hello world!"


# your routes here

"""
get all posts.
"""
@app.route("/api/posts/")
def get_posts():
    # return all posts.
    return json.dumps({"posts": list(posts.values())}), 200

"""
create a post and update "posts" dictionary.
"""
@app.route("/api/posts/", methods = ["POST"])
def create_post():
    global post_id_count
    # retrieve the new post.
    body = json.loads(request.data)
    # Check to ensure body is not None.
    if body is None:
        return json.dumps({"error": "No post found!"}), 404
    # get messages.
    title = body.get("title")
    link = body.get("link")
    username = body.get("username")
    # make sure all three messages are provided.
    if title is None or link is None or username is None:
        # report the bad request error with the status code of 400.
        return json.dumps({"error": "bad request: messages are incomplete"}), 400
    # initialize a new task.
    post = {
        "id": post_id_count,
        "upvotes": 1, # default the upvotes of the new post to 1.
        "title": title,
        "link": link,
        "username": username
    }
    # update the posts dictionary.
    posts[post_id_count] = post
    # increment the id_count.
    post_id_count += 1
    return json.dumps(post), 201

"""
get one post by its id.
"""
@app.route("/api/posts/<int:post_id>/")
def get_post(post_id):
    # get the post by post_id.
    post = posts.get(post_id)
    # if the post doesn't exist.
    # report the not found error message with the status code of 404.
    if post is None:
        return json.dumps({"error": "post not found"}), 404
    # if the post exists, return the post and the status code of 200.
    return json.dumps(post), 200

"""
delete a post by its id.
"""
@app.route("/api/posts/<int:post_id>/", methods = ["DELETE"])
def delete_post(post_id):
    # get the post from posts dictionary by id.
    post = posts.get(post_id)
    # if the post doesn't exist.
    # report the not found error message with the status code of 404.
    if post is None:
        return json.dumps({"error": "post not found"}), 404
    # if the post exists.
    # delete it from the posts dictionary.
    # and return the post and the status code of 200.
    del posts[post_id]
    return json.dumps(post), 200

"""
get comments for a specific post.
"""
@app.route("/api/posts/<int:post_id>/comments/")
def get_comments(post_id):
    # retrieve comments by the post id.
    comments_onepost = comments_allposts.get(post_id)
    # if comments of that post doesn't exist,
    # report the not found error with the status code of 404.
    if comments_onepost is None:
        return json.dumps({"error": "comments not found"}), 404
    # if comments exist,
    # return comments with the status code of 200.
    return json.dumps({"comments": list(comments_onepost.values())}), 200

"""
Post a comment for a specific post.
"""
@app.route("/api/posts/<int:post_id>/comments/", methods = ["POST"])
def create_comment(post_id):
    # check whether the post exists.
    post = posts.get(post_id)
    if post is None:
        return {"error": "post not found"}, 404
    # get the global variable comment_id_count.
    global comment_id_count
    # get the comment messages from the POST request.
    body = json.loads(request.data)
    # Check to ensure body is not None.
    if body is None:
        return json.dumps({"error": "No post found!"}), 404
    # retrieve the text and username info from body.
    text = body.get("text")
    username = body.get("username")
    # if any of these messages is missing,
    # report the bad request error with the status code of 400.
    if text is None or username is None:
        return json.dumps({"error": "bad request error: comment messages are incomplete"}), 400
    # if messages are complete, create a dictionary of this comment info.
    comment = {
        "id":  comment_id_count,
        "upvotes": 1, # default the upvotes of new comments to 1.
        "text": text,
        "username": username
    }
    # retrieve existing comments.
    comments_onepost = comments_allposts.get(post_id)
    # if there're no existing comments yet, initialize an empty dictionary.
    if comments_onepost is None:
        comments_onepost = {}
    # add current comment to the dictionary.
    comments_onepost[comment_id_count] = comment
    comments_allposts[post_id] = comments_onepost
    # increment the comment id count by 1.
    comment_id_count += 1
    # return the comment with the status code of 201.
    return json.dumps(comment), 201

"""
Edit a comment for a specific post.
"""
@app.route("/api/posts/<int:post_id>/comments/<int:comment_id>/", methods = ["POST"])
def edit_comment(post_id, comment_id):
    # get the comment messages from the request.
    body = json.loads(request.data)
    # Check to ensure body is not None.
    if body is None:
        return json.dumps({"error": "No post found!"}), 404
    # retrieve the text from body.
    text = body.get("text")
    # check the request.
    # if the text is missing, report the bad request error with the status code of 400.
    if text is None:
        return json.dumps({"error": "bad request error: text is missing"}), 400
    # get all comments by the post id.
    comments_onepost = comments_allposts.get(post_id)
    # if there're no comments for this post, report not found error with the status code of 404.
    if comments_onepost is None:
        return json.dumps({"error": "not found error: no comments for the post"}), 404
    # if comments exist, get the specific comment by the comment_id.
    comment = comments_onepost.get(comment_id)
    # if this comment doesn't exist, report not found error with the status code of 404.
    if comment is None:
        return json.dumps({"error": "not found error: this comment doesn't exist"}), 404
    # if the comment exists, change the text.
    comment["text"] = text
    # update the comment.
    comments_onepost[comment_id] = comment
    comments_allposts[post_id] = comments_onepost
    # return the updated comment with the status code of 200.
    return json.dumps(comment), 200

"""
Belows are extra routes for challenge credits.
"""
# extra routes start.

# Tier I.

"""
create a post and update "posts" dictionary.
check the type preconditions and logical preconditions.
"""
@app.route("/api/extra/posts/", methods = ["POST"])
def extra_create_post():
    global post_id_count
    # retrieve the new post.
    body = json.loads(request.data)
    # Check to ensure body is not None.
    if body is None:
        return json.dumps({"error": "No post found!"}), 404
    # get messages.
    title = body.get("title")
    link = body.get("link")
    username = body.get("username")
    # make sure all three messages are provided.
    if title is None or link is None or username is None:
        # report the bad request error with the status code of 400.
        return json.dumps({"error": "bad request: messages are incomplete"}), 400
    # check type precondition.
    if type(title) is not str or type(link) is not str or type(username) is not str:
        # report the bad request error with the status code of 400 if the input type is wrong.
        return json.dumps({"error": "bad request error: input types are incorrect"}), 401 # This should be 400?
    # check logical precondition. (invalid URL)
    pat = re.compile(r"(http(s)?://)?([\w-]+\.)+?[\w-]+[.com]+(/[/?%&=]*)?")
    if (not re.fullmatch(pat, link)):
        # report the bad request error with the status code of 400 if the link is invalid.
        return json.dumps({"error": "bad request error: invalid url"}), 400
    # initialize a new task.
    post = {
        "id": post_id_count,
        "upvotes": 1, # default the upvotes of the new post to 1.
        "title": title,
        "link": link,
        "username": username
    }
    # update the posts dictionary.
    posts[post_id_count] = post
    # increment the id_count.
    post_id_count += 1
    return json.dumps(post), 201

"""
Post a comment for a specific post.
check the type preconditions and logical preconditions.
"""
@app.route("/api/extra/posts/<int:post_id>/comments/", methods = ["POST"])
def extra_create_comment(post_id):
    # check whether the post exists.
    post = posts.get(post_id)
    if post is None:
        return {"error": "post not found"}, 404
    # get the global variable comment_id_count.
    global comment_id_count
    # get the comment messages from the POST request.
    body = json.loads(request.data)
    # Check to ensure body is not None.
    if body is None:
        return json.dumps({"error": "No post found!"}), 404
    # retrieve the text and username info from body.
    text = body.get("text")
    username = body.get("username")
    # if any of these messages is missing,
    # report the bad request error with the status code of 400.
    if text is None or username is None:
        return json.dumps({"error": "bad request error: comment messages are incomplete"}), 400
    # check the input types - must be strings.
    if (type(text) is not str or type(username) is not str):
        # if types are incorrect, report the bad request error with the status code of 400.
        return json.dumps({"error": "bad request error: incorrect input types"}), 401
    # if messages are complete, create a dictionary of this comment info.
    comment = {
        "id":  comment_id_count,
        "upvotes": 1, # default the upvotes of new comments to 1.
        "text": text,
        "username": username
    }
    # retrieve existing comments.
    comments_onepost = comments_allposts.get(post_id)
    # if there're no existing comments yet, initialize an empty dictionary.
    if comments_onepost is None:
        comments_onepost = {}
    # add current comment to the dictionary.
    comments_onepost[comment_id_count] = comment
    comments_allposts[post_id] = comments_onepost
    # increment the comment id count by 1.
    comment_id_count += 1
    # return the comment with the status code of 201.
    return json.dumps(comment), 201

"""
Edit a comment for a specific post.
check the type preconditions.
"""
@app.route("/api/extra/posts/<int:post_id>/comments/<int:comment_id>/", methods = ["POST"])
def extra_edit_comment(post_id, comment_id):
    # get the comment messages from the request.
    body = json.loads(request.data)
    # Check to ensure body is not None.
    if body is None:
        return json.dumps({"error": "No post found!"}), 404
    # retrieve the text from body.
    text = body.get("text")
    # check the request.
    # if the text is missing, report the bad request error with the status code of 400.
    if text is None:
        return json.dumps({"error": "bad request error: text is missing"}), 400
    # check the type - must be str.
    if type(text) is not str:
        # if the type is not str, report the bad request error with the status code of 400.
        return json.dumps({"error": "bad request error: invalid input type"}), 401
    # get all comments by the post id.
    comments_onepost = comments_allposts.get(post_id)
    # if there're no comments for this post, report not found error with the status code of 404.
    if comments_onepost is None:
        return json.dumps({"error": "not found error: no comments for the post"}), 404
    # if comments exist, get the specific comment by the comment_id.
    comment = comments_onepost.get(comment_id)
    # if this comment doesn't exist, report not found error with the status code of 404.
    if comment is None:
        return json.dumps({"error": "not found error: this comment doesn't exist"}), 404
    # if the comment exists, change the text.
    comment["text"] = text
    # update the comment.
    comments_onepost[comment_id] = comment
    comments_allposts[post_id] = comments_onepost
    # return the updated comment with the status code of 200.
    return json.dumps(comment), 200

# Tier II.

"""
increment the upvotes value of a post.
check the type preconditions - must be int.
"""
@app.route("/api/extra/posts/<int:post_id>/", methods = ["POST"])
def increment_post_upvotes(post_id):
    # get the post by id.
    post = posts.get(post_id)
    # if the post doesn't exist, report not found error (404).
    if post is None:
        return json.dumps({"error": "post not found"}), 404
    # get the request body.
    body = json.loads(request.data)
    # if the requst body is None, increment the upvote by 1.
    if body is None:
        post["upvotes"] += 1
        return json.dumps(post), 200
    # if the upvote is not specified, increment by 1.
    increment = body.get("upvotes")
    if increment is None:
        post["upvotes"] += 1
        return json.dumps(post), 200
    # check the type of upvotes - must be int.
    if type(increment) is not int:
        return json.dumps({"error": "input type incorrect"}), 400
    # increment the upvote.
    post["upvotes"] += increment
    # return the updated post with the status code 200.
    return json.dumps(post), 200

"""
sort through URL parameters.
"""
@app.route("/api/extra/posts/")
def get_sorted_posts():
    # get the sorting instruction.
    sort = request.args.get("sort", default="*")
    # check the type and content - must be str and one of the "increasing" and "decreasing".
    if (type(sort) is not str or (sort!="increasing" and sort!="decreasing")):
        return json.dumps({"error": "bad request"}), 400
    # sort posts increasingly.
    if sort == "increasing":
        res = list(sorted(posts.values(), key = lambda value: value["upvotes"]))
    # sort posts decreasingly.
    else:
        res = list(sorted(posts.values(), key = lambda value: value["upvotes"], reverse = True))
    # return sorted posts.
    return json.dumps({"posts": res}), 200

# extra routes end.

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
