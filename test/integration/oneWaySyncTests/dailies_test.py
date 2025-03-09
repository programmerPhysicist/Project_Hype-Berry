# pylint: disable=missing-function-docstring, missing-module-docstring, invalid-name, import-error
# integration test for one_way_sync.py
import pickle
from datetime import datetime
import pytest
import requests
import vcr
from tzlocal import get_localzone
from mockito import when, mock, when2, verify, captor, ANY
from one_way_sync import sync_todoist_to_habitica
from todoist_api_python import models
from common_fixtures import empty_pickle, fake_config_file, mock_web_calls # pylint: disable=unused-import
# pylint: enable=invalid-name


def case1():
    hab_val = {"data": []}

    due_dict = {'date': '2024-12-27',
                'datetime': None,
                'is_recurring': True,
                'string': 'every day',
                'timezone': None}
    duedate = models.Due.from_dict(due_dict)
    created_at = '2025-01-04T00:00:00.0Z'

    todoist_task = models.Task(None,  # assignee id
                               None,  # assigner id
                               0,     # comment count
                               False, # is_completed
                               'Test task 1', # content
                               created_at,    # created_at
                               '59292300',    # creater_id
                               '',            # description
                               duedate,       # due
                               '8296278113',  # id
                               [],            # labels
                               0,             # order
                               None,          # parent id
                               1,             # priority
                               '9187482462',  # project id
                               '19099659',    # section id
                               None,          # url
                               ''             # duration
                               )
    todo_tasks = [todoist_task]
    completed_todos = []

    inputs = {'hab_task': hab_val,
              'completed_habs': hab_val,
              'todo_tasks': todo_tasks,
              'done_tasks': completed_todos}

    return inputs


def verify_post_request(data):
    if data['text'] == 'Test task 1':
        assert data['type'] == 'todo'
        assert data['text'] == 'Test task 1'
        assert data['date'] == '12/27/2024, 00:00:00'
        assert data['alias'] == '8296278113'
        assert data['priority'] == '2'
        assert data['attribute'] == 'str'
        return True
    return False


def verify_pickle_dump(dump_dict):
    data = dump_dict.value
    # check 'simple' values
    assert '8296278113' in data.keys()
    data = data['8296278113']
    assert data['recurs']
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
    assert tod_data['created_at'] == '2025-01-04T00:00:00.0Z'
    assert tod_data['priority'] == 1
    # Check hab_task
    hab_data = hab_task.task_dict
    assert hab_data['type'] == 'daily'
    assert hab_data['alias'] == '96935939'
    assert hab_data['text'] == 'Some test task'
    assert hab_data['priority'] == 1
    expected_due = datetime(2024, 12, 27, tzinfo=get_localzone())
    due = hab_task.due
    assert due == expected_due


# pylint: disable=missing-class-docstring
class TestDailies:
    test_vcr = vcr.VCR(
        serializer='yaml',
        cassette_library_dir="/tmp/throwaway",
        record_mode='none'
    )

    # pylint: disable=redefined-outer-name, unused-argument, too-many-locals, too-few-public-methods
    @pytest.mark.parametrize("mock_web_calls", [case1()], indirect=True)
    @pytest.mark.parametrize("pickle_in", [empty_pickle()], indirect=True)
    def test(self,
             fake_config_file,
             mock_web_calls):
        # pylint: enable=redefined-outer-name, unused-argument

        # set default response
        response = mock({'status': 200, 'ok': True}, spec=requests.Response)

        # mock out post to Habitica
        when(requests).post(...).thenReturn(response)

        # mock out put to Habitica
        when(requests).put(...).thenReturn(response)

        # mock out web call to get id
        hab_task = {'text': 'Some test task', 'priority': '2', 'attribute': '',
                    'type': 'daily', '_id': 'a94e8f46-5c14-f14a-f189-e669e239730a',
                    'completed': False, 'alias': '96935939', 'date': '12/27/2024, 00:00:00'}
        hab_val2 = {"data": hab_task}

        response2 = mock({'status': 200, 'ok': True}, spec=requests.Response)
        task_url = 'https://habitica.com/api/v3/tasks/8296278113'
        when(requests).get(headers={'url': 'https://habitica.com',
                                    'x-api-user': 'cd18fc9f-b649-4384-932a-f3bda6fe8102',
                                    'x-api-key': '18f22441-2c87-6d8e-fb2a-3fa670837b5a'},
                           url=task_url).thenReturn(response2)
        when(response2).json().thenReturn(hab_val2)

        # mock dump of pickle file
        pkl_out = mock()
        pkl_file = mock()
        when2(open, ...).thenCallOriginalImplementation()
        when2(open, 'oneWay_matchDict.pkl', 'wb').thenReturn(pkl_file)
        when(pickle).Pickler(...).thenReturn(pkl_out)
        when(pkl_out).dump(...)

        # using get_all_habtasks() which contains requests.get(), uses the monkeypatch
        with self.test_vcr.use_cassette("null.yaml"):
            sync_todoist_to_habitica()

        # verify post request
        the_data = captor(ANY(dict))
        the_headers = captor(ANY(dict))
        verify(requests, times=1).post(url='https://habitica.com/api/v3/tasks/user/',
                                       data=the_data,
                                       headers=the_headers)
        task = the_data.value
        assert task['type'] == 'daily'
        assert task['frequency'] == 'daily'

        # verify pickle dump
        dump_dict = captor(ANY(dict))
        verify(pkl_out, times=1).dump(dump_dict)
        verify_pickle_dump(dump_dict)
