from cleanwin_monitor.cli import self_test

def test_self_test():
    assert self_test() == 0
