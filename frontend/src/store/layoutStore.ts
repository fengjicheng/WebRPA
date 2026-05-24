/**
 * WebRPA 编辑器面板布局 Store
 *
 * 职责：
 * 1. 持久化用户对左/右/底/上栏的拖拽尺寸偏好
 * 2. 记录三个核心面板（模块库 / 配置面板 / 日志栏）当前停靠在哪个 dock zone
 *
 * 全部存到 localStorage，不写项目目录。
 */
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export type PanelId = 'modules' | 'config' | 'log'
export type DockZone = 'left' | 'right' | 'top' | 'bottom'

interface LayoutState {
  /** 左 / 右 zone 宽度（px） */
  leftWidth: number
  rightWidth: number
  /** 底 / 上 zone 高度（px） */
  bottomHeight: number
  topHeight: number
  /** 每个面板当前停靠的 zone */
  panelDocks: Record<PanelId, DockZone>

  setLeftWidth: (w: number) => void
  setRightWidth: (w: number) => void
  setBottomHeight: (h: number) => void
  setTopHeight: (h: number) => void
  /**
   * 把指定面板移动到目标 dock zone。
   * 如果目标 zone 已被另一个面板占用 → 自动让那个面板搬到本面板原来的 zone（互换位置）。
   */
  setPanelDock: (panel: PanelId, zone: DockZone) => void
  resetLayout: () => void
}

const DEFAULTS = {
  leftWidth: 256,
  rightWidth: 320,
  bottomHeight: 256,
  topHeight: 220,
  panelDocks: {
    modules: 'left' as DockZone,
    config: 'right' as DockZone,
    log: 'bottom' as DockZone,
  },
}

export const LAYOUT_LIMITS = {
  left: { min: 180, max: 560 },
  right: { min: 240, max: 720 },
  bottom: { min: 120, max: 720 },
  top: { min: 120, max: 720 },
}

const clamp = (v: number, min: number, max: number) => Math.max(min, Math.min(max, v))

export const useLayoutStore = create<LayoutState>()(
  persist(
    (set, get) => ({
      ...DEFAULTS,
      setLeftWidth: (w) => set({ leftWidth: clamp(w, LAYOUT_LIMITS.left.min, LAYOUT_LIMITS.left.max) }),
      setRightWidth: (w) => set({ rightWidth: clamp(w, LAYOUT_LIMITS.right.min, LAYOUT_LIMITS.right.max) }),
      setBottomHeight: (h) => set({ bottomHeight: clamp(h, LAYOUT_LIMITS.bottom.min, LAYOUT_LIMITS.bottom.max) }),
      setTopHeight: (h) => set({ topHeight: clamp(h, LAYOUT_LIMITS.top.min, LAYOUT_LIMITS.top.max) }),
      setPanelDock: (panel, zone) => {
        const docks = { ...get().panelDocks }
        const prevZone = docks[panel]
        if (prevZone === zone) return
        // 找出当前占着 zone 的面板（如果有）
        const occupier = (Object.keys(docks) as PanelId[]).find(p => p !== panel && docks[p] === zone)
        docks[panel] = zone
        if (occupier) {
          // 让被挤掉的面板去原来位置（互换）
          docks[occupier] = prevZone
        }
        set({ panelDocks: docks })
      },
      resetLayout: () => set({ ...DEFAULTS }),
    }),
    {
      name: 'webrpa.editor.layout',
      storage: createJSONStorage(() => localStorage),
      version: 2,
    },
  ),
)
