
Info Reactor
============

Info reactors are the components to react to a parsed ``Info`` instance. MCDR uses reactors to trigger command parsing or dispatch plugin events

If you want to add more behaviors to MCDR, like dispatching new events and so on, rather than use a plugin, you can design you own info reactor. Since info reactors can access to the inner ``MCDReforgedServer`` instance which is the core object of MCDR, so it may have much more possible usages. But yes, as always, use with cautions

Similar to `custom server handler <handler>`__\ , you info reactor class needs to inherit from the class ``AbstractInfoReactor``. Then you need to implement the ``react`` method to give it some functionalities

After you finish coding your reactor, you need to add you reactor class path to the `custom_info_reactors <../configure.html#custom-info-reactors>`__ option of the configure file, then your reactor will start working automatically
