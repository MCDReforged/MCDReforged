# Document cheatsheet

for MCDR

## Requirement

```
cd docs/
pip install -r requirements.txt
```

python3 of course

## Build document

```
cd docs/
make clean
make html
```

The document will be generated in `docs/build/html/` in zh_CN

If you want to switch the language, modify line 72 in `docs/source/conf.py` or set the value of environment variable `READTHEDOCS_LANGUAGE`

## Update zh_CN translation

```
cd docs/source/
sphinx-build -b gettext . _locale
sphinx-intl update -p _locale -l zh_CN
```

Then check che changed `.po` files in `docs/source/_locale/zh_CN/`. For the changes:

- Empty translations will be generated for new texts
- `#, fuzzy` comments will be added to the translation for changed texts. Fixed the translation and remove the `#, fuzzy` comment
- Translations for removed texts will be moved to the bottom of the `.po` file and be commented out
