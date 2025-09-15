import os
import time
import cv2
from PIL import Image
import pytesseract
import numpy as np
import subprocess
from libs import orc_chinese
def adb_screencap(filename="screen.png"):
    # os.system(f"adb devices")
    os.system(f"adb exec-out screencap -p > ../pics/adb/{filename}")
    return filename

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
    x1, y1 = int(w * 0.419), int(h * 0.476)
    x2, y2 = int(w * 0.545), int(h * 0.509)

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
    text = pytesseract.image_to_string(processed, config=r'--psm 7')

    return text

# 用于放大图片，太小不好识别
def upscale(img, scale=2):
    w, h = img.size
    return img.resize((w * scale, h * scale), Image.Resampling.LANCZOS)

def main():
    last_timestamp = None
    # adb_tap(0.0885, 0.7426)  # 战报按钮坐标 (需修改)
    # 1. 点开战报窗口
    img_file = adb_screencap("list.png")
    img_file_pre_path = "../pics/adb/"
    ts = extract_timestamp(img_file_pre_path + img_file)

    print(ts)
    # adb_tap(0.95104, 0.0463)  # 战报按钮坐标 (需修改)
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
    main()
    # adb_screencap()