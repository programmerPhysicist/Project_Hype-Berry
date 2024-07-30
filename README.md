# Habitica+Todoist

## __:warning: This script is a work in progress, and may or may not currently work!__

This is intended to be a two-way sync of Habitica and Todoist. Any tasks that can't be found in both services should appear on the others, with the same status. If you complete a task on one service, it should appear as completed on another. Tasks that are created on Habitica should be sent to the 'Inbox' project on Todoist.

AS A NOTE: in order to have two way syncing, you MUST have a paid copy of Todoist. It's not possible for me to port complete tasks from Todoist otherwise. If you do not have a paid copy of Todoist, the following will happen:

1. Completed tasks will not sync between the services.
2. Tasks that you begin and complete from one service to the other will not transfer between the two.

That means that if you create a task in Todoist and then check it off, right now it will _not_ send the points to Habitica.

## INSTALLATION

There are a number dependencies you'll need to install, and the commands to install them are as follows:
```
pip install todoist_api_python requests scriptabit tzlocal iso8601 python-dateutil
```
Finally, you need to add your API tokens to the `Habitica-Plus-Todoist/source/auth.cfg.example` file. You can find your Habitica API User ID and API key by visiting https://habitica.com/user/settings/api while logged in, and your Todoist API token can be found by visiting https://todoist.com/prefs/integrations while logged in. Once you've added these tokens, you should rename the file to `Habitica-Plus-Todoist/source/auth.cfg` (remove the '.example' at the end).

## TASK DIFFICULTY

I originally felt that it would be good if task difficulty translated between tasks created on Todoist and Habitica. Therefore, task difficulty should sync with the following code by default, as laid out in `main.py`

Todoist priority | Habitica difficulty
---------------- | -------------------
p1 | Hard
p2 | Medium
p3 | Easy
p4 | Easy

If you'd like to change how the sync interprets difficulty or priority, please edit `main.py`. For example, my personal setup actually includes translating Todoist p4 to Easy, rather than Trivial, because I find that Trivial yields so few rewards they aren't worth it to me.

## USAGE

Try running `python oneWaySync.py` in your terminal. (You have to run the command from the same directory that auth.cfg exists in).

## Credit

This program is a hard fork of [Habitica-Todo](https://github.com/eringiglio/Habitica-todo), with some fixes added. Habitica-Todo has been abandoned by its original author.

# Tests

To run tests, you will need to run the following pip command to install additional dependencies:
```
pip install pytest vcrpy mockito
```
