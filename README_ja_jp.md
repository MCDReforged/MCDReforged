MCDReforged
--------

[![Python Versions](https://img.shields.io/pypi/pyversions/mcdreforged.svg)](https://pypi.org/project/mcdreforged)
[![PyPI Version](https://img.shields.io/pypi/v/mcdreforged.svg)](https://pypi.org/project/mcdreforged)
[![Docker](https://img.shields.io/docker/v/mcdreforged/mcdreforged/latest?label=docker)](https://hub.docker.com/r/mcdreforged/mcdreforged)
[![License](https://img.shields.io/github/license/MCDReforged/MCDReforged.svg)](https://github.com/MCDReforged/MCDReforged/blob/master/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/mcdreforged/badge/)](https://docs.mcdreforged.com/)

![MCDR-banner](https://raw.githubusercontent.com/MCDReforged/MCDReforged/master/logo/images/logo_long.png)

[English](README.md) | [简中](README_zh_cn.md) | [繁中](README_zh_tw.md) | **日本語**

> これはPythonに基づくMinecraftサーバー制御ツールです

MCDReforged（以下はMCDRと略す）は全然Minecraftサーバーを修正しないとき、MCDRのプラグインシステムでサーバーを管理するツールです。

簡単の電卓、プレーヤー・ハイライト、Bilibili弾幕さんから、複雑のスコアボード、結構ファイル、自動バックアップまで、MCDRとそれに対応するプラグインで実現できます！

[MCDaemon 1.0](https://github.com/kafuuchino-desu/MCDaemon)のようなアイデアをくれたChino_Desuにありがとうございました。

Discordで私を連絡してください：`Fallen_Breath#1215`

## 強み

- 運行於伺服端之上，完全不需要修改伺服端，保留原汁原味的原版特性
- サーバーの修正必要性が全然ありません。
- 可熱重載的插件系統，無須重啟伺服端即可更新插件
- 多平台/伺服端的兼容性，支援在 Linux / Windows 下運行 vanilla、paper 以及 bungeecord 等伺服端

## 実行原理は何ですか？

/*
MCDR 使用了 [Popen](https://docs.python.org/zh-cn/3/library/subprocess.html#subprocess.Popen) 来將伺服端作為一個子進程啟動，
因此它便擁有了控制伺服端標準輸入/輸出流的能力

Minecraft 伺服器的控制台輸出擁有著穩定的輸出格式，並包含著大量與伺服器有關的有用信息（如玩家聊天信息）。
藉此，MCDR 可以解析並分析伺服端輸出，將他们抽象成不同的事件並派發给插件進行響應

在 Minecraft 内置命令系統的幫助下，MCDR 可以通過向伺服端標準輸入流發送 Minecraft 命令来與 Minecraft 伺服器做出交互
*/

そうです！できれば、MCDRにサーボコンソールを見つめ、サーボ出力に素早く反応し、サーボに命令を入力するロボットと考えられます。

## プラグイン

[ここ](https://github.com/MCDReforged/PluginCatalogue) はMCDRプラグイン倉庫です。

## ドキュメント

もっと多い情報を了解したいですか？[ドキュメント](https://docs.mcdreforged.com/zh_CN/latest/)を見よう
