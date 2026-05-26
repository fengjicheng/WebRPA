"""系统对话框相关API - 文件/文件夹选择

直接调用 Windows 现代 Common Item Dialog API（Vista+ 引入的 IFileOpenDialog），
通过 ctypes in-process 调用：
- 速度极快（无 PowerShell 子进程冷启动开销，毫秒级弹出）
- 文件夹和文件都用同一套 Explorer 风格界面
- 路径直接以宽字符返回，没有编码问题
"""
import logging
import sys
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system", tags=["system-dialog"])


class OpenUrlRequest(BaseModel):
    url: str


class FolderSelectRequest(BaseModel):
    title: Optional[str] = "选择文件夹"
    initialDir: Optional[str] = None


class FileSelectRequest(BaseModel):
    title: Optional[str] = "选择文件"
    initialDir: Optional[str] = None
    fileTypes: Optional[list[tuple[str, str]]] = None


# ============================================================
# ctypes IFileOpenDialog 调用（Windows 资源管理器风格对话框）
# ============================================================

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes, POINTER, byref, c_void_p, c_wchar_p, c_uint, c_ulong, c_int, HRESULT, Structure
    from ctypes.wintypes import HWND, LPCWSTR

    # COM 常量
    CLSCTX_INPROC_SERVER = 0x1
    COINIT_APARTMENTTHREADED = 0x2
    S_OK = 0
    S_FALSE = 1
    SIGDN_FILESYSPATH = 0x80058000

    # FileOpenOptions (FILEOPENDIALOGOPTIONS)
    FOS_OVERWRITEPROMPT = 0x2
    FOS_STRICTFILETYPES = 0x4
    FOS_NOCHANGEDIR = 0x8
    FOS_PICKFOLDERS = 0x20  # 选择文件夹模式
    FOS_FORCEFILESYSTEM = 0x40
    FOS_ALLNONSTORAGEITEMS = 0x80
    FOS_NOVALIDATE = 0x100
    FOS_ALLOWMULTISELECT = 0x200
    FOS_PATHMUSTEXIST = 0x800
    FOS_FILEMUSTEXIST = 0x1000
    FOS_CREATEPROMPT = 0x2000
    FOS_SHAREAWARE = 0x4000
    FOS_NOREADONLYRETURN = 0x8000
    FOS_NOTESTFILECREATE = 0x10000
    FOS_HIDEMRUPLACES = 0x20000
    FOS_HIDEPINNEDPLACES = 0x40000
    FOS_NODEREFERENCELINKS = 0x100000
    FOS_DONTADDTORECENT = 0x2000000
    FOS_FORCESHOWHIDDEN = 0x10000000
    FOS_DEFAULTNOMINIMODE = 0x20000000

    # GUID 字符串
    CLSID_FileOpenDialog = "{DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7}"
    IID_IFileOpenDialog = "{D57C7288-D4AD-4768-BE02-9D969532D960}"

    ole32 = ctypes.OleDLL("ole32.dll")
    shell32 = ctypes.OleDLL("shell32.dll")

    class GUID(Structure):
        _fields_ = [
            ("Data1", ctypes.c_ulong),
            ("Data2", ctypes.c_ushort),
            ("Data3", ctypes.c_ushort),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    def _make_guid(s: str) -> GUID:
        g = GUID()
        ole32.IIDFromString(c_wchar_p(s), byref(g))
        return g

    class COMDLG_FILTERSPEC(Structure):
        _fields_ = [("pszName", LPCWSTR), ("pszSpec", LPCWSTR)]

    def _show_file_open_dialog(
        title: str,
        initial_dir: Optional[str] = None,
        pick_folders: bool = False,
        file_types: Optional[list[tuple[str, str]]] = None,
    ) -> str:
        """打开 Vista+ Common Item Dialog，返回选中的路径（取消则返回 ""）"""
        # 初始化 COM（每次单独 init，避免污染主进程的 COM 模式）
        hr = ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
        # S_FALSE 表示已经初始化过，也算成功
        if hr not in (S_OK, S_FALSE):
            logger.warning(f"[Dialog] CoInitializeEx 返回 0x{hr & 0xFFFFFFFF:08X}")

        try:
            clsid = _make_guid(CLSID_FileOpenDialog)
            iid = _make_guid(IID_IFileOpenDialog)
            pdialog = c_void_p()
            hr = ole32.CoCreateInstance(
                byref(clsid),
                None,
                CLSCTX_INPROC_SERVER,
                byref(iid),
                byref(pdialog),
            )
            if hr != S_OK or not pdialog.value:
                logger.error(f"[Dialog] CoCreateInstance 失败: 0x{hr & 0xFFFFFFFF:08X}")
                return ""

            # vtable 索引（IFileOpenDialog 继承 IFileDialog 继承 IModalWindow）
            # IUnknown: 0=QI 1=AddRef 2=Release
            # IModalWindow: 3=Show
            # IFileDialog: 4=SetFileTypes 5=SetFileTypeIndex 6=GetFileTypeIndex
            #              7=Advise 8=Unadvise 9=SetOptions 10=GetOptions
            #              11=SetDefaultFolder 12=SetFolder 13=GetFolder
            #              14=GetCurrentSelection 15=SetFileName 16=GetFileName
            #              17=SetTitle 18=SetOkButtonLabel 19=SetFileNameLabel
            #              20=GetResult 21=AddPlace 22=SetDefaultExtension
            #              23=Close 24=SetClientGuid 25=ClearClientData 26=SetFilter
            vtbl = ctypes.cast(pdialog, POINTER(POINTER(c_void_p)))[0]

            def _vmethod(idx: int, restype, argtypes):
                func_ptr = vtbl[idx]
                return ctypes.WINFUNCTYPE(restype, *argtypes)(func_ptr)

            Release = _vmethod(2, HRESULT, [c_void_p])
            Show = _vmethod(3, HRESULT, [c_void_p, HWND])
            SetFileTypes = _vmethod(4, HRESULT, [c_void_p, c_uint, POINTER(COMDLG_FILTERSPEC)])
            SetOptions = _vmethod(9, HRESULT, [c_void_p, c_ulong])
            GetOptions = _vmethod(10, HRESULT, [c_void_p, POINTER(c_ulong)])
            SetFolder = _vmethod(12, HRESULT, [c_void_p, c_void_p])
            SetTitle = _vmethod(17, HRESULT, [c_void_p, LPCWSTR])
            GetResult = _vmethod(20, HRESULT, [c_void_p, POINTER(c_void_p)])

            try:
                # 1. 设置标题
                if title:
                    SetTitle(pdialog, title)

                # 2. 设置 options
                opts = c_ulong(0)
                GetOptions(pdialog, byref(opts))
                new_opts = opts.value | FOS_FORCEFILESYSTEM | FOS_PATHMUSTEXIST
                if pick_folders:
                    new_opts |= FOS_PICKFOLDERS
                else:
                    new_opts |= FOS_FILEMUSTEXIST
                SetOptions(pdialog, new_opts)

                # 3. 文件类型过滤（只对文件模式有效）
                if not pick_folders and file_types:
                    # 把 [(desc, "*.ext"), ...] 转换为 COMDLG_FILTERSPEC 数组
                    n = len(file_types)
                    Arr = COMDLG_FILTERSPEC * n
                    arr = Arr()
                    # 必须保持引用避免 GC（保留 LPCWSTR 字符串到本地变量列表）
                    _strs = []
                    for i, (desc, pattern) in enumerate(file_types):
                        d = c_wchar_p(desc)
                        p = c_wchar_p(pattern)
                        _strs.append(d)
                        _strs.append(p)
                        arr[i].pszName = d
                        arr[i].pszSpec = p
                    SetFileTypes(pdialog, n, arr)

                # 4. 设置初始文件夹（可选）
                if initial_dir:
                    try:
                        # 用 SHCreateItemFromParsingName 把字符串路径变成 IShellItem
                        IID_IShellItem = _make_guid("{43826D1E-E718-42EE-BC55-A1E261C37BFE}")
                        psi = c_void_p()
                        SHCreateItemFromParsingName = shell32.SHCreateItemFromParsingName
                        SHCreateItemFromParsingName.restype = HRESULT
                        SHCreateItemFromParsingName.argtypes = [
                            LPCWSTR, c_void_p, POINTER(GUID), POINTER(c_void_p),
                        ]
                        hr2 = SHCreateItemFromParsingName(
                            initial_dir, None, byref(IID_IShellItem), byref(psi)
                        )
                        if hr2 == S_OK and psi.value:
                            SetFolder(pdialog, psi)
                            # IShellItem.Release
                            si_vtbl = ctypes.cast(psi, POINTER(POINTER(c_void_p)))[0]
                            si_release = ctypes.WINFUNCTYPE(HRESULT, c_void_p)(si_vtbl[2])
                            si_release(psi)
                    except Exception as e:
                        logger.warning(f"[Dialog] 设置初始目录失败: {e}")

                # 5. 显示对话框（None=用前台窗口当 owner）
                hr = Show(pdialog, None)
                if hr != S_OK:
                    # 0x800704C7 = ERROR_CANCELLED
                    return ""

                # 6. 拿结果（IShellItem -> 路径）
                psi_result = c_void_p()
                hr = GetResult(pdialog, byref(psi_result))
                if hr != S_OK or not psi_result.value:
                    return ""

                try:
                    # IShellItem.GetDisplayName(SIGDN_FILESYSPATH) -> 文件系统路径
                    si_vtbl = ctypes.cast(psi_result, POINTER(POINTER(c_void_p)))[0]
                    GetDisplayName = ctypes.WINFUNCTYPE(
                        HRESULT, c_void_p, c_int, POINTER(c_wchar_p)
                    )(si_vtbl[5])
                    Release_si = ctypes.WINFUNCTYPE(HRESULT, c_void_p)(si_vtbl[2])
                    pname = c_wchar_p()
                    hr = GetDisplayName(psi_result, SIGDN_FILESYSPATH, byref(pname))
                    if hr == S_OK and pname.value:
                        path = pname.value
                        # 释放 CoTaskMemAlloc 出来的字符串
                        ole32.CoTaskMemFree(pname)
                        Release_si(psi_result)
                        return path
                    Release_si(psi_result)
                    return ""
                except Exception as e:
                    logger.error(f"[Dialog] 取结果失败: {e}", exc_info=True)
                    return ""
            finally:
                Release(pdialog)
        finally:
            try:
                ole32.CoUninitialize()
            except Exception:
                pass


def select_folder_windows(title: str, initial_dir: str = None) -> str:
    """打开 Vista+ 现代文件夹选择对话框（资源管理器风格）"""
    if sys.platform != "win32":
        return ""
    logger.info(f"[文件夹选择器] {title}")
    try:
        return _show_file_open_dialog(title or "选择文件夹", initial_dir, pick_folders=True)
    except Exception as e:
        logger.error(f"[文件夹选择器] 失败: {e}", exc_info=True)
        return ""


def select_file_windows(title: str, initial_dir: str = None, file_filter: str = None) -> str:
    """打开 Vista+ 现代文件选择对话框

    file_filter 是 PowerShell 风格："Excel文件|*.xlsx|所有文件|*.*"
    内部转换为 [(desc, pattern), ...] 列表传给 IFileOpenDialog。
    """
    if sys.platform != "win32":
        return ""
    logger.info(f"[文件选择器] {title}")
    file_types: Optional[list[tuple[str, str]]] = None
    if file_filter:
        try:
            parts = file_filter.split("|")
            # 两两一组
            file_types = [(parts[i], parts[i + 1]) for i in range(0, len(parts) - 1, 2)]
        except Exception:
            file_types = None
    try:
        return _show_file_open_dialog(
            title or "选择文件", initial_dir, pick_folders=False, file_types=file_types
        )
    except Exception as e:
        logger.error(f"[文件选择器] 失败: {e}", exc_info=True)
        return ""


@router.post("/open-url")
async def open_url(request: OpenUrlRequest):
    """使用系统默认浏览器打开URL"""
    import webbrowser
    try:
        webbrowser.open(request.url)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/select-folder")
async def select_folder(request: FolderSelectRequest):
    """打开文件夹选择对话框（资源管理器风格，速度极快）"""
    try:
        logger.info(f"[API] 收到文件夹选择请求: {request}")

        folder_path = select_folder_windows(
            title=request.title or "选择文件夹",
            initial_dir=request.initialDir,
        )

        if folder_path:
            logger.info(f"[API] 文件夹选择成功: {folder_path}")
            return {"success": True, "path": folder_path}
        else:
            logger.info("[API] 用户取消了文件夹选择")
            return {"success": False, "path": None, "message": "用户取消选择"}
    except Exception as e:
        logger.error(f"[API] 文件夹选择失败: {str(e)}", exc_info=True)
        return {"success": False, "path": None, "error": str(e)}


@router.post("/select-file")
async def select_file(request: FileSelectRequest):
    """打开文件选择对话框（资源管理器风格，速度极快）"""
    try:
        logger.info(f"[API] 收到文件选择请求: {request}")

        file_filter = None
        if request.fileTypes:
            filter_parts = []
            for desc, pattern in request.fileTypes:
                filter_parts.append(f"{desc}|{pattern}")
            file_filter = "|".join(filter_parts)

        file_path = select_file_windows(
            title=request.title or "选择文件",
            initial_dir=request.initialDir,
            file_filter=file_filter,
        )

        if file_path:
            logger.info(f"[API] 文件选择成功: {file_path}")
            return {"success": True, "path": file_path}
        else:
            logger.info("[API] 用户取消了文件选择")
            return {"success": False, "path": None, "message": "用户取消选择"}
    except Exception as e:
        logger.error(f"[API] 文件选择失败: {str(e)}", exc_info=True)
        return {"success": False, "path": None, "error": str(e)}
