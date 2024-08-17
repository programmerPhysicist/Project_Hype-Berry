"""Module for todo api plus"""
from todoist_api_python.api import TodoistAPI
from todoist_api_python.endpoints import get_sync_url
from todoist_api_python.http_requests import get
from todoist_api_python.models import Task
import requests


def dict_to_task(obj, url):
    '''Helper function to convert dict to Task class'''
    obj['comment_count'] = obj['note_count']
    obj['is_completed'] = obj['completed_at'] != ''
    obj['created_at'] = "unknown"
    obj['creator_id'] = obj['user_id']
    obj['description'] = obj['content']
    obj["priority"] = ''
    obj['url'] = url
    return Task.from_dict(obj)


class TodoAPIPlus(TodoistAPI):
    """Extend TodoistAPI class"""
    def __init__(self, token: str, session: requests.Session | None = None) -> None:
        TodoistAPI.__init__(self, token, session)

    def get_all_completed_items(self):
        '''Get all completed tasks from Todoist API'''
        url = get_sync_url('completed/get_all')
        completed_items = get(self._session, url, self._token)
        tasks = completed_items['items']
        return [dict_to_task(obj, url) for obj in tasks]
