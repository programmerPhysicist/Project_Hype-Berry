# pylint: disable=missing-function-docstring, missing-module-docstring, invalid-name, import-error, missing-class-docstring
# integration test for oneWaySync.py
import os
import pickle
import pytest
from mockito import when, mock, unstub, when2, kwargs, verify, captor, ANY, arg_that
from oneWaySync import sync_todoist_to_habitica
from oneWaySync import get_all_completed_items # pylint: disable=unused-import
import oneWaySync
from todoist_api_python import models
import requests
from common_fixtures import empty_pickle
# pylint: enable=invalid-name


@pytest.fixture(scope="package")
def no_requests(monkeypatch):
    """Remove requests.sessions.Session.request for all tests."""
    monkeypatch.delattr("requests.sessions.Session.request")


@pytest.fixture(scope="package")
def no_pickle(monkeypatch):
    """Remove pickle for all tests."""
    monkeypatch.delattr("pickle")


@pytest.fixture(scope='function')
def fake_config_file(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("config")
    cfg_for_test = os.path.join(tmp, "auth.cfg")
    cfg = open(cfg_for_test, 'w')
    li = ["[Habitica]\n", "url = https://habitica.com\n",
          "login = cd18fc9f-b649-4384-932a-f3bda6fe8102\n",
          "password = 18f22441-2c87-6d8e-fb2a-3fa670837b5a\n",
          "\n", "[Todoist]\n",
          "api-token = d1347120363c2b310653f610d382729bd51e13c6\n", "\n"]
    cfg.writelines(li)
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
    task_url = 'https://habitica.com/api/v3/tasks/8296278113'
    when(requests).get(headers={'url': 'https://habitica.com',
                                'x-api-user': 'cd18fc9f-b649-4384-932a-f3bda6fe8102',
                                'x-api-key': '18f22441-2c87-6d8e-fb2a-3fa670837b5a'},
                                url=task_url).thenReturn(response2)
    when(response2).json().thenReturn(request.param['json2'])

    # mock call to Todoist
    tasks = request.param['todo_tasks']
    api = mock()
    when(oneWaySync).get_tasks(...).thenReturn((tasks, api))

    # mock out call to Todoist for completed tasks
    tasks = request.param['done_tasks']
    when(oneWaySync).get_all_completed_items(...).thenReturn(tasks)


def case1():
    hab_task = {'text': 'Some test task', 'priority': '', 'attribute': '',
                'type': 'todo', '_id': 'a94e8f46-5c14-f14a-f189-e669e239730a',
                'completed': False, 'alias': '96935939'}
    json_val = {"data": []}
    json_val2 = {"data": hab_task}

    todoist_task = models.Task(None, None, 0, False, 'Test task 1',
                               '1987-11-04T09:54:16.1134110Z', '59292300',
                               '', None, '8296278113', [], 0, None, 1,
                               '9187482462', '19099659', None, '')
    todo_tasks = [todoist_task]
    completed_todos = []

    inputs = {'json': json_val,
              'json2': json_val2,
              'todo_tasks': todo_tasks,
              'done_tasks': completed_todos}

    return inputs


def check_headers(headers):
    assert headers['url'] == 'https://habitica.com'
    assert headers['x-api-user'] == 'cd18fc9f-b649-4384-932a-f3bda6fe8102'
    assert headers['x-api-key'] == '18f22441-2c87-6d8e-fb2a-3fa670837b5a'


def verify_post_request(data):
    if data['text'] == 'Test task 1':
        assert data['type'] == 'todo'
        assert data['text'] == 'Test task 1'
        assert data['date'] == ''
        assert data['alias'] == '8296278113'
        assert data['priority'] == '2'
        assert data['attribute'] == 'str'
        return True
    return False


class TestIntegration:
    # pylint: disable=redefined-outer-name, unused-argument, too-many-locals, too-few-public-methods
    @pytest.mark.parametrize("mocked_inputs", [case1()], indirect=True)
    @pytest.mark.parametrize("pickle_in", [empty_pickle()], indirect=True)
    def test_new_task_todoist(self,
                              fake_config_file,
                              mocked_inputs,
                              pickle_in):
        # pylint: enable=redefined-outer-name, unused-argument

        # set default response
        response = mock({'status': 200, 'ok': True}, spec=requests.Response)

        # mock out post to Habitica
        when(requests).post(...).thenReturn(response)

        # mock out put to Habitica
        when(requests).put(...).thenReturn(response)

        # mock dump of pickle file
        pkl_out = mock()
        pkl_file = mock()
        when2(open, ...).thenCallOriginalImplementation()
        when2(open, 'oneWay_matchDict.pkl', 'wb').thenReturn(pkl_file)
        when(pickle).Pickler(...).thenReturn(pkl_out)
        when(pkl_out).dump(...)

        # using get_all_habtasks() which contains requests.get(), uses the monkeypatch
        sync_todoist_to_habitica()

        # verify post request
        the_url = captor(ANY(str))
        the_data = captor(ANY(dict))
        the_headers = captor(ANY(dict))
        verify(requests, times=1).post(url='https://habitica.com/api/v3/tasks/user/',
                                       data=arg_that(verify_post_request),
                                       headers=the_headers)
        check_headers(the_headers.value)

        # verify put request
        the_url = captor(ANY(str))
        verify(requests, times=1).put(headers=the_headers, url=the_url, data=the_data)
        check_headers(the_headers.value)
        assert the_url.value == 'https://habitica.com/api/v3/tasks/96935939'
        data = the_data.value
        assert data['alias'] == '96935939'
        assert data['text'] == 'Some test task'
        assert data['priority'] == 1

        # verify pickle dump
        dump_dict = captor(ANY(dict))
        verify(pkl_out, times=1).dump(dump_dict)
        data = dump_dict.value
        # check 'simple' values
        assert '8296278113' in data.keys()
        data = data['8296278113']
        assert data['recurs'] == 'No'
        assert data['duelast'] == 'NA'
        # Get objects to verify
        assert 'tod' in data.keys()
        tod_task = data['tod']
        assert 'hab' in data.keys()
        hab_task = data['hab']
        # Check tod_task
        tod_data = tod_task.task_dict
        assert tod_data['content'] == 'Test task 1'
        assert tod_data['id'] == '8296278113'
        assert tod_data['created_at'] == '1987-11-04T09:54:16.1134110Z'
        # TODO: this doesn't seem right, maybe fix?
        assert tod_data['priority'] == 1
        # Check hab_task
        hab_data = hab_task.task_dict
        assert hab_data['type'] == 'todo'
        assert hab_data['alias'] == '96935939'
        assert hab_data['text'] == 'Some test task'
        assert hab_data['priority'] == 1

        # clean-up
        unstub()
