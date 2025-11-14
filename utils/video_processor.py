import os
from re import M
import subprocess
import json
import asyncio
from PIL import Image
from typing import List, Dict, Optional, Any

class VideoProcessor:
    """
    视频处理工具类，提供独立的视频处理功能模块
    """
    
    def __init__(self):
        """
        初始化VideoProcessor类
        """
        # 检查ffmpeg是否已安装
        if not self._check_ffmpeg():
            raise RuntimeError("ffmpeg未安装，请先安装ffmpeg工具包")
    
    def _check_ffmpeg(self) -> bool:
        """
        检查ffmpeg是否已安装
        
        Returns:
            bool: ffmpeg是否已安装
        """
        try:
            subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def create_output_directory(self, directory: str) -> None:
        """
        创建输出目录
        
        Args:
            directory: 目录路径
        """
        os.makedirs(directory, exist_ok=True)
    
    def convert_and_slice(self, input_file: str, output_dir: str, title: str = "output", 
                         resolutions: Optional[List[str]] = None, segment_time: int = 10) -> Dict[str, Dict[str, str]]:
        """
        将视频按指定分辨率转码并切片，在单次运行中完成多个分辨率的转换
        
        Args:
            input_file: 输入视频文件路径
            output_dir: 输出目录
            title: 输出文件前缀
            resolutions: 分辨率列表，默认使用['1080p']
            segment_time: 切片时长（秒）
            
        Returns:
            dict: 包含每个分辨率的输出文件路径
        """
        # 检查输入文件是否存在
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"输入文件不存在: {input_file}")
        
        # 确保输出目录存在
        self.create_output_directory(output_dir)
        
        # 默认分辨率
        if resolutions is None:
            resolutions = ['1080p']
        
        # 分辨率配置
        resolution_config = {
            '4k': {'width': 3840, 'height': 2160},
            '1080p': {'width': 1920, 'height': 1080},
            '720p': {'width': 1280, 'height': 720}
        }
        
        # 验证所有指定的分辨率是否支持
        for res in resolutions:
            if res not in resolution_config:
                raise ValueError(f"不支持的分辨率: {res}")
        
        # 统一使用单次多分辨率处理方式 - 使用更简单的参数结构
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-y',  # 覆盖现有文件
            '-sc_threshold', '0',
            '-force_key_frames', f'\"expr:gte(t,n_forced*{segment_time})\"',
            '-g', str(int(segment_time * 2))
        ]
        map = []
        # 为每个分辨率添加视频和音频流处理参数
        for idx, res in enumerate[str](resolutions):
            map.append(f"v:{idx},a:{idx}")
            config = resolution_config[res]
            output_file = os.path.join(output_dir, f"{title}_{res}")
            
            # 添加流映射（每个分辨率都需要视频和音频流）
            cmd.extend(['-map', '0:v:0'])
            cmd.extend(['-map', '0:a:0'])
            # 设置视频编码器参数
            cmd.extend([f'-c:v:{idx}', 'libx264'])
            cmd.extend([f'-filter:v:{idx}', f'scale={config["width"]}:{config["height"]}'])
        cmd.extend([
            "-c:a", "aac",
            "-f", "hls",
            "-var_stream_map", f'"{" ".join(map)}"',
            "-hls_time", str(segment_time),
            "-hls_playlist_type", "vod",
            "-hls_list_size", "0",
            "-hls_segment_filename", "temp_%v/s%03d.ts" ,
            "temp_%v/playlist.m3u8" 
        ])
            
        # 添加输出参数 - 使用更简单的结构
        results = {}
        for idx, res in enumerate(resolutions):
            output_file = os.path.join(output_dir, f"{title}_{res}")
            # 记录结果
            results[res] = {
                'm3u8_path': f'{output_file}.m3u8',
                'source_file': f"temp_{idx}/playlist.m3u8" ,
                'segment_pattern': f'{output_file}_%03d.ts'
            }
        
        # 执行单次命令处理所有分辨率
        try:
            print(f"执行ffmpeg命令处理{len(resolutions)}个分辨率...")
            subprocess.run(
                " ".join(cmd),
                check=True,
                capture_output=True,
                text=True,
                shell=False
            )
            print(f"✅ 成功完成{len(resolutions)}个分辨率的转码和切片")
            return results
        except subprocess.CalledProcessError as e:
            print(f"ffmpeg错误输出: {e.stderr}")
            raise RuntimeError(f"ffmpeg命令执行失败: {e}")
        except Exception as e:
            raise RuntimeError(f"转码失败: {e}")
    
    def extract_cover(self, input_file: str, output_path: str, time_seconds: float = 0.0) -> str:
        """
        提取视频指定秒数的封面
        
        Args:
            input_file: 输入视频文件路径
            output_path: 输出封面图片路径
            time_seconds: 提取封面的时间点（秒）
            
        Returns:
            str: 输出封面图片路径
        """
        # 检查输入文件是否存在
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"输入文件不存在: {input_file}")
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            self.create_output_directory(output_dir)
        
        # 构建ffmpeg命令
        cmd = [
            'ffmpeg',
            '-ss', str(time_seconds),
            '-i', input_file,
            '-vframes', '1',
            '-q:v', '2',  # 高质量
            output_path
        ]
        
        # 执行命令
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                shell=False
            )
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg命令执行失败: {e}")
        except Exception as e:
            raise RuntimeError(f"提取封面失败: {e}")
    
    def generate_and_stitch_thumbnails(self, input_file: str, output_dir: str, title: str = "output",
                                     interval: int = 5, cols: int = 5, rows: int = 2,
                                     thumb_width: int = 160, thumb_height: int = 90) -> tuple[str, int]:
        """
        生成缩略图并拼接成预览图
        
        Args:
            input_file: 输入视频文件路径
            output_dir: 输出目录
            title: 输出文件前缀
            interval: 缩略图间隔（秒）
            thumb_count: 生成的缩略图数量
            cols: 拼接图的列数
            rows: 拼接图的行数
            thumb_width: 单个缩略图的宽度
            thumb_height: 单个缩略图的高度（0表示按比例）
            
        Returns:
            tuple[str, int]: (输出预览图路径, 实际拼接的缩略图数量)
        """
        # 检查输入文件是否存在
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"输入文件不存在: {input_file}")
        
        # 确保输出目录存在
        self.create_output_directory(output_dir)
        
        # 临时缩略图目录
        thumb_dir = os.path.join(output_dir, f"{title}_thumbs")
        self.create_output_directory(thumb_dir)
        
        # 获取视频时长
        duration = self._get_video_duration(input_file)
        
        # 实际间隔就是输入的interval
        actual_interval = interval
        # 根据视频时长和间隔计算实际生成的缩略图数量
        max_possible_count = int(duration / interval) + 1
        
        # 生成缩略图
        thumb_files = []
        for i in range(max_possible_count):
            time_point = (i + 1) * actual_interval
            thumb_file = os.path.join(thumb_dir, f"thumb_{i:03d}.jpg")
            
            # 构建ffmpeg命令
            cmd = [
                'ffmpeg',
                '-ss', str(time_point),
                '-i', input_file,
                '-vframes', '1',
                '-q:v', '2',
                '-vf', f'scale={thumb_width}:{thumb_height if thumb_height > 0 else "-1"}',  # 根据参数设置缩略图尺寸
                thumb_file
            ]
            
            try:
                subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    shell=False
                )
                if os.path.exists(thumb_file):
                    thumb_files.append(thumb_file)
            except:
                # 忽略单个缩略图生成失败
                continue
        
        # 拼接缩略图
        if not thumb_files:
            raise RuntimeError("无法生成任何缩略图")
        
        # 计算每个拼图能容纳的最大缩略图数量
        max_thumbs_per_image = cols * rows
        # 计算需要创建的拼图数量
        num_images = (len(thumb_files) + max_thumbs_per_image - 1) // max_thumbs_per_image
        
        preview_paths = []
        
        # 生成每个拼图
        for img_idx in range(num_images):
            # 计算当前拼图包含的缩略图范围
            start_idx = img_idx * max_thumbs_per_image
            end_idx = min(start_idx + max_thumbs_per_image, len(thumb_files))
            current_thumbs = thumb_files[start_idx:end_idx]
            
            # 计算实际需要的行数
            # 如果当前拼图中的缩略图数量不足预设行数，按实际行数设置
            actual_rows = (len(current_thumbs) + cols - 1) // cols
            
            # 计算实际需要的列数
            # 如果当前拼图中的缩略图数量不足一行，按实际列数设置
            actual_cols = min(len(current_thumbs), cols)
            if actual_rows == 1:  # 如果只有一行，使用实际列数
                result_width = actual_cols * thumb_width
            else:
                result_width = cols * thumb_width
                
            result_height = actual_rows * thumb_height
            result_img = Image.new('RGB', (result_width, result_height), (0, 0, 0))
            
            # 粘贴缩略图
            for idx, thumb_file in enumerate(current_thumbs):
                try:
                    img = Image.open(thumb_file)
                    x = (idx % cols) * thumb_width
                    y = (idx // cols) * thumb_height
                    result_img.paste(img, (x, y))
                    img.close()
                except:
                    # 忽略单个缩略图粘贴失败
                    continue
            
            # 保存结果
            if num_images > 1:
                # 如果有多个拼图，添加序号
                preview_path = os.path.join(output_dir, f"{title}_preview_{img_idx + 1}.jpg")
            else:
                # 只有一个拼图时保持原命名
                preview_path = os.path.join(output_dir, f"{title}_preview.jpg")
            
            result_img.save(preview_path)
            result_img.close()
            preview_paths.append(preview_path)
        
        # 返回所有拼图路径和实际拼接的缩略图数量
        return preview_paths, len(thumb_files)
    
    def _get_video_duration(self, input_file: str) -> float:
        """
        获取视频时长
        
        Args:
            input_file: 视频文件路径
            
        Returns:
            float: 视频时长（秒）
        """
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            input_file
        ]
        
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            data = json.loads(result.stdout)
            return float(data['format']['duration'])
        except:
            return 0.0
    
    def create_master_playlist(self, output_dir: str, title: str = "output",
                             resolutions: Optional[List[str]] = None, input_file: str = None) -> str:
        """
        创建主m3u8播放列表文件
        
        Args:
            output_dir: 输出目录
            title: 输出文件前缀
            resolutions: 分辨率列表，默认使用所有可用分辨率
            input_file: 输入视频文件路径，用于获取视频持续时间
            
        Returns:
            str: 主m3u8文件路径
        """
        # 分辨率配置
        resolution_info = {
            "4k": {"width": 3840, "height": 2160},
            "1080p": {"width": 1920, "height": 1080},
            "720p": {"width": 1280, "height": 720}
        }
        
        # 列出所有文件
        try:
            all_files = os.listdir(output_dir)
        except Exception as e:
            raise RuntimeError(f"无法读取输出目录: {e}")
        
        # 如果没有指定分辨率，使用所有可用的分辨率
        if resolutions is None:
            resolutions = [res for res in ["4k", "1080p", "720p"] 
                          if f"{title}_{res}.m3u8" in all_files]
        
        # 获取源文件持续时间（如果提供了源文件路径）
        total_duration = 0.0
        if input_file and os.path.exists(input_file):
            total_duration = self._get_video_duration(input_file)
        
        # 创建主m3u8内容
        master_content_lines = []
        master_content_lines.append("#EXTM3U")
        master_content_lines.append("#EXT-X-VERSION:3")
        
        # 按分辨率从高到低排序添加
        for res in ["4k", "1080p", "720p"]:
            if res in resolutions and f"{title}_{res}.m3u8" in all_files:
                # 查找当前分辨率的所有TS切片文件
                ts_files = [f for f in all_files 
                          if f.startswith(f"{title}_{res}_") and f.endswith(".ts")]
                print(f"{res} TS文件: {ts_files}")
                
                if ts_files and total_duration > 0:
                    # 计算所有TS文件的总大小
                    total_size_bytes = 0
                    for ts_file in ts_files:
                        ts_path = os.path.join(output_dir, ts_file)
                        if os.path.exists(ts_path):
                            total_size_bytes += os.path.getsize(ts_path)
                    
                    # 使用总大小和源文件持续时间计算码率
                    if total_size_bytes > 0:
                        bitrate = int((total_size_bytes * 8) / total_duration)
                        print(f"{res} 计算的码率: {bitrate} bps")
                    else:
                        bitrate = 1000000  # 默认码率
                else:
                    # 使用默认码率
                    bitrate = 1000000
                
                # 添加流信息
                width = resolution_info[res]["width"]
                height = resolution_info[res]["height"]
                master_content_lines.append(f"#EXT-X-STREAM-INF:BANDWIDTH={bitrate},RESOLUTION={width}x{height}")
                master_content_lines.append(f"{title}_{res}.m3u8")
        
        # 组合成最终的m3u8内容
        master_content_str = "\n".join(master_content_lines)
        
        # 写入master.m3u8文件
        master_file_path = os.path.join(output_dir, f"{title}.m3u8")
        try:
            with open(master_file_path, 'w', encoding='utf-8') as f:
                f.write(master_content_str)
        except Exception as e:
            raise RuntimeError(f"写入主m3u8文件失败: {e}")
        
        return master_file_path
    
    def _get_video_bitrate(self, file_path: str) -> int:
        """
        获取视频文件的码率（通过文件大小和持续时间计算）
        
        Args:
            file_path: 视频文件路径
            
        Returns:
            int: 视频码率（bps）
        """
        try:
            # 获取文件大小（字节）
            file_size = os.path.getsize(file_path)
            
            # 使用ffprobe获取视频持续时间
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                try:
                    # 解析JSON输出获取持续时间
                    data = json.loads(result.stdout)
                    if 'format' in data and 'duration' in data['format']:
                        duration = float(data['format']['duration'])
                        
                        if duration > 0:
                            # 计算码率 = 文件大小(字节) * 8 / 持续时间(秒)（单位：bps）
                            bitrate = int((file_size * 8) / duration)
                            return bitrate
                except (json.JSONDecodeError, ValueError):
                    pass
        except Exception as e:
            print(f"计算码率时出错: {e}")
        
        # 默认码率
        return 1000000

