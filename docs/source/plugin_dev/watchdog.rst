
.. _watchdog:

Watchdog
=========

Watchdog is a daemon thread monitoring the task executor thread

All MCDR related events are dispatched and executed one by one in the task executor thread as tasks.
When a task in the task executor thread runs for more than 10 seconds, watchdog will consider the task executor is blocked and recreate a new task executor for MCDR,
so that bad-designed plugin will not able to block the logic of MCDR forever

The 10s execution time limit can be configured with the :ref:`config-watchdog_threshold` option in the configure file

If you want to do some time costly tasks in your plugin, execute them in a new thread is highly recommended. `@new_thread <api.html#new-thread>`__ decorator provides an easy way to do that
