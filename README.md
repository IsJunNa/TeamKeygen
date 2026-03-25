# TeamKeygen

一个基于终端界面的自动化脚本项目，主流程集中在 [team.py](/Applications/Project/TeamKeygen/team.py)。

它当前负责的事情主要有：

- 管理 `CDKEY`
- 自动校验兑换码、开卡、轮询开卡结果
- 申请注册邮箱并收取验证码
- 创建 OpenAI 账号并执行后续订阅流程
- 自动落盘 `access_token / refresh_token / token json`
- 按阈值把新注册账号自动导入到 CPA 管理平台
- 在终端里提供菜单式配置中心

## 开始前先看

- 这是一个命令行项目，不是网页后台
- 主入口文件是 [team.py](/Applications/Project/TeamKeygen/team.py)
- 运行配置保存在 [config/config.py](/Applications/Project/TeamKeygen/config/config.py)
- 成功账号汇总保存在 [data/team_accounts.json](/Applications/Project/TeamKeygen/data/team_accounts.json)
- 当前终端 UI 已接入 `rich`，没有安装时会自动退回普通显示

## 项目结构

```text
TeamKeygen/
├── team.py                          # 主入口：注册、开卡、订阅、配置菜单
├── README.md                        # 项目说明
├── config/
│   ├── config.py                    # 当前生效配置
│   └── cdkeys.json                  # CDKEY 源文件（记录 code / use）
├── data/
│   ├── local_graph_accounts.txt     # 本地 Outlook / Graph 邮箱账号池
│   └── team_accounts.json           # 成功账号汇总
├── scripts/
│   ├── outlook_graph_mail_debug.py  # Outlook Graph 收件调试脚本
│   └── tempmail_lol_register.py     # Tempmail.lol 调试脚本
└── logs/
    └── runs/                        # 历史运行产物
```

## 环境要求

建议环境：

- Python 3.9+
- macOS / Linux
- 能正常访问项目依赖的外部接口

当前代码里会用到这些 Python 包：

- `curl_cffi`
- `rich`

如果你的环境里还没装，可以先执行：

```bash
python3 -m pip install curl_cffi rich
```

## 3 分钟上手

### 1. 准备邮箱池

如果你使用本地 Outlook / Graph 邮箱模式，编辑 [data/local_graph_accounts.txt](/Applications/Project/TeamKeygen/data/local_graph_accounts.txt)。

每行一个账号，格式是：

```text
邮箱----邮箱密码----Client ID----Refresh Token
```

示例：

```text
demo@outlook.com----password123----xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx----refresh_token_here
```

### 2. 准备卡码

卡码只看一个文件：

- [config/cdkeys.json](/Applications/Project/TeamKeygen/config/cdkeys.json)

程序会直接从这里读取 `CDKEY`，每次现场 `validate / redeem`；达到最大使用次数后，会把对应项从这个文件里移除。

当前已支持多卡商切换。

- `NCET`
- `EFunCard`

无论卡商来源是哪一个，程序都会统一格式化成：

```text
卡号 MM/YY CVV 地址
```

### 3. 启动程序

```bash
python3 team.py
```

启动后主菜单里常用的是：

- `开始运行`
- `注册类型`
- `生成账户数`
- `配置中心`

## 配置中心怎么用

程序里的 `配置中心` 已经按类别拆好了，不需要你去记配置项名字。

### 文件路径

用于修改这些文件位置：

- 本地邮箱文件
- CDKEY 文件
- 成功账号文件

### 导入数据

适合直接在终端里粘贴数据。

- `粘贴追加 CDKEY`
- `粘贴覆盖 CDKEY`

支持：

- 多行粘贴
- 空格分隔
- 逗号分隔
- 自动去重

说明：

- `CDKEY` 是源数据仓
- `粘贴追加 CDKEY` 会在保留现有内容的前提下自动去重追加
- `粘贴覆盖 CDKEY` 会直接覆盖当前 `CDKEY` 文件，并把新导入码的 `use` 重置为 `0`
- `兑换码` 是实际运行消费池

### 邮箱注册

用于设置：

- 邮箱提供商
- 注册邮箱前缀
- 注册邮箱域名

当前支持的邮箱来源：

- `DuckMail`
- `NPCMail`
- `GPTMail`
- `JunMail`
- `LaMail`
- `CFMail`
- `TempMail.lol` (`tempmail_lol`)
- `本地Outlook邮箱` (`local_graph`)

如果你用的是 [data/local_graph_accounts.txt](/Applications/Project/TeamKeygen/data/local_graph_accounts.txt)，通常把邮箱提供商设成 `本地Outlook邮箱`。
如果你要接入 `JunMail`，把邮箱提供商设成 `JunMail`，并在 `接口与密钥` 里配置 `JunMail API Key` 和 `JunMail Base URL`。

### 接口与密钥

用于设置：

- `卡商`
- `NPCMail API Key`
- `GPTMail API Key`
- `JunMail API Key`
- `JunMail Base URL`
- `DuckMail Bearer`
- `DuckMail Base URL`
- `LaMail API Key`
- `LaMail Base URL`
- `LaMail 域名`
- `CFMail Profile`
- `CPA 上传 URL / Token / Proxy`
- `CPA 自动导入阈值`
- `注册前 CPA 清理`
- `AISub API Key`
- `NCET Base URL`
- `EFunCard Base URL`
- `EFunCard CSRF Token`
- `EFunCard 城市库 URL`
- `AISub Base URL`
- `OpenAI Client ID`
- `OpenAI Originator`
- `OpenAI POW 参数`

