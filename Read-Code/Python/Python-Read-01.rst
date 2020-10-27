Python 源码阅读系列 1
---------------------------------

前言
===================

此文档为学习 《Python 源码剖析》 笔记。 代码基于 Python 2.5

Python 源代码组织
===================

Python 2.5 的代码结构如下：

.. image:: img/code-structure.png

- **Include** : 该目录下包含了 Python 提供的所有头文件，如果用户需要自己用 \
  C 或 C++ 来编写自定义模块拓展 Python ，那么久需要用到这里提供的文件。

- **Lib** : 该目录包含了 Python 自带的所有标准库， Lib 中的库都是用 Python \
  语言编写的。

- **Modules** : 该目录中包含了所有用 C 语言编写的模块，比如 ``random`` 、 \
  ``cStringIO`` 等。 ``Modules`` 中的模块是那些对速度要求非常严格的模块，而\
  有一些对速度没有太严格要求的模块，比如 ``os`` ，就是用 Python 编写， 而且\
  放在 Lib 目录下。

- **Parser** : 该目录中包含了 Python 解释器中的 Scanner 和 Parser 部分，即\
  对 Python 源代码进行词法分析和语法分析的部分，。除了这些， Parser 目录下还\
  包含了一些有用的工具，这些工具能够根据 Python 语言的语法自动生成 Python 语\
  言的词法和语法分析器，于 YACC 非常类似。

- **Objects** : 该目录中包含了所有 Python 的内建对象，包括整数、List、Dict\
  等。同时，该目录还包括了 Python 在运行时所需要的所有的内部使用对象的实现。

- **Python** : 该目录下包含了 Python 解释器中的 Compiler 和执行引擎部分，是\
  Python 运行的核心所在。

- **PCBuild** : 包含了 Visual Studio 2003 的工程文件，研究 Python 源代码就\
  从这里开始（书中使用 VS2003 对 Python 进行编译）

- **PCBuild8** : 包含了 Visual Studio 2005 使用的工程文件

编译的时候只选择 ``pythoncore`` 和 ``python`` 子工程，但是编译的时候仍然会报\
错，缺少了一个必要文件，源码包中没有提供，需要编译 ``make_buildinfo`` 和 \
``make_versioninfo`` 子工程生成。

编译成功后，结果都在 build 文件夹下，主要有两个： python25.dll 和 python.exe 。\
Python 解释器的全部代码都在 python25.dll 中。对于 WinXP 系统，安装 python \
时，python25.dll 会被拷贝到 ``C:\Windows\system32`` 下。（此结果来自与书中，后\
续我会尝试在本地编译一次试试）

修改 Python 源代码
--------------------------

书中修改了一个函数的源代码，它的原始代码在 Objects/intobject.c 里面，代码如下：

.. code-block:: c

    static int
    int_print(PyIntObject *v, FILE *fp, int flags)
        /* flags -- not used but required by interface */
    {
        fprintf(fp, "%ld", v->ob_ival);
        return 0;
    }

然后借用 Python 的 C API 中提供的输出对象接口，代码在 Include/object.h 文件里，\
代码如下：

.. code-block:: c

    PyAPI_FUNC(int) PyObject_Print(PyObject *, FILE *, int);

修改后的代码如下：

.. code-block:: c

    static int
    int_print(PyIntObject *v, FILE *fp, int flags)
        /* flags -- not used but required by interface */
    {
      
        PyObject* str = PyString_FromString("i am in int_print");
        PyObject_Print(str, stdout, 0);
        printf("\n");

        fprintf(fp, "%ld", v->ob_ival);
        return 0;
    }


``PyString_FromString`` 是 Python 提供的 C API ，用于从 C 中的原生字符数组创建出 \
Python 中的字符串对象。 ``PyObject_Print`` 函数中第二个参数指明的是输出目标。代码\
中使用的是 ``stdout`` ，即指定的输出目标是标准输出。

重定向输出：

.. code-block:: c 

    static PyObject *
    int_repr(PyIntObject *v)
    {
        char buf[64];
        PyOS_snprintf(buf, sizeof(buf), "%ld", v->ob_ival);
        return PyString_FromString(buf);
    }

添加重定向输出后的代码：

.. code-block:: c 

    static PyObject *
    int_repr(PyIntObject *v)
    {
        if(PyInt_AsLong(v) == -999){
            PyObject* str = PyString_FromString("i am in int_repr");
            PyObject* out = PySys_GetObject("stdout");
            if (out != NULL) {
                PyObject_Print(str, stdout, 0);
                printf("\n");
            }
        }

        char buf[64];
        PyOS_snprintf(buf, sizeof(buf), "%ld", v->ob_ival);
        return PyString_FromString(buf);
    }

``PyInt_AsLong`` 的功能是将 Python 的整数对象转换为 C 中的 int 值。

通常 Python 的源代码中会使用 PyObject_GC_New , PyObject_GC_Malloc, \
PyMem_MALLOC , PyObject_MALLOC 等 API ，只需坚持一个原则，即凡是以 New \
结尾的， 都以 C++ 中的 new 操作符视之；凡是以 Malloc 结尾的，都以 C 中的 \
malloc 操作符视之。（C++ 中的 new 我不知道啊^_^!,找时间了解一下）。