class AsyncVideoProcessor:
    """
    异步视频处理工具类，提供异步版本的视频处理功能
    """
    
    def __init__(self):
        """
        初始化AsyncVideoProcessor类
        """
        # 创建同步处理器实例
        self.processor = VideoProcessor()
    
    async def convert_and_slice_async(self, input_file: str, output_dir: str, title: str = "output",
                                     resolutions: Optional[List[str]] = None) -> Dict[str, Dict[str, str]]:
        """
        异步将视频按指定分辨率转码并切片
        
        Args:
            input_file: 输入视频文件路径
            output_dir: 输出目录
            title: 输出文件前缀
            resolutions: 分辨率列表
            
        Returns:
            dict: 包含每个分辨率的输出文件路径
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.processor.convert_and_slice,
            input_file,
            output_dir,
            title,
            resolutions
        )
    
    async def extract_cover_async(self, input_file: str, output_path: str, time_seconds: float = 0.0) -> str:
        """
        异步提取视频指定秒数的封面
        
        Args:
            input_file: 输入视频文件路径
            output_path: 输出封面图片路径
            time_seconds: 提取封面的时间点（秒）
            
        Returns:
            str: 输出封面图片路径
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.processor.extract_cover,
            input_file,
            output_path,
            time_seconds
        )
    
    async def generate_and_stitch_thumbnails_async(self, input_file: str, output_dir: str, title: str = "output",
                                                 interval: int = 5, thumb_count: int = 10) -> str:
        """
        异步生成缩略图并拼接成预览图
        
        Args:
            input_file: 输入视频文件路径
            output_dir: 输出目录
            title: 输出文件前缀
            interval: 缩略图间隔（秒）
            thumb_count: 生成的缩略图数量
            
        Returns:
            str: 输出预览图路径
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.processor.generate_and_stitch_thumbnails,
            input_file,
            output_dir,
            title,
            interval,
            thumb_count
        )
    
    async def get_video_info_async(self, uri: str) -> Dict[str, Any]:
        """
        异步获取视频信息
        
        Args:
            uri: 视频文件路径
            
        Returns:
            dict: 视频信息字典
        """
        # 初始化文件信息字典
        file_info = {
            "uri": uri,
            "file_exists": False,
            "file_size": None,
            "file_type": None,
            "is_video": False,
            "video_info": None
        }
        
        # 检查文件是否存在
        if os.path.isfile(uri):
            file_info["file_exists"] = True
            file_info["file_size"] = os.path.getsize(uri)
            file_info["file_type"] = os.path.splitext(uri)[1].lower()
            
            # 检查是否为视频文件
            video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']
            if file_info["file_type"] in video_extensions:
                file_info["is_video"] = True
                
                # 使用ffprobe获取视频元数据
                try:
                    # 构建ffprobe命令
                    cmd = [
                        "ffprobe",
                        "-v", "quiet",
                        "-print_format", "json",
                        "-show_format",
                        "-show_streams",
                        uri
                    ]
                    
                    # 在异步环境中执行子进程
                    proc = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    stdout, stderr = await proc.communicate()
                    
                    if proc.returncode == 0:
                        # 解析JSON输出
                        metadata = json.loads(stdout.decode('utf-8', errors='ignore'))
                        
                        # 初始化视频信息字典
                        video_info = {
                            "resolution": None,
                            "width": None,
                            "height": None,
                            "frame_rate": None,
                            "duration": None,
                            "bit_rate": None
                        }
                        
                        # 提取视频流信息
                        for stream in metadata.get("streams", []):
                            if stream.get("codec_type") == "video":
                                # 提取分辨率
                                if "width" in stream and "height" in stream:
                                    video_info["width"] = stream["width"]
                                    video_info["height"] = stream["height"]
                                    video_info["resolution"] = f"{stream['width']}x{stream['height']}"
                                
                                # 提取帧率
                                if "r_frame_rate" in stream:
                                    # 处理分数形式的帧率 (如 30/1)
                                    try:
                                        num, den = stream["r_frame_rate"].split("/")
                                        frame_rate = float(num) / float(den)
                                        video_info["frame_rate"] = round(frame_rate, 2)
                                    except:
                                        video_info["frame_rate"] = stream["r_frame_rate"]
                        
                        # 提取格式信息
                        format_info = metadata.get("format", {})
                        
                        # 提取时长
                        if "duration" in format_info:
                            try:
                                duration = float(format_info["duration"])
                                video_info["duration"] = round(duration, 2)
                            except:
                                video_info["duration"] = format_info["duration"]
                        
                        # 提取码率
                        if "bit_rate" in format_info:
                            try:
                                bit_rate = int(format_info["bit_rate"])
                                video_info["bit_rate"] = round(bit_rate / 1000, 2)  # 转换为kbps
                            except:
                                video_info["bit_rate"] = format_info["bit_rate"]
                        
                        file_info["video_info"] = video_info
                    else:
                        # ffprobe执行失败
                        file_info["video_info"] = {
                            "error": "无法提取视频元数据，请确保已安装ffmpeg工具包"
                        }
                        file_info["is_video"] = False
                except Exception as e:
                    # 捕获其他可能的异常
                    file_info["video_info"] = {
                        "error": f"提取视频信息时出错: {str(e)}"
                    }
                    file_info["is_video"] = False
        
        return file_info