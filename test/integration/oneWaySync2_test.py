# pylint: disable=missing-function-docstring, missing-module-docstring, invalid-name, missing-class-docstring
# pylint: disable=global-statement
import os
import shutil
import logging
import json
import pickle
import requests

# test imports
# pylint: disable=import-error
import pytest
import vcr
from mockito import when, mock, unstub, when2, verify, captor, ANY, patch
from common_fixtures import empty_pickle
from oneWaySync import sync_todoist_to_habitica
# pylint: enable=invalid-name


class TestHelpers:
    def __init__(self):
        self.counter = 1
        self.resp_counter = 1
        self.uri = ""

    @staticmethod
    def get_root():
        pwd = os.getcwd()
        root = pwd.split("Habitica-Plus-Todoist")[0]
        root = os.path.join(root, "Habitica-Plus-Todoist")
        return root

    @staticmethod
    def get_cassette_dir():
        the_dir = os.path.join(TestHelpers.get_repo_path(), 'test/fixtures/cassettes')
        return the_dir

    @staticmethod
    def get_repo_path():
        if '__file__' in globals():
            self_name = globals()['__file__']
        elif '__file__' in locals():
            self_name = locals()['__file__']
        else:
            self_name = __name__
        file_path = self_name.split("Habitica-Plus-Todoist")[0]
        root = os.path.join(file_path, "Habitica-Plus-Todoist")
        return root

    def handle_request(self):
        def get_uri(request):
            habitica_uri = "https://habitica.com/api/v3/tasks/user/"
            self.uri = request.uri
            if request.uri == habitica_uri and request.method == "POST":
                return None
            else:
                return request
        return get_uri

    def scrub_response(self, debug=False):
        def before_record_response(response):
            todoist_uri1 = "https://api.todoist.com/rest/v2/tasks"
            todoist_uri2 = "https://api.todoist.com/sync/v9/completed/get_all"
            habitica_uri = "https://habitica.com/api/v3/tasks/user/"

            cookie = response['headers']['Set-Cookie']
            elem_num = len(cookie)
            for i in range(elem_num):
                response['headers']['Set-Cookie'][i] = "<redacted>"

            response['headers']['X-Amz-Cf-Id'] = "<redacted>"

            body = response['body']['string']
            s_json = json.loads(body)
            if self.uri == habitica_uri and s_json['success']:
                data = s_json['data']
                elem_num = len(data)
                for i in range(elem_num):
                    if data[i]['type'] == 'habit':
                        data[i]['text'] = "some test habit "+str(self.counter)
                        if 'alias' in data[i].keys():
                            data[i]['alias'] = "sometesthabit"+str(self.counter)
                    elif data[i]['type'] == 'todo' or data[i]['type'] == 'daily':
                        data[i]['text'] = "some test task "+str(self.counter)
                        if data[i]['checklist']:
                            cl_count = len(data[i]['checklist'])
                            for j in range(cl_count):
                                data[i]['checklist'][j]['text'] = "item "+str(j)
                    elif data[i]['type'] == 'reward':
                        data[i]['text'] = "some reward"
                    else:
                        print('Warning: Unknown type')
                        breakpoint()
                    if data[i]['notes'] != "":
                        data[i]['notes'] = "Test notes"
                    if data[i]['challenge']:
                        data[i]['challenge']['shortName'] = "Test challenge"
                    data[i]['userId'] = 'cd18fc9f-b649-4384-932a-f3bda6fe8102'
                    self.counter += 1
                s_json['data'] = data
                notifications = s_json['notifications']
                num_nots = len(notifications)
                for i in range(num_nots):
                    msg = notifications[i]
                    if msg['type'] == 'GROUP_INVITE_ACCEPTED':
                        body_text = msg['data']['bodyText']
                        the_split = body_text.split(' accepted')
                        username1 = the_split[0]
                        body_text = body_text.replace(username1, "username1")
                        the_str = the_split[1]
                        the_str = the_str.split('to ')[1]
                        username2 = the_str.split('\'s')[0]
                        body_text = body_text.replace(username2, "username2")
                        s_json['notifications'][i]['data']['bodyText'] = body_text
                body = json.dumps(s_json)
                response['body']['string'] = body.encode()
            elif self.uri == todoist_uri2:
                items = s_json['items']
                num_items = len(items)
                for i in range(num_items):
                    s_json['items'][i]['content'] = "some test task "+str(self.counter)
                    s_json['items'][i]['user_id'] = "34534534534"
                    self.counter += 1
                for key in s_json['projects']:
                    s_json['projects'][key]['name'] = "some test project "+str(self.counter)
                    self.counter += 1
                for key in s_json['sections']:
                    s_json['sections'][key]['user_id'] = "34534534534"
                body = json.dumps(s_json)
                response['body']['string'] = body.encode()
            elif self.uri == todoist_uri1:
                items = s_json
                num_items = len(items)
                for i in range(num_items):
                    s_json[i]['content'] = "some test task "+str(self.counter)
                    s_json[i]['user_id'] = "34534534534"
                    self.counter += 1
                body = json.dumps(s_json)
                response['body']['string'] = body.encode()
                return response
            if debug:
                # output unminified json in separate files
                json_object = json.dumps(s_json, indent=4)
                name = "response_after"+str(self.resp_counter)+".json"
                fullpath = os.path.join(TestHelpers.get_cassette_dir(), name)
                with open(fullpath, "w") as outfile:
                    outfile.write(json_object)
                self.resp_counter += 1
            return response
        return before_record_response


