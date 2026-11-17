"""PyBot Android 聊天界面（Flet 壳）。

PyBot 本身是命令行程序（stdin/stdout），没有界面。这个文件只做一件事：
给它包一个最小聊天界面，调用 bot/runtime.py 的 turn()/reply() 回答。

关键设计（都是被逼出来的）：
- bot 启动时要 import 全部模块，本地实测约 13 秒，手机上只会更慢，
  所以界面先出现，显示“正在加载”，import 放在后台线程做，好了才放开输入框。
- 每轮回答也要放后台线程跑（README 说一轮约 1 秒），避免界面卡住。
- 用 runtime.turn() 而不是 reply()，这样能拿到是哪个模块出的回答，
  显示在气泡下方（和 Hugging Face Space 的 demo 一样）。

bot/ 目录是上游 huggingface/pybot 的原样拷贝（见 sync_bot.sh），不要手改。
"""

from __future__ import annotations

import asyncio
import traceback

import flet as ft

# 加载失败时界面上显示的提示（不直接抛错闪退，方便定位问题）。
LOAD_FAILED = "PyBot 加载失败，请看日志后重试。"


def load_runtime():
    """后台线程里 import bot。第一次 import 要编译全部模块，最耗时的一步。"""
    from bot import runtime

    return runtime


def make_bubble(text: str, *, is_user: bool, module: str | None = None) -> ft.Control:
    """一条消息气泡。用户在右（蓝底白字），PyBot 在左（灰底黑字）。"""
    inner = [ft.Text(text, size=15, selectable=True)]
    if module:
        inner.append(ft.Text(f"module: {module}", size=11, color="#8a94a6"))
    return ft.Row(
        [ft.Container(
            content=ft.Column(inner, spacing=2, tight=True),
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            border_radius=12,
            bgcolor="#2f6fed" if is_user else "#eef1f6",
        )],
        alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
    )


async def main(page: ft.Page) -> None:
    page.title = "PyBot"
    page.theme_mode = ft.ThemeMode.LIGHT

    memory: dict = {}
    runtime = None  # 后台加载完成后才有值

    messages = ft.ListView(expand=True, spacing=8, auto_scroll=True, padding=12)
    status = ft.Text("正在加载 PyBot…（第一次要十几秒）", size=13, color="#6b7889")
    spinner = ft.ProgressRing(width=18, height=18, stroke_width=2)
    status_row = ft.Row([spinner, status], spacing=8)

    text_field = ft.TextField(
        hint_text="输入消息…",
        expand=True,
        disabled=True,
        autofocus=True,
    )
    send_btn = ft.IconButton(icon=ft.Icons.SEND, tooltip="发送", disabled=True)

    def refresh() -> None:
        # Flet 1.0 里 update() 是同步方法，同步和异步 main 里都这么调。
        page.update()

    async def add_message(text: str, *, is_user: bool, module: str | None = None) -> None:
        messages.controls.append(make_bubble(text, is_user=is_user, module=module))
        refresh()

    async def set_busy(busy: bool) -> None:
        text_field.disabled = busy or runtime is None
        send_btn.disabled = busy or runtime is None
        refresh()

    async def send(_e: ft.ControlEvent | None = None) -> None:
        text = (text_field.value or "").strip()
        if not text or runtime is None:
            return
        text_field.value = ""
        await set_busy(True)
        await add_message(text, is_user=True)

        if text.lower() == "/reset":
            memory.clear()
            messages.controls.clear()
            await add_message("已清空，重新开始吧。", is_user=False)
            await set_busy(False)
            return

        try:
            # turn() 是纯函数调用，放线程里跑，不堵界面。
            result = await asyncio.to_thread(runtime.turn, text, memory)
            reply = " ".join(str(result["reply"]).split()) or "Hello!"
            await add_message(reply, is_user=False, module=result.get("module"))
        except Exception:  # noqa: BLE001 - 一轮失败只显示提示，不闪退
            traceback.print_exc()
            await add_message("这一轮出错了，换个说法再试一次。", is_user=False)
        await set_busy(False)

    text_field.on_submit = send
    send_btn.on_click = send

    page.appbar = ft.AppBar(
        title=ft.Text("PyBot"),
        center_title=False,
        bgcolor="#2f6fed",
        color="white",
    )
    page.add(
        ft.Column(
            [
                messages,
                status_row,
                ft.Row([text_field, send_btn], spacing=8),
            ],
            expand=True,
            spacing=8,
        )
    )
    refresh()

    # --- 后台加载 bot：界面先出来，加载在线程里做 ---
    try:
        runtime = await asyncio.to_thread(load_runtime)
    except Exception:  # noqa: BLE001 - 加载失败也要留在界面上说明原因
        traceback.print_exc()
        status.value = LOAD_FAILED
        spinner.visible = False
        refresh()
        return

    status.value = "PyBot 就绪：没有权重、没有训练，只有规则。"
    spinner.visible = False
    await set_busy(False)
    await add_message(
        "你好，我是 PyBot，一个用纯 Python 规则写的聊天机器人。问我点什么吧。",
        is_user=False,
    )


if __name__ == "__main__":
    ft.run(main)
