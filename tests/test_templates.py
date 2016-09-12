import os
from unittest import TestCase
from unittest.mock import patch

TEMPLATE_DIRS = [os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')]


class Jinja2TemplateTests(TestCase):
    @patch('kobin.current_config')
    def test_file(self, mock_current_config):
        """ Templates: Jinja2 file """
        mock_current_config.return_value = {'TEMPLATE_DIRS': TEMPLATE_DIRS}
        j2 = Jinja2Template(name='jinja2', template_dirs=TEMPLATE_DIRS)
        actual = j2.render(var='kobin')
        expected = "Hello kobin World."
        self.assertEqual(actual, expected)
