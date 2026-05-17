import { useWorkflowStore, moduleTypeLabels, getModuleDefaultTimeout, type NodeData } from '@/store/workflowStore'
import { useGlobalConfigStore } from '@/store/globalConfigStore'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Input } from '@/components/ui/input'
import { NumberInput } from '@/components/ui/number-input'
import { Label } from '@/components/ui/label'
import { SelectNative as Select } from '@/components/ui/select-native'
import { Button } from '@/components/ui/button'
import { VariableInput } from '@/components/ui/variable-input'
import { Trash2, Crosshair, Loader2, Ban, ChevronLeft, ChevronRight, Settings } from 'lucide-react'
import { useState, useCallback, useRef, useEffect } from 'react'
import { elementPickerApi, desktopPickerApi } from '@/services/api'

// 导入拆分的配置组件
import { ReadExcelConfig } from './config-panels/ReadExcelConfig'
import { SimilarSelectorDialog } from './config-panels/SimilarSelectorDialog'
import { UrlInputDialog } from './config-panels/UrlInputDialog'
import {
  OpenPageConfig,
  UseOpenedPageConfig,
  ClickElementConfig,
  HoverElementConfig,
  InputTextConfig,
  GetElementInfoConfig,
  WaitConfig,
  WaitElementConfig,
  WaitImageConfig,
  WaitPageLoadConfig,
  PageLoadCompleteConfig,
  SetVariableConfig,
  IncrementDecrementConfig,
  PrintLogConfig,
  PlaySoundConfig,
  SystemNotificationConfig,
  PlayMusicConfig,
  PlayVideoConfig,
  ViewImageConfig,
  InputPromptConfig,
  TextToSpeechConfig,
  JsScriptConfig,
  PythonScriptConfig,
  ExtractTableDataConfig,
  SwitchTabConfig,
  GroupConfig,
  SubflowHeaderConfig,
  RefreshPageConfig,
  GoBackConfig,
  GoForwardConfig,
  HandleDialogConfig,
  InjectJavaScriptConfig,
  SwitchIframeConfig,
  SwitchToMainConfig,
} from './config-panels/BasicModuleConfigs'
import {
  SelectDropdownConfig,
  SetCheckboxConfig,
  DragElementConfig,
  ScrollPageConfig,
  UploadFileConfig,
  DownloadFileConfig,
  SaveImageConfig,
  GetChildElementsConfig,
  GetSiblingElementsConfig,
  ScreenshotConfig,
  OCRCaptchaConfig,
  SliderCaptchaConfig,
  SendEmailConfig,
  SetClipboardConfig,
  GetClipboardConfig,
  KeyboardActionConfig,
  RealMouseScrollConfig,
  ShutdownSystemConfig,
  LockScreenConfig,
  WindowFocusConfig,
  RealMouseClickConfig,
  RealMouseMoveConfig,
  RealMouseDragConfig,
  RealKeyboardConfig,
  RunCommandConfig,
  ClickImageConfig,
  ImageExistsConfig,
  GetMousePositionConfig,
  ScreenshotScreenConfig,
  RenameFileConfig,
  NetworkCaptureConfig,
  MacroRecorderConfig,
  ElementExistsConfig,
  ElementVisibleConfig,
  NetworkMonitorStartConfig,
  NetworkMonitorWaitConfig,
  NetworkMonitorStopConfig,
} from './config-panels/AdvancedModuleConfigs'
import {
  AIChatConfig,
  AIVisionConfig,
  ApiRequestConfig,
  AISmartScraperConfig,
  AIElementSelectorConfig,
  FirecrawlScrapeConfig,
  FirecrawlMapConfig,
  FirecrawlCrawlConfig,
} from './config-panels/AIModuleConfigs'
import {
  DesktopAppStartConfig,
  DesktopAppConnectConfig,
  DesktopAppCloseConfig,
  DesktopAppGetInfoConfig,
  DesktopAppWaitReadyConfig,
  DesktopWindowActivateConfig,
  DesktopWindowStateConfig,
  DesktopWindowMoveConfig,
  DesktopWindowResizeConfig,
  DesktopWindowTopmostConfig,
  DesktopWindowListConfig,
  DesktopWindowCaptureConfig,
  DesktopFindControlConfig,
  DesktopControlInfoConfig,
  DesktopControlTreeConfig,
  DesktopWaitControlConfig,
  DesktopClickControlConfig,
  DesktopInputControlConfig,
  DesktopGetTextConfig,
  DesktopSetValueConfig,
  DesktopSelectComboConfig,
  DesktopCheckboxConfig,
  DesktopRadioConfig,
  DesktopDragControlConfig,
  DesktopMenuClickConfig,
  DesktopListOperateConfig,
  DesktopSendKeysConfig,
  DesktopGetPropertyConfig,
  DesktopDialogHandleConfig,
  DesktopScrollControlConfig,
  DesktopGetControlInfoConfig,
  DesktopGetControlTreeConfig,
} from './config-panels/DesktopModuleConfigs'
import {
  ConditionConfig,
  LoopConfig,
  ForeachConfig,
  ForeachDictConfig,
  ScheduledTaskConfig,
  SubflowConfig,
} from './config-panels/ControlModuleConfigs'
import {
  WebhookTriggerConfig,
  HotkeyTriggerConfig,
  FileWatcherTriggerConfig,
  EmailTriggerConfig,
  ApiTriggerConfig,
  MouseTriggerConfig,
  ImageTriggerConfig,
  SoundTriggerConfig,
  FaceTriggerConfig,
  ElementChangeTriggerConfig,
  GestureTriggerConfig,
} from './config-panels/TriggerModuleConfigs'
import {
  RegexExtractConfig,
  StringReplaceConfig,
  StringSplitConfig,
  StringJoinConfig,
  StringConcatConfig,
  StringTrimConfig,
  StringCaseConfig,
  StringSubstringConfig,
  JsonParseConfig,
  Base64Config,
  RandomNumberConfig,
  GetTimeConfig,
  ListOperationConfig,
  ListGetConfig,
  ListLengthConfig,
  ListExportConfig,
  DictOperationConfig,
  DictGetConfig,
  DictKeysConfig,
  TableAddRowConfig,
  TableAddColumnConfig,
  TableSetCellConfig,
  TableGetCellConfig,
  TableDeleteRowConfig,
  TableClearConfig,
  TableExportConfig,
} from './config-panels/DataModuleConfigs'
import {
  ListSumConfig,
  ListAverageConfig,
  ListMaxConfig,
  ListMinConfig,
  ListSortConfig,
  ListUniqueConfig,
  ListSliceConfig,
  MathRoundConfig,
  MathBaseConvertConfig,
  MathFloorConfig,
  MathModuloConfig,
  MathAbsConfig,
  MathSqrtConfig,
  MathPowerConfig,
} from './config-panels/MathListConfigs'
import {
  ListReverseConfig,
  ListFindConfig,
  ListCountConfig,
  ListFilterConfig,
  ListMapConfig,
  ListMergeConfig,
  ListFlattenConfig,
  ListChunkConfig,
  ListRemoveEmptyConfig,
  ListIntersectionConfig,
  ListUnionConfig,
  ListDifferenceConfig,
  ListCartesianProductConfig,
  ListShuffleConfig,
  ListSampleConfig,
} from './config-panels/ListAdvancedConfigs'
import {
  DictMergeConfig,
  DictFilterConfig,
  DictMapValuesConfig,
  DictInvertConfig,
  DictSortConfig,
  DictDeepCopyConfig,
  DictGetPathConfig,
  DictFlattenConfig,
} from './config-panels/DictAdvancedConfigs'
import {
  MathLogConfig,
  MathTrigConfig,
  MathExpConfig,
  MathGcdConfig,
  MathLcmConfig,
  MathFactorialConfig,
  MathPermutationConfig,
  MathPercentageConfig,
  MathClampConfig,
  MathRandomAdvancedConfig,
} from './config-panels/MathAdvancedConfigs'
import {
  StatMedianConfig,
  StatModeConfig,
  StatVarianceConfig,
  StatStdevConfig,
  StatPercentileConfig,
  StatNormalizeConfig,
  StatStandardizeConfig,
  CsvParseConfig,
  CsvGenerateConfig,
  ListToStringAdvancedConfig,
} from './config-panels/StatisticsConfigs'
import {
  DbConnectConfig,
  DbQueryConfig,
  DbExecuteConfig,
  DbInsertConfig,
  DbUpdateConfig,
  DbDeleteConfig,
  DbCloseConfig,
} from './config-panels/DatabaseModuleConfigs'
import {
  FormatConvertConfig,
  CompressImageConfig,
  CompressVideoConfig,
  ExtractAudioConfig,
  TrimVideoConfig,
  MergeMediaConfig,
  AddWatermarkConfig,
  FaceRecognitionConfig,
  ImageOCRConfig,
  DownloadM3U8Config,
  RotateVideoConfig,
  VideoSpeedConfig,
  ExtractFrameConfig,
  AddSubtitleConfig,
  AdjustVolumeConfig,
  ResizeVideoConfig,
  ImageGrayscaleConfig,
  ImageRoundCornersConfig,
  AudioToTextConfig,
  QRGenerateConfig,
  QRDecodeConfig,
  ScreenRecordConfig,
  CameraCaptureConfig,
  CameraRecordConfig,
} from './config-panels/MediaModuleConfigs'
import {
  ListFilesConfig,
  CopyFileConfig,
  MoveFileConfig,
  DeleteFileConfig,
  CreateFolderConfig,
  FileExistsConfig,
  GetFileInfoConfig,
  ReadTextFileConfig,
  WriteTextFileConfig,
  RenameFolderConfig,
} from './config-panels/FileModuleConfigs'
import {
  QQSendMessageConfig,
  QQSendImageConfig,
  QQSendFileConfig,
  QQGetFriendsConfig,
  QQGetGroupsConfig,
  QQGetGroupMembersConfig,
  QQGetLoginInfoConfig,
  QQWaitMessageConfig,
} from './config-panels/QQModuleConfigs'

