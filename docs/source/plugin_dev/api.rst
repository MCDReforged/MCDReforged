
.. _api-package:

API Packages for Plugins
========================

When your plugin needs to import something from MCDR, rather than directly import the package you want, you can import the packages in ``mcdreforged.api``

``mcdreforged.api`` is the package for plugin developers to import. By only importing from the api package, the import of the target class in the plugin can be decoupled from the actual location of the target class. If MCDR refactors the target class and moves its location in the future, only importing from the api package can keep your plugin unaffected

all
---

.. code-block:: python

    from mcdreforged.api.all import *

This is the simplest way to import everything you want for plugin development. It's a life saver for lazy man

You can also use the following way as an approach with more security since it doesn't use ``*``

.. code-block:: python

    import mcdreforged.api.all as mcdr

    # access stuffs with mcdr.Something

Continue reading to see what it will actually import

command
-------

``command`` package contains the necessities for building a command tree or create your own command, including command tree node classes, command exceptions and some command utils

For example, if you want the class ``Literal`` and ``IllegalArgument`` for building your command tree ``on_error`` exception handling, you can do it like this

.. code-block:: python

    from mcdreforged.api.command import Literal, IllegalArgument

Of course if you are lazy enough you can just

.. code-block:: python

    from mcdreforged.api.command import *

decorator
---------

``decorator`` package contains some useful function decorators for plugin development

new_thread
^^^^^^^^^^

This is a one line solution to make your function executes in parallels. When decorated with this decorator, functions will be executed in a new daemon thread

This decorator only changes the return value of the function to the created ``Thread`` instance. Beside the return value, it reserves all signatures of the decorated function, so you can safely use the decorated function as if there's no decorating at all

It's also a simple compatible upgrade method for old MCDR 0.x plugins

Example:

.. code-block:: python

    from mcdreforged.api.decorator import new_thread

    def do_something1(text: str):
        print(text)
        time.sleep(5)
        return text

    @new_thread
    def do_something2(text: str):
        print(text)
        time.sleep(5)
        return text

    def on_info(server, info):
        # do_something1('hello')
        do_something2('there')

The only difference between ``do_something1`` and ``do_something2`` is that ``do_something2`` is decorated by ``@new_thread``. So when executing ``do_something2``, it won't lag the following execution of MCDR like ``do_something1`` since ``do_something2`` will execute on another thread

About the returned value of the decorated function, it's a ``FunctionThread`` object. Inherited from ``Thread``, it has 1 extra method comparing to the ``Thread`` class:

.. code-block:: python

    def get_return_value(self, block: bool = False, timeout: Optional[float] = None)

As the name of the method, it's used to get the return value of the original function. An ``RuntimeError`` will be risen if ``block=False`` and the thread is still alive, then if exception occurs in the thread the exception will be risen here

.. code-block:: python

    print(do_something2('task').get_return_value(block=True))  # will be "task"

If you only want to wait for the decorated function to complete, you can simple use the ``join`` method from class ``threading.Thread``. Remember the return value of the decorated function has already been changed in to the ``FunctionThread`` instance

.. code-block:: python

    do_something2('task').join()

In addition to simply and directly use a raw ``@new_thread``, it's recommend to add a thread name argument for the decorator

.. code-block:: python

    @new_thread('My Plugin Thread')
    def do_something3(text: str):
        print(threading.current_thread().name)  # will be "My Plugin Thread"
        time.sleep(10)

So when you logs something by ``server.logger``, a meaningful thread name will be displayed instead of a plain and meaningless ``Thread-3``

In case you want to access the original un-decorated function, you can access the ``original`` field of the decorated function

.. code-block:: python

    print(do_something2.original('task'))  # will be "task"

event_listener
^^^^^^^^^^^^^^

This decorator is used to register a custom event listener without involving `PluginServerInterface <classes/PluginServerInterface.html#register-event-listener>`__

It accepts a single str or PluginEvent indicating the event you are listening to as parameter, and will register the function as the callback of the given listener

It's highly suggested to use this decorator only in the entry point of your plugin so it can work correctly and register the event listener in the correct time

Example:

.. code-block:: python

    @event_listener(MCDRPluginEvents.GENERAL_INFO)
    def my_on_info(server, info):
        server.logger.info('on info in my own listener')

Which is equivalent to:

.. code-block:: python

    def on_load(server, old):
        server.register_event_listener(MCDRPluginEvents.GENERAL_INFO, my_on_info)

