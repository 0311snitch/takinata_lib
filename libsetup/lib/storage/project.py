import sqlite3
import copy
import lib.conf as conf
from lib.exception import *
from lib.models.models import *
from lib.controllers.user import UserController
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker

engine = create_engine(conf.get_path_to_db())
Session = sessionmaker(bind=engine)
session = Session()


class ProjectStorage:
    @classmethod
    def add_project_to_db(cls, project, user):
        """
        Add an instance of the Project class to the database
        :param project: the instance of the Project class that you want to add
        :param user: an instance of the User class that is the Creator of the project
        :return: None. Project added to database
        """
        all_projectnames = session.query(Project).all()
        yep = False
        for i in all_projectnames:
            if project.name == i.name and user.id == i.user_id:
                yep = True
        if not yep:
            session.add(project)
            session.commit()
            session.close()
        else:
            raise ProjectWithThisNameAlreadyExist()

    @classmethod
    def get_all_persons_in_project_by_id(cls, project_id):
        """
        Return list of persons that exists in project
        :param project: project to check
        :return: list of executors
        """
        pr = session.query(Project).filter(Project.id == project_id).first()
        to_send = pr.users
        # to_send = to_send[::-1]
        session.close()
        return to_send

    @classmethod
    def add_person_to_project(cls, person, project):
        """
        Adds the specified user to the project if the command was executed on behalf of the project creator
        :param person: person to add to the project
        :param project: project where you want to add the user
        :return: None. User was added to database
        """
        new_project = session.query(Project).filter(Project.id == project).first()
        new_project.users.append(person)
        session.commit()
        session.close()

    @classmethod
    def is_admin(cls, username, project_id):
        """
        Checks whether the specified user is the creator of the project
        :param person: the supposed creator
        :param project: project to check
        :return: True of False depending on whether the user is the creator
        """
        user = UserController.get_user_by_name(username)
        project = ProjectStorage.get_project_by_id(project_id)
        guys = ProjectStorage.get_all_persons_in_project_by_id(project.id)
        if int(project.user_id) == user.id:
            return True
        else:
            return False

    @classmethod
    def check_permission(cls, username, project_id):
        """
        Checks whether the specified user is participating in the project
        :param person: the supposed worker
        :param project: project to check
        :return: True of False depending on whether the user is the executor
        """
        user = UserController.get_user_by_name(username)
        project = ProjectStorage.get_project_by_id(project_id)
        guys = ProjectStorage.get_all_persons_in_project_by_id(project.id)
        for i in guys:
            if i.id == user.id:
                return True
        raise NoPermission

    @classmethod
    def delete_person_from_project(cls, person, project):
        """
        Remove the specified user from the project
        :param person: person to remove
        :param project: project where you want to remove the user
        :return: None. User was deleted from project
        """
        new_project = session.query(Project).filter(Project.id == project.id).first()
        delUser = None
        for user in new_project.users:
            if user.id == person.id:
                delUser = user
        new_project.users.remove(delUser)
        session.commit()
        session.close()

    @classmethod
    def delete_with_object(cls, project):
        """
        Delete the specified project that was passed in the arguments
        :param project: project whitch you want to delete
        :return: None. Project was deleted
        """
        session.delete(project)
        session.commit()
        session.close()

    @classmethod
    def get_project_by_name(cls, user, name):
        """
        Getting the project with the specified name from the database
        :param name: name of the project
        :return: project with that name
        """
        project = session.query(Project).filter(Project.name == name and Project.user_id == user.id).first()
        session.close()
        return project

    @classmethod
    def get_project_by_id(cls, pid):
        """
        Getting the project with the specified name from the database
        :param name: name of the project
        :return: project with that id
        """
        project = session.query(Project).filter(Project.id == pid).first()
        session.close()
        return project

    @classmethod
    def show_all(cls):
        """
        Displays a list of all projects in which the specified user is involved
        :return: project list
        """
        projects = session.query(Project).all()
        session.close()
        return projects

    @classmethod
    def save(self, project):
        """
        Saves the transferred instance of the Project class to the database
        :param project: project to save
        :return: None. Project was saved in database
        """
        new_project = session.query(Project).filter(Project.id == project.id).first()
        new_project.name = project.name
        new_project.description = project.description
        session.commit()
        session.close()
