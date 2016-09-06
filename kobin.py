import cgi
import collections
import json
from jinja2 import Environment, PackageLoader  # type: ignore
import os
import types
from typing import (  # type: ignore
    Callable, Dict, List, Tuple, Union, Any, Iterable, get_type_hints
)
from wsgiref.headers import Headers  # type: ignore
import http.client as http_client
from urllib.parse import SplitResult, parse_qs
from http.cookies import SimpleCookie  # type: ignore

DEFAULT_ARG_TYPE = str

config = None  # type: Config

HTTP_CODES = http_client.responses.copy()
_HTTP_STATUS_LINES = dict((k, '%d %s' % (k, v)) for (k, v) in HTTP_CODES.items())


# Config
class Config(dict):
    default_config = {
        'TEMPLATE_DIR': 'templates',
    }

    def __init__(self, module_name: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.module_name = module_name
        self.root_path = os.path.abspath(module_name)
        self.update(self.default_config)
        self.jinja2_env = Environment(
            loader=PackageLoader(self.module_name, self['TEMPLATE_DIR'])
        )

    def load_from_pyfile(self, file_name: str) -> None:
        t = types.ModuleType('config')  # type: ignore
        file_path = os.path.join(self.root_path, file_name)
        with open(file_path) as config_file:
            exec(compile(config_file.read(), file_path, 'exec'), t.__dict__)  # type: ignore
            self.load_from_module(t)

    def load_from_module(self, module) -> None:
        configs = {key: getattr(module, key) for key in dir(module) if key.isupper()}
        self.update(configs)


# Request class
class Request:
    """A wrapper for WSGI environment dictionaries."""
    __slots__ = ('environ', '_body', 'charset',)

    def __init__(self, environ, charset='utf-8') -> None:
        self.environ = environ
        self.charset = charset
        self._body = None  # type: bytes

    def get(self, value: str, default=None):
        return self.environ.get(value, default)

    @property
    def path(self) -> str:
        """ The value of ``PATH_INFO`` with exactly one prefixed slash (to fix
            broken clients and avoid the "empty path" edge case). """
        return '/' + self.environ.get('PATH_INFO', '').lstrip('/')

    @property
    def url(self) -> str:
        protocol = self.get('HTTP_X_FORWARDED_PROTO') or self.get('wsgi.url_scheme', 'http')
        host = self.get('HTTP_X_FORWARDED_HOST') or self.get('HTTP_HOST')
        query_params = self.get("QUERY_STRING")
        url_split_result = SplitResult(protocol, host, self.path, query_params, '')  # type: ignore
        return url_split_result.geturl()

    @property
    def method(self) -> str:
        """ The ``REQUEST_METHOD`` value as an uppercase string. """
        return self.environ.get('REQUEST_METHOD', 'GET').upper()

    @property
    def forms(self) -> Dict[str, str]:
        form = cgi.FieldStorage(  # type: ignore
            fp=self.environ['wsgi.input'],
            environ=self.environ,
            keep_blank_values=True,
        )
        params = {k: form[k].value for k in form}
        return params

    @property
    def query(self) -> Dict[str, List[str]]:
        return parse_qs(self.environ['QUERY_STRING'])

    @property
    def body(self) -> bytes:
        if self._body is None:
            content_length = int(self.environ.get('CONTENT_LENGTH', 0))
            self._body = self.environ['wsgi.input'].read(content_length)
        return self._body

    @property
    def text(self) -> str:
        return self.body.decode(self.charset)

    @property
    def json(self) -> Dict:
        return json.loads(self.text)

    @property
    def cookies(self) -> Dict[str, str]:
        cookies = SimpleCookie(self.environ.get('HTTP_COOKIE', '')).values()
        return {c.key: c.value for c in cookies}

    def get_cookie(self, key: str, default: str=None, secret=None) -> str:
        value = self.cookies.get(key)
        return value or default

    def __getitem__(self, key):
        return self.environ[key]

    def __delitem__(self, key):
        self[key] = ""
        del (self.environ[key])

    def __setitem__(self, key, value):
        """ Change an environ value and clear all caches that depend on it. """
        self.environ[key] = value
        todelete = ()

        if key == 'wsgi.input':
            todelete = ('body', 'forms', 'files', 'params', 'post', 'json')
        elif key == 'QUERY_STRING':
            todelete = ('query', 'params')
        elif key.startswith('HTTP_'):
            todelete = ('headers', 'cookies')

        for key in todelete:
            self.environ.pop('kobin.request.' + key, None)

    def __len__(self):
        return len(self.environ)

    def __repr__(self):
        return '<{cls}: {method} {url}>'.format(
            cls=self.__class__.__name__, method=self.method, url=self.path
        )


# Response class
class Response:
    __slots__ = ('_body', '_status_code', 'headers', 'charset', '_cookies',)
    default_content_type = 'text/plain; charset=UTF-8'
    _status_code = None

    def __init__(self, body: Union[str, bytes]='',
                 status: int=200, headers=None, charset='utf-8') -> None:
        self._body = body
        self.status = status
        self.headers = Headers()
        self.charset = charset
        self._cookies = SimpleCookie()  # type: SimpleCookie

        if headers:
            for name, value in headers.items():
                self.headers.add_header(name, value)

    @property
    def status_code(self):
        """ The HTTP status code as an integer (e.g. 404)."""
        return self._status_code

    @property
    def status(self):
        """ The HTTP status line as a string (e.g. ``404 Not Found``)."""
        if not 100 <= self._status_code <= 999:
            raise ValueError('Status code out of range.')
        status = _HTTP_STATUS_LINES.get(self._status_code)
        return str(status or ('{} Unknown'.format(self._status_code)))

    @status.setter
    def status(self, status_code: int):
        if not 100 <= status_code <= 999:
            raise ValueError('Status code out of range.')
        self._status_code = status_code

    @property
    def body(self) -> bytes:
        if isinstance(self._body, str):
            return self._body.encode(self.charset)
        return self._body

    @property
    def header_list(self) -> List[Tuple[str, str]]:
        if 'Content-Type' not in self.headers:
            self.headers.add_header('Content-Type', self.default_content_type)
        if self._cookies:
            for c in self._cookies.values():
                self.headers.add_header('Set-Cookie', c.OutputString())
        return self.headers.items()

    def set_cookie(self, key: str, value: Any, expires: str=None, path: str=None, **options: Dict[str, Any]) -> None:
        from datetime import timedelta, datetime, date
        import time
        self._cookies[key] = value
        if expires:
            self._cookies[key]['expires'] = expires
        if path:
            self._cookies[key]['path'] = path

        for k, v in options.items():
            if k == 'max_age':
                if isinstance(v, timedelta):
                    v = v.seconds + v.days * 24 * 3600
            if k == 'expires':
                if isinstance(v, (date, datetime)):
                    v = v.timetuple()
                elif isinstance(v, (int, float)):
                    v = v.gmtime(value)
                v = time.strftime("%a, %d %b %Y %H:%M:%S GMT", v)  # type: ignore
            self._cookies[key][k.replace('_', '-')] = v

    def delete_cookie(self, key, **kwargs) -> None:
        kwargs['max_age'] = -1
        kwargs['expires'] = 0
        self.set_cookie(key, '', **kwargs)


class JSONResponse(Response):
    default_content_type = 'text/json; charset=UTF-8'

    def __init__(self, dic: Union[Dict, collections.OrderedDict], status: int=200,
                 headers: Dict[str, str]=None, charset: str='utf-8', **dump_args) -> None:
        super().__init__(json.dumps(dic, **dump_args),
                         status=status, headers=headers, charset=charset)


class TemplateResponse(Response):
    default_content_type = 'text/html; charset=UTF-8'

    def __init__(self, filename: str, status: int=200, headers: Dict[str, str]=None,
                 charset='utf-8', **tpl_args) -> None:
        template = config.jinja2_env.get_template(filename)
        super().__init__(template.render(**tpl_args),
                         status=status, headers=headers, charset=charset)


# Router
def http404(request) -> 'Response':
    return Response(body='404 Not Found', status=404)


def split_by_slash(path: str) -> List[str]:
    stripped_path = path.lstrip('/').rstrip('/')
    return stripped_path.split('/')


class Route:
    def __init__(self, rule: str, method: str, name: str,
                 callback: Callable[..., 'Response']) -> None:
        self.rule = rule
        self.method = method.upper()
        self.name = name
        self.callback = callback

    @property
    def callback_types(self) -> Dict[str, Any]:
        return get_type_hints(self.callback)

    def get_typed_url_vars(self, url_vars: Dict[str, str]) -> Dict[str, Any]:
        typed_url_vars = {}  # type: Dict[str, Any]
        for k, v in url_vars.items():
            arg_type = self.callback_types.get(k, DEFAULT_ARG_TYPE)
            typed_url_vars[k] = arg_type(v)
        return typed_url_vars

    def _match_method(self, method: str) -> bool:
        return self.method == method.upper()

    def _match_path(self, path: str) -> Dict[str, Any]:
        split_rule = split_by_slash(self.rule)
        split_path = split_by_slash(path)
        url_vars = {}  # type: Dict[str, str]

        if len(split_rule) != len(split_path):
            return None

        for r, p in zip(split_rule, split_path):
            if r.startswith('{') and r.endswith('}'):
                url_var_key = r.lstrip('{').rstrip('}')
                url_vars[url_var_key] = p
                continue
            if r != p:
                return None
        return self.get_typed_url_vars(url_vars)

    def match(self, method: str, path: str) -> Dict[str, Any]:
        if not self._match_method(method):
            return None

        url_vars = self._match_path(path)
        if url_vars is not None:
            return self.get_typed_url_vars(url_vars)


class Router:
    def __init__(self) -> None:
        self.routes = []  # type: List['Route']

    def match(self, environ: Dict[str, str]) -> Tuple[Callable[..., 'Response'], Dict[str, Any]]:
        method = environ['REQUEST_METHOD'].upper()
        path = environ['PATH_INFO'] or '/'

        for route in self.routes:
            url_vars = route.match(method, path)
            if url_vars is not None:
                return route.callback, url_vars
        return http404, {}

    def add(self, method: str, rule: str, name: str,
            callback: Callable[..., 'Response']) -> None:
        """ Add a new rule or replace the target for an existing rule. """
        route = Route(method=method.upper(), rule=rule, name=name, callback=callback)
        self.routes.append(route)

    def reverse(self, name, **kwargs) -> str:
        for route in self.routes:
            if name == route.name:
                return route.rule.format(**kwargs)


# WSGI Application Class
class Kobin:
    def __init__(self, module_name: str) -> None:
        self.router = Router()

        global config
        config = Config(module_name)
        config.jinja2_env.globals.update(
            reverse=self.router.reverse
        )

    def route(self, rule: str=None, method: str='GET', name: str='',
              callback: Callable[..., bytes]=None) -> Callable[..., bytes]:
        def decorator(callback_func):
            self.router.add(method, rule, name, callback_func)
            return callback_func
        return decorator(callback) if callback else decorator

    def wsgi(self, env: Dict[str, Any], start_response) -> Iterable[bytes]:
        callback, kwargs = self.router.match(env)
        request = Request(env)
        response = callback(request, **kwargs)
        start_response(response.status, response.header_list)
        return [response.body]

    def __call__(self, env, start_response) -> Iterable[bytes]:
        """It is called when receive http request."""
        return self.wsgi(env, start_response)
