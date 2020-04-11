# -*- coding: utf-8 -*-
import copy
import re
import json
try:
	import Queue
except ImportError:
	import queue as Queue

work_queue = Queue.Queue()
query_count = 0


def convertMinecraftJson(text):
	text = re.sub(r'^.* has the following entity data: ', '', text)  # yeet prefix
	text = re.sub(r'(?<=\d)[a-zA-Z](?=\D)', '', text)  # remove letter after number
	text = re.sub(r'([a-zA-Z.]+)(?=:)', '"\g<1>"', text)  # add quotation marks to all
	list_a = re.split(r'""[a-zA-Z.]+":', text)  # split good texts
	list_b = re.findall(r'""[a-zA-Z.]+":', text)  # split bad texts
	result = list_a[0]
	for i in range(len(list_b)):
		result += list_b[i].replace('""', '"').replace('":', ':') + list_a[i + 1]
	return json.loads(result)


def getPlayerInfo(server, name, path=''):
	if len(path) >= 1 and not path.startswith(' '):
		path = ' ' + path
	command = 'data get entity {}{}'.format(name, path)
	if hasattr(server, 'MCDR') and server.is_rcon_running():
		result = server.rcon_query(command)
	else:
		global query_count
		query_count += 1
		try:
			server.execute(command)
			global work_queue
			while work_queue.empty():
				pass
			result = work_queue.get()
		finally:
			query_count -= 1
	return convertMinecraftJson(result)


def cleanQueue():
	while not work_queue.empty():
		work_queue.get()


def onServerInfo(server, info):
	global work_queue
	if info.isPlayer == 0:
		if ' has the following entity data: ' in info.content:
			if query_count > 0:
				work_queue.put(info.content)
			else:
				cleanQueue()


def on_info(server, info):
	info2 = copy.deepcopy(info)
	info2.isPlayer = info2.is_player
	onServerInfo(server, info2)
