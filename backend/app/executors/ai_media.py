"""AI生图、生视频模块执行器"""
import json
import time
from typing import Any, Optional
from app.executors.base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor


@register_executor
class AIGenerateImageExecutor(ModuleExecutor):
    """AI生图执行器"""
    
    @property
    def module_type(self) -> str:
        return "ai_generate_image"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """使用AI生成图片"""
        try:
            import httpx
            import base64
            from pathlib import Path
            
            provider = config.get('provider', 'openai')  # openai, stability, midjourney
            prompt = context.resolve_value(config.get('prompt', ''))
            negative_prompt = context.resolve_value(config.get('negativePrompt', ''))
            size = config.get('size', '1024x1024')  # 图片尺寸
            quality = config.get('quality', 'standard')  # standard, hd
            style = config.get('style', 'vivid')  # vivid, natural
            n = int(config.get('n', 1))  # 生成数量
            save_path = context.resolve_value(config.get('savePath', ''))
            variable_name = config.get('variableName', 'ai_image_urls')
            
            if not prompt:
                return ModuleResult(
                    success=False,
                    message="提示词不能为空",
                    error="提示词为空"
                )
            
            # 根据不同的提供商调用不同的API
            if provider == 'openai':
                # OpenAI DALL-E API
                api_key = context.resolve_value(config.get('apiKey', ''))
                api_base = context.resolve_value(config.get('apiBase', 'https://api.openai.com/v1'))
                model = config.get('model', 'dall-e-3')
                
                if not api_key:
                    return ModuleResult(
                        success=False,
                        message="API Key不能为空",
                        error="API Key为空"
                    )
                
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{api_base}/images/generations",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model,
                            "prompt": prompt,
                            "n": n,
                            "size": size,
                            "quality": quality,
                            "style": style
                        }
                    )
                    
                    if response.status_code != 200:
                        return ModuleResult(
                            success=False,
                            message=f"API请求失败: {response.status_code}",
                            error=response.text
                        )
                    
                    result = response.json()
                    image_urls = [item['url'] for item in result.get('data', [])]
                    
                    # 如果指定了保存路径，下载图片
                    if save_path and image_urls:
                        saved_paths = []
                        for i, url in enumerate(image_urls):
                            img_response = await client.get(url)
                            if img_response.status_code == 200:
                                # 生成文件名
                                if n == 1:
                                    file_path = save_path
                                else:
                                    path_obj = Path(save_path)
                                    file_path = str(path_obj.parent / f"{path_obj.stem}_{i+1}{path_obj.suffix}")
                                
                                # 保存图片
                                with open(file_path, 'wb') as f:
                                    f.write(img_response.content)
                                saved_paths.append(file_path)
                        
                        context.set_variable(variable_name, saved_paths)
                        
                        return ModuleResult(
                            success=True,
                            message=f"AI生图成功，已保存 {len(saved_paths)} 张图片",
                            data={'urls': image_urls, 'paths': saved_paths}
                        )
                    else:
                        context.set_variable(variable_name, image_urls)
                        
                        return ModuleResult(
                            success=True,
                            message=f"AI生图成功，生成 {len(image_urls)} 张图片",
                            data={'urls': image_urls}
                        )
            
            elif provider == 'stability':
                # Stability AI API
                api_key = context.resolve_value(config.get('apiKey', ''))
                api_base = context.resolve_value(config.get('apiBase', 'https://api.stability.ai'))
                engine_id = config.get('engineId', 'stable-diffusion-xl-1024-v1-0')
                
                if not api_key:
                    return ModuleResult(
                        success=False,
                        message="API Key不能为空",
                        error="API Key为空"
                    )
                
                # 解析尺寸
                width, height = map(int, size.split('x'))
                
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{api_base}/v1/generation/{engine_id}/text-to-image",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "text_prompts": [
                                {"text": prompt, "weight": 1.0},
                                {"text": negative_prompt, "weight": -1.0} if negative_prompt else None
                            ],
                            "cfg_scale": 7,
                            "height": height,
                            "width": width,
                            "samples": n,
                            "steps": 30
                        }
                    )
                    
                    if response.status_code != 200:
                        return ModuleResult(
                            success=False,
                            message=f"API请求失败: {response.status_code}",
                            error=response.text
                        )
                    
                    result = response.json()
                    artifacts = result.get('artifacts', [])
                    
                    # 保存图片
                    saved_paths = []
                    for i, artifact in enumerate(artifacts):
                        image_data = base64.b64decode(artifact['base64'])
                        
                        # 生成文件名
                        if n == 1:
                            file_path = save_path if save_path else f"ai_image_{int(time.time())}.png"
                        else:
                            if save_path:
                                path_obj = Path(save_path)
                                file_path = str(path_obj.parent / f"{path_obj.stem}_{i+1}{path_obj.suffix}")
                            else:
                                file_path = f"ai_image_{int(time.time())}_{i+1}.png"
                        
                        # 保存图片
                        with open(file_path, 'wb') as f:
                            f.write(image_data)
                        saved_paths.append(file_path)
                    
                    context.set_variable(variable_name, saved_paths)
                    
                    return ModuleResult(
                        success=True,
                        message=f"AI生图成功，已保存 {len(saved_paths)} 张图片",
                        data={'paths': saved_paths}
                    )
            
            else:
                return ModuleResult(
                    success=False,
                    message=f"不支持的AI提供商: {provider}",
                    error="提供商不支持"
                )
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[AIGenerateImageExecutor] 执行失败: {error_detail}")
            return ModuleResult(
                success=False,
                message=f"AI生图失败: {str(e)}",
                error=str(e)
            )


