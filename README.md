
## 运行方法
1. 根据requirements.txt安装正确的环境
2. 编辑 `config.yaml` 文件，填写正确的配置参数
3. 在命令行中执行：  
   ```bash
   python battleIdentify.py

## 已经完成的功能
1. 基本的识别功能
2. 基本的数据库存储功能
3. 多个图片尺寸的适配
4. 模拟器自动截图功能
## 未完成的功能
1. 多线程orc识别（ps.目前主线程识别70份战报140个图片的速度大概是20几秒似乎不需要这个功能）


## tesseract_cmd需配置成自己安装的orc地址
1. tesseract_cmd = 'D:\\java\\py3\\tesseractOcr\\tesseract.exe'
2. 下载地址：https://digi.bib.uni-mannheim.de/tesseract/


-- 1.识别时间戳 是否是昨天，不是则往下滚动200像素点，再循环判断到至昨天的时间，然后点击第一封

模拟器比例设置宽/高≈2.174附近，否则截图之后识别比例不对