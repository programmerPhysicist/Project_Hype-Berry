# integration test for oneWaySync.py
import pytest
import os
import sys
from mockito import when, mock, unstub, when2, kwargs, verify, captor, any
# TODO: move PATH change to conftest.py file
dir_path = os.path.dirname(os.path.realpath(__file__))
dir_path = os.path.join(dir_path, "../../source")
src_path = os.path.abspath(dir_path)
sys.path.insert(0, src_path)
from oneWaySync import sync_todoist_to_habitica
from oneWaySync import get_all_completed_items
import oneWaySync
from todoist_api_python import models
from todoist_api_python.api import TodoistAPI
import requests
import pickle
import main

# TODO: unit tests
'''
def test_configFileMissing():
    with pytest.raises(SystemExit):
        sync_todoist_to_habitica()

def test_badConfigFile():
    sync_todoist_to_habitica()
'''

@pytest.fixture(scope="package")
def no_requests(monkeypatch):
    """Remove requests.sessions.Session.request for all tests."""
    monkeypatch.delattr("requests.sessions.Session.request")

@pytest.fixture(scope="package")
def no_pickle(monkeypatch):
    """Remove pickle for all tests."""
    monkeypatch.delattr("pickle")

@pytest.fixture()
def fake_config_file(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("config")
    cfgForTest = os.path.join(tmp, "auth.cfg")
    cfg = open(cfgForTest, 'w')
    L = ["[Habitica]\n", "url = https://habitica.com\n",
         "login = cd18fc9f-b649-4384-932a-f3bda6fe8102\n",
         "password = 18f22441-2c87-6d8e-fb2a-3fa670837b5a\n",
         "\n", "[Todoist]\n", 
         "api-token = d1347120363c2b310653f610d382729bd51e13c6\n", "\n"]
    cfg.writelines(L)
    cfg.close()
    os.chdir(tmp)

@pytest.fixture
def mocked_inputs(request):
     # mock out the web call to Habitica
    response = mock({'status': 200, 'ok': True}, spec=requests.Response)
    when(requests).get('https://habitica.com/api/v3/tasks/user/', **kwargs).thenReturn(response)
    when(response).json().thenReturn(request.param['json'])

    # mock out web call to get id
    response2 = mock({'status': 200, 'ok': True}, spec=requests.Response)
    when(requests).get(headers={'url': 'https://habitica.com', 'x-api-user': 'cd18fc9f-b649-4384-932a-f3bda6fe8102', 'x-api-key': '18f22441-2c87-6d8e-fb2a-3fa670837b5a'}, url='https://habitica.com/api/v3/tasks/8296278113').thenReturn(response2)
    when(response2).json().thenReturn(request.param['json2'])

    # mock call to Todoist
    tasks = request.param['todo_tasks']
    api = mock()
    when(oneWaySync).get_tasks(...).thenReturn((tasks, api))

    # mock read in of pickle file
    pkl_file = mock()
    pkl_load = mock()
    matchDict = request.param['pickle_tasks']
    when2(open, ...).thenCallOriginalImplementation()
    when2(open, 'oneWay_matchDict.pkl', 'rb').thenReturn(pkl_file)
    when(pickle).Unpickler(...).thenReturn(pkl_load)
    when(pkl_load).load().thenReturn(matchDict)

    # mock out call to Todoist for completed tasks
    tasks = request.param['done_tasks']
    when(oneWaySync).get_all_completed_items(...).thenReturn(tasks)

def case1():
    habTask = {'text': 'Some test task', 'priority': '', 'attribute': '',
                'type': 'todo', '_id': 'a94e8f46-5c14-f14a-f189-e669e239730a', 
                'completed': False, 'alias': '96935939'}
    jsonVal = {"data": []}
    jsonVal2 = {"data": habTask}

    todoistTask = models.Task(None, None, 0, False, 'Test task 1', 
                             '1987-11-04T09:54:16.1134110Z', '59292300', 
                             '', None, '8296278113', [], 0, None, 1, 
                             '9187482462', '19099659', None, '')
    todoTasks = [todoistTask]

    completedTodos = []
    matchDict = {}

    inputs = {'json': jsonVal,
              'json2': jsonVal2,
              'todo_tasks': todoTasks,
              'done_tasks': completedTodos,
              'pickle_tasks': matchDict}

    return inputs

def checkHeaders(headers):
    assert headers['url'] == 'https://habitica.com'
    assert headers['x-api-user'] == 'cd18fc9f-b649-4384-932a-f3bda6fe8102'
    assert headers['x-api-key'] == '18f22441-2c87-6d8e-fb2a-3fa670837b5a'

class TestIntegration:
    @pytest.mark.parametrize("mocked_inputs", [case1()], indirect=True)
    def test_newTaskFromTodoist(self,
                                fake_config_file,
                                mocked_inputs):

        # set default response
        response = mock({'status': 200, 'ok': True}, spec=requests.Response)

        # mock out post to Habitica
        when(requests).post(...).thenReturn(response)

        # mock out put to Habitica
        when(requests).put(...).thenReturn(response)

        # using get_all_habtasks() which contains requests.get(), uses the monkeypatch
        sync_todoist_to_habitica()

        # verify post request
        theUrl = captor(any(str))
        theData = captor(any(dict))
        theHeaders = captor(any(dict))
        verify(requests, times=1).post(url=theUrl, data=theData, headers=theHeaders)
        assert theUrl.value == 'https://habitica.com/api/v3/tasks/user/'
        data = theData.value
        assert data['type'] == 'todo'
        assert data['text'] == 'Test task 1'
        assert data['date'] == ''
        assert data['alias'] == '8296278113'
        assert data['priority'] == '2'
        assert data['attribute'] == 'str'
        checkHeaders(theHeaders.value)

        # verify put request
        verify(requests, times=1).put(headers=theHeaders, url=theUrl, data=theData)
        checkHeaders(theHeaders.value)
        assert theUrl.value == 'https://habitica.com/api/v3/tasks/96935939'
        data = theData.value
        assert data['alias'] == '96935939'
        assert data['text'] == 'Some test task'
        assert data['priority'] == 1

        # clean-up
        unstub()