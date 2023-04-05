import json
import os
from db import db
from db import Course
from db import Assignment
from db import User
from flask import Flask
from flask import request

app = Flask(__name__)
db_filename = "cms.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

# Success response.
def success_request(data, code = 200):
    return json.dumps(data), code

# Failure response.
def failure_request(message, code = 404):
    return json.dumps({"error": message}), code

# Greet.
@app.route("/")
def greet():
    """
    Endpoint for greeting the user by reading the netid in the .env file.
    """
    return os.environ.get("NETID") + " was here!"

# Get all courses.
@app.route("/api/courses/")
def get_courses():
    courses = [course.serialize() for course in Course.query.all()]
    return success_request({"courses": courses})

# Create a course.
@app.route("/api/courses/", methods=["POST"])
def create_course():
    # Load and check the request.
    body = json.loads(request.data)
    if body == None:
        return failure_request("Empty request!", 400)
    code = body.get("code")
    name = body.get("name")
    if (code == None or name == None):
        return failure_request("Incomplete request!", 400)
    if (type(code) is not str or type(name) is not str):
        return failure_request("Wrong data type! Require strings", 400)

    # Create a new course.
    new_course = Course(code = code, name = name)
    db.session.add(new_course)
    db.session.commit()
    return success_request(new_course.serialize(), 201)

# Get a specific course by id.
@app.route("/api/courses/<int:course_id>/")
def get_course(course_id):
    course = Course.query.filter_by(id=course_id).first()
    if course == None:
        return failure_request("Course not found!")
    return success_request(course.serialize())

# Delete a specific course by id.
@app.route("/api/courses/<int:course_id>/", methods=["DELETE"])
def delete_course(course_id):
    course = Course.query.filter_by(id = course_id).first()
    if course == None:
        return failure_request("Course not found!")
    db.session.delete(course)
    db.session.commit()
    return success_request(course.serialize(), 200)

# Create a user.
@app.route("/api/users/", methods=["POST"])
def create_user():
    # Load and check the request.
    body = json.loads(request.data)
    if body == None:
        return failure_request("Empty request!", 400)
    name = body.get("name")
    netid = body.get("netid")
    if (netid == None or name == None):
        return failure_request("Incomplete request!", 400)
    if (type(netid) is not str or type(name) is not str):
        return failure_request("Wrong data type! Require strings", 400)
    
    # Create and add the new user.
    new_user = User(name = name, netid = netid)
    db.session.add(new_user)
    db.session.commit()
    return success_request(new_user.serialize(), 201)

# Get a specific user by id
@app.route("/api/users/<int:user_id>/")
def get_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user == None:
        return failure_request("User not found!")
    return success_request(user.serialize())

# Add a user to a course.
@app.route("/api/courses/<int:course_id>/add/", methods=["POST"])
def add_user_to_course(course_id):
    # Load and check the request.
    body = json.loads(request.data)
    if body == None:
        return failure_request("Empty request!", 400)
    user_id = body.get("user_id")
    user_type = body.get("type")
    if (user_id == None or user_type == None):
        return failure_request("Incomplete request!", 400)
    if (type(user_id) is not int or type(user_type) is not str):
        return failure_request("Wrong data type!", 400)
    
    # Check whether the course and the student exists.
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return failure_request("Course not found!")
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_request("User not found!")
    
    # Add the student to student list, instructor to the instructor list.
    if user_type == "student":
        course.students.append(user)
    else:
        course.instructors.append(user)
    db.session.commit()
    
    return success_request(course.serialize())

# Create an assignment for a course.
@app.route("/api/courses/<int:course_id>/assignment/", methods=["POST"])
def create_assignment_for_course(course_id):
    # Load and check the request.
    body = json.loads(request.data)
    if body == None:
        return failure_request("Empty request!", 400)
    title = body.get("title")
    due_date = body.get("due_date")
    if (title == None or due_date == None):
        return failure_request("Incomplete request!", 400)
    if (type(title) is not str or type(due_date) is not int):
        return failure_request("Wrong data type!", 400)

    # Check whether the course exists.
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return failure_request("Course not found!")
    
    # Create and add a new assignment.
    new_assignment = Assignment(title = title, due_date = due_date, course_id = course_id)
    db.session.add(new_assignment)
    db.session.commit()
    return success_request(new_assignment.serialize(), 201)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
