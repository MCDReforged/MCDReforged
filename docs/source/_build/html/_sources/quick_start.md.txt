# Quick Start

This is a quick start tutorial of MCDReforged (abbreviated as MCDR, omitted below)

## Requirements

MCDR requires python3 runtime. The python version need to be at least 3.6

## Install

MCDR is available in [pypi](https://pypi.org/project/mcdreforged). It can be installed via `pip` command

```bash
pip install mcdreforged
```

For Chinese users, you can added a `-i https://pypi.tuna.tsinghua.edu.cn/simple` prefix to the command to use Tsinghua tuna mirror website to speed up the installation

```bash
pip install mcdreforged -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## Start up

Let's say your are going to start MCDR in a folder named `my_mcdr_server`. Then you can run the following commands:

```bash
cd my_mcdr_server
python -m mcdreforged
```

At the first run, MCDR will generated the default configure and permission files, as well as some default folders. The file structure will be like this

```
my_mcdr_server/
 ├─ config/
 ├─ logs/
 │   └─ MCDR.log
 ├─ plugins/
 ├─ server/
 ├─ config.yml
 └─ permission.yml
```

Now put your server files into the server folder (`server` by default), then modify the configuration file `config.yml` and permission file `permission.yml` correctly. After you can start MCDR again and it correctly launch and handle the server

```bash
python -m mcdreforged
``` 

## Upgrade

With the help of [pypi](https://pypi.org/project/mcdreforged/), MCDR can be easily upgraded via a single command

```bash
pip install mcdreforged --upgrade
```

That's it! 

For Chinese users, you can use tuna mirror to speed up the upgrading too

```bash
pip install mcdreforged --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple
```

Development builds are available in [Test PyPi](https://test.pypi.org/project/mcdreforged/#history), you can install them if you have special needs

## Start from source

Instead of installing MCDR from pypi, you can execute the source file of MCDR directly. 

Download the source files of MCDR in the [github release page](https://github.com/Fallen-Breath/MCDReforged/releases), and decompress the file to your server folder

```
my_mcdr_server/
 ├─ mcdreforged/
 │   └─ ..
 ├─ MCDReforged.py
 └─ ..
```

Then you can start MCDR with the same command as above

```bash
python -m mcdreforged
``` 

Alternatively you can execute `MCDReforged.py` with python to start MCDR

```bash
python MCDReforged.py
```

`MCDReforged.py` is just a simple wrapper for launching MCDR with the following codes

```python
import sys

from mcdreforged.__main__ import main

if __name__ == '__main__':
    sys.exit(main())
```

`MCDReforged.py` also works for MCDR installed by `pip` command

For windows users, if you have bound a correct python interpreter to `*.py` files you can also double click the `MCDReforged.py` to start MCDR
