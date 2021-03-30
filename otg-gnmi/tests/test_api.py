import pytest

def test_client_stubs():
    print('Start Running Unit Test')
    return True

if __name__ == '__main__':
    pytest.main(['-s', __file__])