import os
import logging
import warnings
import multiprocessing

warnings.filterwarnings("ignore")
logging.getLogger("httpx").setLevel(logging.WARNING)

# 设置DeepSeek和硅基流动的API密钥（请替换为你的实际密钥）
os.environ["DEEPSEEK_API_KEY"] = "your-deepseek-api-key"
os.environ["SILICONFLOW_API_KEY"] = "your-siliconflow-api-key"
os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"

from videorag._llm import deepseek_bge_config
from videorag import VideoRAG, QueryParam
from videorag._llm import ollama_config

if __name__ == '__main__':
    # 必须的设置
    multiprocessing.set_start_method('spawn')

    # 将你的视频文件路径放入这个列表中
    video_paths = [
        '/home/gjw/output.mp4',
    ]
    
    # 初始化 VideoRAG，指定一个工作目录来存放索引文件
    videorag = VideoRAG(llm=ollama_config, working_dir=f"./videorag-workdir1")
    
    # 开始处理视频
    videorag.insert_video(video_path_list=video_paths)