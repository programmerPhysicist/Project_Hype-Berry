# pylint: disable=missing-function-docstring, missing-class-docstring, missing-module-docstring
import os
import json

from urllib.parse import parse_qsl, urlencode


class TestHelpers:
    counter = 1
    resp_counter = 1
    uri = ""

    @staticmethod
    def get_root():
        dir_path = os.path.dirname(os.path.realpath(__file__))
        root = dir_path.split("Project_Hype-Berry")[0]
        root = os.path.join(root, "Project_Hype-Berry")
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
        file_path = self_name.split("Project_Hype-Berry")[0]
        root = os.path.join(file_path, "Project_Hype-Berry")
        return root

    @classmethod
    def handle_request(cls):
        def get_uri(request):
            cls.uri = request.uri
            if request.method == "PUT":
                try:
                    body = json.loads(request.body)
                except ValueError:
                    body = bytes.decode(request.body)
                    query_dict = dict(parse_qsl(body))
                    query_dict['text'] = "some test task " + str(cls.counter)
                    cls.counter += 1
                    body = urlencode(query_dict)
                    request.body = body.encode()
                else:
                    body['text'] = "some test task " + str(cls.counter)
                    cls.counter += 1
                    request.body = json.dumps(body)
            return request
        return get_uri

    def scrub_habitica_resp(self, s_json):
        data = s_json['data']
        elem_num = len(data)
        for i in range(elem_num):
            if data[i]['type'] == 'habit':
                data[i]['text'] = "some test habit " + str(self.counter)
                if 'alias' in data[i].keys():
                    data[i]['alias'] = "sometesthabit" + str(self.counter)
            elif data[i]['type'] == 'todo' or data[i]['type'] == 'daily':
                data[i]['text'] = "some test task " + str(self.counter)
                if data[i]['checklist']:
                    cl_count = len(data[i]['checklist'])
                    for j in range(cl_count):
                        data[i]['checklist'][j]['text'] = "item " + str(j)
            elif data[i]['type'] == 'reward':
                data[i]['text'] = "some reward"
            else:
                print('Warning: Unknown type')
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
        return s_json

    def scrub_habitica_put_resp(self, s_json):
        if 'data' in s_json.keys():
            s_json['data']['text'] = "some test task " + str(self.counter)
            s_json['data']['userId'] = "cd18fc9f-b649-4384-932a-f3bda6fe8102"
        return s_json

    def scrub_todoist_tasks(self, s_json):
        items = s_json
        num_items = len(items)
        for i in range(num_items):
            s_json[i]['content'] = "some test task " + str(self.counter)
            s_json[i]['description'] = "some test description"
            s_json[i]['user_id'] = "34534534534"
            self.counter += 1
        return s_json

    def scrub_todoist_completed(self, s_json):
        items = s_json['items']
        num_items = len(items)
        for i in range(num_items):
            s_json['items'][i]['content'] = "some test task " + str(self.counter)
            s_json['items'][i]['user_id'] = "34534534534"
            self.counter += 1
        for key in s_json['projects']:
            s_json['projects'][key]['name'] = "some test project " + str(self.counter)
            self.counter += 1
        for key in s_json['sections']:
            s_json['sections'][key]['user_id'] = "34534534534"
        return s_json

    @classmethod
    def scrub_response(cls, debug=False):
        def before_record_response(response):
            todoist_uri1 = "https://api.todoist.com/rest/v2/tasks"
            todoist_uri2 = "https://api.todoist.com/sync/v9/completed/get_all"
            habitica_uri1 = "https://habitica.com/api/v3/tasks/user/"
            habitica_uri2 = "https://habitica.com/api/v3/tasks"

            if 'Set-Cookie' in response['headers'].keys():
                cookie = response['headers']['Set-Cookie']
                elem_num = len(cookie)
                for i in range(elem_num):
                    response['headers']['Set-Cookie'][i] = "<redacted>"

            response['headers']['X-Amz-Cf-Id'] = "<redacted>"
            body = response['body']['string']
            try:
                s_json = json.loads(body)
            except json.JSONDecodeError as e:
                print(e)
                return response
            resp_type = ""
            if cls.uri == habitica_uri1 and s_json['success']:
                s_json = cls.scrub_habitica_resp(cls, s_json)
                resp_type = "habitica_"
            elif habitica_uri2 in cls.uri:
                s_json = cls.scrub_habitica_put_resp(cls, s_json)
                resp_type = "habitica_put_"
            elif cls.uri == todoist_uri2:
                s_json = cls.scrub_todoist_completed(cls, s_json)
                resp_type = "todoist_completed_"
            elif cls.uri == todoist_uri1:
                s_json = cls.scrub_todoist_tasks(cls, s_json)
                resp_type = "todoist_task_"
            if debug:
                # output unminified json in separate files
                json_object = json.dumps(s_json, indent=4)
                name = resp_type + "response" + str(cls.resp_counter) + ".json"
                fullpath = os.path.join(TestHelpers.get_cassette_dir(), name)
                with open(fullpath, "w") as outfile:
                    outfile.write(json_object)
                cls.resp_counter += 1

            body = json.dumps(s_json)
            response['body']['string'] = body.encode()
            return response
        return before_record_response