import {
  WeChatSendMessageConfig,
  WeChatSendFileConfig,
} from './config-panels/WeChatModuleConfigs'
import {
  NotifyDiscordConfig,
  NotifyTelegramConfig,
  NotifyDingTalkConfig,
  NotifyWeComConfig,
  NotifyFeishuConfig,
  NotifyBarkConfig,
  NotifySlackConfig,
  NotifyMSTeamsConfig,
  NotifyPushoverConfig,
  NotifyPushBulletConfig,
  NotifyGotifyConfig,
  NotifyServerChanConfig,
  NotifyPushPlusConfig,
  NotifyWebhookConfig,
  NotifyNtfyConfig,
  NotifyMatrixConfig,
  NotifyRocketChatConfig,
} from './config-panels/NotifyModuleConfigs'
import {
  WebhookRequestConfig,
  FeishuBitableWriteConfig,
  FeishuBitableReadConfig,
  FeishuSheetWriteConfig,
  FeishuSheetReadConfig,
  OracleConnectConfig,
  OracleQueryConfig,
  OracleExecuteConfig,
  PostgreSQLConnectConfig,
  PostgreSQLQueryConfig,
  PostgreSQLExecuteConfig,
  MongoDBConnectConfig,
  MongoDBFindConfig,
  MongoDBInsertConfig,
  MongoDBUpdateConfig,
  MongoDBDeleteConfig,
  SQLServerConnectConfig,
  SQLServerQueryConfig,
  SQLServerExecuteConfig,
  SQLiteConnectConfig,
  SQLiteQueryConfig,
  SQLiteExecuteConfig,
  RedisConnectConfig,
  RedisGetConfig,
  RedisSetConfig,
  RedisDelConfig,
  RedisHGetConfig,
  RedisHSetConfig,
  OracleInsertConfig,
  OracleUpdateConfig,
  OracleDeleteConfig,
  PostgreSQLInsertConfig,
  PostgreSQLUpdateConfig,
  PostgreSQLDeleteConfig,
  SQLServerInsertConfig,
  SQLServerUpdateConfig,
  SQLServerDeleteConfig,
  SQLiteInsertConfig,
  SQLiteUpdateConfig,
  SQLiteDeleteConfig,
  OracleDisconnectConfig,
  PostgreSQLDisconnectConfig,
  MongoDBDisconnectConfig,
  SQLServerDisconnectConfig,
  SQLiteDisconnectConfig,
  RedisDisconnectConfig,
  SSHConnectConfig,
  SSHExecuteCommandConfig,
  SSHUploadFileConfig,
  SSHDownloadFileConfig,
  SSHDisconnectConfig,
  AIGenerateImageConfig,
  AIGenerateVideoConfig,
  ProbabilityTriggerConfig,
  SapLoginConfig,
  SapLogoutConfig,
  SapRunTcodeConfig,
  SapSetFieldValueConfig,
  SapGetFieldValueConfig,
  SapClickButtonConfig,
  SapSendVKeyConfig,
  SapGetStatusMessageConfig,
  SapGetTitleConfig,
  SapCloseWarningConfig,
  SapSetCheckboxConfig,
  SapSelectComboBoxConfig,
  SapReadGridViewConfig,
  SapExportGridViewExcelConfig,
  SapSetFocusConfig,
  SapMaximizeWindowConfig,
} from './config-panels'
import {
  AllureInitConfig,
  AllureStartTestConfig,
  AllureAddStepConfig,
  AllureAddAttachmentConfig,
  AllureStopTestConfig,
  AllureGenerateReportConfig,
} from './config-panels/TestAllureConfigs'
import {
  PhoneTapConfig,
  PhoneSwipeConfig,
  PhoneLongPressConfig,
  PhoneInputTextConfig,
  PhonePressKeyConfig,
  PhoneScreenshotConfig,
  PhoneStartMirrorConfig,
  PhoneStopMirrorConfig,
  PhoneInstallAppConfig,
  PhoneStartAppConfig,
  PhoneStopAppConfig,
  PhoneUninstallAppConfig,
  PhonePushFileConfig,
  PhonePullFileConfig,
  PhoneClickImageConfig,
  PhoneClickTextConfig,
  PhoneWaitImageConfig,
  PhoneImageExistsConfig,
  PhoneSetVolumeConfig,
  PhoneSetBrightnessConfig,
  PhoneSetClipboardConfig,
  PhoneGetClipboardConfig,
} from './config-panels/PhoneModuleConfigs'
import {
  PDFToImagesConfig,
  ImagesToPDFConfig,
  PDFMergeConfig,
  PDFSplitConfig,
  PDFExtractTextConfig,
  PDFExtractImagesConfig,
  PDFEncryptConfig,
  PDFDecryptConfig,
  PDFAddWatermarkConfig,
  PDFRotateConfig,
  PDFDeletePagesConfig,
  PDFGetInfoConfig,
  PDFCompressConfig,
  PDFInsertPagesConfig,
  PDFReorderPagesConfig,
  PDFToWordConfig,
} from './config-panels/PDFModuleConfigs'
import {
  MarkdownToHTMLConfig,
  HTMLToMarkdownConfig,
  MarkdownToPDFConfig,
  MarkdownToDocxConfig,
  DocxToMarkdownConfig,
  HTMLToDocxConfig,
  DocxToHTMLConfig,
  MarkdownToEPUBConfig,
  EPUBToMarkdownConfig,
  LaTeXToPDFConfig,
  RSTToHTMLConfig,
  OrgToHTMLConfig,
  UniversalDocConvertConfig,
} from './config-panels/DocumentConvertConfigs'
import {
  ImageResizeConfig,
  ImageCropConfig,
  ImageRotateConfig,
  ImageFlipConfig,
  ImageBlurConfig,
  ImageSharpenConfig,
  ImageBrightnessConfig,
  ImageContrastConfig,
  ImageColorBalanceConfig,
  ImageConvertFormatConfig,
  ImageAddTextConfig,
  ImageMergeConfig,
  ImageThumbnailConfig,
  ImageFilterConfig,
  ImageGetInfoConfig,
  ImageRemoveBgConfig,
} from './config-panels/PillowImageConfigs'
import {
  ExportLogConfig,
  ClickTextConfig,
  HoverImageConfig,
  HoverTextConfig,
  DragImageConfig,
  ShareFolderConfig,
  ShareFileConfig,
  StopShareConfig,
  StartScreenShareConfig,
  StopScreenShareConfig,
} from './config-panels/AdvancedModuleConfigs'
import {
  ImageFormatConvertConfig,
  VideoFormatConvertConfig,
  AudioFormatConvertConfig,
  VideoToAudioConfig,
  VideoToGIFConfig,
  BatchFormatConvertConfig,
} from './config-panels/FormatFactoryConfigs'
import {
  FileHashCompareConfig,
  FileDiffCompareConfig,
  FolderHashCompareConfig,
  FolderDiffCompareConfig,
  RandomPasswordGeneratorConfig,
  URLEncodeDecodeConfig,
  MD5EncryptConfig,
  SHAEncryptConfig,
  TimestampConverterConfig,
  RGBToHSVConfig,
  RGBToCMYKConfig,
  HEXToCMYKConfig,
  UUIDGeneratorConfig,
  PrinterCallConfig,
} from './config-panels/UtilityToolsConfigs'
import { CustomModuleConfig } from './config-panels/CustomModuleConfig'

interface ConfigPanelProps {
  selectedNodeId?: string | null  // 改为可选，优先使用 store 中的值
}

