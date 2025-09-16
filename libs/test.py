"""
精确滚动（带视觉反馈）示例
依赖: opencv-python, pillow, numpy
adb must be available in PATH.

思路：
- 传入参考区域 ref_box_ratio = (x1,y1,x2,y2) (百分比)
- 传入目标滑动像素 item_pixels 或 item_ratio
- 截图 -> 提取模板 -> swipe -> 再截图 -> 模板匹配 -> 计算实际移动 -> 若有误差则微调
"""

import os
import subprocess
import time
from PIL import Image
import numpy as np
import cv2

# ---------- 基础工具 ----------
def adb_screencap_to_pil(filename="screen.png"):
    """用 adb exec-out 截屏并保存到本地文件，然后返回 PIL.Image"""
    # 注意：在某些环境下 exec-out 的重定向在 windows 需特殊处理，若失败可以改为 /sdcard/ 路径方式
    cmd = f"adb exec-out screencap -p > {filename}"
    subprocess.run(cmd, shell=True, check=True)
    return Image.open(filename)

def get_screen_size():
    out = subprocess.check_output("adb shell wm size", shell=True).decode().strip()
    # 格式: "Physical size: 1280x720"
    if ":" in out:
        out = out.split(":")[-1].strip()
    w, h = map(int, out.split("x"))
    return w, h

def crop_by_ratio(pil_img, box_ratio):
    """box_ratio = (x1,y1,x2,y2) 百分比 -> 返回 PIL.Image"""
    w, h = pil_img.size
    x1 = int(w * box_ratio[0]); y1 = int(h * box_ratio[1])
    x2 = int(w * box_ratio[2]); y2 = int(h * box_ratio[3])
    return pil_img.crop((x1, y1, x2, y2)), (x1, y1, x2, y2)

