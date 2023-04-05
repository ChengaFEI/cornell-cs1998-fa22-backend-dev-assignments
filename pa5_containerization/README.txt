Name: Cheng Fei
NetID: cf482

Challenges Attempted: Tier I/II
For Tier I:
I installed Anaconda distribution. It offers a GUI to manage Python source code, programs, and dependencies. Also, it provides a cloud environment. Anaconda is very useful for data science since it integrates a bunch of data science packages for Python.

Working Endpoint: GET /api/courses/
Your Docker Hub Repository Link: https://hub.docker.com/repository/docker/chengafei/pa5

Questions:
Explain the concept of containerization in your own words.
Containerization is the packaging of the software source code with the required dependencies (libraries/binaries) to create an executable file (container) in an isolated process that is operable/runnable across platforms and operating systems.

What is the difference between a Docker image and a Docker container?
The relationship between a Docker image and a Docker container is similar to that between a blueprint and a building. A Docker image is a read-only file that records the essential data of the contained software and the supporting files. A Docker container is a read-write copy built based on the Docker image that allows modification.

What is the command to list all Docker images?
docker images

What is the command to list all Docker containers?
docker ps

What is a Docker tag, and what is it used for?
A Docker tag is the name of a Docker image. It identifies a Docker file, especially from a remote Docker repository.

What is Docker Hub, and what is it used for?
Docker hub is the Docker images library. It stores Docker images from local users and shares them across operating systems and users. 

What is Docker compose used for?
Docker-compose file automates rapid execution of containerized software.

What is the difference between the RUN and CMD commands?
Both commands automate shell commands. But the CMD command only calls the executing instruction, like "python3 app.py"; all other shell commands are execute by the RUN command. 