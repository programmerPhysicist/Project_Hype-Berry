#!/usr/bin/env python
import requests
import json
from hab_task import HabTask
import os
import main
import manaPull

auth = main.get_habitica_login('auth.cfg')

manaPull.cast_all_mana(auth,'valorousPresence')

manaPull.assgn_user_attr_pts(auth)