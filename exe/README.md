# pybot Windows EXE 打包（准备文件，本地验证用）

pybot：Hugging Face 的纯 Python 规则聊天机器人，零依赖，`bot/` 约 41 MB、528 个 `.py` 文件。
核心入口是 `bot/runtime.py` 的 `reply(text, memory)`；`pybot.py` 只是命令行壳。

## 布局

```
pybot-build/
  pybot-src/          # huggingface/pybot 浅克隆，commit 7d63c7fbebb44c7e466e5c8b5c1f341ab767929e
  exe/
    pybot.spec        # PyInstaller 配置（Windows 控制台 pybot.exe，one-dir）
    build-exe.yml     # GitHub Actions workflow（windows-latest），本地文件，未推送
    README.md         # 本文件
  venv/               # 本地 Linux 验证用的虚拟环境（可删）
```

## 关键点：动态导入

`bot/runtime.py` 在 import 时用 `pkgutil.iter_modules()` + `importlib.import_module()`
动态发现 `bot/modules/` 里的全部模块，静态分析扫不到这些导入。
`pybot.spec` 用 `collect_all("bot")` 把整个 `bot` 包（datas + binaries + hiddenimports）
显式收进来；不加这一步，打出来的包会在启动时缺模块。

## 本地验证（Linux，同一套 spec）

```sh
python3 -m venv venv
venv/bin/pip install "pyinstaller>=6.0"
cd exe
../venv/bin/pyinstaller pybot.spec --noconfirm --distpath dist --workpath build-tmp
./dist/pybot/pybot -p "hi, i'm Sam" -v
```

`-v` 会在 stderr 打印 `[module: xxx | N ms]`，能看到模块名即说明动态发现的模块都加载了。
实测见下方“验证结果”。

## Windows 上真正出 EXE 的步骤（还没跑）

1. 把 `build-exe.yml` 放进一个仓库的 `.github/workflows/`（该仓库需包含 `exe/pybot.spec`，
   即本目录结构），或在 Windows 本机跑：
   `pip install pyinstaller` 后 `cd exe && pyinstaller pybot.spec --noconfirm`。
2. 产物在 `exe/dist/pybot/`：`pybot.exe` + `_internal/`，直接双击运行（控制台程序）。
3. 冒烟测试：`pybot.exe -p "hi, i'm Sam" -v`，应输出问候语，并在 stderr 显示模块名。
4. 如需安装包，用 Inno Setup 把 `dist/pybot/` 打成 setup.exe（与 pmvault 同一套做法）。

注意：workflow 里 pybot 源码是直接从 huggingface/pybot 按 commit 钉住克隆的，
构建不依赖 fork；签名（Windows 代码签名证书）目前没有，EXE 未签名，
SmartScreen 首次运行会提示未知发布者。

## 验证结果（本机 Linux，2026-11-18）

- 构建：PyInstaller 6.22.3，one-dir，`./dist/pybot/pybot`，构建耗时约 31 秒，退出码 0。
- 包体积：71 MB（`pybot` 可执行文件 14 MB + `_internal/` 58 MB）；包内含全部 528 个 `.py`
  文件，其中 `bot/modules/` 110 个。唯一缺失模块警告是 Windows 专用的
  `_winapi` / `nt` / `winreg`（Linux 构建上的预期警告，Windows 上会有这些模块）。
- 启动耗时：冷启动约 9.0 秒（含加载全部模块；比源码直接跑的 13 秒还快一点，
  因为是预编译的 .pyc）；第二次运行 9.9 秒。单轮回答本身 2.5–3.5 秒。
- 冒烟输出（均退出码 0）：
  - `pybot -p "hi, i'm Sam" -v` → `Nice to meet you, Sam. What can I help with?`
    `[module: chat | 2519 ms]` —— `-v` 显示模块名，证明动态发现的模块都加载了。
  - `pybot -p "how long should i boil an egg" -v` →
    `Lower eggs into already boiling water: 6 minutes for a runny yolk, …`
    `[module: answers | 3501 ms]`。
- 结论：同一套 spec 的打包逻辑在 Linux 上已验证通过；Windows 上只需在
  windows-latest runner（或 Windows 本机）跑同样的 spec，预期产物为
  `dist/pybot/pybot.exe` + `_internal/`，体积与启动时间与 Linux 接近。
