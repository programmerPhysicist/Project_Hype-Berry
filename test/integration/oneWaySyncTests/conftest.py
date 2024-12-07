# pytest fixtures
import pytest
from mockito import when
import main


@pytest.fixture(scope="package", autouse=True)
def pickle_in(request):
    ''' mock read in of pickle file'''
    match_dict = request.param['pickle_tasks']
    when(main).openMatchDict().thenReturn(match_dict)
