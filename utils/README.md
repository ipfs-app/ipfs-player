# 视频转HLS工具 (video_to_m3u8.py)

## 功能介绍

`video_to_m3u8.py` 是一个功能强大的视频处理脚本，能够将普通视频文件转换为适用于网页播放的HLS（HTTP Live Streaming）格式。该脚本具有以下核心功能：

- **多分辨率转码**：支持将视频转换为4K、1080p、720p等多种分辨率
- **HLS切片**：将视频切分为小段的.ts文件，并生成对应的.m3u8播放列表
- **主播放列表生成**：自动创建包含所有分辨率信息的主.m3u8文件
- **视频封面提取**：从视频中提取第一帧作为封面图片
- **缩略图生成**：按照指定时间间隔生成视频缩略图，并拼接成预览图
- **元数据记录**：生成files.json文件，记录视频相关信息

## 核心文件

- **video_to_m3u8.py**：主脚本文件，包含命令行接口和视频处理流程控制
- **video_processor.py**：视频处理核心类，实现了各种具体的视频处理功能
- **requirements.txt**：项目依赖文件

## 依赖要求

- **FFmpeg**：必须安装并添加到系统环境变量中
- **Python 3.x**
- **所需Python库**：可通过requirements.txt安装

## 使用方法

### 基本用法

```bash
python video_to_m3u8.py -i <输入视频文件> -o <输出目录> -title <输出文件名前缀>
```

### 参数说明

| 参数 | 短参数 | 说明 | 默认值 | 必需 |
|------|--------|------|--------|------|
| --input | -i | 输入视频文件路径 | 无 | 是 |
| --output | -o | 输出目录 | output | 否 |
| --title | --title | 输出文件前缀，例如: ABC-123 | output | 否 |
| --resolution | -r | 输出分辨率，可选值: 4k, 1080p, 720p, all (同时输出所有分辨率) | all | 否 |
| --time | -t | 切片时长（秒） | 120 | 否 |

### 使用示例

#### 示例1：基本转换，使用所有默认参数

```bash
python video_to_m3u8.py -i input.mp4
```

#### 示例2：指定输出目录和文件名前缀

```bash
python video_to_m3u8.py -i input.mp4 -o output_dir -title my_video
```

#### 示例3：只转换特定分辨率

```bash
python video_to_m3u8.py -i input.mp4 -r 1080p 720p
```

#### 示例4：自定义切片时长

```bash
python video_to_m3u8.py -i input.mp4 -t 60
```

## 输出文件说明

执行脚本后，将在输出目录中生成以下文件（假设title为"my_video"）：

- **my_video.m3u8**：主播放列表文件，包含所有分辨率信息
- **my_video_4k.m3u8**：4K分辨率的播放列表
- **my_video_1080p.m3u8**：1080p分辨率的播放列表  
- **my_video_720p.m3u8**：720p分辨率的播放列表
- **my_video_4k_001.ts, my_video_1080p_001.ts, my_video_720p_001.ts**：视频切片文件
- **my_video.jpg**：视频封面图片
- **my_video_preview_1.jpg, my_video_preview_2.jpg, ...**：缩略图预览图
- **my_video_thumbs/**：存放原始缩略图的文件夹
- **files.json**：记录视频信息的JSON文件

## files.json 结构说明

生成的`files.json`文件包含以下信息：

```json
{
  "title": "视频标题",
  "duration": 视频时长（秒）,
  "master_m3u8": "主播放列表文件名",
  "thumbnail": "封面图片文件名",
  "preview": ["预览图文件名1", "预览图文件名2", ...],
  "preview_count": 缩略图总数,
  "resolutions": [
    {
      "name": "分辨率名称",
      "playlist": "对应的m3u8文件名"
    }
  ]
}
```

## 技术细节

- 脚本使用`VideoProcessor`类封装了所有视频处理功能
- 视频转码和切片通过调用系统的FFmpeg命令完成
- 支持自定义切片时长，默认为120秒
- 缩略图默认每5秒生成一张
- 支持中文文件名和路径

## 注意事项

1. 请确保FFmpeg已正确安装并添加到系统环境变量中
2. 视频处理可能需要较长时间，取决于视频大小和选择的分辨率
3. 转换过程中会消耗较多系统资源，请确保系统有足够的内存和CPU资源
4. 对于特别大的视频文件，建议先使用其他工具进行预处理或压缩

## 错误处理

脚本包含完善的错误处理机制，即使某个步骤失败，也会尝试完成其他可能的任务，并在最后报告成功转换的部分。如果遇到错误，请检查：

- 输入文件是否存在且格式正确
- FFmpeg是否正确安装
- 输出目录是否有写入权限
- 系统是否有足够的资源处理视频