import json
import os
import yaml
from PIL import Image

def load_json(file_path):
    """
    加载 JSON 文件并返回 Python 字典
    
    参数:
    file_path (str): JSON 文件路径
    
    返回:
    dict: 解析后的 Python 字典
    
    异常:
    FileNotFoundError: 创建文件并返回空字典
    json.JSONDecodeError: JSON 格式错误时抛出
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        # 如果文件不存在，创建新文件并返回空字典
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump({}, file)
        return {}
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"JSON 解析错误: {e.msg}", e.doc, e.pos) from None

def load_dict(file_path):
    """
    从JSON文件中加载角色字典
    :param file_path: JSON文件路径
    :return: 角色字典列表, 战法字典列表
    """
    try:
        # 打开并读取JSON文件[9,10,11](@ref)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取数据
        character_list = data.get('characters', [])
        tactics_list = data.get('tactics', [])
        
        # 验证数据格式
        if not isinstance(character_list, list) or not isinstance(tactics_list, list):
            raise ValueError("Invalid data format: data_list should be a list")
        
        print(f"成功加载字典完成")
        return character_list, tactics_list
    
    except FileNotFoundError:
        print(f"错误：文件 {file_path} 不存在")
        return []
    except json.JSONDecodeError:
        print(f"错误：文件 {file_path} 不是有效的JSON格式")
        return []
    except Exception as e:
        print(f"加载失败：{str(e)}")
        return []
    
def load_player_dic(file_path):
    """
    从JSON文件中加载角色字典
    :param file_path: JSON文件路径
    :return: 玩家字典列表
    """
    try:
        # 打开并读取JSON文件[9,10,11](@ref)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取数据
        player_list = data.get('player', [])

        if not isinstance(player_list, list):
            raise ValueError("Invalid data format: player_list should be a list")
        
        print(f"成功加载 {len(player_list)} 个玩家")
        return player_list
    
    except FileNotFoundError:
        print(f"错误：文件 {file_path} 不存在")
        return []
    except json.JSONDecodeError:
        print(f"错误：文件 {file_path} 不是有效的JSON格式")
        return []
    except Exception as e:
        print(f"加载失败：{str(e)}")
        return []
    
def load_image(image_path, image_size):
    img = Image.open(image_path)
    width, height = img.size
    
    # # 验证图片尺寸是否符合预期
    # if width*height != image_size[0]*image_size[1]:
    #     raise ValueError(f"图片尺寸不符合要求，预期尺寸为{image_size}，实际尺寸为{width}x{height}") # 2376x1104
    # else:
    return img
    
def load_battle_report_images_paths(directory):
    """
    获取指定目录中的所有图片地址，确保图片数量为双数
    
    参数:
        directory (str): 图片目录路径
        image_size (tuple): 保留参数（不再使用）
        
    返回:
        list: 图片文件路径列表
        
    异常:
        ValueError: 图片数量非双数时抛出
    """
    # 获取目录中所有图片文件路径
    image_files_paths = []
    valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
    
    for filename in os.listdir(directory):
        if filename.lower().endswith(valid_extensions):
            image_files_paths.append(os.path.join(directory, filename))
    
    # 验证图片数量是否为双数
    # if len(image_files_paths) % 2 != 0:
    #     raise ValueError(f"目录中图片数量必须为双数，当前数量：{len(image_files_paths)}")
    #
    return image_files_paths
