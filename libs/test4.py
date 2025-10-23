
#（不需要完全是一个战报高度，识别区域也可以框选的大一点，就算框的大一点也不是很影响，加上判断时间戳）

# 1. 截屏整屏，框选指定一个为指定模板对比区域photoCompareTemplate


# 2. 裁剪模板区域，胜负平photoStatusTemplate和时间photoTimeTemplate，左侧玩家姓名photoLeftNameTemplate，三个条件同时出现说明滑动条件合适，



# 3. 小距离滑动，每次滑动距离最好是小于战报高度，防止划过1个多


# 4. 截图整个屏幕，裁剪指定模板对比区域photoCompare，从中提取胜负平photoStatus，时间photoTime，photoLeftNameTemplate，
#    这三个不同说明有新的需要进行操作，否则继续滑动（防止滑动太小，框的区域稍大判定也符合了）继续滑动
#    不同就点击进入详情进行截图 然后保存photoStatus，photoTime，替换photoStatusTemplate，photoTimeTemplate，
#    如果判断是不是同一天，就通过photoTime和photoTimeTemplate比较