@register_executor
class AIGenerateVideoExecutor(ModuleExecutor):
    """AI生视频执行器"""
    
    @property
    def module_type(self) -> str:
        return "ai_generate_video"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """使用AI生成视频"""
        try:
            import httpx
            import asyncio
            
            provider = config.get('provider', 'runway')  # runway, pika, luma
            prompt = context.resolve_value(config.get('prompt', ''))
            duration = int(config.get('duration', 5))  # 视频时长（秒）
            aspect_ratio = config.get('aspectRatio', '16:9')  # 宽高比
            fps = int(config.get('fps', 24))  # 帧率
            save_path = context.resolve_value(config.get('savePath', ''))
            variable_name = config.get('variableName', 'ai_video_url')
            
            if not prompt:
                return ModuleResult(
                    success=False,
                    message="提示词不能为空",
                    error="提示词为空"
                )
            
            # 根据不同的提供商调用不同的API
            if provider == 'runway':
                # Runway API
                api_key = context.resolve_value(config.get('apiKey', ''))
                api_base = context.resolve_value(config.get('apiBase', 'https://api.runwayml.com/v1'))
                
                if not api_key:
                    return ModuleResult(
                        success=False,
                        message="API Key不能为空",
                        error="API Key为空"
                    )
                
                async with httpx.AsyncClient(timeout=300.0) as client:
                    # 创建生成任务
                    response = await client.post(
                        f"{api_base}/generations",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "prompt": prompt,
                            "duration": duration,
                            "aspect_ratio": aspect_ratio,
                            "fps": fps
                        }
                    )
                    
                    if response.status_code != 200:
                        return ModuleResult(
                            success=False,
                            message=f"API请求失败: {response.status_code}",
                            error=response.text
                        )
                    
                    result = response.json()
                    task_id = result.get('id')
                    
                    # 轮询任务状态
                    max_attempts = 60  # 最多等待5分钟
                    for attempt in range(max_attempts):
                        await asyncio.sleep(5)  # 每5秒查询一次
                        
                        status_response = await client.get(
                            f"{api_base}/generations/{task_id}",
                            headers={"Authorization": f"Bearer {api_key}"}
                        )
                        
                        if status_response.status_code != 200:
                            continue
                        
                        status_result = status_response.json()
                        status = status_result.get('status')
                        
                        if status == 'completed':
                            video_url = status_result.get('url')
                            
                            # 如果指定了保存路径，下载视频
                            if save_path and video_url:
                                video_response = await client.get(video_url)
                                if video_response.status_code == 200:
                                    with open(save_path, 'wb') as f:
                                        f.write(video_response.content)
                                    
                                    context.set_variable(variable_name, save_path)
                                    
                                    return ModuleResult(
                                        success=True,
                                        message=f"AI生视频成功，已保存到: {save_path}",
                                        data={'url': video_url, 'path': save_path}
                                    )
                            else:
                                context.set_variable(variable_name, video_url)
                                
                                return ModuleResult(
                                    success=True,
                                    message="AI生视频成功",
                                    data={'url': video_url}
                                )
                        
                        elif status == 'failed':
                            return ModuleResult(
                                success=False,
                                message="AI生视频失败",
                                error=status_result.get('error', '未知错误')
                            )
                    
                    return ModuleResult(
                        success=False,
                        message="AI生视频超时",
                        error="任务超时"
                    )
            
            elif provider == 'custom':
                # 自定义API（通用接口）
                api_url = context.resolve_value(config.get('apiUrl', ''))
                api_key = context.resolve_value(config.get('apiKey', ''))
                
                if not api_url:
                    return ModuleResult(
                        success=False,
                        message="API URL不能为空",
                        error="API URL为空"
                    )
                
                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.post(
                        api_url,
                        headers=headers,
                        json={
                            "prompt": prompt,
                            "duration": duration,
                            "aspect_ratio": aspect_ratio,
                            "fps": fps
                        }
                    )
                    
                    if response.status_code != 200:
                        return ModuleResult(
                            success=False,
                            message=f"API请求失败: {response.status_code}",
                            error=response.text
                        )
                    
                    result = response.json()
                    video_url = result.get('url') or result.get('video_url')
                    
                    if not video_url:
                        return ModuleResult(
                            success=False,
                            message="API返回结果中未找到视频URL",
                            error="无效的API响应"
                        )
                    
                    # 如果指定了保存路径，下载视频
                    if save_path:
                        video_response = await client.get(video_url)
                        if video_response.status_code == 200:
                            with open(save_path, 'wb') as f:
                                f.write(video_response.content)
                            
                            context.set_variable(variable_name, save_path)
                            
                            return ModuleResult(
                                success=True,
                                message=f"AI生视频成功，已保存到: {save_path}",
                                data={'url': video_url, 'path': save_path}
                            )
                    else:
                        context.set_variable(variable_name, video_url)
                        
                        return ModuleResult(
                            success=True,
                            message="AI生视频成功",
                            data={'url': video_url}
                        )
            
            else:
                return ModuleResult(
                    success=False,
                    message=f"不支持的AI提供商: {provider}",
                    error="提供商不支持"
                )
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[AIGenerateVideoExecutor] 执行失败: {error_detail}")
            return ModuleResult(
                success=False,
                message=f"AI生视频失败: {str(e)}",
                error=str(e)
            )
