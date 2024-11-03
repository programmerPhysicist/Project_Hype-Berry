#!/usr/bin/env python

"""
This is a version which should work only for people who have paid accounts with todoist. Sorry, but it should handle dailies/recurring tasks in a much more effective and less problematic way via pulling activity logs (available only on todoist premium.)
"""

#Python library imports - this will be functionalities I want to shorten
from os import path # will let me call files from a specific path
import requests
import pickle
import todoist
import main
import random
import json
from hab_task import HabTask
from todo_task import TodTask
from datetime import datetime
from datetime import timedelta
from dateutil import parser
from dates import parse_date_utc

#Here's where I'm putting my login stuff for Todoist.
tod_user = main.tod_login('auth.cfg')
tod_user.sync()
tod_projects = tod_user.projects.all()
tod_inboxID = tod_projects[0].data['id']

#Telling the site where the config stuff for Habitica can go and get a list of habitica tasks...
auth = main.get_habitica_login('auth.cfg')

#Getting all complete and incomplete habitica dailies and todos
hab_tasks, r1 = main.get_all_habtasks(auth)

#Okay, now I need a list of todoist tasks. How do achieve that.
tod_tasks = []
tod_items = tod_user.items
tod_tasklist = tod_items.all()
for i in range(0, len(tod_tasklist)):
    tod_tasks.append(TodTask(tod_tasklist[i].data))

"""
Okay, I want to write a little script that checks whether or not a task is there or not and, if not, ports it.
"""
matchDict = main.openMatchDictTwo()

#Also, update lists of tasks with matchDict file...
matchDict = main.update_tod_matchDict(tod_tasks, matchDict)
matchDict = main.update_hab_matchDict(hab_tasks, matchDict)

#We'll want to just... pull all the unmatched completed tasks out of our lists of tasks. Yeah?
tod_uniq, hab_uniq = main.get_uniqs(matchDict, tod_tasks, hab_tasks)

#Okay, so what if there are two matched tasks in the two uniq lists that really should be paired?
matchDict = main.check_newMatches(matchDict,tod_uniq,hab_uniq)

tod_uniq, hab_uniq = main.get_uniqs(matchDict, tod_tasks, hab_tasks)

#Here anything new in tod gets added to hab
for tod in tod_uniq:
    tid = tod.id
    if tod.recurring == "Yes":
        new_hab = main.make_daily_from_tod(tod)
    else:
        new_hab = main.make_hab_from_tod(tod)
    newDict = new_hab.task_dict
    r = main.write_hab_task(newDict)
    print("Added hab to %s!" % tod.name)
    print(r)
    if r.ok == False:
        fin_hab = main.get_hab_fromID(tid)
    else:
        fin_hab = main.get_hab_fromID(tid)
    matchDict[tid] = {}
    matchDict[tid]['tod'] = tod
    matchDict[tid]['hab'] = fin_hab
    matchDict[tid]['recurs'] = tod.recurring

#And we do the same with tasks unique to habitica, to tods...
for hab in hab_uniq:
    try:
        tid = int(hab.alias)
        #tid = hab.alias
    except:
        tid = 'NEW'
    if tid == 'NEW':
        newTod = main.make_tod_from_hab
        tod_items.add(newTod)
    else:
        #cruft = tod_user.activity.get(object_type='item',object_id=tid)['events'][0]['event_type']
        somelist = tod_user.activity.get(object_type='item',object_id=tid)['events']
        if not somelist:
            cruft = 'Nothing'
        else:
            cruft = somelist[0]['event_type']
        if cruft == 'deleted':
            r = main.delete_hab(hab)
            print(r)
        elif cruft == 'updated':
            print("INFO: Updated task, TID %s" % tid)
        else:
            print("ERROR. PLEASE CHECK HAB WITH TID %s" % tid)


#This routine updates the dailies/recurring tasks
matchDict = main.syncHistories(matchDict)

#This one updates the one-offs:
expired_tids = []
for tid in matchDict:
    tod = matchDict[tid]['tod']
    hab = matchDict[tid]['hab']
    if tod.recurring == 'No':
        if tod.complete == 0:
            try:
                hab.completed
            except:
                print(tid)
            if hab.completed == False:
                matched_hab = main.sync_hab2todo(hab, tod)
                r = main.update_hab(matched_hab)
            elif hab.completed == True:
                fix_tod = tod_user.items.get_by_id(tid)
                fix_tod.close()
                print('completed tod %s' % tod.name)
            else:
                print("ERROR: check HAB %s" % tid)
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
                expired_tids.append(tid)
            else:
                print("ERROR: check HAB %s" % tid)
        else:
            print("ERROR: check TOD %s" % tid)

for tid in expired_tids:
    matchDict.pop(tid)

pkl_file = open('twoWay_matchDict.pkl','wb')
pkl_out = pickle.Pickler(pkl_file, -1)
pkl_out.dump(matchDict)
pkl_file.close()
tod_user.commit()
