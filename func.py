from ctypes import windll, byref, c_ubyte
from ctypes.wintypes import HWND, RECT
from datetime import datetime
from PIL import Image, ImageTk
import win32gui
import win32con
import string
import json
import os


class MACRO:
    def __init__(self, macroType, key, operate, delayTime):
        self.macroType = macroType
        self.key = key
        self.operate = operate
        self.delayTime = delayTime

    def to_dict(self):
        return {
            "macroType": self.macroType,
            "key": self.key,
            "operate": self.operate,
            "delayTime": self.delayTime,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["macroType"], data["key"], data["operate"], data["delayTime"])

    def __repr__(self):
        return (
            f"macro: ({self.macroType}, {self.key}, {self.operate}, {self.delayTime})"
        )


class MacroEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, MACRO):
            return obj.to_dict()
        return super().default(obj)


PostMessageW = windll.user32.PostMessageW
MapVirtualKeyW = windll.user32.MapVirtualKeyW
VkKeyScanA = windll.user32.VkKeyScanA

WM_KEYDOWN = 0x100
WM_KEYUP = 0x101

VkCode = {
    "back": 0x08,
    "Backspace": 0x08,
    "Tab": 0x09,
    "return": 0x0D,
    "Enter": 0x0D,
    "shift": 0x10,
    "control": 0x11,
    "menu": 0x12,
    "pause": 0x13,
    "capital": 0x14,
    "escape": 0x1B,
    "Esc": 0x1B,
    "Space": 0x20,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "print": 0x2A,
    "snapshot": 0x2C,
    "insert": 0x2D,
    "delete": 0x2E,
    "lwin": 0x5B,
    "rwin": 0x5C,
    "numpad0": 0x60,
    "numpad1": 0x61,
    "numpad2": 0x62,
    "numpad3": 0x63,
    "numpad4": 0x64,
    "numpad5": 0x65,
    "numpad6": 0x66,
    "numpad7": 0x67,
    "numpad8": 0x68,
    "numpad9": 0x69,
    "multiply": 0x6A,
    "add": 0x6B,
    "separator": 0x6C,
    "subtract": 0x6D,
    "decimal": 0x6E,
    "divide": 0x6F,
    "F1": 0x70,
    "F2": 0x71,
    "F3": 0x72,
    "F4": 0x73,
    "F5": 0x74,
    "F6": 0x75,
    "F7": 0x76,
    "F8": 0x77,
    "F9": 0x78,
    "F10": 0x79,
    "F11": 0x7A,
    "F12": 0x7B,
    "numlock": 0x90,
    "scroll": 0x91,
    "lshift": 0xA0,
    "Left Shift": 0xA0,
    "rshift": 0xA1,
    "lcontrol": 0xA2,
    "Left Control": 0xA2,
    "rcontrol": 0xA3,
    "lmenu": 0xA4,
    "rmenu": 0xA5,
    "Caps Lock": 0x14,
}


KeyCode = (
    "Esc",
    "Tab",
    "Enter",
    "Space",
    "Backspace",
    "Left Shift",
    "Left Control",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
)


def get_open_windows():
    windows = []

    def callback(hwnd, extra):
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                windows.append((hwnd, title))

    win32gui.EnumWindows(callback, None)
    return windows


def get_virtual_keycode(key: str):
    if len(key) == 1 and key in string.printable:
        return VkKeyScanA(ord(key)) & 0xFF
    else:
        return VkCode[key]


def key_down(handle: HWND, key: str):
    vk_code = get_virtual_keycode(key)
    scan_code = MapVirtualKeyW(vk_code, 0)
    wparam = vk_code
    lparam = (scan_code << 16) | 1
    PostMessageW(handle, WM_KEYDOWN, wparam, lparam)


def key_up(handle: HWND, key: str):
    vk_code = get_virtual_keycode(key)
    scan_code = MapVirtualKeyW(vk_code, 0)
    wparam = vk_code
    lparam = (scan_code << 16) | 0xC0000001
    PostMessageW(handle, WM_KEYUP, wparam, lparam)


def windows_minmize(handle: HWND):
    return win32gui.IsIconic(handle)


def capture(handle: HWND):
    r = RECT()
    windll.user32.GetClientRect(handle, byref(r))
    width, height = r.right, r.bottom

    dc = windll.user32.GetDC(handle)
    cdc = windll.gdi32.CreateCompatibleDC(dc)
    bitmap = windll.gdi32.CreateCompatibleBitmap(dc, width, height)
    windll.gdi32.SelectObject(cdc, bitmap)
    windll.gdi32.BitBlt(cdc, 0, 0, width, height, dc, 0, 0, win32con.SRCCOPY)

    total_bytes = width * height * 4
    buffer = bytearray(total_bytes)
    byte_array = c_ubyte * total_bytes
    windll.gdi32.GetBitmapBits(bitmap, total_bytes, byte_array.from_buffer(buffer))
    windll.gdi32.DeleteObject(bitmap)
    windll.gdi32.DeleteObject(cdc)
    windll.user32.ReleaseDC(handle, dc)

    img_temp = Image.frombuffer("RGBA", (width, height), buffer, "raw", "RGBA", 0, 1)
    r, g, b, a = img_temp.split()
    img = Image.merge("RGBA", (b, g, r, a))
    targetWidth = 250
    targetHeight = 250
    ratio = 1.0
    if width > targetWidth:
        ration = targetWidth / width
    if height > targetHeight:
        ratio = min(ratio, targetHeight / height)
    newWidth = int(width * ratio)
    newHeight = int(height * ratio)
    img = img.resize((newWidth, newHeight))
    imgTk = ImageTk.PhotoImage(img)
    return imgTk


def get_time():
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


def export_macros_json(macros, path):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(macros, f, cls=MacroEncoder, ensure_ascii=False, indent=4)
    except Exception as e:
        return False
    return True


def validate_macro_data(data):
    required_fields = ["macroType", "key", "operate", "delayTime"]

    if not isinstance(data, list):
        return False, "数据格式错误：根节点应为数组"

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            return False, f"第{i}个宏数据格式错误：应为对象"

        for field in required_fields:
            if field not in item:
                return False, f"第{i}个宏缺少必需字段: {field}"

        if not isinstance(item["macroType"], str):
            return False, f"第{i}个宏的macroType应为字符串"
        if not isinstance(item["key"], str):
            return False, f"第{i}个宏的key应为字符串"
        if not isinstance(item["operate"], int):
            return False, f"第{i}个宏的operate应为数字"
        if not isinstance(item["delayTime"], (int, float)):
            return False, f"第{i}个宏的delayTime应为数字"

    return True, "数据正确"


def import_macros_json(path):
    if not os.path.exists(path):
        print(f"文件 {path} 不存在")
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        is_valid, message = validate_macro_data(data)
        if not is_valid:
            print(f"数据验证失败: {message}")
            return []

        macros = [MACRO.from_dict(item) for item in data]
        print(f"从 {path} 加载了 {len(macros)} 个宏")
        return macros

    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return []
    except Exception as e:
        print(f"加载失败: {e}")
        return []
