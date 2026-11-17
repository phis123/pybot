# 打包说明（phis123/pybot fork）

上游 huggingface/pybot 的原样代码未动，打包文件都在这个 fork 里：

- `exe/` — Windows EXE：PyInstaller 配置 `pybot.spec`，构建流程见 `.github/workflows/build-exe.yml`（windows-latest，产物 `pybot-windows`）
- `apk/` — Android APK：Flet 聊天界面壳（`src/main.py` + `src/bot/`），构建流程见 `.github/workflows/build-apk.yml`（`flet build apk`，产物 `pybot-apk`）

两个 workflow 都支持手动触发（Actions 页 → Run workflow）和 `v*` tag 触发。APK 签名用 `KEYSTORE_BASE64`、`KEYSTORE_PASSWORD`、`KEY_PASSWORD`、`KEY_ALIAS` 四个 Secrets，没配就是调试签名。
