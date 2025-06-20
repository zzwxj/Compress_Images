import os
import subprocess
import configparser
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
import argparse
import time

# ==================== 中文路径支持函数 ====================
def read_image_cv(path):
    """支持中文路径的图片读取（替代cv2.imread）"""
    return cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)

def save_image_cv(path, img):
    """支持中文路径的图片保存（替代cv2.imwrite）"""
    ext = os.path.splitext(path)[1]
    success, buffer = cv2.imencode(ext, img)
    if success:
        buffer.tofile(str(path))
    return success

# ==================== 图片压缩核心函数 ====================
def compress_image(input_path, output_path, quality=80):
    """
    压缩单张图片，支持中文路径
    优先使用 pngquant（PNG）或 mozjpeg（JPEG），失败时回退到 Pillow/OpenCV
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 检查文件是否需要重新压缩（修改时间比对）
    if output_path.exists() and input_path.stat().st_mtime <= output_path.stat().st_mtime:
        print(f"⏭️ 跳过未修改文件: {input_path}")
        return False

    print(f"🔄 压缩中: {input_path} -> {output_path}")
    
    try:
        # 处理PNG图片
        if input_path.suffix.lower() == '.png':
            return _compress_png(input_path, output_path, quality)
        
        # 处理JPEG图片
        elif input_path.suffix.lower() in ('.jpg', '.jpeg'):
            return _compress_jpeg(input_path, output_path, quality)
    
    except Exception as e:
        print(f"❌ 压缩失败: {input_path}\n错误信息: {str(e)}")
        return False

def _compress_png(input_path, output_path, quality):
    """压缩PNG图片（优先使用pngquant）"""
    if _check_pngquant_available():
        cmd = [
            'pngquant', '--skip-if-larger', '--force',
            '--quality', f'{max(10, quality-20)}-{quality}',
            str(input_path), '--output', str(output_path)
        ]
        subprocess.run(cmd, check=True)
        return True
    else:
        # 回退到Pillow
        img = Image.open(input_path)
        img.save(output_path, optimize=True, quality=quality)
        return True

def _compress_jpeg(input_path, output_path, quality):
    """压缩JPEG图片（优先使用mozjpeg）"""
    if _check_mozjpeg_available():
        cmd = [
            'cjpeg', '-quality', str(quality), 
            '-outfile', str(output_path), str(input_path)
        ]
        subprocess.run(cmd, check=True)
        return True
    else:
        # 回退到OpenCV（支持中文路径）
        img = read_image_cv(input_path)
        if img is None:
            # 如果OpenCV读取失败，使用Pillow
            img = Image.open(input_path).convert('RGB')
            img.save(output_path, format='JPEG', quality=quality)
        else:
            save_image_cv(output_path, img)
        return True

# ==================== 工具链检测函数 ====================
def _check_pngquant_available():
    """检查系统是否安装pngquant"""
    try:
        subprocess.run(['pngquant', '--version'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  未检测到 pngquant，将使用 Pillow 压缩 PNG")
        return False

def _check_mozjpeg_available():
    """检查系统是否安装mozjpeg（cjpeg命令）"""
    try:
        subprocess.run(['cjpeg', '-version'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  未检测到 mozjpeg (cjpeg)，将使用 OpenCV/Pillow 压缩 JPEG")
        return False

# ==================== 批量处理函数 ====================
def compress_folder(input_dir, output_dir, quality=80):
    """
    递归压缩文件夹内所有图片（支持子目录和中文路径）
    :param input_dir: 输入文件夹路径
    :param output_dir: 输出文件夹路径（为空则覆盖原文件）
    :param quality: 压缩质量（0-100）
    """
    input_dir = Path(input_dir)
    # 如果output_dir为空，则输出目录就是输入目录（覆盖模式）
    output_dir = Path(output_dir) if output_dir else input_dir
    
    total_files = 0
    compressed_files = 0
    skipped_files = 0
    
    start_time = time.time()
    
    for root, _, files in os.walk(input_dir):
        for file in files:
            if not file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            total_files += 1
            src = Path(root) / file
            rel_path = src.relative_to(input_dir)
            dst = output_dir / rel_path
            
            # 压缩图片（支持中文路径）
            result = compress_image(src, dst, quality)
                
            if result is True:
                compressed_files += 1
            elif result is False:
                skipped_files += 1
    
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 50)
    print(f"📊 压缩报告")
    print(f"📂 处理文件总数: {total_files}")
    print(f"🔄 压缩文件数量: {compressed_files}")
    print(f"⏭️ 跳过文件数量: {skressed_files}")
    print(f"⏱️ 总耗时: {elapsed_time:.2f}秒")
    print("=" * 50)
    
    return compressed_files, skipped_files

# ==================== 配置文件管理 ====================
def create_default_config(config_path):
    """创建默认配置文件"""
    config = configparser.ConfigParser()
    config['DEFAULT'] = {
        'input_dir': '/path/to/your/images',  # 需要压缩的图片文件夹路径
        'output_dir': '',  # 输出目录（留空则覆盖原文件）
        'quality': '80',  # 压缩质量 (0-100)
    }
    
    with open(config_path, 'w', encoding='utf-8') as configfile:
        config.write(configfile)
    
    print(f"✅ 已创建默认配置文件: {config_path}")
    print("请编辑此文件后重新运行脚本")

def load_config(config_path):
    """加载配置文件（支持中文路径）"""
    config = configparser.ConfigParser()
    # 显式指定编码为utf-8-sig以支持BOM
    config.read(config_path, encoding='utf-8-sig')
    
    return {
        'input_dir': config['DEFAULT'].get('input_dir', ''),
        'output_dir': config['DEFAULT'].get('output_dir', ''),
        'quality': config['DEFAULT'].getint('quality', 80)
    }

# ==================== 用户界面函数 ====================
def print_intro():
    """打印脚本介绍信息"""
    print("=" * 60)
    print("📸 智能图片压缩脚本 (支持中文路径)")
    print("-" * 60)
    print("功能特点:")
    print("✅ 递归处理所有子目录")
    print("✅ 自动跳过未修改的图片")
    print("✅ 支持 PNG 和 JPEG 格式")
    print("✅ 完整中文路径支持")
    print("✅ 可覆盖原文件或输出到新位置")
    print("✅ 优先使用 pngquant/mozjpeg (如已安装)")
    print("=" * 60)

# ==================== 主程序入口 ====================
if __name__ == "__main__":
    # 配置文件路径（与脚本同目录）
    CONFIG_PATH = Path(__file__).parent / 'compress_images.ini'
    
    # 如果配置文件不存在，则创建默认配置
    if not CONFIG_PATH.exists():
        create_default_config(CONFIG_PATH)
        print("\n请编辑配置文件后重新运行脚本！")
        exit(0)
    
    # 加载配置文件
    try:
        config = load_config(CONFIG_PATH)
    except Exception as e:
        print(f"❌ 配置文件加载失败: {str(e)}")
        print("请检查配置文件格式或删除后重新创建")
        exit(1)
    
    # 解析命令行参数（优先级高于配置文件）
    parser = argparse.ArgumentParser(
        description='批量压缩文件夹图片（含子目录，支持中文路径）',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-i', '--input', 
        default=config['input_dir'], 
        help='输入文件夹路径（配置文件默认值: %(default)s）'
    )
    parser.add_argument(
        '-o', '--output', 
        default=config['output_dir'], 
        help='输出文件夹路径（留空则覆盖原文件，配置文件默认值: %(default)s）'
    )
    parser.add_argument(
        '-q', '--quality', 
        type=int, 
        default=config['quality'], 
        help='压缩质量 (0-100，配置文件默认值: %(default)s)'
    )
    parser.add_argument(
        '--recreate-config', 
        action='store_true',
        help='重新创建默认配置文件（会覆盖现有配置）'
    )
    parser.add_argument(
        '--no-intro', 
        action='store_true',
        help='不显示介绍信息'
    )
    
    args = parser.parse_args()
    
    # 处理重新创建配置文件的请求
    if args.recreate_config:
        create_default_config(CONFIG_PATH)
        print("✅ 配置文件已重新创建")
        exit(0)
    
    # 验证输入目录是否存在
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 错误：输入目录不存在 - {args.input}")
        print("请检查配置文件或命令行参数")
        exit(1)
    
    # 显示介绍信息
    if not args.no_intro:
        print_intro()
    
    print("⚙️ 配置参数:")
    print(f"📁 输入目录: {args.input}")
    print(f"💾 输出目录: {args.output if args.output else '覆盖原文件'}")
    print(f"🛠️ 压缩质量: {args.quality}")
    print("=" * 50)
    print("开始压缩...\n")
    
    # 执行压缩
    try:
        compressed, skipped = compress_folder(args.input, args.output, args.quality)
        print("\n✅ 压缩完成！")
        if args.output:
            print(f"输出位置: {args.output}")
        else:
            print(f"原文件已被压缩版本覆盖")
        
        # 显示压缩结果总结
        if compressed == 0 and skipped > 0:
            print("ℹ️ 所有图片均未修改，无需重新压缩")
    except Exception as e:
        print(f"\n❌ 压缩过程中发生错误: {str(e)}")
        print("请检查输入输出路径是否有特殊字符或权限问题")