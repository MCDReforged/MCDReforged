# MCDReforged 插件元数据重构方案

## 背景

当前 `dev` 分支已经开始对插件元数据进行结构化重构：新增了用于解析 `mcdreforged.plugin.json` 的 Pydantic 模型 `PluginMetadataJsonModel`，并将插件加载后使用的 `Metadata` 改为冻结数据类。现阶段需要在保持兼容性的前提下，补全插件的发行、维护和 Python 依赖信息，并明确 `mcdreforged.plugin.json` 的字段范围。

本文档描述本轮重构的目标、字段范围和兼容原则，不涉及具体实现方式。

## 目标

- 为 `mcdreforged.plugin.json` 增加明确的格式版本。
- 支持结构化的作者、维护者和链接信息。
- 完整支持许可证信息。
- 允许插件指定 Python 依赖文件，不再将文件名固定为 `requirements.txt`。
- 保持现有 `mcdreforged.plugin.json`、单文件插件元数据 `dict` 和 `Metadata` 公开属性兼容。
- 明确 `mcdreforged.plugin.json` 同时承载插件身份、发行、运行和打包信息。

## 设计原则

### 保留两层类型

继续保留以下两个类型及其现有定位：

- `PluginMetadataJsonModel`：描述 `mcdreforged.plugin.json` 的字段并负责严格校验，包括 `schema_version` 等只在读取该文件时使用的信息。
- `Metadata`：插件加载后由 MCDReforged 使用的规范化元数据对象，不保留只服务于 `mcdreforged.plugin.json` 格式解析的信息。

本轮不合并或重命名这两个类型。

### 保留不同插件格式的解析策略

- 单文件插件继续从插件 Python 文件中的元数据 `dict` 宽松解析，保留缺省值和错误值回退能力。
- 目录插件和打包插件的 `mcdreforged.plugin.json` 继续通过 `PluginMetadataJsonModel` 严格校验。

两种解析策略是有意保留的产品行为，本轮不作统一。

### 保持前向兼容

- `mcdreforged.plugin.json` 和单文件插件元数据 `dict` 中的未知字段继续忽略。
- 不禁止额外字段。
- 不增加 `custom` 字段或自定义扩展区。
- `mcdreforged.plugin.json` 和单文件插件元数据 `dict` 已经接受的字段不停止接受。

### 不增加第二个元数据文件

本轮不启用 `mcdreforged.build.json`。`archive_name` 和 `resources` 继续保留在 `mcdreforged.plugin.json` 中；该文件不是仅供插件加载使用的描述文件，也继续包含打包命令需要的字段。

## 字段现状与目标

| 字段 | `dev` 当前情况 | 本轮目标 | 默认值及兼容说明 |
| --- | --- | --- | --- |
| `schema_version` | 不存在 | 在 `PluginMetadataJsonModel` 中新增整数格式版本字段；不进入运行时 `Metadata` | `mcdreforged.plugin.json` 缺失该字段时视为版本 `0`；采用本轮格式的文件使用版本 `1` |
| `id` | `mcdreforged.plugin.json` 中必填并校验；单文件插件允许回退 | 保持不变 | 单文件插件可回退到文件名 |
| `version` | `mcdreforged.plugin.json` 中必填并校验；单文件插件允许回退 | 保持不变 | 单文件插件可回退到 `0.0.0` |
| `name` | 可选字符串 | 保持不变 | 默认使用插件 `id` |
| `description` | 支持字符串或多语言字符串映射 | 保持不变 | 默认 `None` |
| `author` | 支持字符串或字符串列表；运行时为名字列表 | 在 `mcdreforged.plugin.json`、单文件插件元数据 `dict` 和运行时只读属性中保留并标记弃用；不再作为 `Metadata` 的存储字段 | 新插件推荐使用 `authors`；解析后合并到 `authors` |
| `authors` | `PluginMetadataJsonModel` 和 `Metadata` 均无此字段；`Person` 已定义但未用于插件元数据 | 新增结构化作者字段，运行时统一存储 `Person` 对象 | 默认 `None`，表示插件原作者和主要创作者 |
| `maintainers` | `PluginMetadataJsonModel` 中仅有被注释掉的单数 `maintainer` 草稿，实际不接受该字段；`Metadata` 无此字段 | 新增结构化维护者字段，运行时统一存储 `Person` 对象 | 默认 `None`，表示当前负责维护和继续开发插件的人员 |
| `link` | 可选的单一链接字符串 | 在 `mcdreforged.plugin.json`、单文件插件元数据 `dict` 和运行时只读属性中保留并标记弃用；不再作为 `Metadata` 的存储字段 | 新插件推荐使用 `links`；解析后合并到 `links.homepage` |
| `links` | 链接数据类型已定义，但尚未成为元数据字段 | 新增结构化链接字段 | 默认 `None` |
| `license` | 已存在于 `PluginMetadataJsonModel`，但未进入运行时 `Metadata`，调用 `Metadata.to_dict()` 时会丢失 | 完整接入 `PluginMetadataJsonModel`、`Metadata` 和 `Metadata.to_dict()` | 默认 `None`；推荐使用 SPDX License Expression |
| `dependencies` | 插件硬依赖及版本约束映射 | 保持不变 | 默认空映射；本轮不扩展其他依赖关系类型 |
| `requirements_file` | 不存在；插件加载、`mcdreforged pack` 和 `mcdreforged pim pipi` 固定读取 `requirements.txt` | 在 `PluginMetadataJsonModel` 和 `Metadata` 中新增 Python 依赖文件信息 | 缺失表示自动尝试 `requirements.txt`；`null` 表示禁用；字符串表示文件必须存在 |
| `entrypoint` | 多文件插件的入口模块 | 保持不变 | 默认使用插件 `id` |
| `archive_name` | 位于 `mcdreforged.plugin.json` 中，由 `mcdreforged pack` 使用 | 继续作为正式字段保留 | 默认 `None` |
| `resources` | 位于 `mcdreforged.plugin.json` 中，由打包功能使用 | 继续作为正式字段保留 | `PluginMetadataJsonModel` 中默认 `None`，`Metadata` 中按空列表处理 |

