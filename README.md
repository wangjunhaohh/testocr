游戏《率土之滨》战报OCR识别程序  
The OCR recognition application for the battle report of the game 'Infinite Borders'

---

## 运行方法
1. 根据requirements.txt安装正确的环境
2. 编辑 `config.yaml` 文件，填写正确的配置参数
3. 将战报图片放置在配置好的图片存放路径中并且以一份对战图片，一份战法详情图片的顺序依次命名（ps.如果按顺序截图则不用理会）
4. 在命令行中执行：  
   ```bash
   python battleIdentify.py

## 已经完成的功能
1. 基本的识别功能
2. 基本的数据库存储功能

## 未完成的功能
1. 多线程orc识别（ps.目前主线程识别70份战报140个图片的速度大概是20几秒似乎不需要这个功能）
2. 多个图片尺寸的适配（ps.目前仅支持2376x1104尺寸的战报，如有其他需要可开启debug模式挨个调节Report类里关于各个文字对应的图片位置）
3. GUI（ps.对于有一定编码经验的人来说，目前似乎并不是那么需要）
4. 模拟器自动截图功能