说明：

- `OpenAI Client ID` 用于控制 OpenAI OAuth 授权链路里的 `client_id`
- `OpenAI Originator` 会追加到 OpenAI OAuth 授权 URL 的 `originator` 参数
- `OpenAI POW 参数` 会写入 OpenAI 注册链路里 `sentinel/req` 和 `openai-sentinel-token` 的 `p` 字段
- `CPA 上传 URL` 配置后，程序会把 `token_json_dir` 里的 token 文件自动上传到 CPA
- `注册前 CPA 清理` 开启后，会调用 `cpa_20260323/ncs_register.py` 里的清理逻辑先删掉无效号
- 默认留空，不填时按原来的空值请求

### 运行策略

用于设置：

- 注册类型 (`普号` / `Team`)
- 默认代理
- 单卡最大绑定次数
- 日志模式（默认精简，开启后打印详细日志）
- `subscribe` 失败后是否重开号
- `subscribe` 失败次数上限

## 生成账户数是什么意思

主菜单里的 `生成账户数`，就是这次运行最多要生成多少个账号。

限制规则：

- 可以配置成高于当前界面里的预计剩余数量
- 当前界面的 `预计可生成账号 / 预计可生成位置` 只作为参考，不再作为硬性上限
- 如果资源先耗尽，程序会提前停止

## 程序运行时你会看到什么

现在终端提示已经做了收缩，只保留关键节点，主要包括：

- 邮箱是否准备完成
- 验证码是否收到
- OpenAI 账号是否创建成功
- 开卡进度变化
- 订阅是否成功

不会再刷一堆低价值状态码和重复轮询信息。

## 常用文件说明

### [config/config.py](/Applications/Project/TeamKeygen/config/config.py)

这是程序当前真正生效的配置文件。

如果你已经在终端配置中心里改过配置，这里的值通常也会同步更新。

### [config/cdkeys.json](/Applications/Project/TeamKeygen/config/cdkeys.json)

程序唯一消费的 `CDKEY` 源文件。

格式大致是：

```json
[
  {
    "code": "XXXX-XXXX-XXXX-XXXX",
    "use": 0
  }
]
```

也兼容纯文本历史格式；程序在写回时会统一保存成上面的对象数组。

### [data/local_graph_accounts.txt](/Applications/Project/TeamKeygen/data/local_graph_accounts.txt)

本地邮箱账号池。

`local_graph` 模式会按顺序使用这里的账号。

### [data/team_accounts.json](/Applications/Project/TeamKeygen/data/team_accounts.json)

成功账号汇总文件。

每次跑成功的账号结果会追加到这里。

## 常见操作

### 新机器第一次运行

1. 安装 Python 依赖
2. 检查 [config/config.py](/Applications/Project/TeamKeygen/config/config.py)
3. 准备邮箱池文件
4. 准备 `CDKEY` 或兑换码
5. 运行 `python3 team.py`

### 只想导入一批新码

1. 运行 `python3 team.py`
2. 进入 `配置中心`
3. 进入 `导入数据`
4. 选择 `粘贴追加 CDKEY`
5. 直接在终端粘贴

### 只想整批替换现有码

1. 运行 `python3 team.py`
2. 进入 `配置中心`
3. 进入 `导入数据`
4. 选择 `粘贴覆盖 CDKEY`
5. 直接在终端粘贴

### 只想改接口地址或 Key

1. 进入 `配置中心`
2. 进入 `接口与密钥`
3. 修改对应项

## 给开源使用者的建议

如果你准备把这个项目公开：

- 不要把真实 `API Key`、邮箱密码、`Refresh Token` 提交到仓库
- 提交前检查 [config/config.py](/Applications/Project/TeamKeygen/config/config.py) 和 [data/local_graph_accounts.txt](/Applications/Project/TeamKeygen/data/local_graph_accounts.txt)
- 建议把自己的敏感数据替换成占位示例
- 建议补一个 `.gitignore`，忽略本地账号池、运行日志和产出文件

## 建议补充的开源文件

如果你准备长期维护，建议后续再加：

- `LICENSE`
- `.gitignore`
- `requirements.txt`
- `CONTRIBUTING.md`

## 当前 UI 说明

当前终端界面使用 `rich` 做增强，主要作用是：

- 标题面板
- 菜单高亮
- 表格展示
- 彩色日志

如果你的环境没有 `rich`，程序会自动回退成普通终端输出，不会因为 UI 包缺失直接崩掉。

## 最后从哪里开始

如果你是第一次接触这个项目，按这个顺序看：

1. 先看这份 [README.md](/Applications/Project/TeamKeygen/README.md)
2. 再运行 [team.py](/Applications/Project/TeamKeygen/team.py)
3. 在程序里打开 `配置中心`
4. 需要深挖逻辑时，再去看 [team.py](/Applications/Project/TeamKeygen/team.py) 源码
