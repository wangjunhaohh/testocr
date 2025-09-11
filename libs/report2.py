from libs import loader
from libs import orc_characters
from libs import orc_chinese
from concurrent.futures import ThreadPoolExecutor
import time
import re
import os
import itertools

class ReportNotZhanFa:
    def __init__(self, report_images_path ,config):

        # 初始化信息
        self.images_path = report_images_path
        self.config = config
        self.image_size = (self.config["configuration"]["image_size"][0],self.config["configuration"]["image_size"][1])
        self.report_images = []
        self.friend_player_image = None
        self.player_image = None
        self.wuxun_image = None
        self.characters_image = []
        self.tactics_images = []

        self.player = ""
        self.friend_player = ""
        self.wuxunNum = 0
        self.gongchengNum = 0
        self.fandi = 0
        self.characters = []
        self.tactics = []

        self.team_type = ""

        self.__build()
    def __build(self):
        self.report_images.append(loader.load_image(self.images_path, self.image_size))
        self.__image_crop()

    
    def __image_crop(self):
        self.__process_enemy_image(self.report_images[0])
        # self.__process_tactics_image(self.report_images[1])

    
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
        # 2622, 1206 图片长宽 除2 1311 1206
        # （1471，321）（1471，832）（2328，321）（2328，832）
        try:
            # 1. 裁剪右半部分（敌方区域） 左，上，右，下
            x = width/2
            y = height

            # 中间武勋攻城部分
            wuxun_area = img.crop(( width*0.45 , height*0.25,width*0.55,height*0.75))
            friend_area = img.crop((0, 0, width/2, height))
            # 友方玩家名称区域
            friend_player_name_area = friend_area.crop((
                # int(x / 8.90),   # 左边界
                int(x / 1.40),  # 左边界
                int(y / 13.704),  # 上边界
                int(x / 1.10),  # 右边界
                int(y / 8.317)  # 下边界
            ))
            enemy_area = img.crop((width // 2, 0, width, height))
            
            # 2. 玩家名称区域
            player_name_area = enemy_area.crop((
                # int(x / 8.90),   # 左边界
                int(x / 6.90),   # 左边界
                int(y / 13.704),    # 上边界
                int(x /3.10),   # 右边界
                int(y / 8.317)   # 下边界
            ))
            # 3. 武将区域
            enemy_heroes_area = enemy_area.crop((
                int(x / 8.15),    # 左边界 （1471-1311）
                int(y / 1.542),   # 上边界 782
                int(x ),  # 右边界   （2328-1311)
                int(y / 1.4495)    # 下边界  （832）
            ))
            print(enemy_heroes_area)
            # 4. 按照固定坐标将武将区域分成三个独立区域
            # hero3_area = enemy_heroes_area.crop((0, 0, 285, 50))
            first = int((x - x / 8.1)*0.75 / 3)
            tail = int(y / 1.4495 - y / 1.542)
            hero3_area = enemy_heroes_area.crop((0, 0, first, tail))
            hero2_area = enemy_heroes_area.crop((first, 0, first*2, tail))
            hero1_area = enemy_heroes_area.crop((first*2, 0, first*3, tail))

            self.player_image = player_name_area
            self.friend_player_image = friend_player_name_area
            self.characters_image = [hero1_area, hero2_area, hero3_area]
            self.wuxun_image = wuxun_area

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
    
    def orc_start(self, player_list,friend_player_list, character_list, tactics_list, err_corrections={}, debug=False, orc_reader=None):

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
        # 友方玩家识别
        friend_player, friend_player_confidence = orc_chinese.recognize_chinese_text(
            image=self.friend_player_image,
            dictionary=friend_player_list,
            reader=orc_reader,
            err_corrections_dic=err_corrections
        )
        self.friend_player = friend_player
        
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

        #     武勋部分
        wuxun, wuxun_confidence = orc_chinese.recognize_chinese_text(
            image=self.wuxun_image,
            dictionary={},
            reader=orc_reader
        )
        # 处理武勋和攻城
        pattern = r"武勋\+(\d+)"  # 使用捕获武勋数量
        match = re.search(pattern, wuxun)
        pattern2 = r"下降(\d+)"  # 使用捕获攻城数量
        match2 = re.search(pattern2, wuxun)
        pattern3 = r"胜利"  # 用于判断获胜
        match3 = re.search(pattern3, wuxun)
        pattern3_1 = r"要塞"  # 使用判断攻城
        match3_1 = re.search(pattern3_1, wuxun)
        pattern4 = r"占领"  # 使用捕翻地数量
        match4 = re.search(pattern4, wuxun)
        if match:
            self.wuxunNum = match.group(1)  # group(0) 返回整个匹配的字符串
        if match2 and match3 and match3_1:
            self.gongchengNum = match2.group(1)  # group(0) 返回整个匹配的字符串
        if match4 and match3:
            self.fandi = 1  # group(0) 返回整个匹配的字符串
        else:
            self.fandi = 0

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
            
            # # 3. 批量提交战法识别任务
            # tactic_futures = [
            #     executor.submit(
            #         orc_chinese.recognize_chinese_text,
            #         image=tactic,
            #         dictionary=tactics_list,
            #         use_gpu=self.config["configuration"]["use_gpu"],
            #         model_dir=self.config["paths"]["models"]
            #     ) for tactic in self.tactics_images
            # ]

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

            end_time = time.time()

            print(f"识别完成，耗时：{end_time - start_time}秒")
        # 调试输出（保持不变）


