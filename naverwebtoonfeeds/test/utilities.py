def mock_app(**kwargs):
    class MockApp(object):
        def __getattr__(self, name):
            if name in kwargs:
                return kwargs[name]
            else:
                raise AttributeError
    return MockApp()