from unittest import TestCase
from kobin.routes import Router


class RouterTest(TestCase):
    def setUp(self):
        self.router = Router()

    def test_match_static_routes(self):
        def target_func(): pass
        self.router.add('^/tests/$', 'GET', target_func)
        test_env = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/tests/'}
        actual_target, actual_args = self.router.match(test_env)

        self.assertEqual(actual_target, target_func)
        self.assertEqual(actual_args, ())

    def test_match_dynamic_routes_with_numbers(self):
        def target_func(): pass
        self.router.add('^/tests/(?P<year>\d{4})/$', 'GET', target_func)
        test_env = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/tests/2015/'}
        actual_target, actual_args = self.router.match(test_env)

        self.assertEqual(actual_target, target_func)
        self.assertEqual(actual_args, ('2015', ))

    def test_match_dynamic_routes_with_string(self):
        def target_func(): pass
        self.router.add('^/tests/(?P<name>\w+)/$', 'GET', target_func)
        test_env = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/tests/kobin/'}
        actual_target, actual_args = self.router.match(test_env)

        self.assertEqual(actual_target, target_func)
        self.assertEqual(actual_args, ('kobin', ))