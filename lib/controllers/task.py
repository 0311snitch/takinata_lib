import lib.logger as logger
from datetime import *
from lib.exception import *
from lib.models.models import Task
from lib.storage.category import CategoryStorage
from lib.controllers.project import ProjectController
from lib.controllers.category import CategoryController
from lib.storage.project import ProjectStorage
from lib.storage.task import TaskStorage
from lib.controllers.user import UserController


class TaskController:
    """
    The data handler for the Task. Allows to add/delete task, edit, assosiate with other task, set subtask.

    """

    log_tag = "TaskController"
    log = logger.get_logger(log_tag)

    @classmethod
    def add_task(cls, username, password, project_id, category_id, name, desc, type, start_date, start_time, end_date,
                 end_time,
                 priority, parent_task_id=None, assosiated_task_id=None, to_deadline=None):
        """
        Created task with specified project, category etc.
        :param username: user who want create a task
        :param password: user task
        :param project_id: id of project where user want to add task
        :param category_id: id of category to add task
        :param name: task name
        :param desc: task description
        :param type: type of task (one-time or regular)
        :param start_date: date of start task (datetime)
        :param start_time: time to start task
        :param end_date: date of end task (datetime)
        :param end_time: time to end task
        :param priority: task priority (max/min/mid)
        :param parent_task_id: if task - is subtask, parent_task_id - id of parent task
        :param assosiated_task_id: id of task assosiated with
        :param to_deadline:
        :return: None. Task will be atted to database
        """
        user = UserController.get_user_by_name(username)
        if user.password == password:
            period = None
            if (start_date == "" or start_date == None) or (end_date == "" or end_date == None):
                pass
            else:
                start = datetime.strptime(start_date, '%m/%d/%Y')
                end = datetime.strptime(end_date, '%m/%d/%Y')
                today = datetime.today()
                if type not in [1, 2]:
                    raise NoUser
                if start.year < 2018:
                    raise NoUser
                if type == 2:
                    period = (end - start).days
                if end < start:
                    TaskController.log.error("EndDate {} is before StartDate {}".format(end, start))
                    raise EndBeforeStart
                if end < today:
                    TaskController.log.error("EndDate {} is before today {}".format(end, start))
                    raise EndBeforeToday
                if priority not in ['max', 'medium', 'min']:
                    raise NoColumnWithThisName
            if project_id != None:
                project = ProjectController.get_project_by_id(username, password, project_id)
                if ProjectController.check_permission(username, password, project.id):
                    category = CategoryController.get_category_by_id(category_id)
                    if category.project_id == project.id:
                        task_names = TaskStorage.get_all_tasks(category_id)
                    else:
                        raise NoColumnWithThisName
                else:
                    raise NoPermission
            else:
                task_names = TaskStorage.get_all_user_task(UserController.get_user_by_name(username))
            have = False
            for i in task_names:
                if i.name == name:
                    have = True
            if not have:
                task = Task(name=name, desc=desc, start_date=start_date, start_time=start_time, end_date=end_date,
                            end_time=end_time, priority=priority, type=type, period=period, is_archive=0, is_subtask=0,
                            user_id=user.id,
                            category_id=category_id, project_id=project_id, parent_task_id=parent_task_id,
                            assosiated_task_id=assosiated_task_id)
                TaskStorage.add_task_to_db(task)
                TaskController.log.info("Task {} was successfully created by {}".format(name, username))
                return task
            else:
                TaskController.log.error("Task with this name is already exist")
                raise TaskWithThisNameAlreadyExist(name)
        else:
            TaskController.log.error("Incorrect password for {}".format(username))
            raise WrongPassword

    @classmethod
    def delete_task(cls, username, password, task_id):
        """
        Delete the specified task from database
        :param task_id: task id to delete
        :return: None. Task will be deleted from database
        """
        user = UserController.get_user_by_name(username)
        if user.password == password:
            task = TaskStorage.get_task_by_id(task_id)
            if ProjectController.check_permission(username, password, task.project_id):
                if task.is_subtask == 1:
                    TaskStorage.delete_task_from_db(task)
                    TaskController.log.info("Task with id {} was successfully deleted from database".format(task_id))
                else:
                    list = TaskStorage.get_all_subtasks(task)
                    can = True
                    for i in list:
                        if i.is_archive != 1:
                            can = False
                    if can:
                        TaskStorage.delete_task_from_db(task)
                        TaskController.log.info(
                            "Task with id {} was successfully deleted from database".format(task_id))
                    else:
                        TaskController.log.error("Can not to delete task, because task have some subtask")
                        raise CanNotDeleteBecauseSubtasks
            else:
                raise NoPermission

    @classmethod
    def get_all_users_task(cls, username, password):
        """
        Return all tasks, where user situated as executor or creator
        :return: List of 'task' objects
        """
        cats = ProjectController.get_all_user_categories(username, password)
        task_list = []
        for category in cats:
            tasks = TaskController.show_tasks(username, password, category.id)
            task_list = task_list + tasks
        TaskController.log.info("All user tasks were send")
        return task_list

    @classmethod
    def get_assosiated_task(cls, username, password, task):
        """
        Return task, which assosiated with this
        :param task: task to find assosiate task
        :return: Task object
        """
        if type(task) == int:
            task = TaskController.get_task_by_id(task)
        project = ProjectController.get_project_by_id(username, password, task.project_id)
        if ProjectController.check_permission(username, password, project.id):
            task_assosiate = TaskStorage.get_task_by_id(task.assosiated_task_id)
            if task_assosiate != None:
                TaskController.log.info("Assosiated task was send")
                return task_assosiate
            else:
                raise NoTask
        else:
            raise NoPermission

    @classmethod
    def set_assosiated_task(cls, username, password, task, task_id):
        """
        Set task with 'task_id' as assosiated task for 'task'
        :param task:
        :param task_id:
        :return: None. Task 'task' will be assosiated with task with id 'task_id'
        """
        if type(task) == int:
            task = TaskController.get_task_by_id(task)
        task.assosiated_task_id = task_id
        task2 = TaskStorage.get_task_by_id(task_id)
        if ProjectController.check_permission(username, password, task.project_id):
            if task2.is_archive == 1:
                TaskController.log.error("Can not assosiate with 'done' task")
                raise CanNotAssosiateWithDoneTask
            elif task2.type == 2:
                TaskController.log.error("Can not assosiate with regular task")
                raise CanNotAssosiateWithRegularTask
            else:
                task2.assosiated_task_id = task.id
                TaskStorage.save_assosiate(task)
                TaskStorage.save_assosiate(task2)
                TaskController.log.info("Task {} successfully assosiated with {}".format(task.name, task2.name))
        else:
            raise NoPermission

    @classmethod
    def cancel_task(cls, task):
        """
        Set status 'Done' to task
        :param task: task to cancel
        :return: None. Task status will be set to done
        """
        if type(task) == int:
            task = TaskController.get_task_by_id(task)
        if task.assosiated_task_id != None:
            TaskStorage.cancel_task(task)
            TaskStorage.cancel_task(TaskStorage.get_task_by_id(task.assosiated_task_id))
            TaskController.log.info("Task {} was canceled".format(task.name))
        else:
            TaskStorage.cancel_task(task)
            TaskController.log.info("Task {} was cancel".format(task.name))

    @classmethod
    def show_tasks(cls, username, password, category_id):
        """
        Show tasks for the specified category
        :param username:  username
        :param password: password
        :param category_id: category in which user want to find tasks
        :return: List of 'task' objects or 'None' if there is no tasks in this category
        """
        user = UserController.get_user_by_name(username)
        category = CategoryStorage.get_category_by_id(category_id)
        if ProjectController.check_permission(username, password, category.project_id):
            if user.password == password:
                tasks = TaskStorage.get_all_tasks(category_id)
                return tasks
            else:
                log.error("Incorrect password for {}".format(username))
                raise WrongPassword
        else:
            raise NoPermission

    @classmethod
    def show(cls, username, password, task_id):
        """
        :param username:
        :param password:
        :param task_id:
        :return:
        """
        task = TaskController.get_task_by_id(task_id)
        user = UserController.get_user_by_name(username)
        if user.password == password:
            if ProjectController.check_permission(username, password, task.project_id):
                return task
            else:
                raise NoPermission
        else:
            raise WrongPassword

    @classmethod
    def get_parent_task(cls, username, password, task):
        """
        Return parent task of 'task'
        :param task: task in which user want to get parent task
        :return: parent 'task' or none if there is no one
        """
        user = UserController.get_user_by_name(username)
        if user.password == password:
            if ProjectController.check_permission(username, password, task.project_id):
                task = TaskStorage.get_parent_task(task)
                if task != None:
                    return task
                else:
                    raise NoTask
            else:
                raise NoPermission
        else:
            raise WrongPassword

    @classmethod
    def get_all_subtask(cls, task):
        """
        Return all subtasks of 'task'
        :param task: task to find subtasks
        :return: list of 'task' or None if there is one one
        """
        subtasks = TaskStorage.get_all_subtasks(task)
        return subtasks

    @classmethod
    def new_set_subtask(cls, username, password, task1, task2):
        """
        Set 'task1' as subtask to 'task2'
        :param task1: task to set subtask
        :param task2: task to set parent task
        :return: None. All changes in database
        """
        user = UserController.get_user_by_name(username)
        if user.password == password:
            if ProjectController.check_permission(username, password,
                                                  task1.project_id) and ProjectController.check_permission(username,
                                                                                                           password,
                                                                                                           task2.project_id):
                if type(task1) == int and type(task2) == int:
                    task1 = TaskController.get_task_by_id(task1)
                    task2 = TaskController.get_task_by_id(task2)
                task1 = TaskStorage.get_task_by_id(task1.id)
                task2 = TaskStorage.get_task_by_id(task2.id)
                if task1.is_subtask == 0:
                    if task1.start_date > task2.start_date and task1.end_date < task2.end_date:
                        if task1.priority > task2.priority:
                            TaskController.log.error(
                                "Subtask priority () is more that parent task ()".format(task1.priority, task2.priority))
                            raise SubtaskPriorityException
                        else:
                            task1.is_subtask = 1
                            task1.parent_task_id = task2.id
                            task2.is_parent = 1
                            TaskStorage.save_subtask(task1)
                            TaskStorage.save_as_parent(task2)
                            TaskController.log.info(
                                "Task {} was successfully set as subtask for task {}".format(task1.name, task2.name))
                    else:
                        TaskController.log.error("Subtask error date")
                        raise SubtaskDateException
                else:
                    TaskController.log.error("Task is already subtask")
                    raise AlreadySubtask
            else:
                raise NoPermission
        else:
            raise WrongPassword

    @classmethod
    def start_again(cls, username, password, task):
        """
        Realod time field for regular task 'task'
        :param task: task to start again
        :return: None. All changes in database
        """
        if type(task) == int:
            task = TaskController.get_task_by_id(task)
        new_start = datetime.today().date()
        new_end = new_start + timedelta(days=task.period)
        task.start_date = new_start.strftime('%m/%d/%Y')
        task.end_date = new_end.strftime('%m/%d/%Y')
        TaskStorage.refresh_task_date(task)
        TaskController.log.info("Dates for regular task {} were reloaded".format(task.name))

    @classmethod
    def edit(cls, type_of_edit, username, password, project_name, column_name, task_name, new_value):
        """
        Editing an attribute for a specified task
        :param type_of_edit:
        :param username:
        :param password:
        :param project_name:
        :param column_name:
        :param task_name:
        :param new_value:
        :return:
        """

        user = UserStorage.get_user_by_name(username)
        project = ProjectStorage.get_project(project_name)
        column = ColumnStorage.get_column(project_name, column_name)
        task = TaskStorage.get_task(project_name, column_name, task_name)
        if user.password == password:
            ProjectStorage.check_permission(user, project)
            if type_of_edit == 'name':
                task.name = new_value
            elif type_of_edit == 'description' or 'desc':
                task.desc = new_value
            elif type_of_edit == 'tags':
                task.tags = new_value
            elif type_of_edit == 'priority':
                try:
                    task.priority = int(new_value)
                except:
                    log.error("Type error")
                    raise TypeErro
            TaskStorage.save(task)
        else:
            raise WrongPassword

    @classmethod
    def check_notifications(self, username, password):
        """
        Checks tasks for how soon the deadline is and if there are tasks that have a deadline earlier than 20 days, then
        a notification is displayed
        :param username: username of user who want to check
        :param password: user password
        :return: red_list - list of Tasks that you need to urgently run, yellow_list - list of tasks, the deadline of which will come soon,
        green_list - List of tasks that are still long before the deadline

        """
        user = UserController.get_user_by_name(username)
        red_list = []
        yellow_list = []
        green_list = []
        if user.password == password:
            tasks = TaskController.get_all_users_task(username, password)
            for task in tasks:
                if task.user_id != user.id:
                    tasks.remove(task)
            for task in tasks:
                if task.start_date != "" and task.end_date != "" and task.is_archive == 0:
                    task_date = datetime.strptime(task.end_date, '%m/%d/%Y')
                    to_make = (task_date - datetime.today()).days
                    task.to_deadline = to_make
                    if to_make <= 3:
                        red_list.append(task)
                    elif to_make <= 7 and to_make > 3:
                        yellow_list.append(task)
                    else:
                        green_list.append(task)
            TaskController.log.info("All groups of tasks were rerturned for check notifications to {}".format(username))
            return red_list, yellow_list, green_list
        else:
            TaskController.log.error("Incorrect password for {}".format(username))
            raise WrongPassword

    @classmethod
    def get_last_task(cls):
        """
        Return last task from the database
        :return: last task from database
        """
        task = TaskStorage.get_last_task()
        if task != None:
            return task
        else:
            raise NoTask

    @classmethod
    def delete_task_by_name(cls, category_id, name):
        """
        Delete task with specifield name
        :param category_id: id of category where is task situated
        :param name: category name
        :return: None. Delete task from database
        """
        TaskStorage.delete_task_by_name(category_id, name)

    @classmethod
    def get_task_by_id(cls, task_id):
        """
        Return task with specified id
        :param task_id: id of task
        :return: Task or None
        """
        task = TaskStorage.get_task_by_id(task_id)
        if task != None:
            return task
        else:
            raise NoTask