export function ConfigPanel({ selectedNodeId: propSelectedNodeId }: ConfigPanelProps) {
  // 直接从 store 订阅 selectedNodeId，确保实时更新
  const storeSelectedNodeId = useWorkflowStore((state) => state.selectedNodeId)
  const selectedNodeId = propSelectedNodeId ?? storeSelectedNodeId
  
  const nodes = useWorkflowStore((state) => state.nodes)
  const updateNodeData = useWorkflowStore((state) => state.updateNodeData)
  const deleteNode = useWorkflowStore((state) => state.deleteNode)
  const addLog = useWorkflowStore((state) => state.addLog)
  const addVariable = useWorkflowStore((state) => state.addVariable)
  const toggleNodesDisabled = useWorkflowStore((state) => state.toggleNodesDisabled)
  
  // 获取浏览器配置
  const browserConfig = useGlobalConfigStore((state) => state.config.browser)

  const [isPicking, setIsPicking] = useState(false)
  const [pickingField, setPickingField] = useState<string | null>(null)
  const [showUrlDialog, setShowUrlDialog] = useState(false)
  const [pickerUrl, setPickerUrl] = useState('')
  const [pendingField, setPendingField] = useState<string | null>(null)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const pollingRef = useRef<number | null>(null)
  
  // 响应式：小屏幕自动折叠
  useEffect(() => {
    const handleResize = () => {
      // 屏幕宽度小于1280px时自动折叠
      if (window.innerWidth < 1280) {
        setIsCollapsed(true)
      }
    }

    // 初始检查
    handleResize()

    // 监听窗口大小变化
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])
  
  // 相似元素选择状态
  const [showSimilarDialog, setShowSimilarDialog] = useState(false)
  const [similarResult, setSimilarResult] = useState<{
    pattern: string
    count: number
    minIndex: number
    maxIndex: number
  } | null>(null)

  // 桌面元素选择器状态
  const [isDesktopPicking, setIsDesktopPicking] = useState(false)
  const [desktopPickingField, setDesktopPickingField] = useState<string | null>(null)
  const desktopPollingRef = useRef<number | null>(null)

  const selectedNode = nodes.find((n) => n.id === selectedNodeId)
  const nodeData = selectedNode?.data as NodeData | undefined

  // 清理轮询
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
      if (desktopPollingRef.current) {
        clearInterval(desktopPollingRef.current)
      }
    }
  }, [])

  // 切换选中节点时，停止已激活的元素选择器，避免选中结果写入到错误的节点字段
  const lastSelectedNodeIdRef = useRef<string | null | undefined>(selectedNodeId)
  useEffect(() => {
    if (lastSelectedNodeIdRef.current !== selectedNodeId) {
      // 节点真正变化时，关闭还在运行的选择器及相关 UI
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
      if (desktopPollingRef.current) {
        clearInterval(desktopPollingRef.current)
        desktopPollingRef.current = null
      }
      if (isPicking) {
        elementPickerApi.stop().catch(() => {})
        setIsPicking(false)
        setPickingField(null)
      }
      // 无条件关闭相似元素弹窗（即使 isPicking 已为 false）
      setShowSimilarDialog(false)
      setSimilarResult(null)
      // 关闭可能残留的 URL 输入对话框
      setShowUrlDialog(false)
      setPendingField(null)
      if (isDesktopPicking) {
        desktopPickerApi.stop().catch(() => {})
        setIsDesktopPicking(false)
        setDesktopPickingField(null)
      }
      lastSelectedNodeIdRef.current = selectedNodeId
    }
  }, [selectedNodeId, isPicking, isDesktopPicking])

  const handleChange = useCallback((key: string, value: unknown) => {
    if (selectedNodeId) {
      updateNodeData(selectedNodeId, { [key]: value })
    }
  }, [selectedNodeId, updateNodeData])

  const handleDelete = () => {
    if (selectedNodeId) {
      deleteNode(selectedNodeId)
    }
  }

  // 打开URL输入对话框
  const openUrlDialog = useCallback((fieldName: string) => {
    const openPageNode = nodes.find(n => (n.data as NodeData).moduleType === 'open_page')
    const defaultUrl = (openPageNode?.data as NodeData)?.url as string || ''
    setPickerUrl(defaultUrl)
    setPendingField(fieldName)
    setShowUrlDialog(true)
  }, [nodes])

  // 解析URL中的变量引用
  const resolveVariables = useCallback((value: string): string => {
    const variables = useWorkflowStore.getState().variables
    return value.replace(/\{([^}]+)\}/g, (match, varName) => {
      const variable = variables.find(v => v.name === varName.trim())
      return variable ? String(variable.value ?? '') : match
    })
  }, [])

  // 启动元素选择器
  const startElementPicker = useCallback(async (fieldName: string, url: string) => {
    const resolvedUrl = url ? resolveVariables(url) : ''
    setIsPicking(true)
    setPickingField(fieldName)
    setShowUrlDialog(false)
    
    if (resolvedUrl) {
      addLog({ level: 'info', message: `正在启动元素选择器，URL: ${resolvedUrl}` })
    } else {
      addLog({ level: 'info', message: '正在启动元素选择器（使用当前页面）' })
    }

    try {
      // 传递浏览器配置
      const result = await elementPickerApi.start(resolvedUrl || undefined, browserConfig)
      if (result.error) {
        addLog({ level: 'error', message: `启动失败: ${result.error}` })
        setIsPicking(false)
        setPickingField(null)
        return
      }

      addLog({ level: 'success', message: '元素选择器已启动：Ctrl+点击单选，Alt+点击选择相似元素' })

      pollingRef.current = window.setInterval(async () => {
        const selectedResult = await elementPickerApi.getSelected()
        
        if (selectedResult.data?.active === false) {
          if (pollingRef.current) {
            clearInterval(pollingRef.current)
            pollingRef.current = null
          }
          setIsPicking(false)
          setPickingField(null)
          return
        }
        
        if (selectedResult.data?.selected && selectedResult.data.element) {
          const selector = selectedResult.data.element.selector
          handleChange(fieldName, selector)
          addLog({ level: 'success', message: `已选择元素: ${selector}` })
          
          await elementPickerApi.stop()
          if (pollingRef.current) {
            clearInterval(pollingRef.current)
            pollingRef.current = null
          }
          setIsPicking(false)
          setPickingField(null)
          return
        }
        
        const similarRes = await elementPickerApi.getSimilar()
        if (similarRes.data?.selected && similarRes.data.similar) {
          const similar = similarRes.data.similar
          addLog({ level: 'success', message: `找到 ${similar.count} 个相似元素` })
          
          setSimilarResult({
            pattern: similar.pattern,
            count: similar.count,
            minIndex: similar.minIndex,
            maxIndex: similar.maxIndex,
          })
          setShowSimilarDialog(true)
          
          if (pollingRef.current) {
            clearInterval(pollingRef.current)
            pollingRef.current = null
          }
        }
      }, 500)

    } catch (error) {
      addLog({ level: 'error', message: `启动元素选择器失败: ${error}` })
      setIsPicking(false)
      setPickingField(null)
    }
  }, [addLog, handleChange, resolveVariables, browserConfig])

  // 确认相似元素选择
  const handleSimilarConfirm = useCallback(async (variableName: string) => {
    if (!similarResult || !pickingField) return
    
    const finalSelector = similarResult.pattern.replace('{index}', `{${variableName}}`)
    handleChange(pickingField, finalSelector)
    
    addVariable({
      name: variableName,
      value: similarResult.minIndex,
      type: 'number',
      scope: 'global'
    })
    
    addLog({ 
      level: 'success', 
      message: `已设置相似元素选择器，变量 ${variableName} 范围: ${similarResult.minIndex}-${similarResult.maxIndex}` 
    })
    
    setShowSimilarDialog(false)
    setSimilarResult(null)
    await elementPickerApi.stop()
    setIsPicking(false)
    setPickingField(null)
  }, [similarResult, pickingField, handleChange, addVariable, addLog])

  // 停止元素选择器
  const stopElementPicker = useCallback(async () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
    await elementPickerApi.stop()
    setIsPicking(false)
    setPickingField(null)
    setShowSimilarDialog(false)
    setSimilarResult(null)
    addLog({ level: 'info', message: '元素选择器已停止' })
  }, [addLog])

  // 启动桌面元素选择器
  const startDesktopPicker = useCallback(async (fieldName: string) => {
    setIsDesktopPicking(true)
    setDesktopPickingField(fieldName)
    
    addLog({ level: 'info', message: '正在启动桌面元素选择器...' })

    try {
      const result = await desktopPickerApi.start()
      if (result.error || !result.data?.success) {
        addLog({ level: 'error', message: `启动失败: ${result.error || result.data?.message}` })
        setIsDesktopPicking(false)
        setDesktopPickingField(null)
        return
      }

      addLog({ level: 'success', message: '桌面元素选择器已启动：将鼠标移动到目标元素上，按Ctrl+点击捕获' })

      // 轮询检查是否捕获到元素
      desktopPollingRef.current = window.setInterval(async () => {
        const capturedResult = await desktopPickerApi.getCaptured()
        
        if (capturedResult.data?.success && capturedResult.data.element) {
          const element = capturedResult.data.element
          
          // 构建控件路径字符串
          const controlPath = element.control_path || ''
          
          // 保存到配置
          handleChange(fieldName, controlPath)
          
          // 显示捕获信息
          const info = [
            `控件类型: ${element.control_type}`,
            element.name ? `名称: ${element.name}` : '',
            element.automation_id ? `自动化ID: ${element.automation_id}` : '',
            element.class_name ? `类名: ${element.class_name}` : '',
          ].filter(Boolean).join(', ')
          
          addLog({ level: 'success', message: `已捕获桌面元素: ${info}` })
          
          // 停止选择器
          await desktopPickerApi.stop()
          if (desktopPollingRef.current) {
            clearInterval(desktopPollingRef.current)
            desktopPollingRef.current = null
          }
          setIsDesktopPicking(false)
          setDesktopPickingField(null)
        }
      }, 500)

    } catch (error) {
      addLog({ level: 'error', message: `启动桌面元素选择器失败: ${error}` })
      setIsDesktopPicking(false)
      setDesktopPickingField(null)
    }
  }, [addLog, handleChange])

  // 停止桌面元素选择器
  const stopDesktopPicker = useCallback(async () => {
    if (desktopPollingRef.current) {
      clearInterval(desktopPollingRef.current)
      desktopPollingRef.current = null
    }
    await desktopPickerApi.stop()
    setIsDesktopPicking(false)
    setDesktopPickingField(null)
    addLog({ level: 'info', message: '桌面元素选择器已停止' })
  }, [addLog])

  if (!selectedNode || !nodeData) {
    return (
      <aside className={`border-l border-[hsl(var(--border))] bg-[hsl(var(--card))] flex flex-col transition-[width] duration-200 ${isCollapsed ? 'w-12' : 'w-80'}`}>
        {isCollapsed ? (
          <button 
            type="button"
            className="flex flex-col items-center py-3 gap-2 hover:bg-[hsl(var(--muted))] transition-colors h-full w-full has-hover-only"
            onClick={() => setIsCollapsed(false)}
            title="展开配置面板"
          >
            <span className="flex items-center justify-center w-7 h-7 rounded-md bg-[hsl(var(--brand-50))] text-[hsl(var(--brand-600))]">
              <ChevronLeft className="w-4 h-4" />
            </span>
            <Settings className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
          </button>
        ) : (
          <>
            <div className="p-4 border-b border-[hsl(var(--border))] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="flex items-center justify-center w-7 h-7 rounded-md bg-[hsl(var(--brand-50))] text-[hsl(var(--brand-600))]">
                  <Settings className="w-4 h-4" />
                </span>
                <h2 className="text-sm font-semibold text-[hsl(var(--foreground))]">配置面板</h2>
              </div>
              <button
                onClick={() => setIsCollapsed(true)}
                className="p-1.5 rounded-md text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--muted))] transition-colors"
                title="收起"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 flex items-center justify-center p-4">
              <div className="text-center animate-fade-in">
                <div className="bg-[hsl(var(--card))] w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center">
                  <Crosshair className="w-8 h-8 text-muted-foreground/40" />
                </div>
                <p className="text-sm text-muted-foreground">
                  选择一个节点查看配置
                </p>
              </div>
            </div>
          </>
        )}
      </aside>
    )
  }

  // 渲染带选择器按钮的输入框
  const renderSelectorInput = (id: string, label: string, placeholder: string) => {
    const rawValue = (nodeData[id] as string) || ''
    const isXPath = rawValue.startsWith('xpath=')
    const displayValue = isXPath ? rawValue.slice(6) : rawValue
    const selectorType = isXPath ? 'xpath' : 'css'

    const handleSelectorChange = (v: string) => {
      const currentIsXPath = ((nodeData[id] as string) || '').startsWith('xpath=')
      handleChange(id, currentIsXPath ? (v ? 'xpath=' + v : '') : v)
    }

    const toggleSelectorType = () => {
      if (isXPath) {
        handleChange(id, displayValue)
      } else {
        handleChange(id, rawValue ? 'xpath=' + rawValue : '')
      }
    }

    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor={id}>{label}</Label>
          <button
            type="button"
            onClick={toggleSelectorType}
            className="text-xs px-1.5 py-0.5 rounded border border-border text-muted-foreground hover:text-foreground hover:border-foreground transition-colors"
            title="切换 CSS / XPath 选择器模式"
          >
            {selectorType === 'css' ? 'CSS' : 'XPath'}
          </button>
        </div>
        <div className="flex gap-2">
          <VariableInput
            value={displayValue}
            onChange={handleSelectorChange}
            placeholder={selectorType === 'xpath' ? '//div[@class="example"]' : placeholder}
            className="flex-1"
          />
          <Button
            variant="outline"
            size="icon"
            onClick={() => isPicking && pickingField === id ? stopElementPicker() : openUrlDialog(id)}
            title={isPicking && pickingField === id ? '停止选择' : '可视化选择元素'}
            disabled={isPicking && pickingField !== id}
          >
            {isPicking && pickingField === id ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Crosshair className="w-4 h-4" />
            )}
          </Button>
        </div>
        {isPicking && pickingField === id && (
          <p className="text-xs text-blue-500">Ctrl+点击单选，Alt+点击选择相似元素</p>
        )}
      </div>
    )
  }

  // 渲染桌面元素选择器输入框
  const renderDesktopSelectorInput = (id: string, label: string, placeholder: string) => (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <div className="flex gap-2">
        <VariableInput
          value={(nodeData[id] as string) || ''}
          onChange={(v) => handleChange(id, v)}
          placeholder={placeholder}
          className="flex-1"
        />
        <Button
          variant="outline"
          size="icon"
          onClick={() => isDesktopPicking && desktopPickingField === id ? stopDesktopPicker() : startDesktopPicker(id)}
          title={isDesktopPicking && desktopPickingField === id ? '停止选择' : '捕获桌面元素'}
          disabled={isDesktopPicking && desktopPickingField !== id}
        >
          {isDesktopPicking && desktopPickingField === id ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Crosshair className="w-4 h-4" />
          )}
        </Button>
      </div>
      {isDesktopPicking && desktopPickingField === id && (
        <p className="text-xs text-orange-500">将鼠标移动到目标元素上，按Ctrl+点击捕获</p>
      )}
    </div>
  )

  // 渲染模块配置
  const renderModuleConfig = () => {
    const props = { data: nodeData, onChange: handleChange, renderSelectorInput }
    
    switch (nodeData.moduleType) {
      case 'open_page':
        return <OpenPageConfig data={nodeData} onChange={handleChange} />
      case 'use_opened_page':
        return <UseOpenedPageConfig data={nodeData} onChange={handleChange} />
      case 'click_element':
        return <ClickElementConfig {...props} />
      case 'hover_element':
        return <HoverElementConfig {...props} />
      case 'input_text':
        return <InputTextConfig {...props} />
      case 'get_element_info':
        return <GetElementInfoConfig {...props} />
      case 'wait':
        return <WaitConfig {...props} />
      case 'wait_element':
        return <WaitElementConfig {...props} />
      case 'wait_image':
        return <WaitImageConfig data={nodeData} onChange={handleChange} />
      case 'refresh_page':
        return <RefreshPageConfig data={nodeData} onChange={handleChange} />
      case 'go_back':
        return <GoBackConfig data={nodeData} onChange={handleChange} />
      case 'go_forward':
        return <GoForwardConfig data={nodeData} onChange={handleChange} />
      case 'handle_dialog':
        return <HandleDialogConfig data={nodeData} onChange={handleChange} />
      case 'inject_javascript':
        return <InjectJavaScriptConfig data={nodeData} onChange={handleChange} />
      case 'switch_iframe':
        return <SwitchIframeConfig data={nodeData} onChange={handleChange} />
      case 'switch_to_main':
        return <SwitchToMainConfig />
      case 'close_page':
        return (
          <p className="text-sm text-muted-foreground">
            关闭当前打开的网页，无需额外配置
          </p>
        )
      case 'set_variable':
        return <SetVariableConfig data={nodeData} onChange={handleChange} />
      case 'increment_decrement':
        return <IncrementDecrementConfig data={nodeData} onChange={handleChange} />
      case 'print_log':
        return <PrintLogConfig data={nodeData} onChange={handleChange} />
      case 'play_sound':
        return <PlaySoundConfig data={nodeData} onChange={handleChange} />
      case 'system_notification':
        return <SystemNotificationConfig data={nodeData} onChange={handleChange} />
      case 'play_music':
        return <PlayMusicConfig data={nodeData} onChange={handleChange} />
      case 'play_video':
        return <PlayVideoConfig data={nodeData} onChange={handleChange} />
      case 'view_image':
        return <ViewImageConfig data={nodeData} onChange={handleChange} />
      case 'input_prompt':
        return <InputPromptConfig data={nodeData} onChange={handleChange} />
      case 'text_to_speech':
        return <TextToSpeechConfig data={nodeData} onChange={handleChange} />
      case 'js_script':
        return <JsScriptConfig data={nodeData} onChange={handleChange} />
      case 'python_script':
        return <PythonScriptConfig data={nodeData} onChange={handleChange} />
      case 'extract_table_data':
        return <ExtractTableDataConfig {...props} />
      case 'switch_tab':
        return <SwitchTabConfig data={nodeData} onChange={handleChange} />
      case 'select_dropdown':
        return <SelectDropdownConfig {...props} />
      case 'set_checkbox':
        return <SetCheckboxConfig {...props} />
      case 'drag_element':
        return <DragElementConfig {...props} />
      case 'scroll_page':
        return <ScrollPageConfig data={nodeData} onChange={handleChange} />
      case 'upload_file':
        return <UploadFileConfig {...props} />
      case 'download_file':
        return <DownloadFileConfig {...props} />
      case 'save_image':
        return <SaveImageConfig {...props} />
      case 'get_child_elements':
        return <GetChildElementsConfig {...props} />
      case 'get_sibling_elements':
        return <GetSiblingElementsConfig {...props} />
      case 'screenshot':
        return <ScreenshotConfig {...props} />
      case 'ocr_captcha':
        return <OCRCaptchaConfig {...props} />
      case 'slider_captcha':
        return <SliderCaptchaConfig {...props} />
      case 'send_email':
        return <SendEmailConfig data={nodeData} onChange={handleChange} />
      case 'set_clipboard':
        return <SetClipboardConfig data={nodeData} onChange={handleChange} />
      case 'get_clipboard':
        return <GetClipboardConfig data={nodeData} onChange={handleChange} />
      case 'keyboard_action':
        return <KeyboardActionConfig {...props} />
      case 'real_mouse_scroll':
        return <RealMouseScrollConfig data={nodeData} onChange={handleChange} />
      case 'shutdown_system':
        return <ShutdownSystemConfig data={nodeData} onChange={handleChange} />
      case 'lock_screen':
        return <LockScreenConfig />
      case 'window_focus':
        return <WindowFocusConfig data={nodeData} onChange={handleChange} />
      case 'real_mouse_click':
        return <RealMouseClickConfig data={nodeData} onChange={handleChange} />
      case 'real_mouse_move':
        return <RealMouseMoveConfig data={nodeData} onChange={handleChange} />
      case 'real_mouse_drag':
        return <RealMouseDragConfig data={nodeData} onChange={handleChange} />
      case 'real_keyboard':
        return <RealKeyboardConfig data={nodeData} onChange={handleChange} />
      case 'run_command':
        return <RunCommandConfig data={nodeData} onChange={handleChange} />
      case 'click_image':
        return <ClickImageConfig data={nodeData} onChange={handleChange} />
      case 'image_exists':
        return <ImageExistsConfig data={nodeData} onChange={handleChange} />
      case 'element_exists':
        return <ElementExistsConfig {...props} />
      case 'element_visible':
        return <ElementVisibleConfig {...props} />
      case 'get_mouse_position':
        return <GetMousePositionConfig data={nodeData} onChange={handleChange} />
      case 'screenshot_screen':
        return <ScreenshotScreenConfig data={nodeData} onChange={handleChange} />
      case 'rename_file':
        return <RenameFileConfig data={nodeData} onChange={handleChange} />
      case 'network_capture':
        return <NetworkCaptureConfig data={nodeData} onChange={handleChange} />
      case 'macro_recorder':
        return <MacroRecorderConfig data={nodeData} onChange={handleChange} />
      case 'ai_chat':
        return <AIChatConfig data={nodeData} onChange={handleChange} />
      case 'ai_vision':
        return <AIVisionConfig {...props} />
      case 'ai_smart_scraper':
        return <AISmartScraperConfig data={nodeData} onChange={handleChange} />
      case 'ai_element_selector':
        return <AIElementSelectorConfig data={nodeData} onChange={handleChange} />
      case 'firecrawl_scrape':
        return <FirecrawlScrapeConfig data={nodeData} onChange={handleChange} />
      case 'firecrawl_map':
        return <FirecrawlMapConfig data={nodeData} onChange={handleChange} />
      case 'firecrawl_crawl':
        return <FirecrawlCrawlConfig data={nodeData} onChange={handleChange} />
      case 'api_request':
        return <ApiRequestConfig data={nodeData} onChange={handleChange} />
      case 'condition':
        return <ConditionConfig {...props} />
      case 'loop':
        return <LoopConfig data={nodeData} onChange={handleChange} />
      case 'foreach':
        return <ForeachConfig data={nodeData} onChange={handleChange} />
      case 'foreach_dict':
        return <ForeachDictConfig data={nodeData} onChange={handleChange} />
      case 'scheduled_task':
        return <ScheduledTaskConfig data={nodeData} onChange={handleChange} />
      case 'subflow':
        return <SubflowConfig data={nodeData} onChange={handleChange} />
      case 'break_loop':
        return (
          <p className="text-sm text-muted-foreground">
            跳出当前循环，继续执行循环后的模块
          </p>
        )
      case 'continue_loop':
        return (
          <p className="text-sm text-muted-foreground">
            跳过当前循环的剩余部分，进入下一次循环
          </p>
        )
      case 'stop_workflow':
        return (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              立即停止整个工作流的执行，不再执行后续模块
            </p>
            <div className="space-y-2">
              <Label htmlFor="stopReason">停止原因（可选）</Label>
              <Input
                id="stopReason"
                value={(nodeData.stopReason as string) || ''}
                onChange={(e) => handleChange('stopReason', e.target.value)}
                placeholder="输入停止原因，将显示在日志中"
                className="transition-all duration-200 focus:ring-2 focus:ring-red-500/20 focus:border-red-500"
              />
            </div>
          </div>
        )
      // 触发器模块
      case 'webhook_trigger':
        return <WebhookTriggerConfig data={nodeData} onChange={handleChange} />
      case 'hotkey_trigger':
        return <HotkeyTriggerConfig data={nodeData} onChange={handleChange} />
      case 'file_watcher_trigger':
        return <FileWatcherTriggerConfig data={nodeData} onChange={handleChange} />
      case 'email_trigger':
        return <EmailTriggerConfig data={nodeData} onChange={handleChange} />
      case 'api_trigger':
        return <ApiTriggerConfig data={nodeData} onChange={handleChange} />
      case 'mouse_trigger':
        return <MouseTriggerConfig data={nodeData} onChange={handleChange} />
      case 'image_trigger':
        return <ImageTriggerConfig data={nodeData} onChange={handleChange} />
      case 'sound_trigger':
        return <SoundTriggerConfig data={nodeData} onChange={handleChange} />
      case 'face_trigger':
        return <FaceTriggerConfig data={nodeData} onChange={handleChange} />
      case 'gesture_trigger':
        return <GestureTriggerConfig data={nodeData} onChange={handleChange} />
      case 'element_change_trigger':
        return <ElementChangeTriggerConfig {...props} />
      case 'regex_extract':
        return <RegexExtractConfig data={nodeData} onChange={handleChange} />
      case 'string_replace':
        return <StringReplaceConfig data={nodeData} onChange={handleChange} />
      case 'string_split':
        return <StringSplitConfig data={nodeData} onChange={handleChange} />
      case 'string_join':
        return <StringJoinConfig data={nodeData} onChange={handleChange} />
      case 'string_concat':
        return <StringConcatConfig data={nodeData} onChange={handleChange} />
      case 'string_trim':
        return <StringTrimConfig data={nodeData} onChange={handleChange} />
      case 'string_case':
        return <StringCaseConfig data={nodeData} onChange={handleChange} />
      case 'string_substring':
        return <StringSubstringConfig data={nodeData} onChange={handleChange} />
      case 'json_parse':
        return <JsonParseConfig data={nodeData} onChange={handleChange} />
      case 'base64':
        return <Base64Config data={nodeData} onChange={handleChange} />
      case 'random_number':
        return <RandomNumberConfig data={nodeData} onChange={handleChange} />
      case 'get_time':
        return <GetTimeConfig data={nodeData} onChange={handleChange} />
      case 'read_excel':
        return <ReadExcelConfig data={nodeData} onChange={handleChange} />
      case 'list_operation':
        return <ListOperationConfig data={nodeData} onChange={handleChange} />
      case 'list_get':
        return <ListGetConfig data={nodeData} onChange={handleChange} />
      case 'list_length':
        return <ListLengthConfig data={nodeData} onChange={handleChange} />
      case 'list_export':
        return <ListExportConfig data={nodeData} onChange={handleChange} />
      case 'list_sum':
        return <ListSumConfig data={nodeData} onChange={handleChange} />
      case 'list_average':
        return <ListAverageConfig data={nodeData} onChange={handleChange} />
      case 'list_max':
        return <ListMaxConfig data={nodeData} onChange={handleChange} />
      case 'list_min':
        return <ListMinConfig data={nodeData} onChange={handleChange} />
      case 'list_sort':
        return <ListSortConfig data={nodeData} onChange={handleChange} />
      case 'list_unique':
        return <ListUniqueConfig data={nodeData} onChange={handleChange} />
      case 'list_slice':
        return <ListSliceConfig data={nodeData} onChange={handleChange} />
      case 'list_reverse':
        return <ListReverseConfig data={nodeData} onChange={handleChange} />
      case 'list_find':
        return <ListFindConfig data={nodeData} onChange={handleChange} />
      case 'list_count':
        return <ListCountConfig data={nodeData} onChange={handleChange} />
      case 'list_filter':
        return <ListFilterConfig data={nodeData} onChange={handleChange} />
      case 'list_map':
        return <ListMapConfig data={nodeData} onChange={handleChange} />
      case 'list_merge':
        return <ListMergeConfig data={nodeData} onChange={handleChange} />
      case 'list_flatten':
        return <ListFlattenConfig data={nodeData} onChange={handleChange} />
      case 'list_chunk':
        return <ListChunkConfig data={nodeData} onChange={handleChange} />
      case 'list_remove_empty':
        return <ListRemoveEmptyConfig data={nodeData} onChange={handleChange} />
      case 'list_intersection':
        return <ListIntersectionConfig data={nodeData} onChange={handleChange} />
      case 'list_union':
        return <ListUnionConfig data={nodeData} onChange={handleChange} />
      case 'list_difference':
        return <ListDifferenceConfig data={nodeData} onChange={handleChange} />
      case 'list_cartesian_product':
        return <ListCartesianProductConfig data={nodeData} onChange={handleChange} />
      case 'list_shuffle':
        return <ListShuffleConfig data={nodeData} onChange={handleChange} />
      case 'list_sample':
        return <ListSampleConfig data={nodeData} onChange={handleChange} />
      case 'dict_operation':
        return <DictOperationConfig data={nodeData} onChange={handleChange} />
      case 'dict_get':
        return <DictGetConfig data={nodeData} onChange={handleChange} />
      case 'dict_keys':
        return <DictKeysConfig data={nodeData} onChange={handleChange} />
      case 'dict_merge':
        return <DictMergeConfig data={nodeData} onChange={handleChange} />
      case 'dict_filter':
        return <DictFilterConfig data={nodeData} onChange={handleChange} />
      case 'dict_map_values':
        return <DictMapValuesConfig data={nodeData} onChange={handleChange} />
      case 'dict_invert':
        return <DictInvertConfig data={nodeData} onChange={handleChange} />
      case 'dict_sort':
        return <DictSortConfig data={nodeData} onChange={handleChange} />
      case 'dict_deep_copy':
        return <DictDeepCopyConfig data={nodeData} onChange={handleChange} />
      case 'dict_get_path':
        return <DictGetPathConfig data={nodeData} onChange={handleChange} />
      case 'dict_flatten':
        return <DictFlattenConfig data={nodeData} onChange={handleChange} />
      case 'math_round':
        return <MathRoundConfig data={nodeData} onChange={handleChange} />
      case 'math_base_convert':
        return <MathBaseConvertConfig data={nodeData} onChange={handleChange} />
      case 'math_floor':
        return <MathFloorConfig data={nodeData} onChange={handleChange} />
      case 'math_modulo':
        return <MathModuloConfig data={nodeData} onChange={handleChange} />
      case 'math_abs':
        return <MathAbsConfig data={nodeData} onChange={handleChange} />
      case 'math_sqrt':
        return <MathSqrtConfig data={nodeData} onChange={handleChange} />
      case 'math_power':
        return <MathPowerConfig data={nodeData} onChange={handleChange} />
      case 'math_log':
        return <MathLogConfig data={nodeData} onChange={handleChange} />
      case 'math_trig':
        return <MathTrigConfig data={nodeData} onChange={handleChange} />
      case 'math_exp':
        return <MathExpConfig data={nodeData} onChange={handleChange} />
      case 'math_gcd':
        return <MathGcdConfig data={nodeData} onChange={handleChange} />
      case 'math_lcm':
        return <MathLcmConfig data={nodeData} onChange={handleChange} />
      case 'math_factorial':
        return <MathFactorialConfig data={nodeData} onChange={handleChange} />
      case 'math_permutation':
        return <MathPermutationConfig data={nodeData} onChange={handleChange} />
      case 'math_percentage':
        return <MathPercentageConfig data={nodeData} onChange={handleChange} />
      case 'math_clamp':
        return <MathClampConfig data={nodeData} onChange={handleChange} />
      case 'math_random_advanced':
        return <MathRandomAdvancedConfig data={nodeData} onChange={handleChange} />
      case 'stat_median':
        return <StatMedianConfig data={nodeData} onChange={handleChange} />
      case 'stat_mode':
        return <StatModeConfig data={nodeData} onChange={handleChange} />
      case 'stat_variance':
        return <StatVarianceConfig data={nodeData} onChange={handleChange} />
      case 'stat_stdev':
        return <StatStdevConfig data={nodeData} onChange={handleChange} />
      case 'stat_percentile':
        return <StatPercentileConfig data={nodeData} onChange={handleChange} />
      case 'stat_normalize':
        return <StatNormalizeConfig data={nodeData} onChange={handleChange} />
      case 'stat_standardize':
        return <StatStandardizeConfig data={nodeData} onChange={handleChange} />
      case 'csv_parse':
        return <CsvParseConfig data={nodeData} onChange={handleChange} />
      case 'csv_generate':
        return <CsvGenerateConfig data={nodeData} onChange={handleChange} />
      case 'list_to_string_advanced':
        return <ListToStringAdvancedConfig data={nodeData} onChange={handleChange} />
      case 'table_add_row':
        return <TableAddRowConfig data={nodeData} onChange={handleChange} />
      case 'table_add_column':
        return <TableAddColumnConfig data={nodeData} onChange={handleChange} />
      case 'table_set_cell':
        return <TableSetCellConfig data={nodeData} onChange={handleChange} />
      case 'table_get_cell':
        return <TableGetCellConfig data={nodeData} onChange={handleChange} />
      case 'table_delete_row':
        return <TableDeleteRowConfig data={nodeData} onChange={handleChange} />
      case 'table_clear':
        return <TableClearConfig />
      case 'table_export':
        return <TableExportConfig data={nodeData} onChange={handleChange} />
      case 'db_connect':
        return <DbConnectConfig data={nodeData} onChange={handleChange} />
      case 'db_query':
        return <DbQueryConfig data={nodeData} onChange={handleChange} />
      case 'db_execute':
        return <DbExecuteConfig data={nodeData} onChange={handleChange} />
      case 'db_insert':
        return <DbInsertConfig data={nodeData} onChange={handleChange} />
      case 'db_update':
        return <DbUpdateConfig data={nodeData} onChange={handleChange} />
      case 'db_delete':
        return <DbDeleteConfig data={nodeData} onChange={handleChange} />
      case 'db_close':
        return <DbCloseConfig data={nodeData} onChange={handleChange} />
      case 'format_convert':
        return <FormatConvertConfig data={nodeData} onChange={handleChange} />
      case 'compress_image':
        return <CompressImageConfig data={nodeData} onChange={handleChange} />
      case 'compress_video':
        return <CompressVideoConfig data={nodeData} onChange={handleChange} />
      case 'extract_audio':
        return <ExtractAudioConfig data={nodeData} onChange={handleChange} />
      
      // 格式工厂模块
      case 'image_format_convert':
        return <ImageFormatConvertConfig config={nodeData} onChange={(newConfig) => handleChange('config', newConfig)} />
      case 'video_format_convert':
        return <VideoFormatConvertConfig config={nodeData} onChange={(newConfig) => handleChange('config', newConfig)} />
      case 'audio_format_convert':
        return <AudioFormatConvertConfig config={nodeData} onChange={(newConfig) => handleChange('config', newConfig)} />
      case 'video_to_audio':
        return <VideoToAudioConfig config={nodeData} onChange={(newConfig) => handleChange('config', newConfig)} />
      case 'video_to_gif':
        return <VideoToGIFConfig config={nodeData} onChange={(newConfig) => handleChange('config', newConfig)} />
      case 'batch_format_convert':
        return <BatchFormatConvertConfig config={nodeData} onChange={(newConfig) => handleChange('config', newConfig)} />
      
      case 'trim_video':
        return <TrimVideoConfig data={nodeData} onChange={handleChange} />
      case 'merge_media':
        return <MergeMediaConfig data={nodeData} onChange={handleChange} />
      case 'add_watermark':
        return <AddWatermarkConfig data={nodeData} onChange={handleChange} />
      case 'face_recognition':
        return <FaceRecognitionConfig data={nodeData} onChange={handleChange} />
      case 'image_ocr':
        return <ImageOCRConfig data={nodeData} onChange={handleChange} />
      case 'download_m3u8':
        return <DownloadM3U8Config data={nodeData} onChange={handleChange} />
      case 'rotate_video':
        return <RotateVideoConfig data={nodeData} onChange={handleChange} />
      case 'video_speed':
        return <VideoSpeedConfig data={nodeData} onChange={handleChange} />
      case 'extract_frame':
        return <ExtractFrameConfig data={nodeData} onChange={handleChange} />
      case 'add_subtitle':
        return <AddSubtitleConfig data={nodeData} onChange={handleChange} />
      case 'adjust_volume':
        return <AdjustVolumeConfig data={nodeData} onChange={handleChange} />
      case 'resize_video':
        return <ResizeVideoConfig data={nodeData} onChange={handleChange} />
      case 'image_grayscale':
        return <ImageGrayscaleConfig data={nodeData} onChange={handleChange} />
      case 'image_round_corners':
        return <ImageRoundCornersConfig data={nodeData} onChange={handleChange} />
      case 'audio_to_text':
        return <AudioToTextConfig data={nodeData} onChange={handleChange} />
      case 'qr_generate':
        return <QRGenerateConfig data={nodeData} onChange={handleChange} />
      case 'qr_decode':
        return <QRDecodeConfig data={nodeData} onChange={handleChange} />
      case 'screen_record':
        return <ScreenRecordConfig data={nodeData} onChange={handleChange} />
      case 'camera_capture':
        return <CameraCaptureConfig data={nodeData} onChange={handleChange} />
      case 'camera_record':
        return <CameraRecordConfig data={nodeData} onChange={handleChange} />
      case 'list_files':
        return <ListFilesConfig data={nodeData} onChange={handleChange} />
      case 'copy_file':
        return <CopyFileConfig data={nodeData} onChange={handleChange} />
      case 'move_file':
        return <MoveFileConfig data={nodeData} onChange={handleChange} />
      case 'delete_file':
        return <DeleteFileConfig data={nodeData} onChange={handleChange} />
      case 'create_folder':
        return <CreateFolderConfig data={nodeData} onChange={handleChange} />
      case 'file_exists':
        return <FileExistsConfig data={nodeData} onChange={handleChange} />
      case 'get_file_info':
        return <GetFileInfoConfig data={nodeData} onChange={handleChange} />
      case 'read_text_file':
        return <ReadTextFileConfig data={nodeData} onChange={handleChange} />
      case 'write_text_file':
        return <WriteTextFileConfig data={nodeData} onChange={handleChange} />
      case 'rename_folder':
        return <RenameFolderConfig data={nodeData} onChange={handleChange} />
      
      // QQ机器人模块
      case 'qq_send_message':
        return <QQSendMessageConfig data={nodeData} onChange={handleChange} />
      case 'qq_send_image':
        return <QQSendImageConfig data={nodeData} onChange={handleChange} />
      case 'qq_send_file':
        return <QQSendFileConfig data={nodeData} onChange={handleChange} />
      case 'qq_get_friends':
        return <QQGetFriendsConfig data={nodeData} onChange={handleChange} />
      case 'qq_get_groups':
        return <QQGetGroupsConfig data={nodeData} onChange={handleChange} />
      case 'qq_get_group_members':
        return <QQGetGroupMembersConfig data={nodeData} onChange={handleChange} />
      case 'qq_get_login_info':
        return <QQGetLoginInfoConfig data={nodeData} onChange={handleChange} />
      case 'qq_wait_message':
        return <QQWaitMessageConfig data={nodeData} onChange={handleChange} />
      // 微信自动化模块
      case 'wechat_send_message':
        return <WeChatSendMessageConfig data={nodeData} onChange={handleChange} />
      case 'wechat_send_file':
        return <WeChatSendFileConfig data={nodeData} onChange={handleChange} />
      // 手机自动化模块
      case 'phone_tap':
        return <PhoneTapConfig data={nodeData} onChange={handleChange} />
      case 'phone_swipe':
        return <PhoneSwipeConfig data={nodeData} onChange={handleChange} />
      case 'phone_long_press':
        return <PhoneLongPressConfig data={nodeData} onChange={handleChange} />
      case 'phone_input_text':
        return <PhoneInputTextConfig data={nodeData} onChange={handleChange} />
      case 'phone_press_key':
        return <PhonePressKeyConfig data={nodeData} onChange={handleChange} />
      case 'phone_screenshot':
        return <PhoneScreenshotConfig data={nodeData} onChange={handleChange} />
      case 'phone_start_mirror':
        return <PhoneStartMirrorConfig data={nodeData} onChange={handleChange} />
      case 'phone_stop_mirror':
        return <PhoneStopMirrorConfig />
      case 'phone_install_app':
        return <PhoneInstallAppConfig data={nodeData} onChange={handleChange} />
      case 'phone_start_app':
        return <PhoneStartAppConfig data={nodeData} onChange={handleChange} />
      case 'phone_stop_app':
        return <PhoneStopAppConfig data={nodeData} onChange={handleChange} />
      case 'phone_uninstall_app':
        return <PhoneUninstallAppConfig data={nodeData} onChange={handleChange} />
      case 'phone_push_file':
        return <PhonePushFileConfig data={nodeData} onChange={handleChange} />
      case 'phone_pull_file':
        return <PhonePullFileConfig data={nodeData} onChange={handleChange} />
      case 'phone_click_image':
        return <PhoneClickImageConfig data={nodeData} onChange={handleChange} />
      case 'phone_click_text':
        return <PhoneClickTextConfig data={nodeData} onChange={handleChange} />
      case 'phone_wait_image':
        return <PhoneWaitImageConfig data={nodeData} onChange={handleChange} />
      case 'phone_image_exists':
        return <PhoneImageExistsConfig data={nodeData} onChange={handleChange} />
      case 'phone_set_volume':
        return <PhoneSetVolumeConfig data={nodeData} onChange={handleChange} />
      case 'phone_set_brightness':
        return <PhoneSetBrightnessConfig data={nodeData} onChange={handleChange} />
      case 'phone_set_clipboard':
        return <PhoneSetClipboardConfig data={nodeData} onChange={handleChange} />
      case 'phone_get_clipboard':
        return <PhoneGetClipboardConfig data={nodeData} onChange={handleChange} />
      // PDF处理模块
      case 'pdf_to_images':
        return <PDFToImagesConfig config={nodeData} updateConfig={handleChange} />
      case 'images_to_pdf':
        return <ImagesToPDFConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_merge':
        return <PDFMergeConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_split':
        return <PDFSplitConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_extract_text':
        return <PDFExtractTextConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_extract_images':
        return <PDFExtractImagesConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_encrypt':
        return <PDFEncryptConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_decrypt':
        return <PDFDecryptConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_add_watermark':
        return <PDFAddWatermarkConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_rotate':
        return <PDFRotateConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_delete_pages':
        return <PDFDeletePagesConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_get_info':
        return <PDFGetInfoConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_compress':
        return <PDFCompressConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_insert_pages':
        return <PDFInsertPagesConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_reorder_pages':
        return <PDFReorderPagesConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_to_word':
        return <PDFToWordConfig config={nodeData} updateConfig={handleChange} />
      // 文档转换模块
      case 'markdown_to_html':
        return <MarkdownToHTMLConfig config={nodeData} updateConfig={handleChange} />
      case 'html_to_markdown':
        return <HTMLToMarkdownConfig config={nodeData} updateConfig={handleChange} />
      case 'markdown_to_pdf':
        return <MarkdownToPDFConfig config={nodeData} updateConfig={handleChange} />
      case 'markdown_to_docx':
        return <MarkdownToDocxConfig config={nodeData} updateConfig={handleChange} />
      case 'docx_to_markdown':
        return <DocxToMarkdownConfig config={nodeData} updateConfig={handleChange} />
      case 'html_to_docx':
        return <HTMLToDocxConfig config={nodeData} updateConfig={handleChange} />
      case 'docx_to_html':
        return <DocxToHTMLConfig config={nodeData} updateConfig={handleChange} />
      case 'markdown_to_epub':
        return <MarkdownToEPUBConfig config={nodeData} updateConfig={handleChange} />
      case 'epub_to_markdown':
        return <EPUBToMarkdownConfig config={nodeData} updateConfig={handleChange} />
      case 'latex_to_pdf':
        return <LaTeXToPDFConfig config={nodeData} updateConfig={handleChange} />
      case 'rst_to_html':
        return <RSTToHTMLConfig config={nodeData} updateConfig={handleChange} />
      case 'org_to_html':
        return <OrgToHTMLConfig config={nodeData} updateConfig={handleChange} />
      case 'universal_doc_convert':
        return <UniversalDocConvertConfig config={nodeData} updateConfig={handleChange} />
      // Pillow图像处理模块
      case 'image_resize':
        return <ImageResizeConfig config={nodeData} updateConfig={handleChange} />
      case 'image_crop':
        return <ImageCropConfig config={nodeData} updateConfig={handleChange} />
      case 'image_rotate':
        return <ImageRotateConfig config={nodeData} updateConfig={handleChange} />
      case 'image_flip':
        return <ImageFlipConfig config={nodeData} updateConfig={handleChange} />
      case 'image_blur':
        return <ImageBlurConfig config={nodeData} updateConfig={handleChange} />
      case 'image_sharpen':
        return <ImageSharpenConfig config={nodeData} updateConfig={handleChange} />
      case 'image_brightness':
        return <ImageBrightnessConfig config={nodeData} updateConfig={handleChange} />
      case 'image_contrast':
        return <ImageContrastConfig config={nodeData} updateConfig={handleChange} />
      case 'image_color_balance':
        return <ImageColorBalanceConfig config={nodeData} updateConfig={handleChange} />
      case 'image_convert_format':
        return <ImageConvertFormatConfig config={nodeData} updateConfig={handleChange} />
      case 'image_add_text':
        return <ImageAddTextConfig config={nodeData} updateConfig={handleChange} />
      case 'image_merge':
        return <ImageMergeConfig config={nodeData} updateConfig={handleChange} />
      case 'image_thumbnail':
        return <ImageThumbnailConfig config={nodeData} updateConfig={handleChange} />
      case 'image_filter':
        return <ImageFilterConfig config={nodeData} updateConfig={handleChange} />
      case 'image_get_info':
        return <ImageGetInfoConfig config={nodeData} updateConfig={handleChange} />
      case 'image_remove_bg':
        return <ImageRemoveBgConfig config={nodeData} updateConfig={handleChange} />
      // 高级模块
      case 'export_log':
        return <ExportLogConfig data={nodeData} onChange={handleChange} />
      case 'click_text':
        return <ClickTextConfig data={nodeData} onChange={handleChange} />
      case 'hover_image':
        return <HoverImageConfig data={nodeData} onChange={handleChange} />
      case 'hover_text':
        return <HoverTextConfig data={nodeData} onChange={handleChange} />
      case 'drag_image':
        return <DragImageConfig data={nodeData} onChange={handleChange} />
      case 'share_folder':
        return <ShareFolderConfig data={nodeData} onChange={handleChange} />
      case 'share_file':
        return <ShareFileConfig data={nodeData} onChange={handleChange} />
      case 'stop_share':
        return <StopShareConfig data={nodeData} onChange={handleChange} />
      case 'start_screen_share':
        return <StartScreenShareConfig data={nodeData} onChange={handleChange} />
      case 'stop_screen_share':
        return <StopScreenShareConfig data={nodeData} onChange={handleChange} />
      // 实用工具模块
      case 'file_hash_compare':
        return <FileHashCompareConfig config={nodeData} updateConfig={handleChange} />
      case 'file_diff_compare':
        return <FileDiffCompareConfig config={nodeData} updateConfig={handleChange} />
      case 'folder_hash_compare':
        return <FolderHashCompareConfig config={nodeData} updateConfig={handleChange} />
      case 'folder_diff_compare':
        return <FolderDiffCompareConfig config={nodeData} updateConfig={handleChange} />
      case 'random_password_generator':
        return <RandomPasswordGeneratorConfig config={nodeData} updateConfig={handleChange} />
      case 'url_encode_decode':
        return <URLEncodeDecodeConfig config={nodeData} updateConfig={handleChange} />
      case 'md5_encrypt':
        return <MD5EncryptConfig config={nodeData} updateConfig={handleChange} />
      case 'sha_encrypt':
        return <SHAEncryptConfig config={nodeData} updateConfig={handleChange} />
      case 'timestamp_converter':
        return <TimestampConverterConfig config={nodeData} updateConfig={handleChange} />
      case 'rgb_to_hsv':
        return <RGBToHSVConfig config={nodeData} updateConfig={handleChange} />
      case 'rgb_to_cmyk':
        return <RGBToCMYKConfig config={nodeData} updateConfig={handleChange} />
      case 'hex_to_cmyk':
        return <HEXToCMYKConfig config={nodeData} updateConfig={handleChange} />
      case 'uuid_generator':
        return <UUIDGeneratorConfig config={nodeData} updateConfig={handleChange} />
      case 'printer_call':
        return <PrinterCallConfig config={nodeData} updateConfig={handleChange} />
      // 测试报告模块
      case 'allure_init':
        return <AllureInitConfig data={nodeData} onChange={handleChange} />
      case 'allure_start_test':
        return <AllureStartTestConfig data={nodeData} onChange={handleChange} />
      case 'allure_add_step':
        return <AllureAddStepConfig data={nodeData} onChange={handleChange} />
      case 'allure_add_attachment':
        return <AllureAddAttachmentConfig data={nodeData} onChange={handleChange} />
      case 'allure_stop_test':
        return <AllureStopTestConfig data={nodeData} onChange={handleChange} />
      case 'allure_generate_report':
        return <AllureGenerateReportConfig data={nodeData} onChange={handleChange} />
      // 桌面应用自动化模块
      case 'desktop_app_start':
        return <DesktopAppStartConfig data={nodeData} onChange={handleChange} />
      case 'desktop_app_connect':
        return <DesktopAppConnectConfig data={nodeData} onChange={handleChange} />
      case 'desktop_app_close':
        return <DesktopAppCloseConfig data={nodeData} onChange={handleChange} />
      case 'desktop_app_get_info':
        return <DesktopAppGetInfoConfig data={nodeData} onChange={handleChange} />
      case 'desktop_app_wait_ready':
        return <DesktopAppWaitReadyConfig data={nodeData} onChange={handleChange} />
      case 'desktop_window_activate':
        return <DesktopWindowActivateConfig data={nodeData} onChange={handleChange} />
      case 'desktop_window_state':
        return <DesktopWindowStateConfig data={nodeData} onChange={handleChange} />
      case 'desktop_window_move':
        return <DesktopWindowMoveConfig data={nodeData} onChange={handleChange} />
      case 'desktop_window_resize':
        return <DesktopWindowResizeConfig data={nodeData} onChange={handleChange} />
      case 'desktop_window_list':
        return <DesktopWindowListConfig data={nodeData} onChange={handleChange} />
      case 'desktop_window_topmost':
        return <DesktopWindowTopmostConfig data={nodeData} onChange={handleChange} />
      case 'desktop_window_capture':
        return <DesktopWindowCaptureConfig data={nodeData} onChange={handleChange} />
      case 'desktop_find_control':
        return <DesktopFindControlConfig data={nodeData} onChange={handleChange} renderDesktopSelectorInput={renderDesktopSelectorInput} />
      case 'desktop_control_info':
        return <DesktopControlInfoConfig data={nodeData} onChange={handleChange} />
      case 'desktop_control_tree':
        return <DesktopControlTreeConfig data={nodeData} onChange={handleChange} />
      case 'desktop_wait_control':
        return <DesktopWaitControlConfig data={nodeData} onChange={handleChange} renderDesktopSelectorInput={renderDesktopSelectorInput} />
      case 'desktop_click_control':
        return <DesktopClickControlConfig data={nodeData} onChange={handleChange} />
      case 'desktop_input_control':
        return <DesktopInputControlConfig data={nodeData} onChange={handleChange} />
      case 'desktop_get_text':
        return <DesktopGetTextConfig data={nodeData} onChange={handleChange} />
      case 'desktop_set_value':
        return <DesktopSetValueConfig data={nodeData} onChange={handleChange} />
      case 'desktop_select_combo':
        return <DesktopSelectComboConfig data={nodeData} onChange={handleChange} />
      case 'desktop_checkbox':
        return <DesktopCheckboxConfig data={nodeData} onChange={handleChange} />
      case 'desktop_radio':
        return <DesktopRadioConfig data={nodeData} onChange={handleChange} />
      case 'desktop_drag_control':
        return <DesktopDragControlConfig data={nodeData} onChange={handleChange} />
      case 'desktop_menu_click':
        return <DesktopMenuClickConfig data={nodeData} onChange={handleChange} />
      case 'desktop_list_operate':
        return <DesktopListOperateConfig data={nodeData} onChange={handleChange} />
      case 'desktop_send_keys':
        return <DesktopSendKeysConfig data={nodeData} onChange={handleChange} />
      case 'desktop_get_property':
        return <DesktopGetPropertyConfig data={nodeData} onChange={handleChange} />
      case 'desktop_dialog_handle':
        return <DesktopDialogHandleConfig data={nodeData} onChange={handleChange} />
      case 'desktop_scroll_control':
        return <DesktopScrollControlConfig data={nodeData} onChange={handleChange} />
      case 'desktop_get_control_info':
        return <DesktopGetControlInfoConfig data={nodeData} onChange={handleChange} />
      case 'desktop_get_control_tree':
        return <DesktopGetControlTreeConfig data={nodeData} onChange={handleChange} />
      // Apprise多渠道通知模块
      case 'notify_discord':
        return <NotifyDiscordConfig data={nodeData} onChange={handleChange} />
      case 'notify_telegram':
        return <NotifyTelegramConfig data={nodeData} onChange={handleChange} />
      case 'notify_dingtalk':
        return <NotifyDingTalkConfig data={nodeData} onChange={handleChange} />
      case 'notify_wecom':
        return <NotifyWeComConfig data={nodeData} onChange={handleChange} />
      case 'notify_feishu':
        return <NotifyFeishuConfig data={nodeData} onChange={handleChange} />
      case 'notify_bark':
        return <NotifyBarkConfig data={nodeData} onChange={handleChange} />
      case 'notify_slack':
        return <NotifySlackConfig data={nodeData} onChange={handleChange} />
      case 'notify_msteams':
        return <NotifyMSTeamsConfig data={nodeData} onChange={handleChange} />
      case 'notify_pushover':
        return <NotifyPushoverConfig data={nodeData} onChange={handleChange} />
      case 'notify_pushbullet':
        return <NotifyPushBulletConfig data={nodeData} onChange={handleChange} />
      case 'notify_gotify':
        return <NotifyGotifyConfig data={nodeData} onChange={handleChange} />
      case 'notify_serverchan':
        return <NotifyServerChanConfig data={nodeData} onChange={handleChange} />
      case 'notify_pushplus':
        return <NotifyPushPlusConfig data={nodeData} onChange={handleChange} />
      case 'notify_webhook':
        return <NotifyWebhookConfig data={nodeData} onChange={handleChange} />
      case 'notify_ntfy':
        return <NotifyNtfyConfig data={nodeData} onChange={handleChange} />
      case 'notify_matrix':
        return <NotifyMatrixConfig data={nodeData} onChange={handleChange} />
      case 'notify_rocketchat':
        return <NotifyRocketChatConfig data={nodeData} onChange={handleChange} />
      
      // Webhook请求模块
      case 'webhook_request':
        return <WebhookRequestConfig data={nodeData} onChange={handleChange} />
      
      // 飞书自动化模块
      case 'feishu_bitable_write':
        return <FeishuBitableWriteConfig data={nodeData} onChange={handleChange} />
      case 'feishu_bitable_read':
        return <FeishuBitableReadConfig data={nodeData} onChange={handleChange} />
      case 'feishu_sheet_write':
        return <FeishuSheetWriteConfig data={nodeData} onChange={handleChange} />
      case 'feishu_sheet_read':
        return <FeishuSheetReadConfig data={nodeData} onChange={handleChange} />
      
      // Oracle数据库模块
      case 'oracle_connect':
        return <OracleConnectConfig data={nodeData} onChange={handleChange} />
      case 'oracle_query':
        return <OracleQueryConfig data={nodeData} onChange={handleChange} />
      case 'oracle_execute':
        return <OracleExecuteConfig data={nodeData} onChange={handleChange} />
      case 'oracle_insert':
        return <OracleInsertConfig data={nodeData} onChange={handleChange} />
      case 'oracle_update':
        return <OracleUpdateConfig data={nodeData} onChange={handleChange} />
      case 'oracle_delete':
        return <OracleDeleteConfig data={nodeData} onChange={handleChange} />
      
      // PostgreSQL数据库模块
      case 'postgresql_connect':
        return <PostgreSQLConnectConfig data={nodeData} onChange={handleChange} />
      case 'postgresql_query':
        return <PostgreSQLQueryConfig data={nodeData} onChange={handleChange} />
      case 'postgresql_execute':
        return <PostgreSQLExecuteConfig data={nodeData} onChange={handleChange} />
      case 'postgresql_insert':
        return <PostgreSQLInsertConfig data={nodeData} onChange={handleChange} />
      case 'postgresql_update':
        return <PostgreSQLUpdateConfig data={nodeData} onChange={handleChange} />
      case 'postgresql_delete':
        return <PostgreSQLDeleteConfig data={nodeData} onChange={handleChange} />
      
      // MongoDB数据库模块
      case 'mongodb_connect':
        return <MongoDBConnectConfig data={nodeData} onChange={handleChange} />
      case 'mongodb_find':
        return <MongoDBFindConfig data={nodeData} onChange={handleChange} />
      case 'mongodb_insert':
        return <MongoDBInsertConfig data={nodeData} onChange={handleChange} />
      case 'mongodb_update':
        return <MongoDBUpdateConfig data={nodeData} onChange={handleChange} />
      case 'mongodb_delete':
        return <MongoDBDeleteConfig data={nodeData} onChange={handleChange} />
      
      // SQL Server数据库模块
      case 'sqlserver_connect':
        return <SQLServerConnectConfig data={nodeData} onChange={handleChange} />
      case 'sqlserver_query':
        return <SQLServerQueryConfig data={nodeData} onChange={handleChange} />
      case 'sqlserver_execute':
        return <SQLServerExecuteConfig data={nodeData} onChange={handleChange} />
      case 'sqlserver_insert':
        return <SQLServerInsertConfig data={nodeData} onChange={handleChange} />
      case 'sqlserver_update':
        return <SQLServerUpdateConfig data={nodeData} onChange={handleChange} />
      case 'sqlserver_delete':
        return <SQLServerDeleteConfig data={nodeData} onChange={handleChange} />
      
      // SQLite数据库模块
      case 'sqlite_connect':
        return <SQLiteConnectConfig data={nodeData} onChange={handleChange} />
      case 'sqlite_query':
        return <SQLiteQueryConfig data={nodeData} onChange={handleChange} />
      case 'sqlite_execute':
        return <SQLiteExecuteConfig data={nodeData} onChange={handleChange} />
      case 'sqlite_insert':
        return <SQLiteInsertConfig data={nodeData} onChange={handleChange} />
      case 'sqlite_update':
        return <SQLiteUpdateConfig data={nodeData} onChange={handleChange} />
      case 'sqlite_delete':
        return <SQLiteDeleteConfig data={nodeData} onChange={handleChange} />
      
      // Redis数据库模块
      case 'redis_connect':
        return <RedisConnectConfig data={nodeData} onChange={handleChange} />
      case 'redis_get':
        return <RedisGetConfig data={nodeData} onChange={handleChange} />
      case 'redis_set':
        return <RedisSetConfig data={nodeData} onChange={handleChange} />
      case 'redis_del':
        return <RedisDelConfig data={nodeData} onChange={handleChange} />
      case 'redis_hget':
        return <RedisHGetConfig data={nodeData} onChange={handleChange} />
      case 'redis_hset':
        return <RedisHSetConfig data={nodeData} onChange={handleChange} />
      
      // 数据库断开连接模块
      case 'oracle_disconnect':
        return <OracleDisconnectConfig data={nodeData} onChange={handleChange} />
      case 'postgresql_disconnect':
        return <PostgreSQLDisconnectConfig data={nodeData} onChange={handleChange} />
      case 'mongodb_disconnect':
        return <MongoDBDisconnectConfig data={nodeData} onChange={handleChange} />
      case 'sqlserver_disconnect':
        return <SQLServerDisconnectConfig data={nodeData} onChange={handleChange} />
      case 'sqlite_disconnect':
        return <SQLiteDisconnectConfig data={nodeData} onChange={handleChange} />
      case 'redis_disconnect':
        return <RedisDisconnectConfig data={nodeData} onChange={handleChange} />
      
      // SSH远程操作模块
      case 'ssh_connect':
        return <SSHConnectConfig data={nodeData} onChange={handleChange} />
      case 'ssh_execute_command':
        return <SSHExecuteCommandConfig data={nodeData} onChange={handleChange} />
      case 'ssh_upload_file':
        return <SSHUploadFileConfig data={nodeData} onChange={handleChange} />
      case 'ssh_download_file':
        return <SSHDownloadFileConfig data={nodeData} onChange={handleChange} />
      case 'ssh_disconnect':
        return <SSHDisconnectConfig data={nodeData} onChange={handleChange} />
      
      // SAP GUI 自动化模块
      case 'sap_login':
        return <SapLoginConfig data={nodeData} onChange={handleChange} />
      case 'sap_logout':
        return <SapLogoutConfig data={nodeData} onChange={handleChange} />
      case 'sap_run_tcode':
        return <SapRunTcodeConfig data={nodeData} onChange={handleChange} />
      case 'sap_set_field_value':
        return <SapSetFieldValueConfig data={nodeData} onChange={handleChange} />
      case 'sap_get_field_value':
        return <SapGetFieldValueConfig data={nodeData} onChange={handleChange} />
      case 'sap_click_button':
        return <SapClickButtonConfig data={nodeData} onChange={handleChange} />
      case 'sap_send_vkey':
        return <SapSendVKeyConfig data={nodeData} onChange={handleChange} />
      case 'sap_get_status_message':
        return <SapGetStatusMessageConfig data={nodeData} onChange={handleChange} />
      case 'sap_get_title':
        return <SapGetTitleConfig data={nodeData} onChange={handleChange} />
      case 'sap_close_warning':
        return <SapCloseWarningConfig data={nodeData} onChange={handleChange} />
      case 'sap_set_checkbox':
        return <SapSetCheckboxConfig data={nodeData} onChange={handleChange} />
      case 'sap_select_combobox':
        return <SapSelectComboBoxConfig data={nodeData} onChange={handleChange} />
      case 'sap_read_gridview':
        return <SapReadGridViewConfig data={nodeData} onChange={handleChange} />
      case 'sap_export_gridview_excel':
        return <SapExportGridViewExcelConfig data={nodeData} onChange={handleChange} />
      case 'sap_set_focus':
        return <SapSetFocusConfig data={nodeData} onChange={handleChange} />
      case 'sap_maximize_window':
        return <SapMaximizeWindowConfig data={nodeData} onChange={handleChange} />
      // 自定义模块
      case 'custom_module':
        return <CustomModuleConfig data={nodeData} onChange={handleChange} />
      
      // AI生图生视频模块
      case 'ai_generate_image':
        return <AIGenerateImageConfig data={nodeData} onChange={handleChange} />
      case 'ai_generate_video':
        return <AIGenerateVideoConfig data={nodeData} onChange={handleChange} />
      
      // 概率触发器模块
      case 'probability_trigger':
        return <ProbabilityTriggerConfig data={nodeData} onChange={handleChange} />
      
      // 网络监听模块
      case 'network_monitor_start':
        return <NetworkMonitorStartConfig data={nodeData} onChange={handleChange} />
      case 'network_monitor_wait':
        return <NetworkMonitorWaitConfig data={nodeData} onChange={handleChange} />
      case 'network_monitor_stop':
        return <NetworkMonitorStopConfig data={nodeData} onChange={handleChange} />
      
      case 'wait_page_load':
        return <WaitPageLoadConfig data={nodeData} onChange={handleChange} />
      case 'page_load_complete':
        return <PageLoadCompleteConfig data={nodeData} onChange={handleChange} />
      case 'group':
        return <GroupConfig data={nodeData} onChange={handleChange} />
      case 'subflow_header':
        return <SubflowHeaderConfig data={nodeData} onChange={handleChange} />
      case 'note':
        return (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              便签模块用于在画布上添加注释，不会被执行
            </p>
            <div className="space-y-2">
              <Label htmlFor="noteContent">便签内容</Label>
              <textarea
                id="noteContent"
                value={(nodeData.content as string) || ''}
                onChange={(e) => handleChange('content', e.target.value)}
                placeholder="在这里输入便签内容..."
                className="w-full min-h-[100px] px-3 py-2 text-sm border rounded-md resize-y"
              />
            </div>
          </div>
        )
      default:
        return (
          <p className="text-sm text-muted-foreground">
            该模块暂无额外配置
          </p>
        )
    }
  }

  return (
    <>
      {/* URL输入对话框 */}
      <UrlInputDialog
        isOpen={showUrlDialog}
        url={pickerUrl}
        onUrlChange={setPickerUrl}
        onClose={() => setShowUrlDialog(false)}
        onConfirm={() => pendingField && startElementPicker(pendingField, pickerUrl)}
      />
      
      {/* 相似元素选择对话框 */}
      {similarResult && (
        <SimilarSelectorDialog
          isOpen={showSimilarDialog}
          onClose={() => {
            setShowSimilarDialog(false)
            setSimilarResult(null)
            stopElementPicker()
          }}
          onConfirm={handleSimilarConfirm}
          pattern={similarResult.pattern}
          count={similarResult.count}
          minIndex={similarResult.minIndex}
          maxIndex={similarResult.maxIndex}
        />
      )}
      
      <aside className={`border-l border-[hsl(var(--border))] bg-[hsl(var(--card))] flex flex-col transition-[width] duration-200 ${isCollapsed ? 'w-12' : 'w-80'}`}>
        {isCollapsed ? (
          <button 
            type="button"
            className="flex flex-col items-center py-3 gap-2 hover:bg-[hsl(var(--muted))] transition-colors h-full w-full has-hover-only"
            onClick={() => setIsCollapsed(false)}
            title="展开配置面板"
          >
            <span className="flex items-center justify-center w-7 h-7 rounded-md bg-[hsl(var(--brand-50))] text-[hsl(var(--brand-600))]">
              <ChevronLeft className="w-4 h-4" />
            </span>
            <Settings className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
            <span className="text-[10px] text-[hsl(var(--muted-foreground))]" style={{ writingMode: 'vertical-rl' }}>
              {moduleTypeLabels[nodeData.moduleType]}
            </span>
          </button>
        ) : (
          <>
            <div className="bg-[hsl(var(--card))] p-4 border-b border-[hsl(var(--border))] flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0">
                <span className="flex items-center justify-center w-7 h-7 rounded-md bg-[hsl(var(--brand-50))] text-[hsl(var(--brand-600))] flex-shrink-0">
                  <Settings className="w-4 h-4" />
                </span>
                <div className="min-w-0">
                  <h2 className="text-sm font-semibold text-[hsl(var(--foreground))] truncate">{moduleTypeLabels[nodeData.moduleType]}</h2>
                  <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5">节点配置</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Button 
                  variant={nodeData.disabled ? 'tonal-warning' : 'outline'} 
                  size="icon" 
                  onClick={() => {
                    toggleNodesDisabled([selectedNode.id])
                    addLog({ level: 'info', message: nodeData.disabled ? '已启用模块' : '已禁用模块' })
                  }}
                  title={nodeData.disabled ? '启用模块 (Ctrl+D)' : '禁用模块 (Ctrl+D)'}
                >
                  <Ban className="w-4 h-4" />
                </Button>
                <Button 
                  variant="tonal-danger" 
                  size="icon" 
                  onClick={handleDelete} 
                  title="删除模块"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setIsCollapsed(true)}
                  title="收起配置面板"
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4 animate-fade-in">
                {/* 通用配置 */}
                <div className="space-y-2">
                  <Label htmlFor="name">节点名称</Label>
                  <Input
                    id="name"
                    value={(nodeData.name as string) || ''}
                    onChange={(e) => handleChange('name', e.target.value)}
                    placeholder="可选的节点名称"
                    className="transition-all duration-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                </div>

                {/* 模块特定配置 */}
                {renderModuleConfig()}

                {/* 高级配置 */}
                <div className="pt-4 border-t space-y-4">
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    高级配置
                  </h3>
                  <div className="space-y-2">
                    <Label htmlFor="timeout">超时时间 (秒)</Label>
                    <NumberInput
                      id="timeout"
                      value={(nodeData.timeout as number) ?? getModuleDefaultTimeout(nodeData.moduleType as import('@/types').ModuleType)}
                      onChange={(v) => handleChange('timeout', v)}
                      defaultValue={getModuleDefaultTimeout(nodeData.moduleType as import('@/types').ModuleType)}
                      min={0}
                    />
                    <p className="text-xs text-muted-foreground">
                      0 表示不限制超时，当前模块建议: {(getModuleDefaultTimeout(nodeData.moduleType as import('@/types').ModuleType) / 1000).toFixed(0)}秒
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="timeoutAction">运行超时后</Label>
                    <Select
                      id="timeoutAction"
                      value={(nodeData.timeoutAction as string) || 'retry'}
                      onChange={(e) => handleChange('timeoutAction', e.target.value)}
                    >
                      <option value="retry">重试</option>
                      <option value="skip">跳过该模块，继续执行</option>
                      <option value="stop">停止工作流执行</option>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      {(nodeData.timeoutAction as string) === 'skip' 
                        ? '超时后跳过此模块，直接执行后续流程'
                        : (nodeData.timeoutAction as string) === 'stop'
                        ? '超时后立即停止整个工作流执行'
                        : '超时后按重试次数进行重试'}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="retryCount">重试次数</Label>
                    <NumberInput
                      id="retryCount"
                      value={(nodeData.retryCount as number) ?? 0}
                      onChange={(v) => handleChange('retryCount', v)}
                      defaultValue={0}
                      min={0}
                      max={10}
                    />
                  </div>
                  {((nodeData.retryCount as number) ?? 0) > 0 && (
                    <div className="space-y-2">
                      <Label htmlFor="retryExhaustedAction">重试耗尽后</Label>
                      <Select
                        id="retryExhaustedAction"
                        value={(nodeData.retryExhaustedAction as string) || 'stop'}
                        onChange={(e) => handleChange('retryExhaustedAction', e.target.value)}
                      >
                        <option value="stop">停止工作流</option>
                        <option value="skip">跳过该模块，继续执行</option>
                      </Select>
                      <p className="text-xs text-muted-foreground">
                        {(nodeData.retryExhaustedAction as string) === 'skip' 
                          ? '重试次数用完后跳过此模块，继续执行后续流程'
                          : '重试次数用完后停止整个工作流'}
                      </p>
                    </div>
                  )}
                </div>

                {/* 变量使用提示 */}
                <div className="pt-4 border-t">
                  <div className="bg-[hsl(var(--card))] p-3 rounded-xl border border-blue-200/30 shadow-sm">
                    <p className="text-xs text-muted-foreground">
                      提示：在任意输入框中使用 <code className="bg-[hsl(var(--card))] px-1.5 py-0.5 rounded text-blue-600 font-mono">{'{变量名}'}</code> 来引用变量值
                    </p>
                  </div>
                </div>
              </div>
            </ScrollArea>
          </>
        )}
      </aside>
    </>
  )
}