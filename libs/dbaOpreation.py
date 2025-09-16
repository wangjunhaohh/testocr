import os
import datetime
import time

import cv2
from PIL import Image
import pytesseract
import numpy as np
import subprocess
from libs import orc_chinese
def adb_check():
    os.system(f"adb devices")
def adb_screencap(filename="screen.png",type="time"):
    """
       :param filename: 文件名
       :param type: 截图类型
       :return: 截图名称
    """
    if(type == "time"):
        os.system(f"adb exec-out screencap -p > ../pics/adb/time/{filename}")
    elif(type == "detail"):
        print()
        os.system(f"adb exec-out screencap -p > ../pics/adb/battle/{filename}")
    return filename
def scroll_one_item(screen_w, screen_h, item_ratio=0.19, x_ratio=0.5, duration=300):
    """
    按百分比滑动一条战报高度
    :param screen_w: 屏幕宽度
    :param screen_h: 屏幕高度
    :param item_ratio: 一条战报占屏幕高度的比例（默认0.35）
    :param x_ratio: 横向滑动位置（默认屏幕中间）
    :param duration: 滑动时长(ms)
    """
    x = int(screen_w * x_ratio)

    # 起点放在屏幕的 70%，终点往上滑 item_ratio
    y1 = int(screen_h * item_ratio)
    y2 = int(y1 - screen_h * item_ratio)

    cmd = f"adb shell input swipe {x} {y1} {x} {y2} {duration}"
    print("执行命令:", cmd)
    os.system(cmd)

def adb_tap(percent_x, percent_y):
    output = subprocess.check_output("adb shell wm size", shell=True).decode()
    # 输出类似 "Physical size: 1280x720"
    size_str = output.strip().split(":")[-1].strip()
    screen_height, screen_width = map(int, size_str.split("x"))
    print(f"screen_width: {screen_width}, screen_height: {screen_height}")
    # 计算点击点
    click_x = int(screen_width * percent_x)
    click_y = int(screen_height * percent_y)
    print(f"click_x: {click_x}, click_y: {click_y}")
    # 发送点击事件
    cmd = f"adb shell input tap {click_x} {click_y}"
    subprocess.run(cmd, shell=True)

def extract_timestamp(screenshot_path):
    """
    截取第一条战报的时间戳区域并 OCR
    """
    """
        从战报截图中提取时间戳
        """

    # 打开图片
    img = Image.open(screenshot_path)
    w, h = img.size  # 动态获取分辨率

    # 这里用百分比定义裁剪区域 [x1%, y1%, x2%, y2%]
    x1, y1 = int(w * 0.433), int(h * 0.476)
    x2, y2 = int(w * 0.5365), int(h * 0.509)

    crop_img = img.crop((x1, y1, x2, y2))
    crop_img.save("screen1.png")

    # 转换为灰度图 + 二值化，方便 OCR，本身背景为灰色，灰度值不宜过大
    gray = cv2.cvtColor(np.array(crop_img), cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 90, 255, cv2.THRESH_BINARY)

    # ---------------------debug时间识别------------------------
    # configs = {
    #     "默认": "",
    #     "单行 (--psm 7)": "--psm 7",
    #     "数字限制": r'--psm 7 -c tessedit_char_whitelist=0123456789:/',
    #     "块文本 (--psm 6)": "--psm 6"
    # }
    #
    # processed = Image.fromarray(binary)
    # for name, cfg in configs.items():
    #     text = pytesseract.image_to_string(processed, config=cfg)
    #     print(f"[{name}] -> {repr(text)}")
    # ---------------------debug------------------------

    # OCR 识别
    processed = Image.fromarray(binary)
    #去掉换行
    text = pytesseract.image_to_string(processed, config=r'--psm 7').replace('\n', '')
    return text

# 用于放大图片，太小不好识别
def upscale(img, scale=2):
    w, h = img.size
    return img.resize((w * scale, h * scale), Image.Resampling.LANCZOS)


def main(nowDay):
    last_timestamp = None
    # 1. 点开战报窗口
    adb_tap(0.0721, 0.7463)  # 战报按钮坐标 (需修改)
    time.sleep(0.5)
    img_file = adb_screencap("list.png","time")
    img_file_pre_path = "../pics/adb/time/"
    identifyTimestamp = extract_timestamp(img_file_pre_path + img_file)
    # 反着比较，不想做字符串替换了 传进来的日期为2025/09/15 ，识别的时间戳为2025/09/15 00:34:45
    if nowDay in identifyTimestamp:
        adb_tap(0.4828, 0.3897)
        save_name = f"{identifyTimestamp.replace(':', '').replace('/', '').replace(' ', '')}.png"
        # 太快会导致截图到上一次的界面 测试0.2不行,0.3大部分可以，为确保延迟0.5
        time.sleep(0.5)
        adb_screencap(save_name,"detail")
        print(identifyTimestamp)
    else:
        print("不是当天")
    adb_tap(0.9660, 0.04975)  # 战报按钮坐标 (需修改)
    # while True:
        # Step1: 打开战报窗口
        # adb_tap(0.109, 0.917)   # 战报按钮坐标 (需修改)
        # time.sleep(1)

        # Step2: 点击“同盟”tab
        # adb_tap(500, 200)    # 同盟 tab 坐标 (需修改)
        # time.sleep(1)
        #
        # # Step3: 截图战报列表
        # img_file = adb_screencap("list.png")
        #
        # # Step4: OCR 第一条战报时间戳
        # ts = extract_timestamp(img_file, region=(1350, 300, 1650, 340))
        #
        # if ts and ts != last_timestamp:
        #     print(f"发现新战报: {ts}")
        #
        #     # Step5: 点击第一条战报
        #     adb_tap(900, 350)   # 第一条战报位置 (需修改)
        #     time.sleep(2)       # 等待详情页加载
        #
        #     # Step6: 截图详情页
        #     save_name = f"battle_{ts.replace(':','-').replace(' ','_')}.png"
        #     adb_screencap(save_name)
        #     print(f"保存详情截图: {save_name}")
        #
        #     # Step7: 关闭详情页
        #     adb_tap(1850, 100)  # 详情页右上角X (需修改)
        #     time.sleep(1)
        #
        #     # Step8: 关闭战报窗口
        #     adb_tap(1850, 100)  # 战报窗口右上角X (需修改)
        #     time.sleep(1)
        #
        #     # Step9: 更新时间戳
        #     last_timestamp = ts
        #
        # else:
        #     print("没有新战报，关闭窗口等待...")
        #     adb_tap(1850, 100)  # 关闭战报窗口
        #     time.sleep(5)

if __name__ == "__main__":
    # adb_check()
    # today = datetime.date.today()
    # # 计算前一天日期
    # yesterday = today - datetime.timedelta(days=1)
    # yesterday_str = yesterday.strftime("%Y/%m/%d")
    # print("前一天日期：", yesterday_str)
    # main(yesterday_str)
    output = subprocess.check_output("adb shell wm size", shell=True).decode()
    # 输出类似 "Physical size: 1280x720"
    size_str = output.strip().split(":")[-1].strip()
    screen_height, screen_width = map(int, size_str.split("x"))
    print(screen_width, screen_height)
    scroll_one_item(screen_width,screen_height)
    # 检测adb是否连接到模拟器
    # adb_screencap()