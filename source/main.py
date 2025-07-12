#!/usr/bin/env python

# import re
from datetime import timedelta
import json
import os
import sys
import pickle
import time
import re
import requests
from dateutil import parser
from hab_task import HabTask
import config

from dates import parse_date_utc

# TODO: Main.py overdue for an overhaul! Let's see.
# Version control, basic paths
VERSION = 'Project_Hype-Berry version 2.1.2'
TASK_VALUE_BASE = 0.9747  # http://habitica.wikia.com/wiki/Task_Value
HABITICA_REQUEST_WAIT_TIME = 0.5  # time to pause between concurrent requests
HABITICA_TASKS_PAGE = '/#/tasks'
# https://trello.com/c/4C8w1z5h/17-task-difficulty-settings-v2-priority-multiplier
PRIORITY = {'easy': 1,
            'medium': 1.5,
            'hard': 2}
AUTH_CONF = os.path.expanduser('~') + '/.config/habitica/auth.cfg'
CACHE_CONF = os.path.expanduser('~') + '/.config/habitica/cache.cfg'

SECTION_CACHE_QUEST = 'Quest'

"""
List of utilities and what they do: scroll down for specific things
add_hab_id:
    used to add a new alias (usually the tod ID number) to a habitica task
check_match_dict:

check_new_matches:

clean_match_dict:

complete_hab:

delete_hab:
    Takes a HabTask object and sends an API call to delete it from the habitica account.
get_all_habtasks:

get_hab_fromID:
    Takes an integer, like a tod ID, and calls hab tasks by that alias from API.
get_uniqs:

make_daily_from_tod:
    Takes a repeating tod task and turns it into a habitica daily.
make_hab_from_tod:
    Takes a single tod task and turns it into a habitica todo.
make_tod_from_hab:
    Takes a habitica task and turns it into a todo. Does not sync dueness or repetitiveness; needs updating.
matchDates:

openMatchDict:

openMatchDictTwo:

synchab2todo:

sync_hab2todo_daily:

sync_hab2todo_todo:

syncHistories:

tod_login:

update_hab:

update_hab_match_dict:

update_tod_match_dict:

write_hab_task:
    takes HabTask object, writes to habitica API (used to make a new task in habitica)

"""

"""
Small utilities written by me start here.
"""


def add_hab_id(tid, hab):
    '''Add alias to Habitica task? '''
    auth = config.get_habitica_login('auth.cfg')
    url = 'https://habitica.com/api/v3/tasks/'
    hab.task_dict['alias'] = str(tid)
    url += hab.task_dict['id']
    # TODO fix this call, sometimes won't
    # convert to json cleanly.
    data = json.dumps(hab.task_dict)
    response = requests.put(headers=auth, url=url, data=data)
    return response


def check_match_dict(match_dict):
    """Troubleshooting"""
    for task in match_dict:
        if match_dict[task].complete == 0:
            if not task.completed:
                print("both undone")
            elif task.completed:
                print("hab done, tod undone")
            else:
                print("something is wroooong check hab %s" % task)
        elif match_dict[task].complete == 1:
            if not task.completed:
                print("hab undone, tod done")
                print(task.name)
            elif task.completed:
                print("both done")
            else:
                print("something is weird check hab %s" % task)
        else:
            print("something is weird check tod %s" % task)


