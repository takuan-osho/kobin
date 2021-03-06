import os
import types
from typing import Any, Callable, Dict, List, Union, Tuple
from .routes import Router, Route
from .environs import request, response
from .exceptions import HTTPError


class Kobin:
    def __init__(self, root_path: str='.') -> None:
        self.router = Router()
        self.config = Config(os.path.abspath(root_path))

    def route(self, rule: str=None, method: str='GET', name: str=None,
              callback: Callable[..., Union[str, bytes]]=None) -> Callable[..., Union[str, bytes]]:
        def decorator(callback_func):
            self.router.add(method, rule, name, callback_func)
            return callback_func
        return decorator(callback) if callback else decorator

    def _handle(self, environ: Dict) -> Union[str, bytes]:
        environ['kobin.app'] = self
        request.bind(environ)  # type: ignore
        response.bind()        # type: ignore
        try:
            callback, kwargs = self.router.match(environ)
            output = callback(**kwargs) if kwargs else callback()
        except HTTPError:
            import sys
            _type, _value, _traceback = sys.exc_info()
            response.apply(_value)
            output = response.body
        except:
            response.apply(HTTPError(500, 'Internal server error.'))
            output = response.body
        return output

    def wsgi(self, environ: Dict,
             start_response: Callable[[bytes, List[Tuple[str, str]]], None]) -> List[bytes]:
        out = self._handle(environ)
        if isinstance(out, str):
            out = out.encode('utf-8')
        start_response(response.status, response.headerlist)
        return [out]

    def __call__(self, environ: Dict, start_response) -> List[bytes]:
        """It is called when receive http request."""
        return self.wsgi(environ, start_response)


class Config(dict):
    default_config = {
        'BASE_DIR': os.path.abspath('.'),
        'TEMPLATE_DIRS': [os.path.join(os.path.abspath('.'), 'templates')],
        'STATICFILES_DIRS': [os.path.join(os.path.abspath('.'), 'static')],
        'STATIC_ROOT': '/static/',

        'PORT': 8080,
        'HOST': '127.0.0.1',
        'SERVER': 'wsgiref',
    }  # type: Dict[str, Any]

    def __init__(self, root_path: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.root_path = root_path
        self.update(self.default_config)

    def load_from_pyfile(self, file_name: str) -> None:
        t = types.ModuleType('config')  # type: ignore
        file_path = os.path.join(self.root_path, file_name)
        with open(file_path) as config_file:
            exec(compile(config_file.read(), file_path, 'exec'), t.__dict__)  # type: ignore
            self.load_from_module(t)

    def load_from_module(self, module) -> None:
        configs = {key: getattr(module, key) for key in dir(module) if key.isupper()}
        self.update(configs)


def current_app() -> Kobin:
    return request['kobin.app']


def current_config() -> Dict[str, Any]:
    return current_app().config
