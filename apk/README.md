# PyBot Android（Flet 壳）

把 Hugging Face 的 [pybot](https://github.com/huggingface/pybot)（纯 Python 规则聊天机器人，
零依赖）包成 Android APK。pybot 本身是命令行程序，没有界面，所以这里用一个最小的
Flet 聊天界面做壳，调用 `bot/runtime.py` 的 `turn()` 回答。

## 目录

| 文件 | 说明 |
|---|---|
| `src/main.py` | Flet 聊天界面：输入框 + 消息列表；启动先显示加载中，后台线程再 import bot |
| `pyproject.toml` | 工程配置（flet==1.0.4，`[tool.flet]` 应用信息，入口在 `src/`） |
| `src/bot/` | 上游 pybot 的原样拷贝（528 个 `.py`，约 41MB），不要手改，用 `sync_bot.sh` 同步 |
| `sync_bot.sh` | 从 `../pybot-src` 把 `bot/` 同步到 `src/bot/` |
| `precheck_ci.py` | CI 预检：确认 Flutter / JDK 17 / Android SDK 就位，`flet build` 不会弹交互提示 |
| `.github/workflows/build-apk.yml` | 云端打 APK 的 workflow（见下） |

## 本地跑

```sh
cd apk
pip install "flet==1.0.4"
flet run
```

首次加载要十几秒（bot 要 import 全部模块），界面会先显示“正在加载”，好了才放开输入框。

注意：本地用 `flet run --web` 时，pip 默认装的最新 fastapi（0.163+）会让
flet-web 启动失败（`FastAPI.__init__() got an unexpected keyword argument
'openapi_prefix'`，是 flet-web 1.0.4 和新版 fastapi 的兼容问题，与本应用无关）。
本地测 web 版时先 `pip install "fastapi==0.115.12"`。`flet run`（桌面版）和
`flet build apk` 不走 FastAPI，不受影响。

自检（不启动界面，只验 import 路径和一轮问答）：

```sh
cd apk/src
python3 -c "from bot import runtime; print(runtime.reply('hi', {}))"
```

## 云端打 APK

workflow 在 `.github/workflows/build-apk.yml`，流程照抄 pmvault 的 `build-apk` job：
Flutter 3.44.8、JDK 17（`17.0.13+11`）、Android SDK，`flet build apk`，
产物上传为 Actions Artifact（`pybot-apk`，保留 30 天）。

**注意：这个 workflow 文件不能由 Muse 直接推送。** Muse 的 GitHub App 安装没有
`workflows` 权限，推 `.github/workflows/` 下的文件会返回 403（pmvault 的
`release.yml` 和 music-play 的 `test.yml` 都是这么卡住的）。两种办法：

1. 在仓库网页上新建 `.github/workflows/build-apk.yml`，把本文件内容贴进去，
   直接提交到目标分支；或
2. 给 GitHub App 加 `workflows` 权限（确认生效）后，再让 Muse 推。

签名：workflow 里用了和 pmvault 同一套可选签名 Secrets（`KEYSTORE_BASE64`、
`KEYSTORE_PASSWORD`、`KEY_PASSWORD`、`KEY_ALIAS`）。没配的话 APK 是调试签名，
能安装，但换签名后无法直接覆盖升级；配了才是发布签名。Secrets 要在目标仓库里
自己配，密钥文件本身不在仓库里。

触发：打 tag `v*`（如 `v0.1.0`）或 Actions 页手动触发（可填版本号，默认 `v0.1.0`）。

## 已知风险（第一次构建前先知道）

- **启动慢**：bot import 全部模块本地要约 13 秒，手机 CPU 更慢，首屏务必有加载提示
  （`main.py` 已做：先出界面，后台线程 import）。如果实测超过 30 秒还进不去，
  考虑启动时只做轻量 import、模块懒加载——那是改 bot 的活，不在本壳的范围。
- **包体积大**：`bot/` 41MB 源码 + Flet/Flutter 引擎，APK 预计 80MB 以上，
  `split_per_abi` 没开的话 arm64 和 armeabi-v7a 打在一个包里更大。
- **动态导入**：`bot/runtime.py` 用 `pkgutil.iter_modules` + `importlib` 动态发现
  `bot/modules/` 的模块。Flet 打包只把 `[tool.flet.app] path` 那个目录（这里是
  `src/`）打进 app.zip，所以 `bot/` 必须放在 `src/` 里面；如果以后换打包工具
  （PyInstaller 之类），必须显式收录整个 `bot` 包。
- **Python 版本**：pybot 要求 >=3.8，Flet 1.0.4 要求 >=3.10；本工程
  `requires-python = ">=3.10"`。Flet Android 内嵌的 Python 版本由 Flet 决定，
  构建日志里会打印，首次构建时核对一下。
- **workflow 没在云端跑过**：本地没有 Flutter/JDK/Android SDK，只做了语法和
  import 验证；第一次触发建议看完整日志，确认自检和预检两步都通过再往下看。
