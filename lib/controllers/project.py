import os
import logging
import lib.logger as logger
from lib.exception import *
from lib.models.models import Project
from lib.controllers.user import UserController
from lib.controllers.category import CategoryController
from lib.storage.project import ProjectStorage
from lib.storage.task import TaskStorage


class ProjectController:
    """
    The data handler for project. Allows to create/delete, edit name/description of project, add/remove users to/from
    project, return projects tasks of project users.

    """

    log_tag = "ProjectController"
    log = logger.get_logger(log_tag)

    @classmethod
    def create(cls, username, password, name, description):
        """
        Create a project with a specified name and description
        :param username: user, who want to create a new project
        :param password: user password
        :param name: name of new project
        :param description: description of new project
        :return: None. Project will be created in database
        """
        user = UserController.get_user_by_name(username)
        if user.password == password:
            projects = ProjectStorage.show_all_for_user(user)
            for project in projects:
                if project.name == name:
                    raise ProjectWithThisNameAlreadyExist
            project = Project(name=name, description=description, user_id=user.id)
            project.users.append(user)
            ProjectStorage.add_project_to_db(project, user)
            ProjectController.log.info("Project {} was successfully created by {}.".format(name, username))
        else:
            ProjectController.log.error("Incorrect password for {}".format(username))
            raise WrongPassword

    @classmethod
    def delete(cls, username, password, name):
        """
        Deletes the project with the specified name
        :param username: user, creator of project
        :param password: user password
        :param name: name of project to delete
        :return: None. Project will be deleted from database
        """
        user = UserController.get_user_by_name(username)
        if user.password == password:
            project = ProjectStorage.get_project_by_name(user, name)
            if  ProjectStorage.is_admin(username, project.id):
                guys = ProjectStorage.get_all_persons_in_project_by_id(project.id)
                for i in guys:
                    ProjectController.su_delete_person_from_project(username, password, i, project)
                ProjectStorage.delete_with_object(project)
                ProjectController.log.info("Project {} was successfully deleted by {}".format(name, username))
            else:
                raise UAreNotAdmin
        else:
            ProjectController.log.error("Incorrect password for {}".format(username))
            raise WrongPassword

    @classmethod
    def delete_by_id(cls, username, password, id):
        """
        Deletes the project with the specified id
        :param username: user, creator of project
        :param password: user password
        :param id: project id of project, which will be deleted
        :return: None. Project will be deleted from database
        """
        user = UserController.get_user_by_name(username)
        if user.password == password:
            if ProjectController.is_admin(user.username, id):
                project = ProjectStorage.get_project_by_id(id)
                guys = ProjectStorage.get_all_persons_in_project_by_id(project.id)
                categories = CategoryController.show_all(username, password, project)
                for category in categories:
                    CategoryStorage.delete_category_from_db(category)
                tasks = TaskStorage.get_all_project(project.id)
                for task in tasks:
                    TaskStorage.delete_task_from_db(task)
                guys = guys[::-1]
                for i in guys:
                    ProjectController.su_delete_person_from_project(username, password, i, project)
                ProjectStorage.delete_with_object(project)
                ProjectController.log.info("Project {} was successfully deleted by {}".format(project.name, username))
            else:
                ProjectController.log.error(
                    "User {} have no permission to delete a {} project".format(username, project.id))
                raise NoPermission
        else:
            ProjectController.log.error("Incorrect password for {}".format(username))
            raise WrongPassword

    @classmethod
    def add_person_to_project(cls, username, password, project_id, person):
        """
        Adds an artist to the project
        :param username: name of project creator
        :param password: creator password
        :param person: the name of the user you want to add to the project
        :param project_id: id of project
        :return: None. Person will be added to project
        """
        admin = UserController.get_user_by_name(username)
        if type(person) == int:
            person = UserController.get_user_by_id(person)
        if admin.password == password:
            if ProjectController.is_admin(admin.username, project_id):
                userlist = ProjectStorage.get_all_persons_in_project_by_id(project_id)
                have = False
                for user in userlist:
                    if user.id == person.id:
                        have = True
                if have == False:
                    ProjectStorage.add_person_to_project(person, project_id)
                    ProjectController.log.info("User was successfully added to project")
                else:
                    ProjectController.log.error("User {} is already exist in this project".format(username))
                    raise UserAlreadyExistInProject
            else:
                ProjectController.log.error("You are not the creator of the project")
                raise UAreNotAdmin
        else:
            ProjectController.log.error("Incorrect password for {}".format(username))
            raise WrongPassword

    @classmethod
    def delete_person_from_project(cls, username, password, project, person):
        """
        The removal of the contractor from the project
        :param username: username of creator
        :param password: creator password
        :param person: person to delete
        :param project: instance of project
        :return: None. User will be deleted from database
        """
        admin = UserController.get_user_by_name(username)
        if type(project) == int:
            project = ProjectController.get_project_by_id(username, password, project)
        if type(person) == int:
            person = UserController.get_user_by_id(person)
        if admin.password == password:
            if ProjectController.is_admin(admin.username, project.id):
                guys = ProjectStorage.get_all_persons_in_project_by_id(project.id)
                have = False
                if int(project.user_id) == person.id:
                    ProjectController.log.error("{} was tried to delete a creator of the project".format(username))
                    raise CannotDeleteCreator
                for i in range(len(guys)):
                    if guys[i].id == person.id:
                        have = True
                if not have:
                    ProjectController.log.error("User {} is not exist".format(person.username))
                    raise UserIsNotExistInProject
                else:
                    ProjectStorage.delete_person_from_project(person, project)
                    ProjectController.log.info(
                        "User {} was successfully deleted from the project".format(person.username))
            else:
                ProjectController.log.error("{} are not the Creator of the project".format(username))
                raise UAreNotAdmin
        else:
            ProjectController.log.error("Incorrect password for {}".format(username))
            raise WrongPassword

    @classmethod
    def su_delete_person_from_project(cls, username, password, person, project):
        """
        Delete all the workers from the project, you can also delete the project Creator
        :param username: name of creator
        :param password: creator password
        :param person: person to delete
        :param project_id: project id
        :return: None. Person will be deleted from project
        """
        admin = UserController.get_user_by_name(username)
        person = UserController.get_user_by_id(person.id)
        if admin.password == password:
            ProjectController.is_admin(admin.username, project.id)
            guys = ProjectStorage.get_all_persons_in_project_by_id(project.id)
            have = False
            for i in range(len(guys)):
                if guys[i].id == person.id:
                    have = True
            if not have:
                ProjectController.log.error("User with id {} is not exist".format(person.id))
                raise UserIsNotExistInProject
            else:
                ProjectStorage.delete_person_from_project(person, project)
                ProjectController.log.info("User {} was sucessfully deleted from the project".format(person.username))
        else:
            ProjectController.log.error("Incorrect password for {}".format(username))
            raise WrongPassword

    @classmethod
    def edit_name_by_id(cls, username, password, project_id, new_name):
        """
        Editing the project name
        :param username: name of project creator
        :param password: creator password
        :param project_name: name of the project to be changed
        :param new_name: new name of project
        :return: None. Project name will be edited in database
        """
        person = UserController.get_user_by_name(username)
        project = ProjectController.get_project_by_id(username, password, project_id)
        projects = ProjectController.show_all(username, password)
        if person.password == password:
            ProjectController.is_admin(person.username, project.id)
            for pr in projects:
                if pr.name == new_name:
                    raise ProjectWithThisNameAlreadyExist
            project.name = new_name
            ProjectStorage.save(project)
            ProjectController.log.info("Name of the project {} was successfully edited".format(project.name))
        else:
            ProjectController.log.error("Incorrect password for {}".format(username))
            raise WrongPassword

    @classmethod
    def edit_description_by_id(cls, username, password, project_id, new_desc):
        """
        Editing the project description
        :param username: name of project creator
        :param password: creator password
        :param project_name: name of the project to be changed
        :param new_desc: new description of project
        :return: None. Project description will be edited in database
        """
        person = UserController.get_user_by_name(username)
        project = ProjectController.get_project_by_id(username, password, project_id)
        if person.password == password:
            ProjectController.is_admin(person.username, project.id)
            project.description = new_desc
            ProjectStorage.save(project)
            ProjectController.log.info("Description of the project {} was successfully edited".format(project.name))
        else:
            ProjectController.log.error("Incorrect password for {}".format(username))
            raise WrongPassword

    @classmethod
    def get_project_tasks(cls, username, password, project):
        """
        Return all tasks that situated in project
        :param username: name of user who gonna take this information
        :param password: user password
        :param project: project to check
        :return: List that containt objects 'task' type
        """
        categories = CategoryController.show_all(username, password, project)
        task_list = []
        for category in categories:
            tasks = TaskStorage.get_all_tasks(category.id)
            task_list = task_list + tasks
        available_tasks = []
        canceled_tasks = []
        for task in task_list:
            if task.is_archive == 0:
                available_tasks.append(task)
            else:
                canceled_tasks.append(task)
        task_list = available_tasks + canceled_tasks
        ProjectController.log.info("All tasks of {} was returned".format(project.name))
        return task_list

    @classmethod
    def get_project_user_info(cls, project_id):
        """
        Return info about users who work in project. Who is creator and who is executor
        :param project_id: id of project info about user want to find
        :return: two 'user' object. Creator - project creator, guys - project executors
        """
        guys = list(ProjectStorage.get_all_persons_in_project_by_id(project_id))
        project = ProjectController.get_project_by_id('1','1',project_id)
        creator = UserController.get_user_by_id(project.user_id)
        for i in guys:
            if i.id == creator.id:
                guys.remove(i)
        ProjectController.log.info(
            "Information of executors project with id {} was successfully returned".format(project_id))
        return creator, guys

    @classmethod
    def get_project_by_id(cls, username, password, id):
        """
        Return project with specified id
        :param username: username
        :param password: user password
        :param id: if of project which user wanna find
        :return: Project with 'id' id.
        """
        project = ProjectStorage.get_project_by_id(id)
        if project == None:
            raise NoProjectWithThisId
        return project

    @classmethod
    def get_all_user_categories(cls, username, password):
        """
        Return all categories, where user consist as executor or creator
        :param username: user, the category for which you want to get
        :param passwowd: user password
        :return: List 'cats' thhat contain all categories of all projects in where user exist or 'None' if there is
        no categories
        """
        user = UserController.get_user_by_name(username)
        projects = ProjectController.show_all(username, password)
        cats = []
        if user.password == password:
            for project in projects:
                categories = CategoryController.show_all(username, password, project)
                cats = cats + categories
                ProjectController.log.info("All categories for {} was returned".format(username))
            return cats
        else:
            ProjectController.log.error("Incorrect password for {}".format(username))
            raise WrongPassword

    @classmethod
    def is_admin(cls, username, project_id):
        """
        Checks whether the specified user is the creator of the project
        :param person: the supposed creator
        :param project: project to check
        :return: True of False depending on whether the user is the creator
        """
        user = UserController.get_user_by_name(username)
        project = ProjectController.get_project_by_id(user.username, user.password, project_id)
        guys = ProjectStorage.get_all_persons_in_project_by_id(project.id)
        if int(project.user_id) == user.id:
            return True
        else:
            return False

    @classmethod
    def check_permission(cls, username, password, project_id):
        """
        Checks whether the specified user is participating in the project
        :param person: the supposed worker
        :param project: project to check
        :return: True of False depending on whether the user is the executor
        """
        user = UserController.get_user_by_name(username)
        project = ProjectController.get_project_by_id(username, user.password, project_id)
        guys = ProjectStorage.get_all_persons_in_project_by_id(project.id)
        for i in guys:
            if i.id == user.id:
                return True
        ProjectController.log.error("User {} have no permissions in {} project".format(username, project.name))
        raise NoPermission

    @classmethod
    def show(cls, username, password, project_id):
        """
        Return all project information. 'project' object, all it categories, tasks and info about project users
        :param username: username
        :param password: user password
        :param project_id: id of project
        :return: dict with info about project: name, info, categories, tasks, executors
        """
        project = ProjectController.get_project_by_id(username, password, project_id)
        if ProjectController.check_permission(username, password, project.id):
            categories = CategoryController.get_all_categories(username, password, project)
            task_list = ProjectController.get_project_tasks(username, password, project)
            creator, guys, = ProjectController.get_project_user_info(project_id)
            ProjectController.log.info(
                "Information about {} was successfully returned to {}".format(project.name, username))
            return {'project': project, 'categories': categories, 'tasks': task_list, 'creator': creator, 'guys': guys}
        else:
            raise NoPermission

    @classmethod
    def show_all(cls, username, password):
        """
        Displays a list of all projects in which user work
        :param username: user which want to find information
        :param password: user password
        :return: List with 'project' objects
        """
        user = UserController.get_user_by_name(username)
        new_list = []
        if user.password == password:
            project_list = ProjectStorage.show_all()
            for project in project_list:
                have = False
                guys = ProjectStorage.get_all_persons_in_project_by_id(project.id)
                for guy in guys:
                    if user.id == guy.id:
                        have = True
                if have:
                    new_list.append(project)
        else:
            ProjectController.log.error("Incorrect password for {}".format(username))
            raise WrongPassword
        ProjectController.log.info("List with all project for {} was successfully returned".format(username))
        return new_list
