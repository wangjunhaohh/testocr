from libs import loader
from libs import orc_characters
from libs import orc_chinese
from concurrent.futures import ThreadPoolExecutor
import time
import os
import itertools

class Report:
    def __init__(self, report_images_path ,config):

        # 初始化信息
        self.images_path = report_images_path
        self.config = config
        self.image_size = (self.config["configuration"]["image_size"][0], self.config["configuration"]["image_size"][1])

        self.report_images = []
        self.player_image = None
        self.characters_image = []
        self.tactics_images = []

        self.player = ""
        self.characters = []
        self.tactics = []

        self.team_type = ""

        self.__build()
    def __build(self):
        for path in self.images_path:
            self.report_images.append(loader.load_image(path, self.image_size))
        self.__image_crop()

    
    def __image_crop(self):
        self.__process_enemy_image(self.report_images[0])
        self.__process_tactics_image(self.report_images[1])

    
    def __process_enemy_image(self, img):
        """
        处理游戏对战截图，精准分割敌方部分并提取玩家名称和武将区域
        武将区域按照固定尺寸分割为三个独立区块
        
        参数:
        image_path (str): 图片文件路径
        
        返回:
        tuple: (玩家名称区域图像路径, [武将区域1图像路径, 武将区域2图像路径, 武将区域3图像路径])
        """
        # 创建输出目录
        width, height = img.size

        try:
            # 1. 裁剪右半部分（敌方区域） 左，上，右，下
            x = width/2
            y = height
            enemy_area = img.crop((width // 2, 0, width, height))
            
            # 2. 玩家名称区域
            player_name_area = enemy_area.crop((
                180,   # 左边界
                88,    # 上边界
                430,   # 右边界
                130    # 下边界
            ))
            print(player_name_area)
            player_name_area.save("./debug/player_name_area.png")
            print(x)
            print(y)
            # 2622, 1206 图片长宽 除2 1311 1206
            # （1471，321）（1471，832）（2328，321）（2328，832）
            # 3. 武将区域
            enemy_heroes_area = enemy_area.crop((
                int(x / 8.15),    # 左边界 （1471-1311）
                int(y / 1.542),   # 上边界 782
                int(x ),  # 右边界   （2328-1311)
                int(y / 1.4495)    # 下边界  （832）
            ))
            print(enemy_heroes_area)
            enemy_heroes_area.save("./debug/enemy_heroes_area.png")
            # 4. 按照固定坐标将武将区域分成三个独立区域
            # hero3_area = enemy_heroes_area.crop((0, 0, 285, 50))
            first = int((x - x / 8.1)*0.75 / 3)
            tail = int(y / 1.4495 - y / 1.542)
            hero3_area = enemy_heroes_area.crop((0, 0, first, tail))
            hero3_area.save("./debug/hero3_area.png")
            hero2_area = enemy_heroes_area.crop((first, 0, first*2, tail))
            hero2_area.save("./debug/hero2_area.png")
            hero1_area = enemy_heroes_area.crop((first*2, 0, first*3, tail))
            hero1_area.save("./debug/hero1_area.png")

            self.player_image = player_name_area
            self.characters_image = [hero1_area, hero2_area, hero3_area]
        
        except Exception as e:
            raise RuntimeError(f"图片处理失败: {str(e)}")

    def __process_tactics_image(self, img):
        try:
            tactics_area = img.crop((
                1220,   # 左边界
                340,    # 上边界
                1600,   # 右边界
                890    # 下边界
            ))

            tactic_n1 = tactics_area.crop((
                30,
                128,
                165,
                160
            ))
            
            tactic_n2 = tactics_area.crop((
                225,
                128,
                360,
                160
            ))

            tactic_n3 = tactics_area.crop((
                30,
                317,
                165,
                350
            ))

            tactic_n4 = tactics_area.crop((
                225,
                317,
                360,
                350
            ))

            tactic_n5 = tactics_area.crop((
                30,
                510,
                165,
                540
            ))
            tactic_n6 = tactics_area.crop((
                225,
                510,
                360,
                540
            ))

            self.tactics_images = [tactic_n1, tactic_n2, tactic_n3, tactic_n4, tactic_n5, tactic_n6]        
        
        except Exception as e:
            raise RuntimeError(f"图片处理失败: {str(e)}")
    
    def orc_start(self, player_list, character_list, tactics_list, err_corrections={}, debug=False, orc_reader=None):

        if debug:
            print("----------------Debug-------------------")
            print("当前查验对象：")
            print(f"玩家名和武将名：{self.images_path[0]}")
            print(f"战法名：{self.images_path[1]}")
            print(">---------------Debug end---------------")

        # 初始化变量名
        player_confidence = 0.0
        character_confidences = []
        tactic_confidences = []

        # 1个玩家名识别
        player, player_confidence = orc_chinese.recognize_chinese_text(
            image=self.player_image, 
            dictionary=player_list, 
            reader=orc_reader,
            err_corrections_dic=err_corrections
            )
        self.player = player
        
        # 3个武将及阵营识别



        for character in self.characters_image:
            character_result, character_confidence= orc_characters.recognize_faction_hero(
                image=character,
                character_list=character_list,
                err_corrections_dic=err_corrections,
                reader=orc_reader,
                use_gpu = True
            )
            self.characters.append(character_result)
            character_confidences.append(character_confidence)

        # 6个战法识别
        for tactic in self.tactics_images:
            tactic_result, tactic_confidence = orc_chinese.recognize_chinese_text(
                image=tactic,
                dictionary=tactics_list,
                reader=orc_reader,
                err_corrections_dic=err_corrections
            )
            self.tactics.append(tactic_result)
            tactic_confidences.append(tactic_confidence)

        if self.config["configuration"]["debug"]:
            print("识别结果:")
            print(self.player, player_confidence)
            for i in range(len(self.characters)):
                # 打印一个character及其置信度
                print(f"Character: {self.characters[i]} (Confidence: {character_confidences[i]})")
                print("********************************************")
                # 计算两个tactics的起始索引
                start_idx = 2 * i
                # 确保索引不越界
                if start_idx < len(self.tactics):
                    # 连续打印两个tactics（同一行）
                    print("Tactics: ", end="")
                    # 第一个tactic
                    print(f"{self.tactics[start_idx]} (Confidence: {tactic_confidences[start_idx]}), ", end="")
                    # 第二个tactic（如果存在）
                    if start_idx + 1 < len(self.tactics):
                        print(f"{self.tactics[start_idx+1]} (Confidence: {tactic_confidences[start_idx+1]})")
                    else:
                        print()  # 换行
                else:
                    print("No more tactics available.")
                

            debug_path = self.config["paths"]["debug"]
            self.player_image.save(os.path.join(debug_path, "player.jpg"))
            print (f"已保存玩家{self.player}图片到 {debug_path} 目录")
            for i, character in enumerate(self.characters_image):
                character_path = os.path.join(debug_path, f"character_{i+1}.jpg")
                character.save(character_path)
                print(f"第{i+1}个武将图片保存到 {debug_path}")
            for i, tactic in enumerate(self.tactics_images):
                tactic.save(f"{debug_path}/tactic_{i}.jpg")
                print(f"已保存第{i+1}个策略图片到{debug_path}")

    from concurrent.futures import ThreadPoolExecutor

    def orc_start_multithread(self, player_list, character_list, tactics_list, thread_count=4):
        """
        多线程OCR识别函数
        :param thread_count: 线程池大小，默认4线程
        """
        # 初始化变量
        player_confidence = 0.0
        character_confidences = []
        tactic_confidences = []
        
        # 创建线程池[6,7](@ref)
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            # 1. 提交玩家名识别任务
            player_future = executor.submit(
                orc_chinese.recognize_chinese_text,
                image=self.player_image,
                dictionary=player_list,
                use_gpu=self.config["configuration"]["use_gpu"],
                model_dir=self.config["paths"]["models"]
            )
            
            # 2. 批量提交武将识别任务[1,6](@ref)
            character_futures = [
                executor.submit(
                    orc_characters.recognize_faction_hero,
                    image=character,
                    character_list=character_list,
                    min_confidence=0.2,
                    use_gpu=self.config["configuration"]["use_gpu"],
                    model_dir=self.config["paths"]["models"]
                ) for character in self.characters_image
            ]
            
            # 3. 批量提交战法识别任务
            tactic_futures = [
                executor.submit(
                    orc_chinese.recognize_chinese_text,
                    image=tactic,
                    dictionary=tactics_list,
                    use_gpu=self.config["configuration"]["use_gpu"],
                    model_dir=self.config["paths"]["models"]
                ) for tactic in self.tactics_images
            ]

            print("等待线程结束...")
            start_time = time.time()
            # 获取玩家结果
            player_result, player_confidence = player_future.result()
            self.player = player_result[0][0]
            
            # 获取武将结果
            for future in character_futures:
                character_result, confidence = future.result()
                self.characters.append(character_result)
                character_confidences.append(confidence)
            
            # 获取战法结果
            for future in tactic_futures:
                tactic_result, confidence = future.result()
                self.tactics.append(tactic_result[0][0])
                tactic_confidences.append(confidence)

            end_time = time.time()

            print(f"识别完成，耗时：{end_time - start_time}秒")
        # 调试输出（保持不变）
        if self.config["configuration"]["debug"]:
            print("识别结果:")
            print("-----------------------------------------")
            print(self.player, player_confidence)
            for i in range(len(self.characters)):
                print(f"Character: {self.characters[i]} (Confidence: {character_confidences[i]})")
                start_idx = 2 * i
                if start_idx < len(self.tactics):
                    print("Tactics: ", end="")
                    print(f"{self.tactics[start_idx]} (Confidence: {tactic_confidences[start_idx]}), ", end="")
                    if start_idx + 1 < len(self.tactics):
                        print(f"{self.tactics[start_idx+1]} (Confidence: {tactic_confidences[start_idx+1]})")
                    else:
                        print()
                else:
                    print("No more tactics available.")
            
            debug_path = self.config["paths"]["debug"]
            self.player_image.save(os.path.join(debug_path, "player.jpg"))
            print(f"已保存玩家{self.player}图片到 {debug_path} 目录")
            for i, character in enumerate(self.characters_image):
                character_path = os.path.join(debug_path, f"character_{i+1}.jpg")
                character.save(character_path)
                print(f"第{i+1}个武将图片保存到 {debug_path}")
            for i, tactic in enumerate(self.tactics_images):
                tactic.save(f"{debug_path}/tactic_{i}.jpg")
                print(f"已保存第{i+1}个策略图片到{debug_path}")



def get_team_type(character_types):
    """
    根据角色类型字典确定队伍类型字符串
    
    参数:
    character_types (dict): 角色-类型字典，格式为{角色名: 类型}，
                            类型可以是字符串(如"骑")或列表(如["骑", "步"])
    
    返回:
    str: 队伍类型字符串，如"步步步"、"骑弓"、"骑步弓"或"步弓/骑步弓"(多种可能时)
    """
    # 类型优先级映射（骑 > 步 > 弓）
    type_priority = {'骑': 0, '步': 1, '弓': 2}
    
    # 统一处理为列表形式
    type_lists = []
    for char, t in character_types.items():
        if isinstance(t, str):
            type_lists.append([t])
        else:
            type_lists.append(t)
    
    # 所有可能的类型组合
    all_combinations = list(itertools.product(*type_lists))
    possible_results = set()
    
    for combo in all_combinations:
        # 获取唯一类型并按优先级排序
        unique_types = sorted(set(combo), key=lambda x: type_priority[x])
        
        # 根据类型数量确定队伍类型
        if len(unique_types) == 1:
            team_type = unique_types[0] * 3  # e.g., "骑骑骑"
        elif len(unique_types) == 2:
            team_type = ''.join(unique_types)  # e.g., "骑步"
        else:  # 三种类型
            team_type = '骑步弓'  # 固定顺序
        
        possible_results.add(team_type)
    
    # 处理结果
    sorted_results = sorted(possible_results)
    return '/'.join(sorted_results) if len(sorted_results) > 1 else sorted_results[0]
