'''Habitica related functions'''
# TODO: convert to class that makes all
# calls to Habitica
import requests
from hab_task import HabTask


def get_all_habtasks(auth):
    # Todoist tasks are, I think, classes. Let's make Habitica tasks classes, too.
    url = 'https://habitica.com/api/v3/tasks/user/'
    # TODO: handle error cases for response
    response = requests.get(url, headers=auth)
    if response.ok:
        hab_raw = response.json()

        # FINALLY getting something I can work with... this will be a list of
        # dicts I want to turn into a list of objects with class hab_tasks.
        # Hrm. Weeeelll, if I make a class elsewhere....
        hab_tasklist = hab_raw['data']
    else:
        hab_tasklist = []
        print(response.reason)

    # keeping records of all our tasks
    hab_tasks = []

    # No habits right now, I'm afraid, in hab_tasks--Todoist gets upset.
    # So we're going to make a list of dailies and todos instead...
    for task in hab_tasklist:
        item = HabTask(task)
        if item.category == 'reward':
            pass
        elif item.category == 'habit':
            pass
        else:
            hab_tasks.append(item)
    return hab_tasks
