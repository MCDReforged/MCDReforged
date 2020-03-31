# -*- coding: utf-8 -*-

import threading


class EventManager:
    def __init__(self):
        self._event_dict = {}

    def register_event_listener(self, event_title, method):
        if event_title in self._event_dict:
            methods_list = self._event_dict[event_title]
        else:
            methods_list = []
        methods_list.append(method)
        self._event_dict[event_title] = methods_list

    def del_event_listener(self, event_type, method):
        if event_type in self._event_dict:
            methods_set = self._event_dict[event_type]
            methods_set.discard(method)
            if len(methods_set) == 0:
                del self._event_dict[event_type]
            else:
                self._event_dict[event_type] = methods_set
        else:
            pass

    def broadcast_event(self, event_type, args=None, do_daemon=True):
        if args is None:
            args = ()
        if event_type not in self._event_dict:
            return 1
        methods_set = self._event_dict[event_type]
        for single_method in methods_set:
            t = threading.Thread(target=single_method, args=args)
            t.setDaemon(do_daemon)
            t.start()
        return 0


event_manager = EventManager()

