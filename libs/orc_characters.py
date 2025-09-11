from pathlib import Path

import cv2
import numpy as np
import yaml
from Levenshtein import distance as levenshtein_distance
from matplotlib.colors import rgb_to_hsv
from sklearn.cluster import KMeans
from PIL import Image
import os

class OCRDictionaryCorrector:
    def __init__(self, word_list, err_corrections_dic):
        self.word_set = set(word_list)
        self.usual_dictionary = err_corrections_dic
    def find_closest_match(self, ocr_text, max_edit_distance=2):
        min_distance = float('inf')
        best_match = None
        if ocr_text in self.usual_dictionary.keys():
            return (self.usual_dictionary[ocr_text], False), 0.0
        
        for word in self.word_set:
            if abs(len(word) - len(ocr_text)) > max_edit_distance:
                return ((ocr_text, word), True), max_edit_distance
            ed = levenshtein_distance(ocr_text, word)
            if ed <= max_edit_distance and ed < min_distance:
                min_distance = ed
                best_match = word
            else:
                return ((ocr_text, word), True), ed
        return (best_match, False), min_distance

class ColorBasedFactionClassifier:
    """基于颜色识别阵营的分类器"""
    def __init__(self):
        # 预定义阵营颜色特征（BGR格式）
        self.faction_colors = {
            "魏": (200, 180, 120),     # 蓝色调
            "蜀": (90, 220, 160),     # 绿色调
            "吴": (90, 90, 180),      # 红色调
            "群": (180, 180, 180),   # 灰色调
            "晋": (180, 180, 90),     # 特殊青色
            "汉": (200, 120, 180)     # 紫色
        }
    
    def identify_faction_by_color(self, image, region=(11,2,38,38), debug=False, debug_path="debug"):
        """
        通过颜色分析识别阵营
        :param image: 输入图像
        :param region: 可选，指定图像区域(x, y, w, h)
        :param debug: 是否调试模式（显示区域）
        :param debug_path: 调试模式下保存区域的路径
        :return: (阵营名称, 置信度)
        """
        if region:
            x, y, w, h = region
            image_roi = image[y:y+h, x:x+w].copy()
        else:
            image_roi = image.copy()

        # 可视化区域
        if debug:
            print("----------Debug----------")
            # 创建矩形标记用于可视化
            vis_img = image.copy()
            cv2.rectangle(vis_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            if debug_path:
                # 保存完整标记图像
                cv2.imwrite(debug_path + "\\_marked.jpg", vis_img)
                # 保存纯区域图像
                cv2.imwrite(debug_path + "\\_region.jpg", image_roi)

        
        # 提取非黑色像素
        non_black_pixels = []
        height, width, _ = image_roi.shape
        
        for y in range(height):
            for x in range(width):
                b, g, r = image_roi[y, x]
                # 排除接近黑色的像素 (RGB值均小于50视为背景)
                if r > 100 or g > 100 or b > 100:
                    non_black_pixels.append([r, g, b])
        
        if not non_black_pixels:
            return "未知", 0.0
        
        # 聚类分析找到主要颜色
        kmeans = KMeans(n_clusters=2, random_state=0)
        kmeans.fit(non_black_pixels)
        
        # 获取主要颜色
        dominant_colors = kmeans.cluster_centers_.astype(int)
        
        # 匹配阵营颜色
        best_match = "未知"
        min_distance = float('inf')
        color_matches = []
        
        for color_name, ref_color in self.faction_colors.items():
            ref_b, ref_g, ref_r = ref_color
            ref_rgb = np.array([[ref_r, ref_g, ref_b]])
            
            for dom_color in dominant_colors:
                # 转换为HSV空间比较色相（忽略明度和饱和度）
                dom_hsv = rgb_to_hsv(dom_color.reshape(1, 1, 3) / 255.0)
                ref_hsv = rgb_to_hsv(ref_rgb.reshape(1, 1, 3) / 255.0)
                
                # 主要比较色相差异
                hue_distance = np.abs(dom_hsv[0, 0, 0] - ref_hsv[0, 0, 0])
                
                # 调整角度差异（色相是圆形的）
                if hue_distance > 0.5:
                    hue_distance = 1 - hue_distance
                
                # 次要比较饱和度
                sat_distance = np.abs(dom_hsv[0, 0, 1] - ref_hsv[0, 0, 1]) * 0.3
                
                # 亮度差异权重较低
                val_distance = np.abs(dom_hsv[0, 0, 2] - ref_hsv[0, 0, 2]) * 0.1
                
                total_distance = hue_distance + sat_distance + val_distance
                color_matches.append((color_name, total_distance))
                
                if total_distance < min_distance:
                    min_distance = total_distance
                    best_match = color_name
        
        # 计算置信度（基于距离值）
        confidence = max(0, 1.0 - min_distance * 2)
        return best_match, confidence

def preprocess_image(image, region=(60,6,131,33)):
    """
    平衡颜色处理的图像预处理
    """
    if region:
        x, y, w, h = region
        image_roi = image[y:y+h, x:x+w].copy()
    else:
        image_roi = image.copy()

    # 1. 转换到Lab色彩空间处理亮度通道
    lab = cv2.cvtColor(image_roi, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # 2. CLAHE对比度限制直方图均衡化
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    
    # 3. 平衡颜色通道
    # 分别处理每个通道
    clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(8, 8))
    b = clahe.apply(b)
    a = clahe.apply(a)
    
    # 4. 合并通道并转换回BGR
    processed_lab = cv2.merge([l, a, b])
    processed_bgr = cv2.cvtColor(processed_lab, cv2.COLOR_LAB2BGR)
    
    # 5. 转换为灰度并进行阈值处理
    gray = cv2.cvtColor(processed_bgr, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_img = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)

    return processed_img

def recognize_faction_hero(
    image,  # 修改：直接传入PIL Image对象
    character_list,       # 完整的角色字典（格式："阵营-角色名"）
    err_corrections_dic = {},
    debug=False,
    reader=None,
    min_confidence=0.2,
    use_gpu=True
):
    """
    增强版阵营武将识别，结合颜色识别阵营和OCR识别武将，然后与完整角色字典匹配
    :param image: PIL Image对象
    :param character_list: 完整的角色字典（格式："阵营-角色名"）
    :param min_confidence: 最低置信度阈值
    :param use_gpu: 是否使用GPU
    :param model_dir: 模型存储目录
    :return: (匹配的角色全名, 置信度)
    """
    
    # 从完整角色字典中提取武将名列表（用于OCR校正）
    hero_dict = [name.split("-")[1] for name in character_list if "-" in name]
    
    # 初始化武将校正器
    hero_corrector = OCRDictionaryCorrector(hero_dict, err_corrections_dic)
    
    # 初始化角色全名校正器
    character_corrector = OCRDictionaryCorrector(character_list, err_corrections_dic)
    
    # 初始化颜色识别器
    color_classifier = ColorBasedFactionClassifier()
    
    # 修改：转换PIL Image为OpenCV格式
    img_array = np.array(image)
    if img_array.size == 0:
        raise ValueError("传入的图像数据为空")
    
    # 修改：颜色空间转换 (RGB->BGR)
    if img_array.ndim == 3 and img_array.shape[2] == 3:
        original_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    elif img_array.ndim == 3 and img_array.shape[2] == 4:
        original_img = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
    else:
        # 处理灰度图或异常情况
        original_img = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
    
    # 图像预处理
    processed_img = preprocess_image(original_img)
    
    # OCR识别（仅用于武将识别）
    results = reader.readtext(
        processed_img,
        detail=1,
        paragraph=False,
        text_threshold=0.15,  # 降低阈值提高敏感度
        contrast_ths=0.02,    # 降低对比度阈值
        width_ths=0.5,        # 放宽宽度阈值
        batch_size=1,
        decoder='beamsearch',
        min_size=3,           # 允许更小的文本
        rotation_info=[0, 5, -5]  # 尝试轻微旋转
    )
    # 全文本合并（按位置排序拼接）
    text_items = []

    hero_candidates = []
    for item in results:
        if len(item) < 3: continue
        bbox, text, prob = item[:3]
        x_min = min(point[0] for point in bbox)  # 左上角X坐标
        text_items.append((x_min, text.strip(), float(prob)))

    # 按X坐标排序后拼接完整字符串
    text_items.sort(key=lambda x: x[0])
    full_text = ''.join([item[1] for item in text_items])
    avg_confidence = sum(item[2] for item in text_items) / len(text_items) if text_items else 0
    # 词典匹配与校正
    if full_text in hero_dict:
        hero_candidates.append((full_text, avg_confidence))
    else:
        corrected, distance = hero_corrector.find_closest_match(full_text)
        hero_candidates.append((corrected[0], avg_confidence))

    # 颜色识别阵营
    faction, color_conf = color_classifier.identify_faction_by_color(original_img)
    faction_result = (faction, max(0.5, color_conf))  # 颜色识别的置信度最低给0.5

    zhenyin,pipeidu = faction_result
    if zhenyin == "未知":
        return ("空-空",False),1.0
    # 处理武将结果
    hero_result = ("", 0.0)
    if hero_candidates:
        hero_candidates.sort(key=lambda x: x[1], reverse=True)
        hero_result = hero_candidates[0]
    
    # 组合阵营和武将名

    if hero_result[0]:
        combined_name = f"{faction}-{hero_result[0]}" if len(str(hero_result[0])) < 5 else f"{faction}-{hero_result[0][0]}"
    else: ""
    combined_confidence = min(faction_result[1], hero_result[1]) if hero_result[0] else faction_result[1]
    
    # 与完整角色字典匹配
    character_match = ("", 0.0)
    if combined_name:
        # 检查是否直接匹配
        if combined_name in character_list:            
            character_match = ((combined_name, False), combined_confidence)
        else:
            # 使用编辑距离寻找最接近的匹配
            corrected, ed = character_corrector.find_closest_match(combined_name)
            if corrected and ed <= 2:  # 允许最大编辑距离为2
                # 根据编辑距离调整置信度
                adjusted_confidence = max(0, combined_confidence * (1 - ed * 0.2))
                character_match = (corrected, adjusted_confidence)
            else:
                character_match = (corrected, combined_confidence)

    return character_match  

# 使用示例
if __name__ == "__main__":
    import loader
    # 从gameData.json加载完整角色字典
    # 这里简化表示，实际应从JSON文件加载
    character_list, tactics_list =  loader.load_dict("../data/gameData.json")

    # 测试图像路径
    image_path = r"../output/img_1.png"
    # image_path = r"../debug/character_2.jpg"

    img = Image.open (image_path)

    import easyocr
    model_path = Path('../models')
    model_path.mkdir(parents=True, exist_ok=True)
    reader1 = easyocr.Reader(
        lang_list=['ch_sim', 'en'],
        gpu=True,
        model_storage_directory=str(model_path),
        download_enabled=False,
        recog_network='zh_sim_g2')

    # 执行识别
    # character, confidence = recognize_faction_hero(
    #     image=img,
    #     character_list=character_list,
    #     min_confidence=0.2,   # 更低的置信度阈值
    #     use_gpu=True,
    #     orc_reader=reader
    #
    # )
    character, confidence = recognize_faction_hero(
        image=img,
        character_list=character_list,
        err_corrections_dic={},
        min_confidence=0.2,  # 更低的置信度阈值
        reader=reader1,
        use_gpu=True
    )
    print(character, confidence  )
    # 结果输出
    print("\n最终识别结果:")
    print("-" * 40)
    print(f"{'角色全名':<12} | {'置信度':<8} | {'字典匹配'}")
    print("-" * 40)
    character_name, flag = character
    # 角色结果
    match = "✓" if character_name in character_list else "✗" if character_name else " "
    print(f"{character_name:<12} | {confidence:.4f}   | {match}")