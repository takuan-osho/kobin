from unittest import TestCase
from kobin.routes import Route, Router, type_args
from kobin.exceptions import HTTPError


class TypeArgsTests(TestCase):
    def test_type_args(self):
        input_type_hints = {'id': int, 'return': None}
        input_args_dict = {'id': '1'}
        actual = type_args(input_args_dict, input_type_hints)
        self.assertEqual(actual['id'], 1)

    def test_default_type(self):
        input_type_hints = {'return': None}
        input_args_dict = {'id': '1'}
        actual = type_args(input_args_dict, input_type_hints)
        self.assertEqual(actual['id'], '1')


class RouteTests(TestCase):
    def test_route_has_four_items(self):
        def dummy_func(num: int) -> None:
            return num
        route = Route(method='GET', path='/hoge', name='dummy-func', callback=dummy_func)
        self.assertEqual(len(route), 4)


class RouterTests(TestCase):
    def setUp(self):
        self.router = Router()

    def test_match_static_routes(self):
        def dummy_func() -> None:
            pass

        self.router.add('GET', '^/tests/$', 'dummy-func', dummy_func)
        test_env = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/tests/'}
        actual_target, actual_args = self.router.match(test_env)

        self.assertIsNone(actual_args)

    def test_match_dynamic_routes_with_casted_number(self):
        def dummy_func(year: int) -> None:
            return year

        self.router.add('GET', '^/tests/(?P<year>\d{4})/$', 'dummy-func', dummy_func)
        test_env = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/tests/2015/'}
        actual_target, actual_args = self.router.match(test_env)
        self.assertEqual(actual_args, {'year': 2015})

    def test_match_dynamic_routes_with_string(self):
        def dummy_func(name):
            return name

        self.router.add('GET', '^/tests/(?P<name>\w+)/$', 'dummy-func', dummy_func)
        test_env = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/tests/kobin/'}
        actual_target, actual_args = self.router.match(test_env)
        self.assertEqual(actual_args, {'name': 'kobin'})

    def test_404_not_found(self):
        test_env = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/this_is_not_found'}
        self.assertRaises(HTTPError, self.router.match, test_env)
