#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频转m3u8切片脚本
功能：将输入视频转换为m3u8格式，支持多分辨率，生成视频封面，以及生成缩略图预览
依赖：需要安装FFmpeg并添加到系统环境变量
"""

import os
import sys
import argparse
from pathlib import Path
import re
from turtle import title
# 导入VideoProcessor工具类
from video_processor import VideoProcessor

# ================== 配置常量 ==================
# TS切片配置
DEFAULT_SEGMENT_TIME = 120  # 默认切片时长（秒）

# 缩略图配置
THUMBNAIL_INTERVAL = 5    # 默认缩略图截取间隔（秒）
THUMBNAIL_COVER_TIME = 5  # 默认封面图时间点（秒）
# =============================================


def main():
    """
    主函数，处理命令行参数并调用VideoProcessor执行视频处理任务
    """
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='视频转m3u8格式工具')
    parser.add_argument('-i', '--input', required=True, help='输入视频文件路径')
    parser.add_argument('-o', '--output', default='output', help='输出目录，默认: output')
    parser.add_argument('-r', '--resolution', nargs='+', default=['all'], choices=['4k', '1080p', '720p', 'all'],
                        help='输出分辨率，可选: 4k, 1080p, 720p, all (同时输出所有分辨率)，默认: all。支持多选，例如：-r 1080p 720p')
    parser.add_argument('-t', '--time', type=int, default=DEFAULT_SEGMENT_TIME, help=f'切片时长（秒），默认: {DEFAULT_SEGMENT_TIME}')
    parser.add_argument('-title', '--title', default='output', help='输出文件前缀，例如: ABC-123')
    
    args = parser.parse_args()
    
    # 快速检查输入文件是否存在
    if not os.path.isfile(args.input):
        print(f"❌ 错误：输入文件不存在 - {args.input}")
        sys.exit(1)
    
    # 创建输出目录
    Path(args.output).mkdir(parents=True, exist_ok=True)
    print(f"📁 输出目录已创建：{args.output}")
    
    # 创建VideoProcessor实例
    try:
        processor = VideoProcessor()
        print("✅ VideoProcessor初始化成功")
    except Exception as e:
        print(f"❌ VideoProcessor初始化失败: {e}")
        sys.exit(1)
    
    print(f"\n📋 开始转换，分辨率模式: {args.resolution}")
    print(f"⏱️  切片时长: {args.time}秒")
    
    # 处理分辨率参数
    use_all_resolutions = 'all' in args.resolution
    
    # 执行视频处理任务
    resolutions_done = []
    
    try:
        # 1. 转换并切片视频
        if use_all_resolutions:
            # 使用所有分辨率
            resolutions = ["4k", "1080p", "720p"]
        else:
            # 使用指定的分辨率
            resolutions = args.resolution
        
        print(f"🔄 开始转换视频为 {', '.join(resolutions)} 分辨率...")
        transcode_result = processor.convert_and_slice(
            input_file=args.input,
            output_dir=args.output,
            title=args.title,
            resolutions=resolutions,
            segment_time=args.time
        )
        # 检查转换结果
        if transcode_result:
            resolutions_done = list(transcode_result.keys())
            print(f"✅ 成功转换的分辨率: {', '.join(resolutions_done)}")
            # 移动文件source_file路径移动到m3u8_path
            for res in resolutions_done:
                source_file = transcode_result[res]['source_file']
                m3u8_path = transcode_result[res]['m3u8_path']
                # 在新位置生成m3u8，内容是ts文件替换后的内容
                print(f"🔄 处理m3u8文件: {source_file} -> {m3u8_path}")
                
                # 读取源m3u8文件并准备修改后的内容
                modified_lines = []
                with open(source_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        match = re.search(r's(\d{3,})\.ts', line)
                        if match:
                            ts_file = f"{args.title}_{res}_{match.group(1)}.ts"
                            source_ts_path = os.path.join(os.path.dirname(source_file), match.group(0))
                            target_ts_path = os.path.join(os.path.dirname(m3u8_path), os.path.basename(ts_file))
                            
                            # 移动ts文件到目标目录
                            if os.path.exists(source_ts_path):
                                os.rename(source_ts_path, target_ts_path)
                                print(f"✅ 移动文件 {match.group(0)} 到 {os.path.basename(ts_file)}")
                            else:
                                print(f"⚠️  文件不存在: {source_ts_path}")
                            
                            # 替换m3u8文件中的ts文件名
                            line = line.replace(match.group(0), os.path.basename(ts_file))
                        modified_lines.append(line)
                
                # 写入修改后的内容到新的m3u8文件
                with open(m3u8_path, 'w') as f:
                    f.writelines(modified_lines)
                print(f"✅ 已在新位置生成m3u8文件: {m3u8_path}")
        else:
            print("❌ 视频转换失败")
            # sys.exit(1)
        
        # 2. 创建主m3u8播放列表
        if resolutions_done:
            print("🔄 创建主m3u8播放列表...")
            master_path = processor.create_master_playlist(
                output_dir=args.output,
                title=args.title,
                input_file=args.input
            )
            if master_path:
                print(f"✅ 主m3u8播放列表已创建: {master_path}")
        
        # 3. 提取视频封面
        print("🔄 提取视频封面...")
        cover_path = processor.extract_cover(
            input_file=args.input,
            output_path=os.path.join(args.output, f"{args.title}.jpg"),
            time_seconds=THUMBNAIL_COVER_TIME
        )
        if cover_path:
            print(f"✅ 视频封面已提取: {cover_path}")
        
        # 4. 生成缩略图预览
        print("🔄 生成缩略图预览...")
        preview_result = processor.generate_and_stitch_thumbnails(
            input_file=args.input,
            output_dir=args.output,
            title=args.title,
            interval=THUMBNAIL_INTERVAL,
            cols=10,rows=10
        )
        preview_paths = preview_result[0]  # 获取预览图路径数组
        if preview_paths:
            print(f"✅ 缩略图预览已生成: 共{len(preview_paths)}张图片")
            for i, path in enumerate(preview_paths, 1):
                print(f"  - 预览图{i}: {path}")
        
        # 5. 生成files.json文件（可选，如果需要保持与原脚本兼容）
        # 注意：VideoProcessor类中没有直接生成files.json的方法，但可以在这里实现
        print("🔄 生成files.json文件...")
        generate_compatibility_json(args.input, args.output, cover_path, preview_paths, args.title, resolutions_done)
        
    except Exception as e:
        print(f"❌ 处理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        
        # 即使发生错误，仍然尝试报告成功的分辨率
        if resolutions_done:
            print(f"\n⚠️  部分转换成功，已处理的分辨率: {', '.join(resolutions_done)}")
        else:
            print("❌ 所有转换任务失败，请检查错误信息")
            sys.exit(1)
    
    print("\n📊 转换结果汇总:")
    print(f"✅ 成功转换的分辨率: {', '.join(resolutions_done) if resolutions_done else '无'}")
    
    if resolutions_done:
        print("\n🎉 部分或全部转换任务完成！")
        print(f"📂 输出文件位于：{os.path.abspath(args.output)}")
        # 列出生成的文件
        print("\n📋 生成的文件:")
        try:
            all_files = [f for f in os.listdir(args.output) if os.path.isfile(os.path.join(args.output, f))]
            
            # 定义优先文件列表
            priority_order = [f"{args.title}.m3u8", f"{args.title}.jpg", "files.json"]
            for res in resolutions_done:
                priority_order.append(f"{args.title}_{res}.m3u8")
            
            # 排序并输出文件信息
            file_priority = {file: priority_order.index(file) if file in priority_order else float('inf') for file in all_files}
            sorted_files = sorted(all_files, key=lambda f: file_priority[f])
            
            for file in sorted_files:
                file_path = os.path.join(args.output, file)
                size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                print(f"   - {file} ({size:.2f} MB)")
        except Exception as e:
            print(f"⚠️  无法列出文件信息: {e}")
    
    return 0


def generate_compatibility_json(input_file, output_dir, thumbnail_path, preview_paths, title, resolutions_done):
    """
    生成files.json文件以保持与原脚本的兼容性
    """
    import json
    import subprocess
    
    json_path = os.path.join(output_dir, "files.json")
    
    # 获取视频时长
    duration = 0
    try:
        cmd_duration = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "format=duration",
            "-of", "json",
            input_file
        ]
        result_duration = subprocess.run(cmd_duration, capture_output=True, text=True)
        if result_duration.returncode == 0:
            duration_data = json.loads(result_duration.stdout)
            duration = float(duration_data['format']['duration'])
    except Exception:
        pass
    
    # 构建JSON数据
    master_m3u8_path = f"{title}.m3u8"
    master_m3u8_exists = os.path.exists(os.path.join(output_dir, master_m3u8_path))
    
    video_info = {
        "title": title,
        "duration": duration,
        "master_m3u8": master_m3u8_path if master_m3u8_exists else None,
        "thumbnail": f"{title}.jpg" if os.path.exists(os.path.join(output_dir, f"{title}.jpg")) else None,
        "preview": [os.path.basename(path) for path in preview_paths if path and os.path.exists(path)] if preview_paths else None,
        "preview_count": len([f for f in os.listdir(os.path.join(output_dir, f"{title}_thumbs")) if f.endswith('.jpg')]) if os.path.exists(os.path.join(output_dir, f"{title}_thumbs")) else 0
    }
    
    # 添加所有分辨率的m3u8文件路径
    video_info["resolutions"] = []
    for res in resolutions_done:
        m3u8_path = os.path.join(output_dir, f"{title}_{res}.m3u8")
        if os.path.exists(m3u8_path):
            video_info["resolutions"].append({
                "name": res,
                "playlist": f"{title}_{res}.m3u8"
            })
    
    # 写入JSON文件
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(video_info, f, ensure_ascii=False, indent=2)
        print(f"✅ files.json已生成: {json_path}")
        return json_path
    except Exception as e:
        print(f"❌ 生成files.json失败: {e}")
        return None


if __name__ == "__main__":
    sys.exit(main())