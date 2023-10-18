#!/usr/bin/env python

"""
One way sync. All the features of todoist-habitrpg; nothing newer or shinier.
Well. Okay, not *technically* one-way--it will sync two way for simple tasks/habitica to-dos, 
just not for recurring todo tasks or dailies. I'm workin' on that.
"""

#Python library imports - this will be functionalities I want to shorten
from os import path # will let me call files from a specific path
import requests
import pickle
#import todoist
from todoist_api_python.api import TodoistAPI
import main
import random
import json
#from hab_task import HabTask
from todo_task import TodTask
from datetime import datetime
from datetime import timedelta
# from dateutil import parser
import logging
import configparser	
import config
import habitica

def get_tasks(token):
    tasks = []
    api = TodoistAPI(token)
    try:
        tasks = api.get_tasks()
    except Exception as error:
        print(error)
    return tasks, api

# todayFilter = todoApi.filters.add('todayFilter', 'today')

#Telling the site where the config stuff for Habitica can go and get a list of habitica tasks...
auth = config.get_started('auth.cfg')

#Getting all complete and incomplete habitica dailies and todos
hab_tasks, r1 = habitica.get_all_habtasks(auth)

# get token for todoist
todoToken = config.getTodoistToken('auth.cfg')

#Okay, now I need a list of todoist tasks.
todoist_tasks, todoApi = get_tasks(todoToken) # todoist_tasks used to be tod_tasks

tod_tasks = []
for i in range(0, len(todoist_tasks)):
    tod_tasks.append(TodTask(todoist_tasks[i]))

# date stuff
today = datetime.now()
today_str = today.strftime("%Y-%m-%d")
one_day = timedelta(days=1)
yesterday = datetime.now() - one_day
yesterday_str = yesterday.strftime("%Y-%m-%d")

"""
Okay, I want to write a little script that checks whether or not a task is there or not and, if not, ports it. 	
"""
matchDict = main.openMatchDict()

#Also, update lists of tasks with matchDict file...
matchDict = main.update_tod_matchDict(tod_tasks, matchDict)
matchDict = main.update_hab_matchDict(hab_tasks, matchDict)

#We'll want to just... pull all the unmatched completed tasks out of our lists of tasks. Yeah? 
tod_uniq, hab_uniq = main.get_uniqs(matchDict, tod_tasks, hab_tasks)

#Okay, so what if there are two matched tasks in the two uniq lists that really should be paired?
matchDict = main.check_newMatches(matchDict,tod_uniq,hab_uniq)

#Here anything new in todoist gets added to habitica
tod_uniq = []
hab_uniq = []
tod_uniq, hab_uniq = main.getNewTodoTasks(matchDict, tod_tasks, hab_tasks)

for tod in tod_uniq:
    tid = tod.id
    if tod.recurring == "Yes":
        new_hab = main.make_daily_from_tod(tod)
    else:
        new_hab = main.make_hab_from_tod(tod)
    newDict = new_hab.task_dict
    r = main.write_hab_task(newDict)
    if r.ok == False:
        errMsg = r.json()['errors'][0]['message']
        alias = r.json()['errors'][0]['value']
        print("ERROR: Code: "+str(r.status_code)+", Error message: \""
                             +errMsg+"\", Task alias: "+alias)
    else:
        print("Added hab to %s!" % tod.name)
        fin_hab = main.get_hab_fromID(tid)
        matchDict[tid] = {}
        matchDict[tid]['tod'] = tod
        matchDict[tid]['hab'] = fin_hab
        matchDict[tid]['recurs'] = tod.recurring
        if matchDict[tid]['recurs'] == 'Yes':
            if tod.dueToday == 'Yes':
                matchDict[tid]['duelast'] = 'Yes'
            else:
                matchDict[tid]['duelast'] = 'No'
        else:
            matchDict[tid]['duelast'] = 'NA'

#Check that anything which has recently been completed gets updated in habitica
for tid in matchDict:
    tod = matchDict[tid]['tod']
    hab = matchDict[tid]['hab']
    if tod.recurring == 'Yes':
        if hab.dueToday == True:
            if hab.completed == False:
                if tod.dueToday == 'Yes':
                    matched_hab = main.sync_hab2todo(hab, tod)
                    r = main.update_hab(matched_hab)
                elif tod.dueToday == 'No':
                    r = main.complete_hab(hab)
                    print('Completed daily hab %s' % hab.name)
                    print(r)
                else:
                    print("error in daily Hab")
            elif hab.completed == True:
                if tod.dueToday == 'Yes':
                    fix_tod = todoApi.items.get_by_id(tid)
#                    fix_tod.close()
                    print('fix the tod! TID %s, NAMED %s' %(tid, tod.name))
                elif tod.dueToday == 'No':
                    continue
                else:
                    print("error, check todoist daily")
        elif hab.dueToday == False:
            try: 
                matchDict[tid]['duelast']
            except:
                matchDict[tid]['duelast'] = 'No'
            if tod.dueToday == 'Yes':
                matchDict[tid]['duelast'] = 'Yes' #this is me keeping a record of recurring tods being completed or not for some of the complicated bits
            if hab.completed == False:
                if matchDict[tid]['duelast'] == 'Yes':
                    if tod.dueToday == 'No':
                        r = main.complete_hab(hab)
                        if r.ok == True:
                            print('Completed hab %s' % hab.name)
                        else:
                            print('check hab ID %s' %tid)
                            print(r.reason)
                        matchDict[tid]['duelast'] = 'No'
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
                r = main.update_hab(matched_hab)
            elif hab.completed == True:
                fix_tod = todoApi.items.get_by_id(tid)
                fix_tod.close()
                print('completed tod %s' % tod.name)
            else: 
                print("ERROR: check HAB %s" % tid)
                #matchDict.pop(tid)
        elif tod.complete == 1:
            if hab.completed == False:
                r = main.complete_hab(hab)
                print(r)
                if r.ok == True:
                    print('Completed hab %s' % hab.name)
                else:
                    print('check hab ID %s' %tid)
                    print(r.reason)
            elif hab.completed == True:
                continue
            else: 
                print("ERROR: check HAB %s" % tid)
        else:
            print("ERROR: check TOD %s" % tid)
    r = []
#    try: 
#        dueNow =  str(parser.parse(matchDict[tid]['tod'].due_date).date())
#    except:
#        dueNow = ''
#    if dueNow != matchDict[tid]['hab'].date and matchDict[tid]['hab'].category == 'todo':
#        matchDict[tid]['hab'].task_dict['date'] = dueNow
#        r = main.update_hab(matchDict[tid]['hab']) 

pkl_file = open('oneWay_matchDict.pkl','wb')
pkl_out = pickle.Pickler(pkl_file, -1)
pkl_out.dump(matchDict)
pkl_file.close()
#todoApi.commit()

