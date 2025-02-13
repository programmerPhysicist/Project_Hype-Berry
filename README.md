# Project Hype-Berry

### __:warning: Alpha script!__
⚠️ Only one way syncing is working right now.
##
This is intended to be a two-way sync of Habitica and Todoist. Any tasks that can't be found in both services should appear on the others, with the same status. If you complete a task on one service, it should appear as completed on another. Tasks that are created on Habitica should be sent to the 'Inbox' project on Todoist.

AS A NOTE: in order to have two way syncing, you MUST have a paid copy of Todoist. It's not possible to sync complete tasks from Todoist otherwise. If you do not have a paid copy of Todoist, the following will happen:

1. Completed tasks will not sync between the services.
2. Tasks that you begin and complete from one service to the other will not transfer between the two.

That means that if you create a task in Todoist and then check it off, right now it will _not_ send the points to Habitica.

## INSTALLATION

### Linux Installation
1. Install the python dependencies:
```
pip install todoist_api_python requests scriptabit tzlocal iso8601 python-dateutil
```
2. Get the source code [here](https://github.com/programmerPhysicist/Project_Hype-Berry/tags)
3. You need to add your API tokens to the **Project_Hype-Berry/source/auth.cfg.example** file
   * To get the _Habitica API User ID_ and _API key_ goto <https://habitica.com/user/settings/api> while logged in
   * To get the _Todoist API token_ goto <https://todoist.com/prefs/integrations> while logged in.
4. Rename the file to **Project_Hype-Berry/source/auth.cfg** (remove the '.example' at the end).
5. Add the folder oneWaySync to $XDG_STATE_HOME: `mkdir $XDG_STATE_HOME/oneWaySync`
6. Add the **oneWaySync.sh** script to Crontab

## TASK DIFFICULTY

I originally felt that it would be good if task difficulty translated between tasks created on Todoist and Habitica. Therefore, task difficulty should sync with the following code by default, as laid out in **main.py**

Todoist priority | Habitica difficulty
---------------- | -------------------
p1 | Hard
p2 | Medium
p3 | Easy
p4 | Easy

If you'd like to change how the sync interprets difficulty or priority, please edit **main.py**. For example, my personal setup actually includes translating Todoist p4 to Easy, rather than Trivial, because I find that Trivial yields so few rewards they aren't worth it to me.

## USAGE

Try running `python one_way_sync.py` in your terminal. (You have to run the command from the same directory that auth.cfg exists in).

Or you can try the provided shell script **oneWaySync.sh** under **Project_Hype-Berry/scripts/**

## Credit

This program is a hard fork of [Habitica-Todo](https://github.com/eringiglio/Habitica-todo), with some fixes added. Habitica-Todo has been abandoned by its original author.

# Tests

To run tests, you will need to run the following pip command to install additional dependencies:
```
pip install pytest vcrpy mockito
```
