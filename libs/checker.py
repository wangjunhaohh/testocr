from libs import saver
from datetime import datetime
def user_correct(answers=None):
    while True:
        user_input = input("> ").strip().lower()
        if answers:
            if user_input in answers:
                return user_input
        else:
            return user_input
        print(f"请重新输入:{answers}")

def check_player(player_tuple, config):
    if player_tuple[1]:
        print(f"识别玩家结果：\n识别结果：{player_tuple[0][0]}, 校正结果：{player_tuple[0][1]}")
        print("是否需要手动校正或保留识别玩家名称？(y/n/k)")
        yorn = user_correct(["y", "n", "k"])
        if yorn == "y":
            print("请输入玩家名称：")
            player_name = user_correct()
            saver.add_player(player_name, config["paths"]["players"])
            return player_name
        elif  yorn == "n":
            return player_tuple[0][1]
        elif yorn == "k":
            return player_tuple[0][0]
    else:
        return player_tuple[0]
    
def check_list(tuples, config):
    list = []
    i = 1
    for tuple in tuples:
        if tuple[1]:
            print(f"识别第{i}个结果：\n识别结果：{tuple[0][0]}, 校正结果：{tuple[0][1]}")
            print("是否需要手动校正对象？(y/n)")
            yorn = user_correct(["y", "n"])
            if yorn == "y":
                print("请输入正确对象：")
                correct = user_correct()
                list.append(correct)
                saver.add_error_correction(tuple[0][0], correct, config["paths"]["err_corrections"])
            else:
                list.append(tuple[0][0])
                saver.add_error_correction(tuple[0][0], tuple[0][1], config["paths"]["err_corrections"])
        else:
            list.append(tuple[0])

        i += 1
    return list
    
def check_report(report_list, config, debug=False):
    import sys
    
    # 自定义日志记录器（同时输出到控制台和文件）
    class Logger:
        def __init__(self, filename, stream):
            self.terminal = stream  # 原始控制台输出流
            self.log = open(filename, "a", encoding="utf-8")  # 以追加模式打开日志文件
        
        def write(self, message):
            self.log.write(message)
            self.terminal.write(message)
            
        def flush(self):
            self.terminal.flush()
            self.log.flush()
        
        def close(self):
            self.log.close()

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = config["paths"]["logs"]+f"/report_check_{current_time}.log"
    # 保存原始标准输出
    original_stdout = sys.stdout
    # 创建日志记录器实例
    logger_instance = Logger(log_file, sys.stdout)
    # 重定向标准输出
    sys.stdout = logger_instance

    try:
        index = 1
        length = len(report_list)
        for report in report_list:
            logger_instance.write(f"----------Check: {index}/{length}-------------------\n")
            logger_instance.write(f"当前查验对象：{report.images_path}\n")
            logger_instance.write(str(report.player)+"\n")
            logger_instance.write(str(report.characters)+"\n")
            logger_instance.write(str(report.friend_player)+"\n")
            logger_instance.write(str(report.wuxunNum)+"\n")
            logger_instance.write(str(report.gongchengNum)+"\n")
            logger_instance.write(str(report.fandi)+"\n")
            # logger_instance.write(str(report.tactics)+"\n")
            # report.player = check_player(report.player, config)
            # report.characters = check_list(report.characters, config)
            # report.tactics = check_list(report.tactics, config)
            index += 1
    except Exception as e:
        logger_instance.write(f"错误：{e}"+"\n")
    finally:
        # 恢复原始标准输出
        sys.stdout = original_stdout
        # 关闭日志文件
        logger_instance.close()