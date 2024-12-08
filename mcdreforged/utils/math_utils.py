import random


def ramdom_range(l: float, r: float) -> float:
	return l + (r - l) * random.random()


def lerp(l: float, r: float, k: float) -> float:
	return l + (r - l) * k
