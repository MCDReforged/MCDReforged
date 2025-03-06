![image](https://github.com/user-attachments/assets/c78dddc8-1343-4fda-ab35-c1b99823742e)MCDReforged
--------

[![Python Versions](https://img.shields.io/pypi/pyversions/mcdreforged.svg)](https://pypi.org/project/mcdreforged)
[![PyPI Version](https://img.shields.io/pypi/v/mcdreforged.svg)](https://pypi.org/project/mcdreforged)
[![Docker](https://img.shields.io/docker/v/mcdreforged/mcdreforged/latest?label=docker)](https://hub.docker.com/r/mcdreforged/mcdreforged)
[![License](https://img.shields.io/github/license/MCDReforged/MCDReforged.svg)](https://github.com/MCDReforged/MCDReforged/blob/master/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/mcdreforged/badge/)](https://docs.mcdreforged.com/)

![MCDR-banner](https://raw.githubusercontent.com/MCDReforged/MCDReforged/master/logo/images/logo_long.png)

[English](README.md) | [简中](README_zh_cn.md) | [繁中](README_zh_tw.md) | **日本語**

> これはPythonで作られたMinecraftサーバー制御ツールです

MCDReforged（以下はMCDRと略します）はMinecraftサーバーを全く修正せずに、MCDRのプラグインシステムでサーバーを管理するツールです。

簡単な電卓、プレーヤー・ハイライト、Bilibili弾幕から、複雑のスコアボード、設定ファイル、自動バックアップまで、MCDRとそれに対応するプラグインで実現できます！

[MCDaemon 1.0](https://github.com/kafuuchino-desu/MCDaemon)のようなアイデアを提供してくれたChino_Desuさんに申し上げます！

Discordでご連絡してください：`Fallen_Breath#1215`

## 強み

- サーバープログラムが一切変更の必要がありません。サーバーの修正が一切不要。
- サーバーの修正必要性が全然ありません。
- ホットロードできます。リスダートしなくてプラグインを更新できます。
- LinuxとWindowsでvanillaやpaperやbungeecordなどサーバープログラムを実行できます。

## 実行原理は何ですか？
MCDRは[Popen](https://docs.python.org/zh-cn/3/library/subprocess.html#subprocess.Popen)を使用し、サーバーをサブプロセスとして起動します。
そのため、サーバーの標準入出力ストリームを制御することが可能です。

Minecraftサーバーコンソールの出力は安定的な出力形式があって、いろいろでサーバーに関連性がある情報もあります（例えばプレーヤーたちのチャットメッセージ）。
これによって、MCDRはサーバーの出力を分析できてから、これらのデータを様々な事件に抽象化してから、プラグインに送信してからインパクトします。
そうです！できれば、MCDRにサーボコンソールを見つめ、サーボ出力に素早く反応し、サーボに命令を入力するロボットと考えられます。

## プラグイン

[ここ](https://github.com/MCDReforged/PluginCatalogue) はMCDRプラグイン倉庫です。

## ドキュメント

もっと多い情報を了解したいですか？[ドキュメント](https://docs.mcdreforged.com/zh_CN/latest/)を見よう
