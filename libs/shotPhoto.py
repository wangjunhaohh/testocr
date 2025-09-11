from PIL import ImageGrab
import time

def screenshot():
    # 截取当前屏幕
    img = ImageGrab.grab()
    # 获取当前时间戳
    timestamp = int(time.time())
    # 生成截图文件名
    filename = f"screenshot_{timestamp}.png"
    # 保存截图
    img.save(filename)
    print(f"截图已保存为：{filename}")

# 调用函数进行截图
screenshot()