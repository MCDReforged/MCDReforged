import dataclasses
import threading
import traceback
from types import FrameType
from typing import Dict, List, Optional, Callable, Tuple

_StackMap = Dict[int, FrameType]


def get_stack_map() -> _StackMap:
	# noinspection PyProtectedMember
	from sys import _current_frames
	return _current_frames()


@dataclasses.dataclass(frozen=True)
class ThreadStackInfo:
	thread: threading.Thread
	stack_summary: traceback.StackSummary

	@property
	def head_line(self) -> str:
		return 'Thread {} (id {})'.format(self.thread.name, self.thread.ident)

	def get_lines(self) -> List[str]:
		lines: List[str] = [self.head_line]
		for ssf in self.stack_summary.format():
			lines.extend(filter(None, ssf.splitlines()))
		return lines


def get_stack_info(thread: threading.Thread, *, stack_map: Optional[_StackMap] = None) -> Optional[ThreadStackInfo]:
	if stack_map is None:
		stack_map = get_stack_map()
	stack_data = stack_map.get(thread.ident)
	if stack_data is None:
		return None
	return ThreadStackInfo(thread, traceback.extract_stack(stack_data))


def get_stack_lines(thread: threading.Thread) -> Optional[List[str]]:
	tsi = get_stack_info(thread)
	if tsi is None:
		return None
	return tsi.get_lines()


def start_thread(func: Callable, args: Tuple, name: Optional[str] = None):
	thread = threading.Thread(target=func, args=args, name=name, daemon=True)
	thread.start()
	return thread
