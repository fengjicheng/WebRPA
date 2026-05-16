# -*- coding: utf-8 -*-
"""
下载 easyocr 模型到项目内置目录
运行一次即可，模型会保存在 models/easyocr/model/ 下
"""
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
model_dir = os.path.join(script_dir, 'models', 'easyocr', 'model')
user_network_dir = os.path.join(script_dir, 'models', 'easyocr', 'user_network')

os.makedirs(model_dir, exist_ok=True)
os.makedirs(user_network_dir, exist_ok=True)

print(f'模型将下载到: {model_dir}')
print('开始初始化 easyocr Reader（会自动下载所需模型）...')
print('需要下载约 200MB，请耐心等待...')

try:
    import easyocr
    reader = easyocr.Reader(
        ['ch_sim', 'en'],
        gpu=False,
        model_storage_directory=model_dir,
        user_network_directory=user_network_dir,
        download_enabled=True,
        verbose=True
    )
    print('\n模型下载完成！')
    print(f'模型文件列表:')
    for f in os.listdir(model_dir):
        size = os.path.getsize(os.path.join(model_dir, f))
        print(f'  {f}  ({size/1024/1024:.1f} MB)')
except Exception as e:
    print(f'下载失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
