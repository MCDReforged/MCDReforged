from pathlib import Path
from typing import Union

# TODO: os.PathLike is not subscriptable in python3.8
# use os.PathLike[str] when python3.8 support is dropped
PathStr = Union[Path, str]
