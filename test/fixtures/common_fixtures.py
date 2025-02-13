# pylint: disable=missing-function-docstring, missing-module-docstring
# non-pytest fixtures
import os
import shutil
import pytest
import requests
from mockito import mock, when, unstub, kwargs
import one_way_sync
from todo_api_plus import TodoAPIPlus as todoAPI

# pylint: disable=import-error
from helpers import TestHelpers


def empty_pickle():
    match_dict = {}
    inputs = {'pickle_tasks': match_dict}
    return inputs


@pytest.fixture
def fake_config_file(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("config")
    cfg_for_test = os.path.join(tmp, "auth.cfg")
    cfg = open(cfg_for_test, 'w')
    line = ["[Habitica]\n", "url = https://habitica.com\n",
            "login = cd18fc9f-b649-4384-932a-f3bda6fe8102\n",
            "password = 18f22441-2c87-6d8e-fb2a-3fa670837b5a\n",
            "\n", "[Todoist]\n",
            "api-token = d1347120363c2b310653f610d382729bd51e13c6\n", "\n"]
    cfg.writelines(line)
    cfg.close()
    os.chdir(tmp)

    yield
    # clean-up
    shutil.rmtree(tmp)


@pytest.fixture()
def auth_cfg(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("config2")
    cfg_test = os.path.join(tmp, "auth.cfg")
    src_path = os.path.join(TestHelpers.get_root(), "source/auth.cfg")
    if os.path.exists(src_path):
        shutil.copy(src_path, cfg_test)
        os.chdir(tmp)

    yield
    # clean-up
    shutil.rmtree(tmp)


@pytest.fixture
def mock_web_calls(request):
    # mock out the web call to Habitica
    response = mock({'status': 200, 'ok': True}, spec=requests.Response)
    when(requests).get('https://habitica.com/api/v3/tasks/user/', **kwargs).thenReturn(response)
    when(response).json().thenReturn(request.param['hab_task']).thenReturn(request.param['completed_habs'])

    # mock call to Todoist
    tasks = request.param['todo_tasks']
    when(one_way_sync).get_tasks(...).thenReturn((tasks, todoAPI))

    # mock out call to Todoist for completed tasks
    tasks = request.param['done_tasks']
    when(todoAPI).get_all_completed_items().thenReturn(tasks)

    yield # run tests

    unstub() # run unstub() to ensure it doesn't break other tests