spam_proof
^^^^^^^^^^

Use a lock to protect the decorated function from being invoked on multiple threads at the same time

If a multiple-invocation happens, only the first invocation can be executed normally, other invocations will be skipped

The type of the lock can be specified with the ``lock_class`` parameter, for example it can be ``threading.RLock`` (default) or ``threading.Lock``

The return value of the decorated function is modified into a bool, indicating if this invocation is executed normally

The decorated function has 2 extra fields:

- ``original`` field: stores the original undecorated function
- ``lock`` field: stores the lock object used in the spam proof logic

Example:

.. code-block:: python

    @spam_proof
    def some_work(arg):
        # doing some important logics
        foo = 1

Which is equivalent to:

.. code-block:: python

    lock = threading.RLock()

    def some_work(arg) -> bool:
        acquired = lock.acquire(blocking=False)
        if acquired:
            try:
                # doing some important logics
                foo = 1
            finally:
                lock.release()
        return acquired


event
-----

``event`` package contains the classes for creating custom events, and classes of MCDR built-in events

You might already read the `dispatch_event <classes/ServerInterface.html#dispatch-event>`__ method in ``ServerInterface`` class. It only accepts a ``PluginEvent`` instance as its first parameter. So if you want to dispatch your custom event, create a ``LiteralEvent`` for simpleness or a custom event class inherited from ``PluginEvent``

exception
---------

There some custom exceptions that is used in MCDR runtime e.g. `ServerInterface <classes/ServerInterface.html>`__ methods. Here comes the way to import them

rcon
----

Package ``rcon`` contains a single class ``RconConnection``. It's is a simply rcon client for connect to any Minecraft servers that supports rcon protocol

Class references: :ref:`class-ref-rcon`

rtext
-----

Recommend to read the page `Raw JSON text format <https://minecraft.gamepedia.com/Raw_JSON_text_format>`__ in Minecraft Wiki first

This is an advanced text component library for Minecraft

Inspired by the `MCD stext API <https://github.com/TISUnion/rtext>`__ made by `Pandaria98 <https://github.com/Pandaria98>`__

Class references: :ref:`class-ref-rtext`

types
-----

Who doesn't want a complete type checking to help you reduce silly mistakes etc. when coding your plugin? If you want to add type hints to the server interface or command source parameter, here's the package for you to import those Usually-used classes

.. code-block:: python

    from mcdreforged.api.types import ServerInterface, Info

    def on_info(server: PluginServerInterface, info: Info):
        # Now auto completion for server and info parameters should be available for IDE
        pass


utils
-----

Some useful kits

Serializable
^^^^^^^^^^^^

A abstract class for easy serializing / deserializing

Inherit it and declare the fields of your class with type annotations, that's all you need to do

.. code-block:: python

    class MyData(Serializable):
        name: str
        values: List[int]

    data = MyData.deserialize({'name': 'abc', 'values': [1, 2]})
    print(data.serialize())  # {'name': 'abc', 'values': [1, 2]}

    data = MyData(name='cde')
    print(data.serialize())  # {'name': 'cde'}

You can also declare default value when declaring type annotations, then during deserializing, if the value is missing, a `copy <https://docs.python.org/3/library/copy.html#copy.copy>`__ of the default value will be assigned

.. code-block:: python

    class MyData(Serializable):
        name: str = 'default'
        values: List[int] = []

    data = MyData(values=[0])
    print(data.serialize())  # {'name': 'default', 'values': [0]}
    print(MyData.deserialize({}).serialize())  # {'name': 'default', 'values': []}
    print(MyData.deserialize({}).values is MyData.deserialize({}).values)  # False

Enum class will be serialized into its member name

.. code-block:: python

    class Gender(Enum):
        male = 'man'
        female = 'woman'


    class MyData(Serializable):
        name: str = 'zhang_san'
        gender: Gender = Gender.male


    data = MyData.get_default()
    print(data.serialize())                                     # {'name': 'zhang_san', 'gender': 'male'}
    data.gender = Gender.female
    print(data.serialize())                                     # {'name': 'zhang_san', 'gender': 'female'}
    MyData.deserialize({'name': 'li_si', 'gender': 'female'})    # -> MyData(name='li_si', gender=Gender.female)

Serializable class nesting is also supported

.. code-block:: python

    class MyStorage(Serializable):
        id: str
        best: MyData
        data: Dict[str, MyData]
