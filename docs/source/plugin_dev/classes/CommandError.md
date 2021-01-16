# CommandError

Sometimes when executing a command, the MCDR command parsing system fail to parse the command for some reason. At that time if you have registered a error listener in the command tree node you will receive a CommandError instance. There are a few useful method of the CommandError instance for plugin developers

## Method

### get_parsed_command

```python
def get_parsed_command(self) -> str
```

Return a prefix of the input command that has been successfully parsed

### get_parsed_command

```python
def get_failed_command(self) -> str:
```

Return a prefix of the input command that is parsing when the failure occurs

### set_handled

```python
def set_handled(self) -> None
```

When handling the command error by error listener on the command tree node, you can use this method to tell MCDR the command error has been handled, so MCDR will not display the default command failure message to the command source like `Unknown argument: !!MCDR reload this<--`
