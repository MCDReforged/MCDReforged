
Telemetry
=========

Since v2.14, MCDR collects and reports anonymous telemetry data about some basic information regarding MCDR and the runtime environment

This data helps MCDR developers analyze usage scenarios and provides data support for the development of future improvements to MCDR's functionality

Telemetry is enabled by default

What will it report
-------------------

The telemetry data contains the following information:

*   A unique UUID v4 identifier, representing the running MCDR instance. The UUID is generated on each MCDR launch, and will not be persisted
*   MCDR and Python version
*   System information, including:

    *   Type, e.g. Windows, Linux
    *   Version, e.g. 10 for Windows, 5.14.0 for Linux
    *   Architecture, e.g. AMD64

*   MCDR information, including:

    *   MCDR uptime
    *   MCDR runtime environment information, e.g. if it's running inside a container or virtualenv
    *   Plugin counts by plugin type
    *   :meth:`Name <mcdreforged.handler.server_handler.ServerHandler.get_name>` of the currently in-used server handler

The collected telemetry data do not contain any personal information, and are not sold or used for advertising purposes

Example telemetry data:

.. code-block:: json

    {
      "uuid": "14bb1768-aa97-4f11-874e-deafd0c09cb0",
      "reporter": "MCDReforged",
      "platform": {
        "mcdr_version": "2.14.0",
        "mcdr_version_pypi": "2.14.0",
        "python_version": "3.12.8",
        "python_implementation": "CPython",
        "system_type": "Windows",
        "system_release": "10",
        "system_architecture": "AMD64"
      },
      "data": {
        "uptime": 10902.91710782051,
        "container_environment": "none",
        "python_package_isolation": "venv",
        "launched_from_source": false,
        "plugin_type_counts": {
          "builtin": 2,
          "solo": 18,
          "packed": 11,
          "directory": 0,
          "linked_directory": 2
        },
        "server_handler_name": "vanilla_handler"
      }
    }

You can also inspect the source code of :class:`~mcdreforged.executor.telemetry_reporter.TelemetryReporter` to see what will be reported

When will it report
-------------------

MCDR will collect and report the telemetry data once per hour

How to disable it
-----------------

If you feel uncomfortable with the telemetry report, or you simply don't want MCDR to report any telemetry data,
you can disable it at any time with any of the following methods

by config
^^^^^^^^^

You can set the value of :ref:`configuration:telemetry` in the config to ``false`` to disable the telemetry

by environment variable
^^^^^^^^^^^^^^^^^^^^^^^

If you want to run / initialize MCDR with telemetry off, you can set the environment variable
``MCDREFORGED_TELEMETRY_DISABLED`` to ``true`` before launching MCDR

.. code-block:: bash

    export MCDREFORGED_TELEMETRY_DISABLED=true

With this environment variable being set to ``true``, the default value of config option :ref:`configuration:telemetry`
will also be set to ``false``
