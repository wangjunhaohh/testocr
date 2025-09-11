import cv2
import numpy as np
from pathlib import Path
from Levenshtein import distance as levenshtein_distance
import os


class OCRDictionaryCorrector:
    def __init__(self, word_list, err_corrections_dic):
        """
        基于词典的OCR结果校正器（增强容错机制）
        :param word_list: 预定义词典列表
        """
        self.word_set = set(word_list)
        self.usual_dictionary = err_corrections_dic

        # 构建前缀树加速匹配
        self.trie = {}
        for word in word_list:
            node = self.trie
            for char in word:
                node = node.setdefault(char, {})
            node['#'] = True
    
    def correct(self, ocr_text, max_edit_distance=2, user_confirmation_threshold=2):
        """
        校正OCR识别文本（增强容错能力）
        :param ocr_text: OCR原始识别文本
        :param max_edit_distance: 最大允许编辑距离
        :return: 校正后的文本
        """
        # 1. 精确匹配
        if ocr_text in self.word_set:
            return ocr_text, False
        
        if ocr_text in self.usual_dictionary.keys():
            return self.usual_dictionary[ocr_text], False
        
        # 2. 前缀树匹配（部分匹配）
        node = self.trie
        matched = ""
        for char in ocr_text:
            if char in node:
                matched += char
                node = node[char]
            else:
                break
        if '#' in node and len(matched) > 1:
            return matched, False
        
        # 3. 编辑距离模糊匹配
        candidates = []
        for word in self.word_set:
            if abs(len(word) - len(ocr_text)) > max_edit_distance:
                continue
            ed = levenshtein_distance(ocr_text, word)
            if ed <= max_edit_distance:
                candidates.append((word, ed))
        
        if candidates:
            # 返回编辑距离最小的词
            best_word, min_ed = min(candidates, key=lambda x: x[1])
            if min_ed <= user_confirmation_threshold:
                return best_word, False
            # 编辑距离超过阈值需要用户确认
            return (ocr_text, best_word), True
        
        # 4. 长度相似度匹配（容错机制）
        if not candidates:
            # 选择词典中长度最接近的词
            len_diff = {w: abs(len(w)-len(ocr_text)) for w in self.word_set}
            min_diff = min(len_diff.values())
            close_words = [w for w, d in len_diff.items() if d == min_diff]        
            # 在长度接近的词中选择编辑距离最小的
            if close_words:
                best_word = min(close_words, key=lambda w: levenshtein_distance(ocr_text, w))
                dist = levenshtein_distance(ocr_text, best_word)
                if dist <= user_confirmation_threshold:
                    return best_word, False
                # 编辑距离超过阈值需要用户确认
                return (ocr_text, best_word), True
        
        # 未找到任何匹配项
        return ocr_text, False

def preprocess_image(image):
    """
    优化版图像预处理（适合小尺寸文本）
    包含图像保存用于调试
    """
    # 原始图像备份
    original = image.copy()
    
    # 1. 转换为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 2. 对比度增强（弱化处理强度）
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(4, 4))
    enhanced = clahe.apply(gray)
    
    # 3. Otsu全局阈值二值化
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 4. 转换为RGB三通道
    processed = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
    
    return processed

def recognize_chinese_text(
    image,  # 修改：直接传入PIL Image对象
    dictionary=None, 
    reader=None,
    err_corrections_dic=None
):
    """
    增强版OCR识别（优化小尺寸文本处理）
    :param image: PIL Image对象
    :param dictionary: 校正词典
    :param use_gpu: 是否使用GPU
    :param model_dir: 模型存储目录
    :return: 识别结果列表[(文本, 置信度)]
    """

    # 初始化校正器
    corrector = OCRDictionaryCorrector(dictionary, err_corrections_dic)

    # 修改：转换PIL Image为OpenCV格式
    img = np.array(image)
    if img.size == 0:
        raise ValueError("传入的图像数据为空")
    
    # 修改：颜色空间转换 (RGB->BGR)
    if img.ndim == 3 and img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    elif img.ndim == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    
    # 获取图像信息
    h, w = img.shape[:2]
    c = 3 if img.ndim == 3 else 1
    
    # 图像预处理（包含调试输出）
    processed_img = preprocess_image(img)
    
    # 优化识别参数（针对小尺寸文本）
    results = reader.readtext(
        processed_img,
        detail=1,
        paragraph=False,
        text_threshold=0.2,        # 降低文本阈值
        contrast_ths=0.05,         # 进一步放宽对比度阈值
        width_ths=0.3,             # 收紧文本框合并
        batch_size=1,              # 小图使用单批次
        decoder='beamsearch',      # 更精准的解码器
        min_size=5,                # 最小文本尺寸
        rotation_info=None         # 禁用旋转检测（小图不需要）
    )
    high_conf_results = []
    best_result = None
    max_prob = 0.0
    
    for i, item in enumerate(results):
        if len(item) >= 3:
            bbox, text, prob = item[:3]
            original_text = text.strip()
            
            # 始终记录最高置信度结果
            if prob > max_prob:
                max_prob = prob
                best_result = (original_text, prob, bbox)
            
            # 收集所有高置信度文本(>=0.2)
            if prob >= 0.2:
                high_conf_results.append({
                    'text': original_text,
                    'prob': prob,
                    'bbox': bbox
                })
    
    # 按从左到右排序（基于左上角X坐标）
    if high_conf_results:
        high_conf_results.sort(key=lambda x: min([pt[0] for pt in x['bbox']]))
    # 结果处理（强制保留最高置信度结果）
    full_text = ''.join([item[1] for item in results if item[2] >= 0]).replace(' ', '').replace('|', '丨')
    
    # 整体字符串校正
    if dictionary and full_text:
        corrector = OCRDictionaryCorrector(dictionary, err_corrections_dic)
        corrected_text = corrector.correct(full_text)
        return corrected_text, max_prob
    
    return full_text, max_prob

# 使用示例
if __name__ == "__main__":
    import loader
    # 确保调试目录存在
    debug_dir = Path("debug")
    debug_dir.mkdir(exist_ok=True)
    
    # 领域词典示例
    domain_dict = loader.load_player_dic("data/testData.json")
    
    # 测试图像路径
    image_path = "output/test_player_name.jpg"
    
    print("\n" + "="*50)
    print(f"🔍 测试-开始识别: {image_path}")
    print("="*50)
    
    # 执行OCR识别
    results = recognize_chinese_text(
        image_path=image_path,
        dictionary=domain_dict,
        use_gpu=True
    )
    
    # 结果统计
    print("\n" + "="*50)
    print("识别结果统计:")
    print("="*50)
    print(f"{'文本':<20} | {'置信度':<8} | {'词典匹配'}")
    print("-" * 45)
    for text, prob in results:
        match = "✓" if text in domain_dict else "✗"
        print(f"{text:<20} | {prob:.4f}   | {match}")
    
    # 补充说明
    if not results:
        print("\n❌ 未识别到有效文本，请检查:")
        print("- 预处理图像是否包含可读文本 (debug/*_processed.jpg)")
        print("- 原始识别详情中的置信度和文本内容")
        print("- 尝试调整 text_threshold 参数值")