## 结构化人员信息

`mcdreforged.plugin.json` 和单文件插件元数据 `dict` 中的 `authors`、`maintainers` 使用相同的人员信息结构，并允许用字符串只填写姓名。转换成 `Metadata` 后，每一项均为 `Person` 对象，不再保留字符串项。

人员信息包含以下字段：

| 字段 | 必需性 | 含义 |
| --- | --- | --- |
| `name` | 必需 | 人员名称 |
| `email` | 可选 | 联系邮箱 |
| `homepage` | 可选 | 个人主页 |

`authors` 用于描述插件原作者和主要创作者；`maintainers` 用于描述当前负责维护、发布和继续开发插件的人员。两者均为描述性信息，不参与权限、信任或插件所有权判断。

`mcdreforged.plugin.json` 和单文件插件元数据 `dict` 继续接受旧字段 `author`，`PluginMetadataJsonModel.author` 标记为弃用。转换成 `Metadata` 时，`author` 的每个姓名转换为 `Person` 并追加到 `authors`；两者同时提供时不根据姓名自动去重。`Metadata` 仅存储 `authors`，`Metadata.author` 是标记弃用的只读属性，其返回值由 `authors` 中的姓名生成。

## 结构化链接信息

`links` 包含以下可选字段：

| 字段 | 含义 |
| --- | --- |
| `homepage` | 插件主页 |
| `source` | 源代码仓库 |
| `documentation` | 使用或开发文档 |
| `issues` | 问题反馈页面 |

当前尚未由 `PluginMetadataJsonModel` 正式接受的草稿字段 `issue` 在启用前统一为 `issues`。`mcdreforged.plugin.json` 和单文件插件元数据 `dict` 继续接受旧字段 `link`，`PluginMetadataJsonModel.link` 标记为弃用。转换成 `Metadata` 时，仅当 `links.homepage` 为 `None` 时才使用 `link` 填充；`links.homepage` 为字符串时保留该字符串。`Metadata` 仅存储 `links`，`Metadata.link` 是标记弃用的只读属性，其返回值来自 `links.homepage`。

`Metadata.to_dict()` 仅输出规范化后的 `authors`、`maintainers` 和 `links`，不重复输出旧 `author`、`link`。

## Python 依赖文件

新增 `requirements_file` 字段，用于声明多文件插件的 Python 依赖文件位置。

`mcdreforged.plugin.json` 中的 `requirements_file` 有三种写法：

