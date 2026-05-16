/**
 * WebRPA 全局 Motion 动效配置
 * 统一管理所有动效的参数，保持整个 UI 风格一致
 */

export const spring = {
  /** 弹性弹出 - 用于弹窗、卡片出现 */
  bouncy: { type: 'spring', stiffness: 400, damping: 25 },
  /** 柔和弹出 - 用于侧边栏、面板 */
  soft: { type: 'spring', stiffness: 260, damping: 30 },
  /** 快速响应 - 用于按钮、小交互 */
  snappy: { type: 'spring', stiffness: 500, damping: 35 },
  /** 慢速平滑 - 用于布局切换 */
  gentle: { type: 'spring', stiffness: 180, damping: 28 },
} as const

export const ease = {
  /** 标准进入缓动 */
  enter: [0.22, 1, 0.36, 1] as [number, number, number, number],
  /** 标准退出缓动 */
  exit: [0.55, 0, 1, 0.45] as [number, number, number, number],
  /** 弹性感缓动 */
  elastic: [0.34, 1.56, 0.64, 1] as [number, number, number, number],
} as const

/** 弹窗遮罩动效 */
export const overlayVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.2 } },
  exit: { opacity: 0, transition: { duration: 0.15 } },
}

/** 弹窗内容动效 - 从中心弹出 */
export const dialogVariants = {
  hidden: { opacity: 0, scale: 0.92, y: 8 },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: spring.bouncy,
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: 4,
    transition: { duration: 0.15, ease: ease.exit },
  },
}

/** 从右侧滑入的面板 */
export const slideInRightVariants = {
  hidden: { opacity: 0, x: 40 },
  visible: {
    opacity: 1,
    x: 0,
    transition: spring.soft,
  },
  exit: {
    opacity: 0,
    x: 40,
    transition: { duration: 0.15, ease: ease.exit },
  },
}

/** 从左侧滑入的面板 */
export const slideInLeftVariants = {
  hidden: { opacity: 0, x: -40 },
  visible: {
    opacity: 1,
    x: 0,
    transition: spring.soft,
  },
  exit: {
    opacity: 0,
    x: -40,
    transition: { duration: 0.15, ease: ease.exit },
  },
}

/** 从下方滑入 */
export const slideUpVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: spring.soft,
  },
  exit: {
    opacity: 0,
    y: 20,
    transition: { duration: 0.15, ease: ease.exit },
  },
}

/** 列表子项交错进入 */
export const listItemVariants = {
  hidden: { opacity: 0, x: -12, scale: 0.97 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    scale: 1,
    transition: {
      ...spring.snappy,
      delay: i * 0.04,
    },
  }),
  exit: { opacity: 0, x: -8, transition: { duration: 0.1 } },
}

/** 节点卡片动效 */
export const nodeVariants = {
  initial: { opacity: 0, scale: 0.8, y: -10 },
  animate: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: spring.bouncy,
  },
}

/** 淡入动效 */
export const fadeVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.2 } },
  exit: { opacity: 0, transition: { duration: 0.1 } },
}

/** 工具栏按钮 hover 动效配置 */
export const toolbarButtonHover = {
  whileHover: { scale: 1.08, y: -1 },
  whileTap: { scale: 0.94 },
  transition: spring.snappy,
}

/** 普通按钮 hover 动效配置 */
export const buttonHover = {
  whileHover: { scale: 1.03 },
  whileTap: { scale: 0.97 },
  transition: spring.snappy,
}

/** 图标按钮 hover 动效配置 */
export const iconButtonHover = {
  whileHover: { scale: 1.15, rotate: 5 },
  whileTap: { scale: 0.9 },
  transition: spring.snappy,
}

/** 卡片 hover 动效 */
export const cardHover = {
  whileHover: { y: -2, boxShadow: '0 8px 30px rgba(0,0,0,0.12)' },
  transition: spring.soft,
}
