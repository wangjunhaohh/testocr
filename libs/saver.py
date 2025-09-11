import json
import os

def add_player(player_name, file_path):
    """
    向JSON文件添加新玩家。如果文件不存在，则创建并初始化；如果存在，则更新"player"列表。
    新增防重复功能：检测玩家名是否已存在[1,2](@ref)
    
    参数:
        player_name (str): 要添加的玩家名字符串。
        file_path (str): JSON文件的路径（例如：'data/players.json'）。
    
    返回:
        None
    """
    try:
        # 1. 确保文件目录存在（如果目录不存在，则创建）
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        # 2. 初始化数据
        data = {}
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                data = {}
        else:
            data = {"player": []}
        
        # 3. 标准化数据结构
        if "player" not in data:
            data["player"] = []
        elif not isinstance(data["player"], list):
            data["player"] = [data["player"]]
        
        # ====== 新增防重复功能 ====== [1,2](@ref)
        # 4. 检查玩家名是否已存在（区分大小写）
        if player_name in data["player"]:
            return  # 直接退出函数
        
        # 5. 不区分大小写检查（增强防重复）
        if any(name.lower() == player_name.lower() for name in data["player"]):
            return  # 直接退出函数
        # ====== 防重复功能结束 ======
        
        # 6. 添加新玩家
        data["player"].append(player_name)
        
        # 7. 保存更新
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")

def add_error_correction(key, value, file_path):
    """
    向JSON文件添加键值对（{"key":"value"}结构）。文件不存在时自动创建。
    
    参数:
        key (str): 要添加的键
        value (str): 要添加的值
        file_path (str): JSON文件路径（如：'data/config.json'）
    
    返回:
        None
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 初始化数据：文件不存在/空时创建新字典；否则读取现有数据
        data = {}
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:  # 处理无效JSON
                    data = {}
        
        # 添加/更新键值对（覆盖已存在键）
        data[key] = value
        
        # 写回文件（格式化输出）
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"✅ 已添加: '{key}': '{value}' → {file_path}")
    
    except Exception as e:
        print(f"❌ 操作失败: {e}")