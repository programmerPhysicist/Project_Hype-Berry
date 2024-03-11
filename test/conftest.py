# pytest fixtures
import pytest
import pickle
from mockito import when, mock, unstub, when2, kwargs, verify, captor, any

@pytest.fixture
def pickle_in(request):
    # mock read in of pickle file
    pkl_file = mock()
    pkl_load = mock()
    matchDict = request.param['pickle_tasks']
    when2(open, ...).thenCallOriginalImplementation()
    when2(open, 'oneWay_matchDict.pkl', 'rb').thenReturn(pkl_file)
    when(pickle).Unpickler(...).thenReturn(pkl_load)
    when(pkl_load).load().thenReturn(matchDict)