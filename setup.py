import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(BASE_PATH, 'README.rst')).read()
CHANGES = open(os.path.join(BASE_PATH, 'CHANGES.rst')).read()

__version__ = '0.1.0'
__author__ = 'Masashi Shibata <contact@c-bata.link>'
__author_email__ = 'contact@c-bata.link'
__license__ = 'MIT License'
__classifiers__ = (
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries',
    'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
    'Topic :: Internet :: WWW/HTTP :: WSGI',
    'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
    'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.5',
)


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='kobin',
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    url='https://github.com/c-bata/kobin',
    description='Kobin is a small and statically-typed web framework.',
    long_description=README + '\n\n' + CHANGES,
    classifiers=__classifiers__,
    py_modules=['kobin'],
    keywords='web framework waf',
    license=__license__,
    include_package_data=True,
    test_suite='tests',
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
)
