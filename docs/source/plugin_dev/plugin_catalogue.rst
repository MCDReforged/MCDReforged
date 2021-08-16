Plugin Catalogue
================

The official MCDR plugin catalogue is the ``next`` branch of repository https://github.com/MCDReforged/PluginCatalogue. Users can browse plugins here and developers can submit their plugins to the catalogue

The catalogue is updated once files change, and every 30 minutes via github action

File structures
---------------

Plugin information is stored in the ``plugins/`` directory in the repository. Each plugin has its own sub-directory named by its plugin id inside the ``plugins/`` directory

.. code-block::

   plugins/
    ├─ my_plugin
    │   └─ plugin_info.json
    └─ another_plugin
        ├─ plugin_info.json
        └─ some_other_files.txt

Plugin Info
^^^^^^^^^^^

``plugin_info.json`` contains the basic information of your plugin

id
~~

The id of your plugin. It needs to be the same with the name of the directory the ``plugin_info.json`` is in

Type: str

authors
~~~~~~~

Optional field, default: ``[]``

A list contains the authors of the plugin. Elements in the list can be a single str representing the name of the author, or a dict contains the author name and the url link of the author

Example:

.. code-block:: json

    "authors": [
        "Someone",
        "That person",
        {
            "name": "AnotherOne",
            "link": "https://github.com/AnotherOne"
        },
        {
            "name": "MyFriend",
            "link": "https://www.myfriend.com"
        }
    ]

Type: List[str or dict]

repository
~~~~~~~~~~

The url of the **github** repository of your plugin

Type: str

branch
~~~~~~

The branch of the git repository where your plugin is in

Type: str

related_path
~~~~~~~~~~~~

Optional field, default: ``.``, which means your plugin files are in the root directory of your repository

The related path of your plugin files in your repository

This is the root directory for plugin catalogue to fetch files from your repository. A ``mcdreforged.plugin.json`` metadata file is expected in this directory

For example, if your plugin repository has following file structure

.. code-block::

    source/
        my_plugin/
            __init__.py
        doc/
            introduction.md
            introduction-zh_cn.md
        mcdreforged.plugin.json
        requirements.txt
    readme.md
    LICENSE

Then the ``related_path`` would be ``source``

Type: str

labels
~~~~~~

Optional field, default: ``[]``

A list of id of `label <#Label>`__ of your plugin. Choose them wisely

Type: List[str]

introduction
~~~~~~~~~~~~

Optional field, default: ``{}``

Introduction is a paragraph written in markdown syntax. It will be shown to user when they are browsing your plugin. Comparing to readme or document, introduction focuses more on showing the features of the plugin to attract new users

For the ``introduction`` field, it's a mapping maps `language <#language>`__ into a file path

The key is the language

The value is the file path of the introduction file in your plugin repository. Field `related_path <#related-path>`__ is considered during the calculation of the real url

Example with the same file structure in `related_path section <#related-path>`__:

.. code-block:: json

    "introduction": {
        "en_us": "doc/introduction.md",
        "zh_cn": "doc/introduction-zh_cn.md"
    }

Alternatively you can don't declare this field but put your introduction file inside the same directory where ``plugin_info.json`` is

It's named by ``introduction.md`` for default language ``en_us`` and named by e.g. ``introduction-zh_cn.md`` for other language

.. code-block::

   plugins/
    └─ my_plugin
        ├─ plugin_info.json
        ├─ introduction.md
        └─ introduction-zh_cn.md

Type: Dict[str, str]

Label
-----

Label describes what your plugin does. A plugin can have multiple labels

All current available labels are shown in the following table

.. list-table::
    :header-rows: 1

    * - Label id
      - Label name
      - Description
    * - information
      - Information
      - Show or get information for users
    * - tool
      - Tool
      - A tool, or a game helper
    * - management
      - Management
      - Manages files or other stuffs of the server
    * - api
      - API
      - Works as a API or a library which provides common functionalities to other plugins

Language
--------

Plugin catalogue supports multiple language for users in different countries

* English (``en_us``)
* Simplified Chinese (``zh_cn``)

The default and fallback language is ``en_us``

Release
-------

Plugin catalogue will automatically detect the releases in your plugin repository and extract the plugin download url in the assets, as long as the release follows the following restrictions:

* Pre-release: It should not be a pre-release
* Release tag name: **the same as the version of the released plugin**, can be in one of the following format

.. list-table::
    :header-rows: 1

    * - Format
      - Example
    * - ``<version>``
      - 1.2.3
    * - ``v<version>``
      - v1.2.3
    * - ``<plugin_id>-<version>``
      - my_plugin_1.2.3
    * - ``<plugin_id>-v<version>``
      - my_plugin_v1.2.3

* Assets: contains 1 asset with ``.mcdr`` file extension name. Other assets will be ignored

  Which also means only `Packed Plugin <plugin_format.html#packed-plugin>`__ is supported

Submit Plugin
-------------

If you want to submit your plugin, create the directory of your plugin inside the ``plugins/`` directory with necessary files, and make a pull request

It's recommended to leave your github link in the `authors <#authors>`__ field so repository maintainers can simply tell if you are the owner of the plugin

All changes files should only be inside the sub-directory named by your plugin id in the ``plugins/`` folder
