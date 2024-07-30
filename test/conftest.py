# pytest fixtures
import pickle
import pytest
from mockito import when, mock, when2


@pytest.fixture
def pickle_in(request):
    ''' mock read in of pickle file'''
    pkl_file = mock()
    pkl_load = mock()
    match_dict = request.param['pickle_tasks']
    when2(open, ...).thenCallOriginalImplementation()
    when2(open, 'oneWay_matchDict.pkl', 'rb').thenReturn(pkl_file)
    when(pickle).Unpickler(...).thenReturn(pkl_load)
    when(pkl_load).load().thenReturn(match_dict)
