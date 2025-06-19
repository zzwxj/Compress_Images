import os
import subprocess
import configparser
from pathlib import Path
from PIL import Image
import argparse

def compress_image(input_path, output_path, quality=80):
    """
    压缩单张图片，优先使用 pngquant（PNG）或 mozjpeg（JPEG），
    失败时回退到 Pillow。
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if input_path.suffix.lower() == '.png':
            # 尝试使用 pngquant 压缩 PNG
            if _check_pngquant_available():
                cmd = [
                    'pngquant', '--skip-if-larger', '--force',
                    '--quality', f'{max(10, quality-20)}-{quality}',
                    str(input_path), '--output', str(output_path)
                ]
                subprocess.run(cmd, check=True)
                return
            # pngquant 不可用时使用 Pillow
            img = Image.open(input_path)
            img.save(output_path, optimize=True, quality=quality)
        
        elif input_path.suffix.lower() in ('.jpg', '.jpeg'):
            # 优先尝试 mozjpeg（需安装）
            if _check_mozjpeg_available():
                cmd = [
                    'cjpeg', '-quality', str(quality), 
                    str(input_path), '>', str(output_path)
                ]
                subprocess.run(' '.join(cmd), shell=True, check=True)
            else:
                # 回退到 Pillow
                img = Image.open(input_path)
                img.save(output_path, format='JPEG', quality=quality)
    except Exception as e:
        print(f"压缩失败 {input_path}: {str(e)}")

def _check_pngquant_available() -> bool:
    """检查系统是否安装 pngquant"""
    try:
        subprocess.run(['pngquant', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def _check_mozjpeg_available() -> bool:
    """检查系统是否安装 mozjpeg（cjpeg 命令）"""
    try:
        subprocess.run(['cjpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def compress_folder(input_dir, output_dir, quality=80):
    """
    递归压缩文件夹内所有图片（支持子目录）
    :param input_dir: 输入文件夹路径
    :param output_dir: 输出文件夹路径（为空则覆盖原文件）
    :param quality: 压缩质量（0-100）
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir) if output_dir else input_dir

    for root, _, files in os.walk(input_dir):
        for file in files:
            if not file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            src = Path(root) / file
            rel_path = src.relative_to(input_dir)
            dst = output_dir / rel_path
            compress_image(src, dst, quality)

def create_default_config(config_path):
    """创建默认配置文件"""
    config = configparser.ConfigParser()
    config['DEFAULT'] = {
        'input_dir': '/path/to/your/images',  # 需要压缩的图片文件夹路径
        'output_dir': '',  # 输出目录（留空则覆盖原文件）
        'quality': '80',  # 压缩质量 (0-100)
        'skip_existing': 'no'  # 是否跳过已压缩文件 (yes/no)
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
        'quality': config['DEFAULT'].getint('quality', 80),
        'skip_existing': config['DEFAULT'].getboolean('skip_existing', False)
    }

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
        '--skip-existing', 
        action='store_true',
        default=config['skip_existing'],
        help='跳过输出目录中已存在的文件（配置文件默认值: %(default)s）'
    )
    parser.add_argument(
        '--recreate-config', 
        action='store_true',
        help='重新创建默认配置文件（会覆盖现有配置）'
    )
    
    args = parser.parse_args()
    
    # 处理重新创建配置文件的请求
    if args.recreate_config:
        create_default_config(CONFIG_PATH)
        exit(0)
    
    # 验证输入目录是否存在
    if not Path(args.input).exists():
        print(f"❌ 错误：输入目录不存在 - {args.input}")
        print("请检查配置文件或命令行参数")
        exit(1)
    
    print("=" * 50)
    print(f"📁 输入目录: {args.input}")
    print(f"💾 输出目录: {args.output if args.output else '覆盖原文件'}")
    print(f"⚙️ 压缩质量: {args.quality}")
    print(f"⏭️ 跳过已存在文件: {'是' if args.skip_existing else '否'}")
    print("=" * 50)
    print("开始压缩...")
    
    # 执行压缩
    compress_folder(args.input, args.output, args.quality)
    
    print("✅ 压缩完成！")
    print(f"输出位置: {args.output if args.output else args.input}")