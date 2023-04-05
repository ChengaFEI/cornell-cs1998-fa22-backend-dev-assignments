from multiprocessing.sharedctypes import Value
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Association between courses and students.
student_association_table = db.Table(
  "student_association", 
  db.Model.metadata,
  db.Column("course_id", db.Integer, db.ForeignKey("courses.id"), nullable = False),
  db.Column("student_id", db.Integer, db.ForeignKey("users.id"), nullable = False)
)

# Association between courses and instructors.
instructor_association_table = db.Table(
  "instructor_association", 
  db.Model.metadata,
  db.Column("course_id", db.Integer, db.ForeignKey("courses.id"), nullable = False),
  db.Column("instructor_id", db.Integer, db.ForeignKey("users.id"), nullable = False)
  )

class Course(db.Model):
  __tablename__ = "courses"
  id = db.Column(db.Integer, primary_key = True, auto_increment = True)
  code = db.Column(db.String, nullable = False)
  name = db.Column(db.String, nullable = False)
  assignments = db.relationship("Assignment", cascade = "delete")
  students = db.relationship("User", secondary = student_association_table, back_populates = "student_courses")
  instructors = db.relationship("User", secondary = instructor_association_table, back_populates = "instructor_courses")
  # Initialize a Course instance.
  def __init__(self, **kwargs):
    self.code = kwargs.get("code", "")
    self.name = kwargs.get("name", "")
  # Serialize the Course instance.
  def serialize(self):
    # Serialize assignments without their courses.
    assignments = [
      {
        "id": assignment.id,
        "title": assignment.title,
        "due_date": assignment.due_date
      } 
      for assignment 
      in self.assignments
    ]
    # Serialize instructors without their courses.
    instructors = [
      {
        "id": instructor.id,
        "name": instructor.name,
        "netid": instructor.netid
      } 
      for instructor 
      in self.instructors
    ]
    # Serialize students without their courses.
    students = [
      {
        "id": student.id,
        "name": student.name,
        "netid": student.netid
      } 
      for student
      in self.students
    ]
    return {
      "id": self.id,
      "code": self.code,
      "name": self.name,
      "assignments": assignments,
      "instructors": instructors,
      "students": students
    }

class Assignment(db.Model):
  __tablename__ = "assignments"
  id = db.Column(db.Integer, primary_key = True, auto_increment = True)
  title = db.Column(db.String, nullable = False)
  due_date = db.Column(db.Integer, nullable = False)
  course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable = False)
  # Initialize an Assignment instance.
  def __init__(self, **kwargs):
    self.title = kwargs.get("title", "")
    self.due_date = kwargs.get("due_date", 0)
    self.course_id = kwargs.get("course_id", 0)
  # Serialize the Assignment instance.
  def serialize(self):
    # Serialize courses without their assignments, instructors, and students field.
    course = Course.query.filter_by(id=self.course_id).first()
    return {
      "id": self.id,
      "title": self.title,
      "due_date": self.due_date,
      "course": {
        "id": course.id,
        "code": course.code,
        "name": course.name
      }
    }

class User(db.Model):
  __tablename__ = "users"
  id = db.Column(db.Integer, primary_key = True, auto_increment = True)
  name = db.Column(db.String, nullable = False)
  netid = db.Column(db.String, nullable = False)
  student_courses = db.relationship("Course", secondary = student_association_table, back_populates = "students")
  instructor_courses = db.relationship("Course", secondary = instructor_association_table, back_populates = "instructors")
  # Initialize a Student instance.
  def __init__(self, **kwargs):
    self.name = kwargs.get("name", "")
    self.netid = kwargs.get("netid", "")
  # Serialize the Student instance.
  def serialize(self):
    # Serialize courses without their assignments, instructors, and students field.
    courses = [
      {
        key: value
        for key, value
        in course.serialize().items()
        if key not in ["assignments", "instructors", "students"]
      }
      for course
      in self.student_courses or self.instructor_courses
    ]
    return {
      "id": self.id,
      "name": self.name,
      "netid": self.netid,
      "courses": courses
    }