def check_new_matches(match_dict, tod_uniq, hab_uniq):
    '''Check for matches between Todoist and Habitica'''
    matchesHab = []
    matchesTod = []
    for tod in tod_uniq:
        tid = tod.id
        for hab in hab_uniq:
            if tod.id == hab.alias:
                match_dict[tid] = {}
                match_dict[tid]['tod'] = tod
                match_dict[tid]['hab'] = hab
                match_dict[tid]['recurs'] = tod.recurring
                matchesTod.append(tod)
                matchesHab.append(hab)
        hab_uniqest = list(set(hab_uniq) - set(matchesHab))
        tod_uniqest = list(set(tod_uniq) - set(matchesTod))

    for tod_task in tod_uniqest:
        tid = tod_task.id
        if tid not in match_dict.keys():
            for hab_task in hab_uniqest:
                if tod_task.name == hab_task.name:
                    try:
                        old_tid = int(hab_task.alias)
                    except:
                        old_tid = ''
                    if old_tid in match_dict.keys():
                        match_dict.pop(old_tid)
                    response = add_hab_id(tid, hab_task)
                    if not response.ok:
                        print("Error updating hab %s! %s" % (hab_task.name, response.reason))
                    else:
                        match_dict[tid] = {}
                        match_dict[tid]['hab'] = hab_task
                        match_dict[tid]['tod'] = tod_task
                        match_dict[tid]['recurs'] = tod_task.recurring
    return match_dict


def clean_match_dict(match_dict):
    '''Unsure if it does what it says'''
    for tid in match_dict:
        if 'recurs' not in match_dict[tid].keys():
            match_dict[tid]['recurs'] = match_dict[tid]['tod'].recurring
    return match_dict


def complete_hab(hab):
    auth = config.get_habitica_login('auth.cfg')
    url = 'https://habitica.com/api/v3/tasks/'
    url += hab.task_dict['id']
    url += '/score/up/'
    hab_dict = hab.task_dict
    hab_dict['completed'] = True
    data = json.dumps(hab_dict)
    response = requests.post(headers=auth, url=url, data=data)
    return response


def delete_hab(hab):
    auth = config.get_habitica_login('auth.cfg')
    url = 'https://habitica.com/api/v3/tasks/'
    url += hab.task_dict['id']
    response = requests.delete(headers=auth, url=url)
    return response


def get_all_habtasks(auth):
    # Todoist tasks are, I think, classes. Let's make Habitica tasks classes, too.
    url = 'https://habitica.com/api/v3/tasks/user/'
    response = requests.get(url, headers=auth)
    hab_raw = response.json()

    # FINALLY getting something I can work with... this will be a list of dicts I want to turn into a list of objects
    # with class hab_tasks. Hrm. Weeeelll, if I make a class elsewhere....
    hab_tasklist = hab_raw['data']

    # keeping records of all our tasks
    hab_tasks = []

    # No habits right now, I'm afraid, in hab_tasks--Todoist gets upset. So we're going to make a list of dailies and
    # todos instead...
    for task in hab_tasklist:
        item = HabTask(task)
        if item.category == 'reward':
            pass
        elif item.category == 'habit':
            pass
        else:
            hab_tasks.append(item)
    return (hab_tasks, response)


def get_hab_fromID(tid):
    auth = config.get_habitica_login('auth.cfg')
    url = 'https://habitica.com/api/v3/tasks/'
    url += str(tid)
    response = requests.get(headers=auth, url=url)
    if response.ok:
        task = response.json()
        hab = HabTask(task['data'])
    else:
        # TODO: log error
        hab = HabTask()
    return hab


# TODO: Rename function
def get_uniqs(match_dict, tod_tasks):
    '''Find tasks not in match_dict '''
    tod_uniq = []

    for tod in tod_tasks:
        tid = tod.id
        if tid not in match_dict.keys():
            if not tod.is_completed:
                tod_uniq.append(tod)

    return tod_uniq


