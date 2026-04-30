from ctypes import windll
import time
import os
import json
import threading
import tkinter
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext
from pathlib import Path
from webbrowser import open as webopen
import func


class GUI_USE:
    def __init__(self, init_window_name):
        self.init_window_name = init_window_name
        self.target_window_hwnd = ""
        self.macros = []
        self.macroInsertPos = tkinter.END
        self.gapTime = 5
        self.macroRunning = False
        self.timeMacroUse = float(0)

    def set_init_window(self):
        self.init_window_name.title("窗口后台宏")
        self.init_window_name.resizable(False, False)
        
        # self.init_window_name.iconbitmap("app.ico")

        icon_path = func.resource_path("app.ico")
        self.init_window_name.iconbitmap(icon_path)
        
        self.init_window_width = 1000
        self.init_window_height = 600
        init_window_x = int(
            (self.init_window_name.winfo_screenwidth() - self.init_window_width) / 2
        )
        init_window_y = int(
            (self.init_window_name.winfo_screenheight() - self.init_window_height) / 2
        )
        # 将窗口居中显示
        self.init_window_name.geometry(
            "{}x{}+{}+{}".format(
                self.init_window_width,
                self.init_window_height,
                init_window_x,
                init_window_y,
            )
        )

        # 窗口布局
        self.topFrame = ttk.Frame(
            self.init_window_name, width=1000, height=60
        )  # , borderwidth=2, relief='sunken'
        self.topFrame.pack(side="top", fill="x", expand=0)
        self.leftFrame = ttk.Frame(self.init_window_name, width=500, height=540)
        self.leftFrame.pack(side="left", fill="y", expand=0)
        self.rightFrame = ttk.Frame(self.init_window_name, width=500, height=540)
        self.rightFrame.pack(side="right", fill="y", expand=0)

        # 目标窗口标签
        self.labelWindows = ttk.Label(self.topFrame, text="目标窗口: ")
        self.labelWindows.place(x=20, y=15, width=60, height=30)
        # 目标窗口选择框
        self.comboboxWindows = ttk.Combobox(self.topFrame)
        self.comboboxWindows["state"] = "readonly"
        self.comboboxWindows.set("请选择目标窗口:")
        self.comboboxWindows.bind("<<ComboboxSelected>>", self.chose_window)
        self.comboboxWindows.place(x=90, y=17, width=530, height=25)
        # 刷新窗口列表按钮
        self.buttonRefreshWindows = ttk.Button(
            self.topFrame, text="刷新窗口列表", command=self.refresh_windows
        )
        self.buttonRefreshWindows.place(x=630, y=15, width=100, height=30)
        # 开始执行按钮
        self.buttonStart = ttk.Button(
            self.topFrame, text="开始执行", command=self.macro_start
        )
        self.buttonStart.place(x=740, y=15, width=100, height=30)
        # 停止执行按钮
        self.buttonStop = ttk.Button(
            self.topFrame, text="停止执行", command=self.macro_stop
        )
        self.buttonStop["state"] = "disable"
        self.buttonStop.place(x=850, y=15, width=100, height=30)

        # 信息输出框标签
        self.labelLog = ttk.Label(self.leftFrame, text="运行日志")
        self.labelLog.place(x=20, y=5, width=60, height=30)
        # 信息输出框
        self.scrolledtextBox = scrolledtext.ScrolledText(self.leftFrame)
        self.scrolledtextBox.see(tkinter.END)
        self.scrolledtextBox.config(state="disabled")
        self.scrolledtextBox.place(x=20, y=40, width=490, height=450)
        # 执行信息标签
        self.labelRunVar = tkinter.StringVar()
        self.labelRunVar.set("选择目标窗口后点开始执行")
        self.labelRun = ttk.Label(self.leftFrame, textvariable=self.labelRunVar)
        self.labelRun.place(x=20, y=490, width=490, height=30)
        # 宏配置标签
        self.labelMacroConfig = ttk.Label(self.leftFrame)
        self.labelMacroConfig.place(x=20, y=510, width=490, height=30)

        # 宏流程标签
        self.labelMacro = ttk.Label(self.rightFrame, text="宏流程")
        self.labelMacro.place(x=10, y=5, width=60, height=30)
        # 总循环间隔标签
        self.labelGapTime = ttk.Label(self.rightFrame, text="总循环间隔(s):")
        self.labelGapTime.place(x=140, y=5, width=90, height=30)
        # 总循环间隔输入
        self.entryGapTime = ttk.Entry(self.rightFrame)
        self.entryGapTime.insert(tkinter.END, f"5.00")
        self.entryGapTime.place(x=240, y=5, width=100, height=30)
        # 更新时间间隔按钮
        self.buttonUpdateGapTime = ttk.Button(
            self.rightFrame, text="更新总循环间隔", command=self.update_gaptime
        )
        self.buttonUpdateGapTime.place(x=350, y=5, width=100, height=30)
        # 宏流程
        self.macroCloumn = ("num", "type", "key", "conduct", "delay")
        self.treeviewMacro = ttk.Treeview(
            self.rightFrame,
            columns=self.macroCloumn,
            show="headings",
            selectmode="browse",
        )
        self.treeviewMacro.bind("<<TreeviewSelect>>", self.get_selected_row)
        self.treeviewMacro.heading("num", text="序号")
        self.treeviewMacro.heading("type", text="类型")
        self.treeviewMacro.heading("key", text="按键")
        self.treeviewMacro.heading("conduct", text="动作")
        self.treeviewMacro.heading("delay", text="延时(ms)")

        self.treeviewMacro.column("num", width=70, anchor="center")
        self.treeviewMacro.column("type", width=100, anchor="center")
        self.treeviewMacro.column("key", width=100, anchor="center")
        self.treeviewMacro.column("conduct", width=100, anchor="center")
        self.treeviewMacro.column("delay", width=100, anchor="center")
        self.treeviewMacro.place(x=10, y=40, width=470, height=400)

        # 键值标签
        self.labelKey = ttk.Label(self.rightFrame, text="键值:")
        self.labelKey.place(x=10, y=450, width=40)
        # 键值下拉框
        self.comboboxKey = ttk.Combobox(
            self.rightFrame, state="readonly", values=func.KeyCode
        )
        self.comboboxKey.current(0)
        self.comboboxKey.place(x=50, y=450, width=80)
        # 动作标签
        self.labelOperate = ttk.Label(self.rightFrame, text="动作:")
        self.labelOperate.place(x=140, y=450, width=40)
        # 动作下拉框
        self.comboboxOperate = ttk.Combobox(
            self.rightFrame, state="readonly", values=("按下", "抬起")
        )
        self.comboboxOperate.current(0)
        self.comboboxOperate.place(x=180, y=450, width=60)
        # 延时标签
        self.labelOperate = ttk.Label(self.rightFrame, text="延时(ms)：")
        self.labelOperate.place(x=250, y=450, width=60)
        # 延时输入
        self.entryDelay = ttk.Entry(self.rightFrame)
        self.entryDelay.insert(tkinter.END, int(100))
        self.entryDelay.place(x=310, y=450, width=80)
        # 插入宏按钮
        self.buttonInsertMacro = ttk.Button(
            self.rightFrame, text="插入宏", command=self.insert_macro
        )
        self.buttonInsertMacro.place(x=400, y=450, width=80)
        # 导入宏按钮
        self.buttonImportMacro = ttk.Button(
            self.rightFrame, text="导入宏", command=self.import_macro
        )
        self.buttonImportMacro.place(x=10, y=490, width=120)
        # 导出宏按钮
        self.buttonExportMacro = ttk.Button(
            self.rightFrame, text="导出宏", command=self.export_macro
        )
        self.buttonExportMacro.place(x=140, y=490, width=120)
        # 清空宏按钮
        self.buttonClearMacro = ttk.Button(
            self.rightFrame, text="清空宏", command=self.clear_macro
        )
        self.buttonClearMacro.place(x=270, y=490, width=120)
        # 删除宏按钮
        self.buttonDeleteMacro = ttk.Button(
            self.rightFrame, text="删除宏", command=self.delete_macro
        )
        self.buttonDeleteMacro.place(x=400, y=490, width=80)

        # 项目地址标签
        self.labbelProjectAddress = ttk.Label(
            self.rightFrame,
            text="项目地址: https://github.com/ZRe-K/back-end-macro",
            foreground="blue",
        )
        self.labbelProjectAddress.bind(
            "<Button-1>",
            lambda event: webopen("https://github.com/ZRe-K/back-end-macro"),
        )
        self.labbelProjectAddress.place(x=10, y=520, width=490, height=20)

        self.refresh_windows()
        self.init_macro()

    def chose_window(self, event):
        windowsChoseIndex = self.comboboxWindows.current()
        self.target_window_hwnd = self.windows[windowsChoseIndex][0]
        print(
            f"窗口标题: {self.windows[windowsChoseIndex][1]}, 窗口句柄: {hex(self.windows[windowsChoseIndex][0])}"
        )
        self.scrolledtextBox.config(state="normal")
        self.scrolledtextBox.insert(
            tkinter.END,
            f"{func.get_time()}  已切换目标窗口: {self.windows[windowsChoseIndex][1]}({hex(self.windows[windowsChoseIndex][0])})\n",
        )
        if not func.windows_minmize(self.windows[windowsChoseIndex][0]):
            imgTk = func.capture(self.windows[windowsChoseIndex][0])
            self.scrolledtextBox.insert(tkinter.END, f"{func.get_time()}  窗口快照:\n")
            self.scrolledtextBox.image_create(tkinter.END, image=imgTk)
            self.scrolledtextBox.insert(tkinter.END, "\n")
            self.labelRunVar.set("窗口快照已在日志中显示")
            if not hasattr(self.scrolledtextBox, "images"):
                self.scrolledtextBox.images = []
            self.scrolledtextBox.images.append(imgTk)
        else:
            self.scrolledtextBox.insert(
                tkinter.END, f"{func.get_time()}  无法获取窗口快照\n"
            )
            self.labelRunVar.set("无法获取窗口快照")
        self.scrolledtextBox.config(state="disabled")

    def refresh_windows(self):
        self.windows = func.get_open_windows()
        self.windowsText = []
        for hdwn, title in self.windows:
            self.windowsText.append(f"{title} ({hex(hdwn)})")
        self.scrolledtextBox.config(state="normal")
        self.scrolledtextBox.insert(
            tkinter.END,
            f"{func.get_time()}  检测到{len(self.windowsText)}个可见窗口,可在下拉框中查看\n",
        )
        self.scrolledtextBox.config(state="disabled")
        self.comboboxWindows["value"] = self.windowsText
        self.comboboxWindows.set("请选择目标窗口:")
        self.target_window_hwnd = ""

    def macro_start(self):
        if self.target_window_hwnd == "":
            messagebox.showinfo("无目标窗口", "请选择目标窗口")
            return
        self.buttonStart["state"] = "disable"
        self.comboboxWindows["state"] = "disable"
        self.buttonRefreshWindows["state"] = "disable"
        self.buttonImportMacro["state"] = "disable"
        self.init_window_name.focus_set()
        self.buttonStop["state"] = "normal"
        self.scrolledtextBox.config(state="normal")
        self.scrolledtextBox.insert(
            tkinter.END, f"{func.get_time()}  目标窗口: {self.comboboxWindows.get()}\n"
        )
        self.scrolledtextBox.insert(
            tkinter.END, f"{func.get_time()}  任务开始, 将在{self.gapTime}秒后执行\n"
        )
        self.scrolledtextBox.config(state="disabled")
        self.scrolledtextBox.see(tkinter.END)

        self.labelRunVar.set("即将开始宏流程")

        self.macroRunning = True
        self.macroRunID = self.init_window_name.after(
            int((self.gapTime - int(self.gapTime)) * 1000),
            self.gap_time_wait,
            int(self.gapTime),
        )

    def gap_time_wait(self, loopTime):
        if not self.macroRunning:
            return
        if loopTime > 0:
            start = time.perf_counter()
            if not self.macroRunning:
                return
            self.scrolledtextBox.config(state="normal")
            self.scrolledtextBox.insert(
                tkinter.END, f"{func.get_time()}  执行倒计时: {loopTime}秒\n"
            )
            self.scrolledtextBox.config(state="disabled")
            self.scrolledtextBox.see(tkinter.END)

            self.labelRunVar.set(f"倒计时: {loopTime}秒")

            end = time.perf_counter()
            timeMacroWait = int((1 - end + start) * 1000)
            self.macroRunID = self.init_window_name.after(
                timeMacroWait, self.gap_time_wait, loopTime - 1
            )
        else:
            self.labelRunVar.set("宏流程执行中")
            self.timeMacroStart = time.perf_counter()
            if len(self.macros) > 0:
                self.macroRunID = self.init_window_name.after(
                    self.macros[0].delayTime, self.macro_loop, 1
                )
            else:
                self.macroRunID = self.init_window_name.after(0, self.macro_loop, 1)

    def macro_loop(self, step):
        if not self.macroRunning:
            return
        if len(self.macros) > 0:
            macro = self.macros[step - 1]
            if macro.operate == 0:
                self.scrolledtextBox.config(state="normal")
                self.scrolledtextBox.insert(
                    tkinter.END,
                    f"{func.get_time()}  步骤{step}/{len(self.macros)}: {macro.key}按下\n",
                )
                self.scrolledtextBox.config(state="disabled")
                func.key_down(self.target_window_hwnd, macro.key)
            else:
                self.scrolledtextBox.config(state="normal")
                self.scrolledtextBox.insert(
                    tkinter.END,
                    f"{func.get_time()}  步骤{step}/{len(self.macros)}: {macro.key}抬起\n",
                )
                self.scrolledtextBox.config(state="disabled")
                func.key_up(self.target_window_hwnd, macro.key)
            self.scrolledtextBox.see(tkinter.END)
        if step < len(self.macros):
            self.macroRunID = self.init_window_name.after(
                self.macros[step].delayTime, self.macro_loop, step + 1
            )
        else:
            self.timeMacroEnd = time.perf_counter()
            self.timeMacroUse = round(self.timeMacroEnd - self.timeMacroStart, 2)

            self.scrolledtextBox.config(state="normal")
            self.scrolledtextBox.insert(
                tkinter.END,
                f"{func.get_time()}  本轮结束，耗时{self.timeMacroUse:.2f}秒\n",
            )
            timeRemain = (
                self.gapTime - self.timeMacroUse
                if self.gapTime - self.timeMacroUse > 0
                else 0
            )
            self.scrolledtextBox.insert(
                tkinter.END, f"{func.get_time()}  等待{timeRemain:.2f}秒后进入下一轮\n"
            )
            self.scrolledtextBox.config(state="disabled")
            self.scrolledtextBox.see(tkinter.END)

            timeRemain = (
                self.gapTime - self.timeMacroUse
                if self.gapTime - self.timeMacroUse > 0
                else 0
            )
            timeWait = timeRemain - int(timeRemain)
            loopTime = int(timeRemain)

            self.macroRunID = self.init_window_name.after(
                int(timeWait * 1000), self.gap_time_wait, loopTime
            )

    def macro_stop(self):
        self.macroRunning = False
        self.init_window_name.after_cancel(self.macroRunID)

        self.scrolledtextBox.config(state="normal")
        self.scrolledtextBox.insert(
            tkinter.END, f"{func.get_time()}  任务已取消，停止宏执行\n"
        )
        self.scrolledtextBox.config(state="disabled")
        self.scrolledtextBox.see(tkinter.END)

        self.labelRunVar.set("宏流程已停止")

        self.buttonStop["state"] = "disable"
        self.init_window_name.focus_set()
        self.buttonStart["state"] = "normal"
        self.comboboxWindows["state"] = "readonly"
        self.buttonRefreshWindows["state"] = "normal"
        self.buttonImportMacro["state"] = "normal"

    def update_gaptime(self):
        self.gapTime = round(float(self.entryGapTime.get()), 3)
        self.scrolledtextBox.config(state="normal")
        timeText = f"{(self.gapTime):.2f}"
        self.scrolledtextBox.insert(
            tkinter.END, f"{func.get_time()}  总循环间隔已更新为{timeText}秒\n"
        )
        self.scrolledtextBox.config(state="disabled")

    def get_selected_row(self, event):
        selected = self.treeviewMacro.selection()
        if selected:
            index = self.treeviewMacro.index(selected)
            self.macroInsertPos = index + 1

    def insert_macro(self):
        macroType = "键盘"
        key = self.comboboxKey.get()
        operate = self.comboboxOperate.current()
        operateStr = "按下" if operate == 0 else "抬起"
        delayTime = self.entryDelay.get()

        if delayTime.isdigit():
            delayTime = int(delayTime)
            newMacro = func.MACRO(macroType, key, operate, delayTime)
            # 新宏的插入位置
            num = (
                (len(self.macros))
                if self.macroInsertPos == tkinter.END
                else self.macroInsertPos
            ) + 1  # 新插入宏序号
            self.macros.insert(num - 1, newMacro)
            newTreeviewLine = self.treeviewMacro.insert(
                "",
                self.macroInsertPos,
                values=(num, macroType, key, operateStr, delayTime),
            )
            # 序号更新
            if not self.macroInsertPos == tkinter.END:
                children = self.treeviewMacro.get_children()
                for i in range(num, len(self.macros)):
                    item = children[i]
                    self.treeviewMacro.set(item, column="num", value=i + 1)

            # 移动选中到新宏上
            if not self.macroInsertPos == tkinter.END:
                self.treeviewMacro.selection_set(newTreeviewLine)

            self.scrolledtextBox.config(state="normal")
            self.scrolledtextBox.insert(
                tkinter.END,
                f"{func.get_time()}  已新增步骤{num}: {macroType}{key}{operateStr}, 延时{delayTime}ms\n",
            )
            self.scrolledtextBox.config(state="disabled")
            self.labelMacroConfig["text"] = f"当前宏配置: 程序内编辑"
        else:
            self.scrolledtextBox.config(state="normal")
            self.scrolledtextBox.insert(
                tkinter.END,
                f"{func.get_time()}  插入宏失败: 延时必须是大于等于0的整数毫秒\n",
            )
            self.scrolledtextBox.config(state="disabled")

    def delete_macro(self):
        if self.macroInsertPos == tkinter.END:
            self.scrolledtextBox.config(state="normal")
            self.scrolledtextBox.insert(
                tkinter.END, f"{func.get_time()}  删除宏失败: 请先选择一个宏\n"
            )
            self.scrolledtextBox.config(state="disabled")
        else:
            children = self.treeviewMacro.get_children()
            item = children[self.macroInsertPos - 1]
            self.macros.pop(self.macroInsertPos - 1)
            self.treeviewMacro.delete(item)
            for i in range(self.macroInsertPos, len(self.macros) + 1):
                item = children[i]
                self.treeviewMacro.set(item, column="num", value=i)
        self.macroInsertPos = tkinter.END
        self.labelMacroConfig["text"] = f"当前宏配置: 程序内编辑"

    def import_macro(self):
        appPathStr = str(Path(__file__).parent.resolve())
        file_path = filedialog.askopenfilename(
            title="导入宏 json",
            initialdir=os.path.expanduser(appPathStr),
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
        )

        if file_path:
            macros = func.import_macros_json(file_path)
            if not macros:
                self.labelRunVar.set(f"从: {file_path} 加载宏失败,文件错误或宏为空")
            else:
                for item in self.treeviewMacro.get_children():
                    self.treeviewMacro.delete(item)
                self.macros = macros
                num = 1
                for macro in macros:
                    self.treeviewMacro.insert(
                        "",
                        tkinter.END,
                        values=(
                            num,
                            macro.macroType,
                            macro.key,
                            ("按下" if macro.operate == 0 else "抬起"),
                            macro.delayTime,
                        ),
                    )
                    num = num + 1

                config = {
                    "default_macros": file_path,
                }
                with open(
                    os.path.join(appPathStr, "macro_config.json"), "w", encoding="utf-8"
                ) as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)

                self.scrolledtextBox.config(state="normal")
                self.scrolledtextBox.insert(
                    tkinter.END,
                    f"{func.get_time()}  成功从: {file_path} 导入{len(macros)}个宏并设为默认\n",
                )
                self.scrolledtextBox.config(state="disabled")
                self.labelRunVar.set(
                    f"成功从: {file_path} 导入{len(macros)}个宏并设为默认"
                )
                self.labelMacroConfig["text"] = f"当前宏配置: {file_path}"

    def export_macro(self):
        appPathStr = str(Path(__file__).parent.resolve())
        file_path = filedialog.asksaveasfilename(
            title="保存宏 json",
            initialdir=os.path.expanduser(appPathStr),
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            defaultextension=".json",
        )

        if file_path:
            if func.export_macros_json(self.macros, file_path):
                self.scrolledtextBox.config(state="normal")
                self.scrolledtextBox.insert(
                    tkinter.END, f"{func.get_time()}  成功导出宏文件到: {file_path}\n"
                )
                self.scrolledtextBox.config(state="disabled")
                self.labelRunVar.set(f"成功导出宏文件到: {file_path}")
            else:
                messagebox.INFO("错误", "导出宏文件失败")

    def clear_macro(self):
        for item in self.treeviewMacro.get_children():
            self.treeviewMacro.delete(item)
        self.macros.clear()

    def init_macro(self):
        appPathStr = str(Path(__file__).parent.resolve())
        file_path = os.path.join(appPathStr, "macro_config.json")
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            defaultMacrosPath = config.get("default_macros")
            macros = func.import_macros_json(defaultMacrosPath)
            if macros:
                self.macros = macros
                num = 1
                for macro in macros:
                    self.treeviewMacro.insert(
                        "",
                        tkinter.END,
                        values=(
                            num,
                            macro.macroType,
                            macro.key,
                            ("按下" if macro.operate == 0 else "抬起"),
                            macro.delayTime,
                        ),
                    )
                    num = num + 1
                self.labelMacroConfig["text"] = f"当前宏配置: {defaultMacrosPath}"
                return

        self.macros.append(func.MACRO("键盘", "C", 0, 100))
        self.treeviewMacro.insert("", tkinter.END, values=(1, "键盘", "C", "按下", 100))
        self.macros.append(func.MACRO("键盘", "C", 1, 100))
        self.treeviewMacro.insert("", tkinter.END, values=(2, "键盘", "C", "抬起", 100))
        self.macros.append(func.MACRO("键盘", "F", 0, 100))
        self.treeviewMacro.insert("", tkinter.END, values=(3, "键盘", "F", "按下", 100))
        self.macros.append(func.MACRO("键盘", "F", 1, 100))
        self.treeviewMacro.insert("", tkinter.END, values=(4, "键盘", "F", "抬起", 100))
        self.labelMacroConfig["text"] = f"当前宏配置: 程序内编辑"


if __name__ == "__main__":
    root = tkinter.Tk()
    BackEndInput = GUI_USE(root)
    BackEndInput.set_init_window()

    root.mainloop()