- 未声明时自动尝试使用 `requirements.txt`；该默认文件不存在时，继续视为没有 Python 依赖。
- 声明为 `null` 时，表示插件不使用 Python 依赖文件，即使插件中存在默认的 `requirements.txt` 也不处理。
- 声明为字符串时，该字符串是相对插件根目录的文件路径，并且对应文件必须存在；显式声明 `requirements.txt` 与字段缺失具有不同语义。
- 字符串指定的依赖文件不存在时，目录插件或打包插件无效，`mcdreforged pack` 的输入目录也无效。
- 该字段仅对目录插件和打包插件生效；单文件插件继续保持现有行为。

`Metadata.requirements_file` 使用三态结构保存上述区别：自动模式携带默认路径，禁用模式不携带路径，必须存在模式携带 `mcdreforged.plugin.json` 中填写的路径。状态枚举定义在 `RequirementsFileSpec` 内部，不定义独立的顶层枚举。插件加载、`mcdreforged pack` 和 `mcdreforged pim pipi` 根据状态判断文件缺失时的行为，不根据路径是否等于 `requirements.txt` 推断状态。

插件加载、`mcdreforged pack` 和 `mcdreforged pim pipi` 必须按相同规则解释 `requirements_file`。

## Schema 版本

新增 `schema_version` 字段：

- `mcdreforged.plugin.json` 未包含该字段时按版本 `0` 处理。
- 采用本轮新增字段的 `mcdreforged.plugin.json` 使用版本 `1`。
- 旧字段 `author`、`link` 在版本 `1` 中仍可继续使用。
- 对未来更高版本保持宽容：提示版本超出当前支持范围，并继续解析当前版本能够识别的字段。

`schema_version` 只描述 `mcdreforged.plugin.json` 的格式。`PluginMetadataJsonModel` 仅承载并校验字段数据，不负责产生日志或警告。插件加载、`mcdreforged pack` 和 `mcdreforged pim pipi` 在完成 Pydantic 校验后检查版本；版本高于当前支持值时，各自通过服务端日志或命令行输出提示，然后继续使用当前代码能够识别的字段。`Metadata` 不保存 `schema_version`，`Metadata.to_dict()` 也不输出该字段。

Schema 版本用于描述 `mcdreforged.plugin.json` 的格式，不替代插件自身版本，也不替代对 MCDReforged 的依赖约束。

## 打包字段

`archive_name` 和 `resources` 继续属于 `mcdreforged.plugin.json`：

- 不启用独立的 `mcdreforged.build.json`。
- 不迁移现有字段。
- 不为现有字段增加弃用提示。
- 移除代码中关于弃用这两个字段的计划性注释。
- 打包配置继续遵循“命令行参数、插件元数据、默认值”的现有层级关系。

现有但尚未启用的 `PluginBuildConfigJsonModel` 不作为本版本功能或公开 API。

## 本轮非目标

以下内容不属于本轮元数据核心重构：

- 可选依赖、推荐依赖、冲突关系或加载顺序。
- 插件 ID namespace 或 group。
- 多入口点模型。
- Minecraft 版本或服务端 Handler 兼容性声明。
- `icon`、contributors 等其他发行信息。
- `custom` 扩展字段。
- 顶层未知字段报错。
- 独立构建配置文件。
- JSON Schema 发布、文档迁移及其他外围工作。
- 额外的路径、URL 等格式校验强化。

## 完成标准

本轮方案完成后应满足：

- 除只用于解析 `mcdreforged.plugin.json` 的 `schema_version` 外，新增字段在 `PluginMetadataJsonModel` 和 `Metadata` 中均有完整表达。
- 存入 `Metadata` 的新增字段不会在 `Metadata.create()` 或 `Metadata.to_dict()` 的转换中丢失。
- `requirements_file` 的自动、禁用和必须存在三种状态在 `Metadata` 和 `Metadata.to_dict()` 返回值中均可区分。
- 插件加载、`mcdreforged pack` 和 `mcdreforged pim pipi` 能检查 `schema_version`，但 `Metadata` 不存储该字段。
- `license` 不再只存在于 `PluginMetadataJsonModel`。
- 插件加载、`mcdreforged pack` 和 `mcdreforged pim pipi` 对 `requirements_file` 使用相同规则。
- 现有 `mcdreforged.plugin.json` 和单文件插件元数据 `dict` 继续兼容。
- 旧 `author`、`link` 输入会合并到规范化字段，运行时不会重复存储新旧两份数据。
- 单文件插件与多文件插件继续保持各自现有的宽松和严格解析策略。
- `mcdreforged.plugin.json` 和单文件插件元数据 `dict` 中的未知字段继续被忽略。
- `archive_name` 和 `resources` 继续保留在 `mcdreforged.plugin.json` 中。
