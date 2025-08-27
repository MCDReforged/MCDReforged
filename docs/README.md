# Document cheatsheet

for MCDR

## Requirement

Requires python >= 3.9

```
cd docs/
pip install -r requirements.txt
```

## Build document

```bash
cd docs/
make clean
make html
```

The document will be generated in `docs/build/html/` in zh_CN

If you want to switch the language, set the value of environment variable `READTHEDOCS_LANGUAGE`

## Update zh_CN translation

```bash
cd docs/
sphinx-build -b gettext ./source ./source/_locale -D language=en_US  # en_US is required to be used when updating translation so the base language is correct
sphinx-intl update -p ./source/_locale -l zh_CN
```

Then check che changed `.po` files in `docs/source/_locale/zh_CN/`. For the changes:

- Empty translations will be generated for new texts
- `#, fuzzy` comments will be added to the translation for changed texts. Fixed the translation and remove the `#, fuzzy` comment
- Translations for removed texts will be moved to the bottom of the `.po` file and be commented out
- Those msgid starting with `Bases: ` are for base class displaying in auto-gen classes, they don't need to be translated

## Auto build server

```bash
cd docs/
sphinx-autobuild ./source ./build/html --watch ../mcdreforged
```

Added `-D language=zh_CN` to the end if you want to autobuild a Chinese version of the doc
