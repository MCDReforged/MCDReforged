Frequently Asked Questions
==========================

``ValueError: check_hostname requires server_hostname`` when installing using pip
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. If you're using Clash For Windows:

   * **Method 1:** Turn on ``Settings → System Proxy → Specify Protocol``
   * **Method 2:** Use ``Service Mode`` with ``TUN Mode`` instead of ``System Proxy``.

2. If you're using other proxy software:

   * **Method 3:** Use something like Proxifier instead of system proxy.
   * **Method 4:** Turn off the proxy in the software or system settings.

3. If you're not using proxy at all:
   
   * Well, idk how to solve it. Maybe you should google it?

Configuration file format error due to unescaped path in ``start_command``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Method 1:** Use a batch script instead of start_command

  Create a batch script named ``srart.bat`` in the server folder with full start command:

  .. code-block:: batch

      "C:\Program Files\Foo\Bar\java.exe" -Xms4G -Xmx4G -jar fabric-server-launch.jar nogui

  Then set ``start_command`` to ``start.bat`` in the MCDR configuration file.

* **Method 2:** Escape the start command according to YAML rules.

Commands from client does not respond, returns garbled code, or appears Decode/EncodeError
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

GBK sucks. `Use UTF-8 <quick_start.html#use-utf-8>`__.
