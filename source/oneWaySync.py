#!/usr/bin/env python

"""
One way sync. All the features of todoist-habitrpg; nothing newer or shinier.
Well. Okay, not *technically* one-way--it will sync two way for simple tasks/
habitica to-dos,
just not for recurring todo tasks or dailies. I'm workin' on that.
"""

# Python library imports - this will be functionalities I want to shorten
# from datetime import datetime, timedelta
import pickle
import time


import main
import json
from todo_task import TodTask
from todo_api_plus import TodoAPIPlus
import config
import habitica
import time


def get_tasks(token):
    tasks = []
    api = TodoAPIPlus(token)
    try:
        tasks = api.get_tasks()
    except Exception as error:
        print(error)
    return tasks, api


def sync_todoist_to_habitica():
    # todayFilter = todo_api.filters.add('todayFilter', 'today')

    # Telling the site where the config stuff for Habitica can go and get a list of habitica tasks...
    auth = config.get_started('auth.cfg')

    # Getting all complete and incomplete habitica dailies and todos
    hab_tasks = habitica.get_all_habtasks(auth)

    # get token for todoist
    todo_token = config.getTodoistToken('auth.cfg')

    # Okay, now I need a list of todoist tasks.
    todoist_tasks, todo_api = get_tasks(todo_token) # todoist_tasks used to be tod_tasks

    tod_tasks = []
    for i in range(0, len(todoist_tasks)):
        tod_tasks.append(TodTask(todoist_tasks[i]))

    # date stuff
    # today = datetime.now()
    # today_str = today.strftime("%Y-%m-%d")
    # one_day = timedelta(days=1)
    # yesterday = datetime.now() - one_day
    # yesterday_str = yesterday.strftime("%Y-%m-%d")

    # Okay, I want to write a little script that checks whether or not a task is there or not and, if not, ports it.
    match_dict = main.openMatchDict()

    # Also, update lists of tasks with match_dict file...
    match_dict = main.update_tod_matchDict(tod_tasks, match_dict)
    match_dict = main.update_hab_matchDict(hab_tasks, match_dict)

    # We'll want to just... pull all the unmatched completed tasks out of our lists of tasks. Yeah?
    tod_done = [TodTask(task) for task in todo_api.get_all_completed_items()]
    tod_uniq, hab_uniq = main.get_uniqs(match_dict, tod_done, hab_tasks)

    # Okay, so what if there are two matched tasks in the two uniq lists that really should be paired?
    match_dict = main.check_newMatches(match_dict, tod_uniq, hab_uniq)

    # Here anything new in todoist gets added to habitica
    tod_uniq = []
    hab_uniq = []
    tod_uniq, hab_uniq = main.getNewTodoTasks(match_dict, tod_tasks, hab_tasks)

    for tod in tod_uniq:
        tid = tod.id
        if tod.recurring == "Yes":
            # TODO fix make_daily_from_tod
            new_hab = main.make_daily_from_tod(tod)
        else:
            new_hab = main.make_hab_from_tod(tod)
        new_dict = new_hab.task_dict

        # sleep to stay within rate limits
        time.sleep(2)
        response = main.write_hab_task(new_dict)
        if not response.ok:
            # TODO: check ['errors'], due to it sometimes not having it
            try:
                json_str = response.json()
            except:
                print("Unknown json error!")
            else:
                err_msg = json_str['errors'][0]['message']
                alias = json_str['errors'][0]['value']
                msg = "Error Code " + str(response.status_code) + ": \"" + err_msg + "\", Task alias: " + alias
                print(msg)
        else:
            print("Added hab to %s!" % tod.name)
            fin_hab = main.get_hab_fromID(tid)
            match_dict[tid] = {}
            match_dict[tid]['tod'] = tod
            match_dict[tid]['hab'] = fin_hab
            match_dict[tid]['recurs'] = tod.recurring
            if match_dict[tid]['recurs'] == 'Yes':
                if tod.dueToday == 'Yes':
                    match_dict[tid]['duelast'] = 'Yes'
                else:
                    match_dict[tid]['duelast'] = 'No'
            else:
                match_dict[tid]['duelast'] = 'NA'

    # Check that anything which has recently been completed gets updated in habitica
    for tid in match_dict:
        tod = match_dict[tid]['tod']
        hab = match_dict[tid]['hab']
        if tod.recurring == 'Yes':
            if hab.dueToday == True:
                if hab.completed == False:
                    if tod.dueToday == 'Yes':
                        matched_hab = main.sync_hab2todo(hab, tod)
                        response = main.update_hab(matched_hab)
                    elif tod.dueToday == 'No':
                        response = main.complete_hab(hab)
                        print('Completed daily hab %s' % hab.name)
                    else:
                        print("error in daily Hab")
                elif hab.completed == True:
                    if tod.dueToday == 'Yes':
                        fix_tod = todo_api.items.get_by_id(tid)
    #                    fix_tod.close()
                        print('fix the tod! TID %s, NAMED %s' %(tid, tod.name))
                    elif tod.dueToday == 'No':
                        continue
                    else:
                        print("error, check todoist daily")
            elif hab.dueToday == False:
                try:
                    match_dict[tid]['duelast']
                except:
                    match_dict[tid]['duelast'] = 'No'
                if tod.dueToday == 'Yes':
                    # this is me keeping a record of recurring tods being completed or not for some of
                    # the complicated bits
                    match_dict[tid]['duelast'] = 'Yes'
                if hab.completed == False:
                    if match_dict[tid]['duelast'] == 'Yes':
                        if tod.dueToday == 'No':
                            response = main.complete_hab(hab)
                            if response.ok:
                                print('Completed Habitica task: %s' % hab.name)
                            else:
                                print('Check Habitica ID %s' %tid)
                                print(response.reason)
                            match_dict[tid]['duelast'] = 'No'
            else:
                print("error, check hab daily")
                print(hab.id)
        elif tod.recurring == 'No':
            if tod.complete == 0:
                try:
                    hab.completed
                except:
                    print(tid)
                if hab.completed == False:
                    matched_hab = main.sync_hab2todo(hab, tod)
                    response = main.update_hab(matched_hab)
                elif hab.completed == True:
                    fix_tod = todo_api.items.get_by_id(tid)
                    fix_tod.close()
                    print('completed tod %s' % tod.name)
                else:
                    print("ERROR: check HAB %s" % tid)
                    # match_dict.pop(tid)
            elif tod.complete == 1:
                if hab.completed == False:
                    response = main.complete_hab(hab)
                    print(response)
                    if response.ok:
                        print('Completed hab %s' % hab.name)
                    else:
                        print('check hab ID %s' %tid)
                        print(response.reason)
                elif hab.completed == True:
                    continue
                else:
                    print("ERROR: check HAB %s" % tid)
            else:
                print("ERROR: check TOD %s" % tid)
        response = []
    #    try:
    #        dueNow =  str(parser.parse(match_dict[tid]['tod'].due_date).date())
    #    except:
    #        dueNow = ''
    #    if dueNow != match_dict[tid]['hab'].date and match_dict[tid]['hab'].category == 'todo':
    #        match_dict[tid]['hab'].task_dict['date'] = dueNow
    #        r = main.update_hab(match_dict[tid]['hab'])

    pkl_file = open('oneWay_match_dict.pkl', 'wb')
    pkl_out = pickle.Pickler(pkl_file, -1)
    pkl_out.dump(match_dict)
    pkl_file.close()
    # todo_api.commit()


if __name__ == "__main__":
    sync_todoist_to_habitica()