def make_daily_from_tod(tod):
    new_hab = {'type': 'daily'}
    new_hab['text'] = tod.name
    new_hab['alias'] = tod.id
    reg = re.compile(r"ev.{0,}(?<!other)\b (mon[^t]|tues|wed|thurs|fri|sun|sat|w(or|ee)kday|weekend)", re.I)

    match = reg.match(tod.date_string)
    if match:
        new_hab['frequency'] = 'weekly'
        daysofWeek = {}
        if 'sun' in tod.date_string:
            daysofWeek['su'] = True
        else:
            daysofWeek['su'] = False
        if 'mon' in tod.date_string:
            daysofWeek['m'] = True
        else:
            daysofWeek['m'] = False
        if 'tues' in tod.date_string:
            daysofWeek['t'] = True
        else:
            daysofWeek['t'] = False
        if 'wed' in tod.date_string:
            daysofWeek['w'] = True
        else:
            daysofWeek['w'] = False
        if 'thurs' in tod.date_string:
            daysofWeek['th'] = True
        else:
            daysofWeek['th'] = False
        if 'fri' in tod.date_string:
            daysofWeek['f'] = True
        else:
            daysofWeek['f'] = False
        if 'sat' in tod.date_string:
            daysofWeek['s'] = True
        else:
            daysofWeek['s'] = False
        if 'weekday' in tod.date_string:
            daysofWeek['m'] = True
            daysofWeek['t'] = True
            daysofWeek['w'] = True
            daysofWeek['th'] = True
            daysofWeek['f'] = True
        if 'weekend' in tod.date_string:
            daysofWeek['su'] = True
            daysofWeek['s'] = True
        new_hab['repeat'] = daysofWeek
    else:
        new_hab['frequency'] = 'daily'
        todStart = tod.due_date['date']
        new_hab['date'] = todStart
        new_hab['everyX'] = 1

    if tod.priority == 1:
        new_hab['priority'] = '2'
    elif tod.priority == 2:
        new_hab['priority'] = '1.5'
    elif tod.priority == 3:
        new_hab['priority'] = '1'
    elif tod.priority == 4:
        new_hab['priority'] = '1'

    finished_hab = HabTask(new_hab)
    return finished_hab


def make_hab_from_tod(tod_task):
    new_hab = {'type': 'todo'}
    new_hab['text'] = tod_task.name
    due = tod_task.due_date
    '''
    try:
        date_listed = list(tod_task.task_dict['due'])
        due_now = str(parser.parse(date_listed).date())
    except:
        due_now = ''
    '''

    new_hab['date'] = due
    new_hab['alias'] = tod_task.id
    if tod_task.priority == 1:
        new_hab['priority'] = '2'
    elif tod_task.priority == 2:
        new_hab['priority'] = '1.5'
    elif tod_task.priority == 3:
        new_hab['priority'] = '1'
    elif tod_task.priority == 4:
        new_hab['priority'] = '1'
    finished = HabTask(new_hab)
    return finished

'''
def make_tod_from_hab(hab):
    project_id = tod_projects[0].data['id']
    tod = {}
    tod['content'] = hab.name
    tod['due_date_utc'] = hab.date
    if hab.priority == '2':
        tod['priority'] = 1
    elif hab.priority == '1.5':
        tod['priority'] == 2
    elif hab.priority == '1':
        tod['priority'] == 3
    else:
        tod['priority'] == 4
'''
#def matchDates(match_dict):
    #'''Error/debugging script to match all hab dates with tod dates.'''
    #from main import sync_hab2todo
'''
    for tid in match_dict:
        tod = match_dict[tid]['tod']
        hab = match_dict[tid]['hab']
        try:
            hab_date = parse_date_utc(hab.date).date()
        except:
            hab_date = ''

        try:
            tod_date = tod.due.date()
        except:
            tod_date = ''

        rList = []
        if tod_date != hab_date:
            print(tod.name)
            new_hab = sync_hab2todo(hab,tod)
            response = update_hab(new_hab)
            match_dict[tid]['hab'] = new_hab
            rList.append(response,hab.name)
'''


def openMatchDict():
    input_file = 'oneWay_matchDict.pkl'
    match_dict = {}
    try:
        if os.path.getsize(input_file) > 0:
            pkl_file = open(input_file, 'rb')
            pkl_load = pickle.Unpickler(pkl_file)
            match_dict = pkl_load.load()
            pkl_file.close()
    except OSError as error:
        print(error)

    for tid in match_dict:
        if 'recurs' not in match_dict[tid].keys():
            tod = match_dict[tid]['tod']
            match_dict[tid]['recurs'] = tod.recurring
    return match_dict