@pytest.fixture()
def fake_or_real_file(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("config2")
    cfg_test = os.path.join(tmp, "auth.cfg")
    src_path = os.path.join(TestHelpers.get_root(), "source/auth.cfg")
    if os.path.exists(src_path):
        shutil.copy(src_path, cfg_test)
        os.chdir(tmp)


# initialization
helper = TestHelpers()

fake_post_count = 0 # pylint: disable=invalid-name


def fake_post(url, data=None, json=None, **kwargs): # pylint: disable=unused-argument, redefined-outer-name
    errors_result = [{'message': 'Task alias already used on another task.',
                      'path': 'alias',
                      'value': data['alias']}]
    json_result = {'sucess': False,
                   'error': 'BadRequest',
                   'message': 'todo validation failed',
                   'errors': errors_result}

    # set default response
    response = mock({'status': 400, 'ok': False,
                     'status_code': '400'},
                     spec=requests.Response)

    when(response).json().thenReturn(json_result)
    global fake_post_count
    fake_post_count += 1
    return response


class TestIntegration2:
    testVcr = vcr.VCR(
        serializer='yaml',
        cassette_library_dir=TestHelpers.get_cassette_dir(),
        record_mode='once',
        match_on=['uri', 'method'],
        filter_headers=[('Authorization', 'Bearer d1347120363c2b310653f610d382729bd51e13c6'),
                        ('x-api-key', '18f22441-2c87-6d8e-fb2a-3fa670837b5a'),
                        ('x-api-user', 'cd18fc9f-b649-4384-932a-f3bda6fe8102'),
                        ('Cookie', "<redacted>")],
        before_record_request=helper.handle_request(),
        before_record_response=helper.scrub_response(debug=False),
        record_on_exception=False,
        decode_compressed_response=True
    )

    # pylint: disable=redefined-outer-name, unused-argument
    @pytest.mark.parametrize("pickle_in", [empty_pickle()], indirect=True)
    def test_alias_already_used(self,
                                fake_or_real_file,
                                pickle_in):
        # pylint: enable=redefined-outer-name, unused-argument
        ''' you need to initialize logging,
            otherwise you will not see anything from vcrpy '''
        logging.basicConfig()
        vcr_log = logging.getLogger("vcr")
        vcr_log.setLevel(logging.DEBUG)

        with self.testVcr.use_cassette("test.yaml"):
            # patch post to habitica with fake
            patch(requests, 'post', replacement=fake_post)

            # mock dump of pickle file
            pkl_out = mock()
            pkl_file = mock()
            when2(open, ...).thenCallOriginalImplementation()
            when2(open, 'oneWay_matchDict.pkl', 'wb').thenReturn(pkl_file)
            when(pickle).Pickler(...).thenReturn(pkl_out)
            when(pkl_out).dump(...)

            # execute
            sync_todoist_to_habitica()

            # verify pickle dump
            dump_dict = captor(ANY(dict))
            verify(pkl_out, times=1).dump(dump_dict)
            data = dump_dict.value
            # assert not bool(data)
            assert bool(data)

            # check # of post to habitica
            # assert fake_post_count == 62
            assert fake_post_count == 0

            # clean-up
            unstub()
