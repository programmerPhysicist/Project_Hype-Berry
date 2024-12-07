# pylint: disable=missing-function-docstring, missing-module-docstring, invalid-name, missing-class-docstring
# pylint: disable=global-statement
import os
import logging
from pathlib import Path
import pickle
import yaml
import pytest
from mockito import when, mock, unstub, when2, verify, captor, ANY, patch, not_, arg_that
import vcr
import requests

# test imports
# pylint: disable=import-error
from common_fixtures import empty_pickle, auth_cfg # pylint: disable=unused-import
from helpers import TestHelpers

from one_way_sync import sync_todoist_to_habitica
# pylint: enable=invalid-name

# initialization
HELPER = TestHelpers()
POST_COUNT = 0
filepath = Path(os.path.join(TestHelpers.get_root(), 'test/fixtures/dump.yaml'))


def fake_post(url, data=None, json=None, **kwargs): # pylint: disable=unused-argument, redefined-outer-name
    errors_result = [{'message': 'Task alias already used on another task.',
                      'path': 'alias',
                      'value': data['alias']}]
    json_result = {'success': False,
                   'error': 'BadRequest',
                   'message': 'todo validation failed',
                   'errors': errors_result}

    # set default response
    response = mock({'status': 400, 'ok': False,
                     'status_code': '400'},
                    spec=requests.Response)

    when(response).json().thenReturn(json_result)
    global POST_COUNT
    POST_COUNT += 1
    return response


def save_pickle_for_test(dump_dict):
    '''Instead of dumping to pickle, we will
       be saving to human readable yaml to use
       in future tests'''
    if not filepath.is_file():
        with open(filepath, 'w') as file:
            yaml.dump(dump_dict, file)
            print("INFO: Created yaml... ")
    else:
        print("INFO: Yaml already exists!")


def read_pickle():
    if filepath.is_file():
        with open(filepath, 'r') as file:
            match_dict = yaml.load(file, Loader=yaml.Loader)
    else:
        match_dict = {}

    inputs = {'pickle_tasks': match_dict}
    return inputs


@pytest.fixture
def expected(request):
    return request.param


@pytest.fixture
def iters(request):
    return request.param


@pytest.fixture
def clean_up():
    # do nothing before test

    yield
    # clean-up needed
    unstub()


def date_matcher(arg):
    if 'date' in arg:
        return arg['date'] is not None and arg['date'] != ''
    return False


class TestEndToEndIntegration:
    test_vcr = vcr.VCR(
        serializer='yaml',
        cassette_library_dir=TestHelpers.get_cassette_dir(),
        record_mode='once',
        match_on=['uri', 'method'],
        filter_headers=[('Authorization', 'Bearer d1347120363c2b310653f610d382729bd51e13c6'),
                        ('x-api-key', '18f22441-2c87-6d8e-fb2a-3fa670837b5a'),
                        ('x-api-user', 'cd18fc9f-b649-4384-932a-f3bda6fe8102'),
                        ('Cookie', "<redacted>")],
        before_record_request=HELPER.handle_request(),
        before_record_response=HELPER.scrub_response(debug=False),
        record_on_exception=False,
        decode_compressed_response=True
    )

    # pylint: disable=redefined-outer-name, unused-argument
    @pytest.mark.parametrize("pickle_in,expected,iters",
                             [(empty_pickle(), 4, 0), (read_pickle(), 8, 69)],
                             indirect=True)
    def test_end_to_end(self,
                        auth_cfg,
                        expected,
                        iters,
                        clean_up):
        # pylint: enable=redefined-outer-name, unused-argument
        ''' you need to initialize logging,
            otherwise you will not see anything from vcrpy '''
        logging.basicConfig()
        vcr_log = logging.getLogger("vcr")
        vcr_log.setLevel(logging.DEBUG)

        with self.test_vcr.use_cassette("test.yaml"):
            # patch post to habitica with fake
            patch(requests, 'post', replacement=fake_post)

            # mock read in of pickle file
            pkl_file = mock()
            pkl_load = mock()
            when2(open, 'oneWay_matchDict.pkl', 'rb').thenReturn(pkl_file)
            when(pickle).Unpickler(...).thenReturn(pkl_load)
            when(pkl_load).load().thenReturn({})

            # mock dump of pickle file
            pkl_out = mock()
            # when2(open, ...).thenCallOriginalImplementation()
            when2(open, 'oneWay_matchDict.pkl', 'wb').thenReturn(pkl_file)
            when(pickle).Pickler(...).thenReturn(pkl_out)
            when(pkl_out).dump(...)

            # mock put
            response = mock({'status': 200, 'ok': True}, spec=requests.Response)
            when(requests).put(...).thenReturn(response)

            # execute
            sync_todoist_to_habitica()

            # verify pickle dump
            dump_dict = captor(ANY(dict))
            verify(pkl_out, times=1).dump(dump_dict)
            data = dump_dict.value
            save_pickle_for_test(data)
            assert len(data.keys()) == 77

            # check put
            if iters != 0:
                the_url = captor(ANY(str))
                the_headers = captor(ANY(dict))

                # catch-all matcher
                verify(requests, times=81).put(...)

                verify(requests, times=iters).put(url=the_url,
                                                  data=not_(arg_that(date_matcher)),
                                                  headers=the_headers)
                '''
                the_data = captor(arg_that(date_matcher))
                verify(requests, times=6).put(url=the_url,
                                              data=the_data,
                                              headers=the_headers)'''

                # result = the_data.value
                # print(result)
            # check # of post to habitica
            assert POST_COUNT == expected