def openMatchDictTwo():
    try:
        pkl_file = open('twoWay_matchDict.pkl', 'rb')
        pkl_load = pickle.Unpickler(pkl_file)
        match_dict = pkl_load.load()
        pkl_file.close()
    except:
        match_dict = {}

    for tid in match_dict:
        if 'recurs' not in match_dict[tid].keys():
            tod = match_dict[tid]['tod']
            match_dict[tid]['recurs'] = tod.recurring
    return match_dict


def purge_habs(hab_uniq):
    '''Unsure what this does '''
    hab_uniqest = []
    cruft = []
    for hab in hab_uniq:
        try:
            tid = int(hab.alias)
            cruft.append(hab)
        except:
            hab_uniqest.append(hab)

    return hab_uniqest


def sync_hab2todo(hab, tod):
    if hab.category == 'daily':
        new_hab = sync_hab2todo_daily(hab, tod)
        return new_hab
    elif hab.category == 'todo':
        new_hab = sync_hab2todo_todo(hab, tod)
        return new_hab
    else:
        print("Error! Hab of incorrect type!")
        sys.exit(1)


def sync_hab2todo_daily(hab, tod):
    # import pytz
    habDict = hab.task_dict
    if tod.priority == 4:
        habDict['priority'] = 2
    elif tod.priority == 3:
        habDict['priority'] = 1.5
    else:
        habDict['priority'] = 1

    # now = datetime.now().replace(tzinfo=pytz.utc).date()
    hab_due = hab.due
    if isinstance(hab_due, str):
        hab_due = parser.parse(hab_due)

    if hab_due.date() != (tod.due.date() - timedelta(days=1)):
            habDict['startDate'] = str(tod.due.date() - timedelta(days=1))

    new_hab = HabTask(habDict)

    return new_hab


def sync_hab2todo_todo(hab, tod):
    habDict = hab.task_dict
    if tod.priority == 4:
        habDict['priority'] = 2
    elif tod.priority == 3:
        habDict['priority'] = 1.5
    else:
        habDict['priority'] = 1

    try:
        due_now = tod.due_date['date']
    except:
        due_now = ''
    try:
        due_old = hab.due
    except:
        due_old = ''

    if due_old != due_now:
        if due_now is not None:
            habDict['date'] = str(due_now)
            print("INFO: Due date will be updated to " + habDict['date'])
        else:
            habDict['date'] = ''

    new_hab = HabTask(habDict)
    return new_hab

'''
def syncHistories(match_dict):

    """
    I wanted to see if I could convince recurring habs and tods to sync based on history.
    Assuming both recur...
    """
    from dates import parse_date_utc
    from dateutil import parser
    from datetime import timedelta
    from main import complete_hab, update_hab
    from main import tod_login
    tod_user = tod_login('auth.cfg')
    todList = {}
    for tid in match_dict:
        try:
            match_dict[tid]['recurs']
        except:
            print(tid)
            match_dict[tid]['recurs'] = match_dict[tid]['tod'].recurring
        if match_dict[tid]['recurs'] == 'Yes':
            hab = match_dict[tid]['hab']
            tod = match_dict[tid]['tod']
            habHistory = hab.history
            todHistory = tod.history
            try:
                lastTod = parser.parse(todHistory[0]['event_date']).date()
            except:
                lastTod = tod.due.date()
            habLen = len(habHistory) - 1
            try:
                lastHab = datetime.fromtimestamp(habHistory[habLen]['date']/1000).date() - timedelta(days=1)
            except:
                lastHab = hab.due.date() - timedelta(days=1)
            lastNow = datetime.today().date()
            if lastHab > hab.due.date():
                new_hab = sync_hab2todo(hab, tod)
                response = update_hab(new_hab)
            if lastTod != lastHab:
                if lastHab < lastTod and hab.dueToday == True:
                    print("Updating daily hab %s to match tod" % tod.name)
                    response = complete_hab(hab)
                    print(response)
                elif lastTod < lastHab: # and hab.dueToday == False:
                    if lastTod < lastNow == False:
                        print("Updating daily tod %s to match hab" % tod.name)
                        #fix_tod = tod_user.items.get_by_id(tid)
                        #fix_tod.close() #this to be uncommented in a week or so
                        print(lastTod)
                        print(lastHab)
                        print(lastNow)
                    elif hab.due.date() < lastNow:
                        print("Hey, tod %s looks like it's getting pretty late. Think about tackling that one?" % tod.name)
                        print(lastTod)
                        print(lastHab)
                        print(hab.due)
                else:
                    print("This one doesn't apply, right?")
                    print(tod.name)
                    print(lastTod)
                    print(lastHab)
                    print(hab.due)
    tod_user.commit()
    return match_dict
'''


