# -*- coding: utf-8 -*-


def calc(text):
	whitelist = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ' ', '.', '+', '-', '*', '/', '(', ')', '<', '>', '=']
	text = text.replace('**', '')  # to avoid eeasee
	text_clean = ''
	for c in text:
		if c in whitelist:
			text_clean += c

	if len(text_clean) == 0:
		return None
	try:
		return str(eval(text_clean))
	except Exception as e:
		return str(e)


def on_info(server, info):
	if info.is_user:
		if info.content.startswith('=='):
			result = calc(info.content[2:])
			if result is not None:
				server.say(result)


if __name__ == '__main__':
	while True:
		print(calc(input()))
