# Quick Start

## Requirements

MCDR requires python3 runtime. The python version need to be at least 3.6

## Install

MCDR is available in [pypi](https://pypi.org/project/mcdreforged). It can be installed via `pip` command

```bash
pip install mcdreforged
```

## Start up

Let's say your are going to start MCDR in a folder named `my_mcdr_server`. Then you can run the following commands:

```bash
cd my_mcdr_server
python -m mcdreforged
```

At the first run, MCDR will generated the default config and permission files, as well as some default folders. The file structure will be like this

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

Now put your server files into the server folder (`server` by default), then modify the configuration file `config.yml` and permission file `permission.yml` correctly. After you can start MCDR again and it correctly handle the server

```bash
python -m mcdreforged
``` 


## Upgrade

With the help of pypi, MCDR can be easily upgraded via a single command

```bash
pip install mcdreforged --upgrade
```

That's it! 

Development builds are avaiable in [Test PyPi](https://test.pypi.org/project/mcdreforged/#history), you can install them if you have special needs

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

Alternatively you can launch `MCDReforged.py` to start MCDR

```bash
python MCDReforged.py
```

For windows users, if you have bound a correct python interpreter to `*.py` files you can also double click the `MCDReforged.py` to start MCDR
