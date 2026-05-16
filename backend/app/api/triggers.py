"""触发器API路由"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.services.trigger_manager import trigger_manager


router = APIRouter(prefix="/api/triggers", tags=["triggers"])


class WebhookTriggerRequest(BaseModel):
    """Webhook触发请求"""
    data: Optional[Dict[str, Any]] = None


@router.post("/webhook/{webhook_id}")
@router.get("/webhook/{webhook_id}")
@router.put("/webhook/{webhook_id}")
@router.delete("/webhook/{webhook_id}")
async def trigger_webhook(webhook_id: str, request: Request):
    """
    触发Webhook
    支持GET/POST/PUT/DELETE方法
    """
    method = request.method

    # 获取请求数据
    try:
        if method in ['POST', 'PUT']:
            body = await request.json()
        else:
            body = dict(request.query_params)
    except:
        body = {}

    # 获取请求头
    headers = dict(request.headers)

    # 构建触发数据
    trigger_data = {
        'method': method,
        'headers': headers,
        'body': body,
        'query': dict(request.query_params),
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }

    # 触发Webhook
    success = trigger_manager.trigger_webhook(webhook_id, method, trigger_data)

    if not success:
        raise HTTPException(status_code=404, detail="Webhook不存在或HTTP方法不匹配")

    return {
        "success": True,
        "message": "Webhook已触发",
        "webhookId": webhook_id,
        "method": method
    }


@router.get("/webhooks")
async def list_webhooks():
    """获取所有已注册的Webhook"""
    from app.utils.config import get_backend_url
    
    webhooks = []
    for webhook_id, data in trigger_manager.webhooks.items():
        webhooks.append({
            'webhookId': webhook_id,
            'method': data['method'],
            'url': f"{get_backend_url()}/api/triggers/webhook/{webhook_id}"
        })
    return {"webhooks": webhooks}


@router.get("/hotkeys")
async def list_hotkeys():
    """获取所有已注册的热键"""
    hotkeys = []
    for trigger_id, data in trigger_manager.hotkeys.items():
        hotkeys.append({
            'triggerId': trigger_id,
            'hotkey': data['original'],
            'normalized': data['hotkey']
        })
    return {"hotkeys": hotkeys}


@router.get("/file-watchers")
async def list_file_watchers():
    """获取所有已注册的文件监控"""
    watchers = []
    for watcher_id, data in trigger_manager.file_watchers.items():
        watchers.append({
            'watcherId': watcher_id,
            'path': data['path'],
            'type': data['type'],
            'pattern': data['pattern']
        })
    return {"watchers": watchers}


@router.get("/email-monitors")
async def list_email_monitors():
    """获取所有已注册的邮件监控"""
    monitors = []
    for monitor_id, data in trigger_manager.email_monitors.items():
        monitors.append({
            'monitorId': monitor_id,
            'server': data['server'],
            'account': data['account'],
            'fromFilter': data['from_filter'],
            'subjectFilter': data['subject_filter']
        })
    return {"monitors": monitors}


# ==================== 手势识别触发器 ====================

@router.post("/gesture/start")
async def start_gesture_recognition(camera_index: int = 0, debug_window: bool = False):
    """启动手势识别"""
    from app.services.gesture_recognition_service import gesture_service
    
    try:
        # 定义手势触发回调
        def on_gesture_detected(gesture_name: str):
            """当检测到手势时触发工作流"""
            trigger_manager.trigger_gesture(gesture_name)
        
        success = gesture_service.start_recognition(
            camera_index=camera_index,
            debug_window=debug_window,
            callback=on_gesture_detected
        )
        
        if success:
            return {"success": True, "message": "手势识别已启动"}
        else:
            # 获取具体的失败原因
            if gesture_service.is_running:
                raise HTTPException(status_code=400, detail="手势识别已在运行中")
            elif not gesture_service.custom_gestures:
                raise HTTPException(status_code=400, detail="没有可用的自定义手势，请先录制手势")
            else:
                raise HTTPException(status_code=500, detail="启动手势识别失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动手势识别失败: {str(e)}")


@router.post("/gesture/stop")
async def stop_gesture_recognition():
    """停止手势识别"""
    from app.services.gesture_recognition_service import gesture_service
    
    gesture_service.stop_recognition()
    return {"success": True, "message": "手势识别已停止"}


@router.get("/gesture/status")
async def get_gesture_status():
    """获取手势识别状态"""
    from app.services.gesture_recognition_service import gesture_service
    
    status = gesture_service.get_status()
    return {"success": True, "status": status}


@router.get("/gesture/custom")
async def get_custom_gestures():
    """获取自定义手势列表"""
    from app.services.gesture_recognition_service import gesture_service
    
    gestures = []
    for gesture_name in gesture_service.custom_gestures.keys():
        gestures.append({
            'name': gesture_name,
            'type': 'custom'
        })
    
    return {"success": True, "gestures": gestures}


class RecordGestureRequest(BaseModel):
    """录制手势请求"""
    gesture_name: str
    timeout: int = 30


@router.post("/gesture/record")
async def record_gesture(request: RecordGestureRequest):
    """录制手势"""
    from app.services.gesture_recognition_service import gesture_service
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    try:
        # 在后台线程中录制手势（因为OpenCV窗口需要在主线程或独立线程中运行）
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            success = await loop.run_in_executor(
                executor,
                gesture_service.record_gesture,
                request.gesture_name,
                0  # camera_index
            )
        
        if success:
            return {
                "success": True,
                "message": f"手势已录制: {request.gesture_name}",
                "gesture_name": request.gesture_name
            }
        else:
            raise HTTPException(status_code=500, detail="手势录制失败或已取消")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"录制手势失败: {str(e)}")


@router.delete("/gesture/custom/{gesture_name}")
async def delete_custom_gesture(gesture_name: str):
    """删除自定义手势"""
    from app.services.gesture_recognition_service import gesture_service
    
    success = gesture_service.delete_gesture(gesture_name)
    if success:
        return {"success": True, "message": f"已删除自定义手势: {gesture_name}"}
    else:
        raise HTTPException(status_code=404, detail=f"自定义手势不存在: {gesture_name}")
