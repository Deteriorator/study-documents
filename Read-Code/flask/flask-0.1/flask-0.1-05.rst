##############################################################################
Python Web 模块之 Flask v0.1
##############################################################################

.. contents::

******************************************************************************
第 2 部分  源码阅读准备 
******************************************************************************

2.3 Flask 工作流程与机制
==============================================================================

2.3.5 Session 
------------------------------------------------------------------------------

2.3.5.1 操作 session
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

在这些配置键中 ， SESSION_COOKIE_NAME 也可以通过 Flask 类的属性来设置 ， 分别为 \
session_cookie_name ， 但是 PERMANENT_SESSION_LIFETIME \
(permanent_session_lifetime) 在 0.1 版本中并不存在 。 session cookie 的值 \
(value) 由下面这行代码生成 ： 

.. code-block:: python 

    data = self.serialize(session_expires or expires)

    def serialize(self, expires=None):
        """Serialize the secure cookie into a string.

        If expires is provided, the session will be automatically invalidated
        after expiration when you unseralize it. This provides better
        protection against session cookie theft.

        :param expires: an optional expiration date for the cookie (a
                        :class:`datetime.datetime` object)
        """
        if self.secret_key is None:
            raise RuntimeError('no secret key defined')
        if expires:
            self['_expires'] = _date_to_unix(expires)
        result = []
        mac = hmac(self.secret_key, None, self.hash_method)
        for key, value in sorted(self.items()):
            result.append('%s=%s' % (
                url_quote_plus(key),
                self.quote(value)
            ))
            mac.update('|' + result[-1])
        return '%s?%s' % (
            mac.digest().encode('base64').strip(),
            '&'.join(result)
        )

在 0.10 版本以前 ， session 序列化为 cookie 的格式为 pickle 。 之后更换为 JSON \
格式是为了增强安全性 ， 避免密钥泄露导致的攻击 。 

2.3.5.2 Session 起源
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

在上一节我们知道 ， session 变量在请求上下文中创建 ， 因此为了探寻 session 的起源 \
， 我们需要将断点设置到创建请求上下文之前 ， 比如在Flask类的 __call__ 方法中 。 不\
过 ， 这样的话整个过程就掺杂了太多不相关的操作 ， 需要频繁使用 Step Out 按钮 ， 作\
为替代 ， 可以采取手动探索的方式来探寻 session 的起源 。 

既然 session 变量在 _RequestContext 中创建 ， 那么生成 session 对象的操作也应该在\
这里 。 打开搜索功能 ， 找到 _RequestContext 的定义后发现相关的代码在 __init__方法\
中 ， 如代码清单所示 。 

.. code-block:: python 

    class _RequestContext(object):

        def __init__(self, app, environ):
            self.app = app
            self.url_adapter = app.url_map.bind_to_environ(environ)
            self.request = app.request_class(environ)
            self.session = app.open_session(self.request)
            self.g = _RequestGlobals()
            self.flashes = None

请求上下文的 __init__() 方法中调用了 open_session() 方法来创建 session ， 也就是\
说 ， 一旦接收到请求 ， 就会创建 session 对象 。 open_session() 方法接收程序实例和\
请求对象作为参数 ， 我们可以猜想到 ， 程序实例是用来获取密钥验证 session 值 ， 而请\
求对象参数是用于获取请求中的 cookie 。 open_session() 方法的定义如代码清单所示 。 

.. code-block:: python 

    [flask.py]

    class Flask(object):

        def open_session(self, request):
            """Creates or opens a new session.  Default implementation stores all
            session data in a signed cookie.  This requires that the
            :attr:`secret_key` is set.

            :param request: an instance of :attr:`request_class`.
            """
            key = self.secret_key
            if key is not None:
                return SecureCookie.load_cookie(request, self.session_cookie_name,
                                                secret_key=key)

在这个方法中 ， 如果请求的 cookie 里包含 session 数据 ， 就解析数据到 session 对象\
里 ， 否则就生成一个空的 session 。 这里要注意的是 ， 如果没有设置秘钥 ， \
open_session() 会返回 None ， 这时在 push() 方法中会调用 make_null_session 来生\
成一个无效的 session 对象 (NullSession 类) ， 对其执行字典操作时会显示警告 。 最终\
返回的 session ， 就是我们一开始在视图函数里使用的那个 session 对象 ， 这就是 \
session 的整个生命轨迹 。 

