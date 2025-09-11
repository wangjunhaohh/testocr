import sqlite3
from datetime import datetime

def create_teamdic(report):
    print(report.characters)
    play,a = report.player
    if a:
        play = play[1]
    else:
        if isinstance(play[0], str):
            play = play
        else:
            play = play[0]
    friend_play, a = report.friend_player
    if a:
        friend_player =friend_play[1]
    else:
        if isinstance(friend_play[0], str):
            friend_player = friend_play
        else:
            friend_player = friend_play[0]
    hero, flag = report.characters[0]
    hero1, flag1 = report.characters[1]
    hero2, flag2 = report.characters[2]
    team_dic = {
        "友方玩家":friend_player,
        "玩家名": play,
        # "队伍类型": report.team_type,
        "大营": hero,
        # "大营战法1": report.tactics[0],
        # "大营战法2": report.tactics[1],
        "中军": hero1,
        # "中军战法1": report.tactics[2],
        # "中军战法2": report.tactics[3],
        "前锋": hero2,
        "武勋": report.wuxunNum,
        "攻城": report.gongchengNum,
        "是否拆下": report.fandi
        # "前锋战法1": report.tactics[4],
        # "前锋战法2": report.tactics[5]
    }

    return team_dic


def create_database_and_table(database, table):
    """创建数据库和表结构（使用中文字段名）"""
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    
    # 创建队伍信息表（全部使用中文字段名）
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {table} (
        编号 INTEGER PRIMARY KEY AUTOINCREMENT,
        友方玩家 TEXT ,
        玩家名 TEXT ,
        大营 TEXT ,
        中军 TEXT ,
        前锋 TEXT ,
        武勋 TEXT ,
        攻城 TEXT ,
        是否拆下 INTEGER ,
        添加时间 TIMESTAMP DEFAULT (datetime('now', 'localtime'))
    )
    ''')
    conn.commit()
    conn.close()

def add_team_data(team_info, database, table):
    """添加队伍数据到数据库（带去重机制）"""
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    # 1. 检查重复数据（排除自增ID和时间戳字段）
    cursor.execute(f'''
    SELECT COUNT(*) FROM {table}
    WHERE
        友方玩家=? AND
        玩家名 = ?  AND
        大营 = ? AND
        中军 = ? AND
        前锋 = ? AND
        武勋 = ? AND
        攻城 = ? AND
        是否拆下 = ?
    ''', (
        team_info['友方玩家'],
        team_info['玩家名'],
        team_info['大营'],
        team_info['中军'],
        team_info['前锋'],
        team_info['武勋'],
        team_info['攻城'],
        team_info['是否拆下']
    ))

    # 2. 存在重复则跳过插入
    if cursor.fetchone()[0] > 0:
        conn.close()
        return False
    
    # 3. 无重复则执行插入
    cursor.execute(f'''
    INSERT INTO {table} (
        友方玩家,
        玩家名, 
        大营,
        中军, 
        前锋,
        武勋,
        攻城,
        是否拆下 
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ? )
    ''', (
        team_info['友方玩家'],
        team_info['玩家名'],
        team_info['大营'],
        team_info['中军'],
        team_info['前锋'],
        team_info['武勋'],
        team_info['攻城'],
        team_info['是否拆下']
    ))

    conn.commit()
    conn.close()
    return True

# 查询所有记录
def selectAll(database, table):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f''' SELECT * FROM {table} ''')
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()
    return rows
def getOwnerWuXun(database, table):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    #  where 添加时间 between datetime('now','weekday 0','-13 days') and  datetime('now','weekday 0','-6 days')
    cursor.execute(f''' SELECT 友方玩家,sum(武勋) wuxun ,sum(攻城) gongcheng,sum(是否拆下) fandi FROM {table}   group by 友方玩家 order by wuxun desc''')
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()
    return rows
