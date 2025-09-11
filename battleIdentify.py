from libs.dbmanager import *
from libs.report import Report
from libs.report2 import ReportNotZhanFa
from libs.report import get_team_type
from libs import loader
from libs import checker
from libs import dbmanager
from pathlib import Path
import easyocr
import torch
import yaml
import threading
from concurrent.futures import ThreadPoolExecutor , as_completed # 导入线程池模块

def print_progress_bar(str, completed, total, bar_length=50):
    """打印文本进度条"""
    percent = completed / float(total)
    arrow = '=' * int(round(percent * bar_length) - 1) + '>'
    spaces = ' ' * (bar_length - len(arrow))
    
    # 构建进度条字符串
    progress_bar = f"\r{str}: [{arrow}{spaces}] {percent*100:.1f}% ({completed}/{total})"
    print(progress_bar, end='', flush=True)
    
    # 完成时打印新行
    if completed == total:
        print()


if __name__ == "__main__":
    with open("config.yaml") as f:
        config = yaml.safe_load(f)



    character_list, tactics_list = loader.load_dict(config["paths"]["data"])
    player_list = loader.load_player_dic(config["paths"]["players"])
    friend_player_list = loader.load_player_dic(config["paths"]["friend_players"])
    # character_type = loader.load_json(config["paths"]["character_type"])
    err_corrections_dic = loader.load_json(config["paths"]["err_corrections"])


    # 加载模型
    model_path = Path(config["paths"]["models"])
    model_path.mkdir(parents=True, exist_ok=True)
    
    model_file = model_path / 'zh_sim_g2.pth'
    if not model_file.exists():
        print("⚠️ 首次使用需下载中文模型(约200MB)，请保持网络畅通...")
    
    # 初始化OCR阅读器
    reader = easyocr.Reader(
        lang_list=['ch_sim', 'en'],
        gpu=config["configuration"]["use_gpu"],
        model_storage_directory=str(model_path),
        download_enabled=False,
        recog_network='zh_sim_g2'
    )

    if hasattr(reader, 'recognizer'):
        recognizer = reader.recognizer
        # 处理可能的DataParallel封装
        if hasattr(recognizer, 'module'):
            recognizer = recognizer.module
            
        # 遍历所有模块并优化RNN层
        for module in recognizer.modules():
            if isinstance(module, (torch.nn.LSTM, torch.nn.GRU)):
                module.flatten_parameters()

    # 创建报告对象列表
    # reports = []
    # for i in range(len(images) // 2):  # 确保双数处理
    #     report = Report((images[i*2], images[i*2+1]), config)
    #     reports.append(report)

    images = loader.load_battle_report_images_paths(config["paths"]["pictures"])
    reports2 = []
    for i in range(len(images)):
        report = ReportNotZhanFa((images[i]), config)
        reports2.append(report)
    """ # 多线程优化部分
    thread_count = config["configuration"].get("thread_count", 4)  # 从配置获取线程数，默认4
    
    # 创建线程锁确保进度更新安全
    progress_lock = threading.Lock()"""
    
    # 初始打印进度条
    total_tasks = len(reports2)
    completed = 0
    print_progress_bar("识别进度", completed, total_tasks)

    for report in reports2:
        report.orc_start(
            player_list=player_list, 
            friend_player_list=friend_player_list,
            character_list=character_list,
            tactics_list=tactics_list,
            err_corrections=err_corrections_dic,
            debug=config["configuration"]["debug"],
            orc_reader=reader
            )
        completed += 1
        print_progress_bar("识别进度", completed, total_tasks)
        

    """with ThreadPoolExecutor(max_workers=thread_count) as executor:
        # 提交所有OCR任务到线程池
        futures = [
            executor.submit(
                report.orc_start,  # 目标函数
                player_list,       # 参数1
                character_list,    # 参数2
                tactics_list,      # 参数3
                err_corrections_dic, # 参数4
                config["configuration"]["debug"], # 参数5       
                reader             # 参数6
            )
            for report in reports
        ]
        
        # 等待所有任务完成并处理结果
        for future in futures:            
            try:
                future.result()  # 阻塞等待单个任务完成
            except Exception as e:
                print(f"OCR处理失败: {str(e)}")
            
            # 更新进度计数
            with progress_lock:
                completed += 1
                print_progress_bar(completed, total_tasks)"""

    checker.check_report(report_list=reports2, config=config, debug=config["configuration"]["debug"])
    dbmanager.create_database_and_table(config["database"]["dbpath"], config["database"]["table"])


    # 初始打印进度条
    completed = 0
    print_progress_bar("数据库录入", completed, total_tasks)
    print("=============================]")

    for report in reports2:
        team_dic = dbmanager.create_teamdic(report)
        print(team_dic)
        dbmanager.add_team_data(team_dic, config["database"]["dbpath"], config["database"]["table"])
        completed += 1
        print_progress_bar("数据库录入", completed, total_tasks)

    selectAll(config["database"]["dbpath"], config["database"]["table"])
    getOwnerWuXun(config["database"]["dbpath"], config["database"]["table"])