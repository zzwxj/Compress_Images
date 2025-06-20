# Compress_Images
图片压缩脚本__基于python一些压缩图片的库/工具

# 安装依赖
pip install opencv-python pillow numpy configparser
#下载慢可以换源  -i https://pypi.tuna.tsinghua.edu.cn/simple

#推荐额外安装命令行工具（效果更佳）：

#PNG：下载 pngquant 并加入 PATH [官网](https://pngquant.org/)

#JPEG：安装 MozJPEG [官网](https://github.com/mozilla/mozjpeg)


# 首次运行
python compress_images.py

脚本会自动创建配置文件compress_images.ini

编辑配置文件

input_dir = /path/to/your/images  ; 需要压缩的图片文件夹路径

output_dir =   ; 输出目录（留空则覆盖原文件）

quality = 80  ; 压缩质量 (0-100)


# 再次运行
python compress_images.py

# 高级选项
#使用命令行参数覆盖配置
python compress_images.py -i /new/input -o /new/output -q 70

#重新创建配置文件（会覆盖现有配置）
python compress_images.py --recreate-config

#不显示介绍信息
python compress_images.py --no-intro