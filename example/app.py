from kobin import Kobin, config, Response, TemplateResponse

app = Kobin(__name__)
config.load_from_pyfile('config.py')


@app.route('/')
def index(request):
    return TemplateResponse('hello_jinja2', name='Kobin')


@app.route('/user/{user_id}/')
def hello(user_id: int):
    return Response('Foo')

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8000, app)
    httpd.serve_forever()
