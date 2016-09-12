from unittest import TestCase
from kobin import Kobin, Response, Config


class KobinTests(TestCase):
    def setUp(self):
        self.app = Kobin('tests')
        self.dummy_start_response = lambda x, y: None

        @self.app.route('/')
        def dummy_func(request):
            return Response('hello', status=200)

        @self.app.route('/{typed_id}/')
        def typed_url_var(request, typed_id: int):
            return typed_id

    def test_typed_url_var(self):
        test_env = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/10'}
        actual = self.app.wsgi(test_env, self.dummy_start_response)
        expected = 10
        self.assertEqual(actual, expected)

    def test_404_not_found(self):
        test_env = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/this_is_not_found'}
        callback, kwargs = self.app.router.match(test_env)
        actual_response = callback(**kwargs)
        expected = 404
        self.assertEqual(actual_response.status_code, expected)

    def test_wsgi(self):
        test_env = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/'}
        actual = self.app.wsgi(test_env, self.dummy_start_response)
        expected = [b'hello']
        self.assertEqual(actual, expected)


class ConfigTests(TestCase):
    def test_constructor_set_root_path(self):
        config = Config('tests')
        config.load_from_pyfile('dummy_config.py')
        self.assertIn('root_path', dir(config))

    def test_load_from_module(self):
        from tests import dummy_config
        config = Config('tests')
        config.load_from_module(dummy_config)
        self.assertIn('UPPER_CASE', config)

    def test_load_from_pyfile(self):
        config = Config('tests')
        config.load_from_pyfile('dummy_config.py')
        self.assertIn('UPPER_CASE', config)

    def test_config_has_not_lower_case_variable(self):
        config = Config('tests')
        config.load_from_pyfile('dummy_config.py')
        self.assertNotIn('lower_case', config)

    def test_failure_for_loading_config(self):
        config = Config('tests')
        self.assertRaises(FileNotFoundError, config.load_from_pyfile, 'no_exists.py')