def update_hab(hab):
    # TODO: Only update when there are actual changes
    auth = config.get_habitica_login('auth.cfg')
    url = 'https://habitica.com/api/v3/tasks/'
    try:
        tag = str(hab.task_dict['alias'])
    except:
        tag = hab.task_dict['id']
    url += tag
    wanted_keys = ['alias', 'text', 'priority', 'date']
    data = {x: hab.task_dict[x] for x in wanted_keys if x in hab.task_dict}
    time.sleep(2)
    try:
        response = requests.put(headers=auth, url=url, data=data)
    except requests.exceptions.RequestException as errex:
        breakpoint()
        print("Exception request")
    if response.ok == 'No':
        print(response.text)
    return response


def update_hab_match_dict(hab_tasks, match_dict):
    '''Update habitica task in matchDict? '''
    hardness = []
    tid_list = []
    expired_tids = []
    aliasError = []
    for hab in hab_tasks:
        if 'alias' in hab.task_dict.keys():
            try:
                tid = int(hab.alias)
                tid = hab.alias
                tid_list.append(tid)
            except:
                aliasError.append(hab)
                tid = None
            if tid in match_dict.keys():
                try:
                    date1 = hab.due.date()
                except:
                    date1 = ''
                try:
                    date2 = match_dict[tid]['hab'].due.date()
                except:
                    date2 = ''

                if date1 != date2 and match_dict[tid]['recurs'] == 'No':
                    # if the hab I see and the match_dict don't agree... sync to the todoist task
                    print(date1)
                    print(date2)
                    new_hab = sync_hab2todo(hab, match_dict[tid]['tod'])
                    response = update_hab(new_hab)
                    print('Dates wrong; updated hab %s !' % hab.name)
                    print(response)

                if hab.hardness != match_dict[tid]['hab'].hardness:
                    print("hardness mismatch!")
                    hardness.append(tid)
                    new_hab = sync_hab2todo(hab, match_dict[tid]['tod'])
                    response = update_hab(new_hab)
                    print(response)
                    print('Updated hab %s !' % hab.name)

                match_dict[tid]['hab'] = hab
    '''
    for hab in aliasError:
        for tid in match_dict:
            matchHab = match_dict[tid]['hab']
            if hab.name == matchHab.name:
                expired_tids.append(tid)
    '''
    for tid in match_dict:
        hab = match_dict[tid]['hab']
        if tid not in tid_list:
            expired_tids.append(tid)

    for tid in expired_tids:
        if tid in match_dict.keys():
            if not match_dict[tid]['hab'].completed:
                match_dict.pop(tid)

    return match_dict


def update_tod_match_dict(tod_tasks, match_dict):
    '''Update Todoist tasks in match dictionary? '''
    tid_list = []
    for tod in tod_tasks:
        tid_list.append(tod.id)
        if tod.id in match_dict.keys():
            match_dict[tod.id]['tod'] = tod
    for tid in list(match_dict):
        if tid not in tid_list:
            match_dict.pop(tid)

    return match_dict


def write_hab_task(task):
    """
    writes a task, if inserted, to Habitica API as a todo.
    To be added: functionality allowing you to specify things like difficulty
    """
    auth = config.get_habitica_login('auth.cfg')
    url = 'https://habitica.com/api/v3/tasks/user/'
#    hab = json.dumps(task)
    response = requests.post(headers=auth, url=url, data=task)
    return response