签名可以确保 session cookie 的内容不被篡改 ， 但这并不意味着没法获取加密前的原始数\
据 。 事实上 ， session cookie 的值可以轻易地被解析出来 (即使不知道密钥) ， 这就是\
为什么我们曾频繁提到 session 中不能存入敏感数据 。 下面是使用 itsdangerous 解析 \
session 内容的示例 ： 

.. code-block:: python 

    >>> from itsdangerous import base64_decode
    >>> s = 'eyJjc3JmX3Rva2VuIjp7IiBiI...'
    >>> data, timstamp, secret = s.split('.')
    >>> base64_decode(data)
    '{"answer":42}'

Flask 提供的 session 将用户会话存储在客户端 ， 和这种存储在客户端的方式相反 ， 另一\
种实现用户会话的方式是在服务器端存储用户会话 ， 而客户端只存储一个 session ID 。 当\
接收到客户端的请求时 ， 可以根据 cookie 中的 session ID 来找到对应的用户会话内容 \
。 这种方法更为安全和强健 ， 你可以使用扩展 Flask-Session \
(https://github.com/fengsp/flask-session) 来实现这种方式的 session 。 

2.3.6 模板渲染 
------------------------------------------------------------------------------

在视图函数中 ， 我们使用 render_template() 函数来渲染模板 ， 传入模板的名称和需要\
注入模板的关键词参数 ： 

.. code-block:: python 

    [example]

    from flask import Flask, render_template
    app = Flask(__name__)

    @app.route('/hello')
    def hello():
        name = 'Flask'
        return render_template('hello.html', name=name)

我们在 return 语句这一行设置断点 ， 程序运行到断点后的第一次步进会调用 \
render_template() 函数 。 render_template() 函数的定义在脚本中 ， 如下所示 。 

.. code-block:: python 

    [flask]

    def render_template(template_name, **context):
        """Renders a template from the template folder with the given
        context.

        :param template_name: the name of the template to be rendered
        :param context: the variables that should be available in the
                        context of the template.
        """
        current_app.update_template_context(context)
        return current_app.jinja_env.get_template(template_name).render(context)

这个函数接收的 template_name 参数是文件名 ， 而 ``**context`` 参数是我们调用 \
render_template() 函数时传入的上下文参数 。 

这个函数先获取程序上下文 ， 然后调用程序实例的 Flask.update_template_context() 方\
法更新模板上下文 ， update_template_context() 的定义如代码所示 。 

.. code-block:: python 

    [flask.py]

    class Flask(object):

        def update_template_context(self, context):
            """Update the template context with some commonly used variables.
            This injects request, session and g into the template context.

            :param context: the context as a dictionary that is updated in place
                            to add extra variables.
            """
            reqctx = _request_ctx_stack.top
            for func in self.template_context_processors:
                context.update(func())

承接上文 ， 我们使用 context_processor 装饰器注册模板上下文处理函数 ， 这些处理函数\
被存储在 Flask.template_context_processors 列表里 ： 

.. code-block:: python  

    [flask.py]

    class Flask(object):

        self.template_context_processors = [_default_template_ctx_processor]

        def context_processor(self, f):
            """Registers a template context processor function."""
            self.template_context_processors.append(f)
            return f

列表中是函数的名称 ， 默认的处理函数是 _default_template_ctx_processor() ， 它把\
当前上下文中的 request 、 session 和 g 注入模板上下文 。 

.. code-block:: python 

    [flask.py]

    def _default_template_ctx_processor():
        """Default template context processor.  Injects `request`,
        `session` and `g`.
        """
        reqctx = _request_ctx_stack.top
        return dict(
            request=reqctx.request,
            session=reqctx.session,
            g=reqctx.g
        )

这个 update_template_context() 方法的主要任务就是调用这些模板上下文处理函数 ， 获\
取返回的字典 ， 然后统一添加到 context 字典 。 这里先复制原始的 context 并在最后更\
新了它 ， 这是为了确保最初设置的值不被覆盖 ， 即视图函数中使用 render_template() \
函数传入的上下文参数优先 。 

render_template() 函数最后使用这个 context 字典调用了 render() 函数 。 代码如下所\
示 : 

.. code-block:: python 

    [flask.py]

    def render_template(template_name, **context):
        current_app.update_template_context(context)
        return current_app.jinja_env.get_template(template_name).render(context)

这里对程序实例 app 调用的 Flask.jinja_env() 方法 ， 代码如下所示 : 

.. code-block:: python 

    [flask.py]

    self.jinja_env = Environment(loader=self.create_jinja_loader(),
                                     **self.jinja_options)

它调用 jinja2.Environment 类创建了一个 Jinja2 环境 ， 用于加载模板 。 这个属性完\
成了 Jinja2 环境在 Flask 中的初始化 ， 向模板上下文中添加了一些全局对象 (比如 \
url_for() 函数 、 get_flashed_messages() 函数以及 config 对象等) ， 更新了一些渲\
染设置 。 

虽然之前已经通过调用 update_template_context() 方法向模板上下文中添加了 request \
、 session 、 g (由 _default_template_ctx_processor() 获取) ， 这里再次添加是为\
了让导入的模板也包含这些变量 。 

在调用 render() 函数前 ， 经过了一段非常漫长的调用过程 ： 模板文件定位 、 加载 、 \
解析等 。 这个函数是 Jinja2 的 render 函数渲染模板 ， 并在渲染前后发送相应的信号 \
。 渲染工作结束后会返回渲染好的 unicode 字符串 ， 这个字符串就是最终的视图函数返回\
值 ， 即响应的主体 ， 也就是返回给浏览器的 HTML 页面 。 

******************************************************************************
第 3 部分  源码阅读之 App 代码阅读
******************************************************************************

3.1 App 代码
==============================================================================

阅读的代码以之前的示例代码为例 ：

.. code-block:: python 

    app = Flask(__name__)


    @app.route('/hello/<name>/test', methods=['POST', 'GET'])
    def hello_test(name):
        if name == "Test":
            return 'Test'
        else:
            return 'hello'


    @app.route('/hello/<name>', methods=['POST', 'GET'])
    def hello(name):
        if name == "Test":
            return 'Test'
        else:
            return 'hello'


    @app.route('/')
    def index():
        return "This is index page"


    if __name__ == '__main__':
        app.run()

3.2 Flask 初始化
==============================================================================

uml 见 :  `Flask-__init__`_

.. _`Flask-__init__`: uml/Flask-__init__.puml

首先 app 为初始化的 Flask 类对象 ， 初始化时传入的参数为 __name__ ， 实际就是当前文\
件名 ， 当然在实际使用中可以其他名称 ， 但是得符合当前的包名 。 看一下初始化代码 ： 

.. code-block:: python 

    class Flask(object):

        def __init__(self, package_name):
            self.debug = False
            self.package_name = package_name
            self.root_path = _get_package_path(self.package_name)
            self.view_functions = {}
            self.error_handlers = {}
            self.before_request_funcs = []
            self.after_request_funcs = []
            self.template_context_processors = [_default_template_ctx_processor]
            self.url_map = Map()
            if self.static_path is not None:
                self.url_map.add(Rule(self.static_path + '/<filename>',
                                    build_only=True, endpoint='static'))
                if pkg_resources is not None:
                    target = (self.package_name, 'static')
                else:
                    target = os.path.join(self.root_path, 'static')
                self.wsgi_app = SharedDataMiddleware(self.wsgi_app, {
                    self.static_path: target
                })
            self.jinja_env = Environment(loader=self.create_jinja_loader(),
                                        **self.jinja_options)
            self.jinja_env.globals.update(
                url_for=url_for,
                get_flashed_messages=get_flashed_messages
            )

初始化的时候会设置一些属性 ， root_path 为当前目录 ， 通过 _get_package_path 进行\
获取 ， 其代码为 ： 

.. code-block:: python 

    def _get_package_path(name):
        """Returns the path to a package or cwd if that cannot be found."""
        try:
            return os.path.abspath(os.path.dirname(sys.modules[name].__file__))
        except (KeyError, AttributeError):
            return os.getcwd()

来测试一下这个方法的实际功能 ： 

.. code-block:: python 

    def _get_package_path(name):
        """Returns the path to a package or cwd if that cannot be found."""
        try:
            print 'name', name
            return os.path.abspath(os.path.dirname(sys.modules[name].__file__))
        except (KeyError, AttributeError):
            return os.getcwd()

    print _get_package_path('flask.py')

    >>>name __main__
    >>>name flask.py
    >>>E:\Projects\github\flask

我有些不解的是 name 为何会是 __main__ ? 最终就是获取绝对路径的功能 。 

self.template_context_processors 的值为 [_default_template_ctx_processor] ， \
实际结果是当前请求上下文的参数字典 ： 

.. code-block:: python 

    def _default_template_ctx_processor():
        """Default template context processor.  Injects `request`,
        `session` and `g`.
        """
        reqctx = _request_ctx_stack.top
        return dict(
            request=reqctx.request,
            session=reqctx.session,
            g=reqctx.g
        )

返回的是当前请求上下文的 request ， session 和 g 字典 。 

self.url_map 是一个 werkzeug.routing.Map 类实例 ， 下面后用到 。 当 static_path \
为空的时候 ， 不做操作 ， 但是 static_path 在类里面已经赋值为 static_path = '/\
static' 它是有值的 ， 所以会将 static_path 添加到路由表中 ， 端点为 static 。

self.jinja_env 为魔板渲染引擎 jinja 的环境 。 

3.3 Flask route
==============================================================================

uml: Flask-route.puml

.. code-block:: python

    @app.route('/hello/<name>/test', methods=['POST', 'GET'])
    def hello_test(name):
        if name == "Test":
            return 'Test'
        else:
            return 'hello'

    def route(self, rule, **options):
        def decorator(f):
            self.add_url_rule(rule, f.__name__, **options)
            self.view_functions[f.__name__] = f
            return f
        return decorator

以 hello_test 为例 ， 在 route 函数中 ， rule = '/hello/<name>/test' ， \
options = {'methods': ['POST', 'GET']} ， decorator 的参数 f = hello_test ， \
然后执行步骤为 ： 

1. 执行 route 函数时 ， 直接返回的是 decorator 对象 

2. decorator 对象内部仍有执行步骤 ， 首先将 hello_test 对象传入到 decorator 内部 。

3. 将 rule ， hello_test 对象的名称 'hello_test' 和 options 作为参数传入到 \
   add_url_rule 函数内部 ， 执行相关操作 ， 详情见下一节 。 

4. 将 hello_test 添加到 view_functions 字典中 ， 形如 ： {'hello_test': \
   hello_test}

5. decorator 对象中返回 hello_test 对象

6. route 函数返回 decorator 对象

3.4 Flask add_url_rule
==============================================================================

uml: Flask-add_url_rule.puml

.. code-block:: python 

    def add_url_rule(self, rule, endpoint, **options):
        options['endpoint'] = endpoint
        options.setdefault('methods', ('GET',))
        self.url_map.add(Rule(rule, **options))

    def add_url_rule(self, rule, endpoint, **options):
        options['endpoint'] = endpoint
        options.setdefault('methods', ('GET',))
        a = Rule(rule, **options)
        self.url_map.add(Rule(rule, **options))

接着上述分析 ， 执行到 add_url_rule 时 ， rule = '/hello/<name>/test' ， \
endpoint = 'hello_test' ， options = {'methods': ['POST', 'GET']} ， 对 \
add_url_rule 做一下变形 ， 方便调试看结果 。

对 a 下断点 ， 执行完毕后 url_map 为
::

    Map([[<Rule '/static/<filename>' -> static>, <Rule '/hello/<name>/test' (POST, HEAD, GET) -> hello_test>]])

首先设置 options 字典中 endpoint 字段为 'hello_test' ， 同时设置默认 methods 字段\
为 ('GET',) ， 如果代码已经设置 ， 就不用修改 ， 否则使用默认的 ， 最后将路由规则添\
加到 url_map 中 ， 由于使用的是 werkzeug 中的方法 ， 这里就不在分析 ， 直接看结果 。 

3.5 Flask run
==============================================================================

uml: Flask-run.puml

.. code-block:: python 

    def run(self, host='localhost', port=5000, **options):
        from werkzeug import run_simple
        if 'debug' in options:
            self.debug = options.pop('debug')
        options.setdefault('use_reloader', self.debug)
        options.setdefault('use_debugger', self.debug)
        return run_simple(host, port, self, **options)

在上述 exam 代码中 ， route 添加完毕之后 ， 将 App 运行起来需要执行 run 函数 。 

首先会判断 debug 是不是在 options 字典里面 ， 如果在 ， self.debug = debug 字段的\
值 ， 同时将 use_reloader 字段和 use_debugger 字段设置为 self.debug 的值 ， 最终\
执行 werkzeug.run_simple 函数将 App 运行起来 ， run_simple 的参数分别是 host ， \
port ， self 以及 options 字典 ， 其中 host 和 port 都有默认值 ， 而 self 参数就\
是 Flask 类的实例化 ， 在 run_simple 中会调用该实例 ， 也因此会执行 \
Flask.__call__() 函数 ， 之前的 wsgi 以类的形式实现时说过了 。 接下来执行 \
__call__() 函数 。 

未完待续 ...

上一篇文章 ： `上一篇`_

下一篇文章 ： `下一篇`_ 

.. _`上一篇`: flask-0.1-04.rst
.. _`下一篇`: flask-0.1-06.rst
