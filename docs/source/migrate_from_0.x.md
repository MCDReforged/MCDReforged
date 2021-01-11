# Migrate from MCDR 0.x

## File structure

Since MCDR now is installed as a python package, unless you run MCDR with source, file / folders below can be removed

- utils/
- resources/
- requirements.txt
- LICENSE
- readme.md
- readme_cn.md

The logging folder is renamed from `log/` to `logs/`

## Config

There come quite a lot of changes to the config file. Although MCDR will still work if you keep the old config file, it's highly recommend to make a new default configure file, and fill your old configures into the new configure file.

You can rename the old `config.yml` to a temporary name like `old_config.yml`, then start MCDR. MCDR will generate a new default configure file and exit. Then open these 2 configure file and migrate.

## Permission

There's no change to the permission system and the permission file, so you can just use the old permission file.

## Plugins

### Meta data

### Listener

### Multi-threading
