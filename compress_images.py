import os
import subprocess
import configparser
from pathlib import Path
from PIL import Image
import argparse
import time

def compress_image(input_path, output_path, quality=80):
    """
    压缩单张图片，优先使用 pngquant（PNG）或 mozjpeg（JPEG），
    失败时回退到 Pillow。
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 检查是否需要压缩（源文件是否比压缩文件新）
        if output_path.exists() and input_path.stat().st_mtime <= output_path.stat().st_mtime:
            print(f"⏭️ 跳过未修改图片: {input_path}")
            return False

        print(f"🔄 正在压缩: {input_path}")

        if input_path.suffix.lower() == '.png':
            # 尝试使用 pngquant 压缩 PNG
            if _check_pngquant_available():
                cmd = [
                    'pngquant', '--skip-if-larger', '--force',
                    '--quality', f'{max(10, quality-20)}-{quality}',
                    str(input_path), '--output', str(output_path)
                ]
                subprocess.run(cmd, check=True)
                return True
            # pngquant 不可用时使用 Pillow
            img = Image.open(input_path)
            img.save(output_path, optimize=True, quality=quality)
            return True
        
        elif input_path.suffix.lower() in ('.jpg', '.jpeg'):
            # 优先尝试 mozjpeg（需安装）
            if _check_mozjpeg_available():
                temp_output = output_path.with_suffix('.temp' + output_path.suffix)
                cmd = [
                    'cjpeg', '-quality', str(quality), 
                    str(input_path), '-outfile', str(temp_output)
                ]
                subprocess.run(cmd, check=True)
                
                # 移动临时文件到目标位置
                temp_output.replace(output_path)
                return True
            else:
                # 回退到 Pillow
                img = Image.open(input_path)
                img.save(output_path, format='JPEG', quality=quality)
                return True
    except Exception as e:
        print(f"❌ 压缩失败 {input_path}: {str(e)}")
        return False
    return False

def _check_pngquant_available() -> bool:
    """检查系统是否安装 pngquant"""
    try:
        subprocess.run(['pngquant', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  pngquant 不可用，将使用 Pillow 处理 PNG 图片")
        return False

def _check_mozjpeg_available() -> bool:
    """检查系统是否安装 mozjpeg（cjpeg 命令）"""
    try:
        subprocess.run(['cjpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  mozjpeg (cjpeg) 不可用，将使用 Pillow 处理 JPEG 图片")
        return False

def compress_folder(input_dir, output_dir, quality=80):
    """
    递归压缩文件夹内所有图片（支持子目录）
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
            
            # 如果是覆盖模式且源文件与目标文件相同，则跳过修改检查
            if output_dir == input_dir and src == dst:
                # 对于覆盖模式，我们总是压缩（但内部会检查修改时间）
                result = compress_image(src, dst, quality)
            else:
                # 对于新位置输出，检查是否需要压缩
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
    print(f"⏭️ 跳过文件数量: {skipped_files}")
    print(f"⏱️ 总耗时: {elapsed_time:.2f}秒")
    print("=" * 50)
    
    return compressed_files, skipped_files

def create_default_config(config_path):
    """创建默认配置文件"""
    config = configparser.ConfigParser()
    config['DEFAULT'] = {
        'input_dir': '/path/to/your/images',  # 需要压缩的图片文件夹路径
        'output_dir': '',  # 输出目录（留空则覆盖原文件）
        'quality': '80',  # 压缩质量 (0-100)
    }
    
    with open(config_path, 'w') as configfile:
        config.write(configfile)
    
    print(f"✅ 已创建默认配置文件: {config_path}")
    print("请编辑此文件后重新运行脚本")

def load_config(config_path):
    """加载配置文件"""
    config = configparser.ConfigParser()
    config.read(config_path)
    
    return {
        'input_dir': config['DEFAULT'].get('input_dir', ''),
        'output_dir': config['DEFAULT'].get('output_dir', ''),
        'quality': config['DEFAULT'].getint('quality', 80)
    }

def print_intro():
    """打印脚本介绍信息"""
    print("=" * 60)
    print("📸 智能图片压缩脚本")
    print("-" * 60)
    print("功能特点:")
    print("✅ 递归处理所有子目录")
    print("✅ 自动跳过未修改的图片")
    print("✅ 支持 PNG 和 JPEG 格式")
    print("✅ 可覆盖原文件或输出到新位置")
    print("✅ 优先使用 pngquant/mozjpeg (如已安装)")
    print("=" * 60)

if __name__ == "__main__":
    # 配置文件路径（与脚本同目录）
    CONFIG_PATH = Path(__file__).parent / 'compress_images.ini'
    
    # 如果配置文件不存在，则创建默认配置
    if not CONFIG_PATH.exists():
        create_default_config(CONFIG_PATH)
        exit(0)
    
    # 加载配置文件
    config = load_config(CONFIG_PATH)
    
    # 解析命令行参数（优先级高于配置文件）
    parser = argparse.ArgumentParser(
        description='批量压缩文件夹图片（含子目录）',
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
    compressed, skipped = compress_folder(args.input, args.output, args.quality)
    
    print("\n✅ 压缩完成！")
    if args.output:
        print(f"输出位置: {args.output}")
    else:
        print(f"原文件已被压缩版本覆盖")
    
    # 显示压缩结果总结
    if compressed == 0 and skipped > 0:
        print("ℹ️ 所有图片均未修改，无需重新压缩")