# ---------- 模板匹配 ----------
def match_template(big_img_pil, template_pil):
    """
    在 big_img 中匹配 template，返回 (best_x, best_y, max_val)
    坐标为 big_img 的像素坐标（左上角）
    """
    big = cv2.cvtColor(np.array(big_img_pil), cv2.COLOR_RGB2GRAY)
    tpl = cv2.cvtColor(np.array(template_pil), cv2.COLOR_RGB2GRAY)

    # 若模板尺寸过小，尝试放大以提高匹配稳定性
    bh, bw = big.shape[:2]
    th, tw = tpl.shape[:2]
    if th < 30 or tw < 30:
        scale = 3
        tpl = cv2.resize(tpl, (tw*scale, th*scale), interpolation=cv2.INTER_CUBIC)

    res = cv2.matchTemplate(big, tpl, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    return max_loc[0], max_loc[1], max_val

# ---------- 滑动函数（直接像素） ----------
def adb_swipe_pixels(x, y1, x2, y2, duration_ms=300):
    cmd = f"adb shell input swipe {x} {y1} {x2} {y2} {duration_ms}"
    subprocess.run(cmd, shell=True)

# ---------- 反馈式精确滑动主函数 ----------
def precise_scroll_one_item(ref_box_ratio,
                            item_pixels=None,
                            item_ratio=None,
                            start_x_ratio=0.5,
                            start_y_ratio=0.7,
                            duration_ms=350,
                            max_correction_attempts=3,
                            match_threshold=0.70):
    """
    参数:
      ref_box_ratio: (x1,y1,x2,y2) - 用百分比指明参考模板区域（列表页第一条中一个稳定的patch）
      item_pixels: 期望滑动像素（优先），如果为 None 则用 item_ratio * screen_h
      item_ratio: 期望滑动比例（screen_h 的比例），当 item_pixels 为 None 时启用
      start_x_ratio, start_y_ratio: swipe 起点的比例（屏幕中间偏下通常稳定）
      duration_ms: 默认 swipe duration
      max_correction_attempts: 最大修正次数
      match_threshold: 模板匹配置信度阈值（0-1）
    返回:
      actual_shift_pixels (int)
    """
    # 1. 截图并提取模板
    screen_before = adb_screencap_to_pil("scr_before.png")
    w, h = screen_before.size
    template_img, (tx1, ty1, tx2, ty2) = crop_by_ratio(screen_before, ref_box_ratio)
    print(tx1, ty1, tx2, ty2)
    #
    # 2. 计算目标滑动像素
    if item_pixels is None:
        if item_ratio is None:
            raise ValueError("必须提供 item_pixels 或 item_ratio 之一")
        item_pixels = int(h * item_ratio)

    # 3. 计算 swipe 的起点和终点（像素）
    sx = int(w * start_x_ratio)
    sy = int(h * start_y_ratio)
    ex = sx
    ey = sy - item_pixels

    print(f"[info] screen={w}x{h}, template_box_pixel=({tx1},{ty1},{tx2},{ty2}), "
          f"target_item_pixels={item_pixels}, swipe {sx},{sy} -> {ex},{ey} dur={duration_ms}ms")
    #
    # # 4. 执行初次 swipe
    # adb_swipe_pixels(sx, sy, ex, ey, duration_ms)
    # time.sleep(0.30 + duration_ms/1000.0)  # 等待动画完成
    #
    # # 5. 截图并匹配模板位置
    # screen_after = adb_screencap_to_pil("scr_after.png")
    # # 在 before 图里模板原始位置中心点
    # ref_before_cx = tx1
    # ref_before_cy = ty1
    #
    # new_x, new_y, score = match_template(screen_after, template_img)
    # print(f"[debug] match score={score:.3f}, new_loc=({new_x},{new_y})")
    #
    # if score < match_threshold:
    #     print("[warn] 匹配置信度低，尝试更宽容的策略（小步滑动直到能匹配或者到尝试上限）")
    #     # 小步滑动寻找模板（防止完全错位）
    #     found = False
    #     step_pixels = max(8, int(item_pixels * 0.15))
    #     attempts = 0
    #     while attempts < 6:
    #         adb_swipe_pixels(sx, sy, sx, sy - step_pixels, int(duration_ms/2))
    #         time.sleep(0.25)
    #         screen_after = adb_screencap_to_pil(f"scr_after_step_{attempts}.png")
    #         new_x, new_y, score = match_template(screen_after, template_img)
    #         print(f"  step {attempts} score={score:.3f}")
    #         if score >= match_threshold:
    #             found = True
    #             break
    #         attempts += 1
    #     if not found:
    #         print("[error] 未能找到模板（匹配失败），返回 0")
    #         return 0
    #
    # # 6. 计算实际移动像素（垂直方向）
    # # 注意：我们用了模板在 before 的 (tx1,ty1) 作为参照点
    # actual_shift = ref_before_cy - new_y
    # print(f"[info] actual_shift = {actual_shift} px")
    #
    # # 7. 如果误差超过阈值，做修正
    # error = item_pixels - actual_shift
    # corrections = 0
    # while abs(error) > 6 and corrections < max_correction_attempts:
    #     # 修正需移动的像素 = error （正表示还要向上移动 error 像素）
    #     # 这里做小步滑动以避免再次过冲，scale duration by proportion
    #     corr_px = int(error)
    #     corr_px = max(-item_pixels, min(item_pixels, corr_px))  # 限制范围
    #     # 将 corr_px 转换为 swipe 参数（向上滑：sy -> sy - corr_px）
    #     corr_start_y = sy
    #     corr_end_y = corr_start_y - corr_px
    #     dur = max(120, int(duration_ms * (abs(corr_px) / max(1, item_pixels))))
    #     print(f"[info] correction {corrections}: corr_px={corr_px}, swipe {sx},{corr_start_y} -> {sx},{corr_end_y} dur={dur}ms")
    #     adb_swipe_pixels(sx, corr_start_y, sx, corr_end_y, dur)
    #     time.sleep(0.25 + dur/1000.0)
    #
    #     screen_after = adb_screencap_to_pil(f"scr_after_corr_{corrections}.png")
    #     new_x, new_y, score = match_template(screen_after, template_img)
    #     print(f"  corr match score={score:.3f}, loc=({new_x},{new_y})")
    #     actual_shift = ref_before_cy - new_y
    #     error = item_pixels - actual_shift
    #     print(f"  after corr actual_shift={actual_shift}, error={error}")
    #     corrections += 1
    #
    # print(f"[done] final actual_shift = {actual_shift} px after {corrections} corrections")
    return 1

# ---------- 示例用法 ----------
if __name__ == "__main__":
    # 参考框（示例，需你根据列表页确定最稳定的局部 patch）
    # 推荐把模板放在第一条条目的左侧头像或某个固定元素
    # 这里用百分比，示例值（你需要微调到实际参考patch）
    ref_box_ratio = (0.06, 0.18, 0.18, 0.36)  # (x1,y1,x2,y2) 百分比，示例

    # 如果你已经知道 item height 的像素（某一分辨率），传 item_pixels。
    # 若不知道，用 item_ratio（item_pixels / screen_h）
    item_ratio = None
    item_pixels = 422  # 若仍想用像素，可传入；若跨分辨率建议使用 item_ratio

    # 若跨分辨率请改成 item_ratio = 422 / 1206  # 之前测量值
    # item_ratio = 422/1206
    item_ratio = None

    # 运行一次尝试（脚本会截屏并在当前目录写入 scr_before.png scr_after.png 等）
    final_shift = precise_scroll_one_item(ref_box_ratio,
                                          item_pixels=item_pixels,
                                          item_ratio=item_ratio,
                                          start_x_ratio=0.5,
                                          start_y_ratio=0.7,
                                          duration_ms=380,
                                          max_correction_attempts=4,
                                          match_threshold=0.65)
    print("实际移动:", final_shift)
