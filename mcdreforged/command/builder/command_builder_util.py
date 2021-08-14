DIVIDER = ' '


def remove_divider_prefix(text):
	return text.lstrip(DIVIDER)


def get_element(text):
	"""
	"my test command" -> "my"
	:type text: str
	:rtype: str
	"""
	pos = text.find(DIVIDER)
	if pos == -1:
		return text
	else:
		return text[:pos]


def __get_var(text, func):
	"""
	Return value, char_read
	value will be None if ValueError occurs
	"""
	arg = get_element(text)
	try:
		value = func(arg)
	except ValueError:
		value = None
	return value, len(arg)


def get_int(text):
	return __get_var(text, int)


def get_float(text):
	return __get_var(text, float)
