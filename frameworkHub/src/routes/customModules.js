/**
 * 自定义模块在线社区 API 路由
 * 提供自定义模块的发布、浏览、下载、删除功能
 */

import { Router } from 'express'
import { body, query, param, validationResult } from 'express-validator'
import rateLimit from 'express-rate-limit'
import { v4 as uuidv4 } from 'uuid'
import { createHash } from 'crypto'
import xss from 'xss'
import db from '../database.js'
import { getClientIP } from '../utils/ip.js'

const router = Router()

// 发布速率限制
const publishLimiter = rateLimit({
  windowMs: 60 * 60 * 1000,
  max: 20,
  message: { error: '发布过于频繁，请1小时后再试' }
})

// 下载速率限制
const downloadLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 40,
  message: { error: '下载过于频繁，请稍后再试' }
})

// XSS 过滤配置
const xssOptions = {
  whiteList: {},
  stripIgnoreTag: true,
  stripIgnoreTagBody: ['script']
}

// 允许的分类
const ALLOWED_CATEGORIES = [
  '全部', '自定义', '自动化', '数据处理', 'AI', '工具', '网页操作', '文件操作',
  '数据库', 'API', '邮件', '通知', '图像处理', '文本处理', 'Excel', 'PDF',
  '爬虫', '测试', '监控', '定时任务', '流程控制', '系统操作', '网络', '安全', '其他'
]

/**
 * 计算自定义模块内容哈希（用于去重）
 */
function calculateModuleHash(moduleData) {
  const normalized = {
    name: moduleData.name || '',
    workflow: moduleData.workflow || { nodes: [], edges: [] },
    parameters: moduleData.parameters || [],
    outputs: moduleData.outputs || []
  }
  const jsonStr = JSON.stringify(normalized)
  return createHash('sha256').update(jsonStr).digest('hex')
}

/**
 * 校验自定义模块内容是否有效
 */
function validateModuleContent(moduleData) {
  if (!moduleData || typeof moduleData !== 'object' || Array.isArray(moduleData)) {
    return { valid: false, error: '无效的模块格式：应为对象' }
  }
  if (!moduleData.name || typeof moduleData.name !== 'string') {
    return { valid: false, error: '模块缺少有效的 name 字段' }
  }
  const wf = moduleData.workflow
  if (!wf || typeof wf !== 'object' || Array.isArray(wf)) {
    return { valid: false, error: '模块缺少有效的 workflow 字段' }
  }
  if (!Array.isArray(wf.nodes)) {
    return { valid: false, error: '模块 workflow.nodes 必须是数组' }
  }
  if (!Array.isArray(wf.edges)) {
    return { valid: false, error: '模块 workflow.edges 必须是数组' }
  }
  if (wf.nodes.length === 0) {
    return { valid: false, error: '模块内部工作流至少需要一个节点' }
  }
  if (wf.nodes.length > 500) {
    return { valid: false, error: '模块节点数量不能超过500个' }
  }
  const totalSize = JSON.stringify(moduleData).length
  if (totalSize > 500000) {
    return { valid: false, error: '模块内容过大（超过500KB），请精简后再发布' }
  }
  return { valid: true, nodeCount: wf.nodes.length }
}

/**
 * 获取自定义模块列表
 * GET /api/custom-modules
 */
router.get('/',
  [
    query('page').optional().isInt({ min: 1 }).toInt(),
    query('limit').optional().isInt({ min: 1, max: 50 }).toInt(),
    query('category').optional().isString().trim(),
    query('search').optional().isString().trim(),
    query('sort').optional().isIn(['newest', 'popular', 'downloads'])
  ],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({ error: '参数错误', details: errors.array() })
    }

    const page = req.query.page || 1
    const limit = req.query.limit || 24
    const offset = (page - 1) * limit
    const category = req.query.category
    const search = req.query.search
    const sort = req.query.sort || 'newest'

    let whereClause = 'WHERE is_active = 1'
    const params = []

    if (category && category !== '全部') {
      whereClause += ' AND category = ?'
      params.push(category)
    }

    if (search) {
      whereClause += ' AND (name LIKE ? OR display_name LIKE ? OR description LIKE ? OR tags LIKE ?)'
      const p = `%${search}%`
      params.push(p, p, p, p)
    }

    let orderClause = 'ORDER BY created_at DESC'
    if (sort === 'popular') {
      orderClause = 'ORDER BY download_count DESC, created_at DESC'
    } else if (sort === 'downloads') {
      orderClause = 'ORDER BY download_count DESC'
    }

    const countStmt = db.prepare(`SELECT COUNT(*) as total FROM custom_modules ${whereClause}`)
    const { total } = countStmt.get(...params)

    const listStmt = db.prepare(`
      SELECT id, name, display_name, description, icon, color, author, category, tags,
        version, node_count, download_count, created_at,
        (SELECT COUNT(*) FROM custom_module_comments c WHERE c.module_id = custom_modules.id AND c.is_active = 1) as comment_count,
        (SELECT IFNULL(ROUND(AVG(rating), 1), 0) FROM custom_module_comments c WHERE c.module_id = custom_modules.id AND c.is_active = 1 AND c.rating > 0) as avg_rating
      FROM custom_modules
      ${whereClause}
      ${orderClause}
      LIMIT ? OFFSET ?
    `)
    const modules = listStmt.all(...params, limit, offset)

    res.json({
      modules: modules.map(m => ({
        ...m,
        tags: m.tags ? m.tags.split(',').filter(Boolean) : []
      })),
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit)
      }
    })
  }
)

/**
 * 获取分类列表
 * GET /api/custom-modules/categories
 */
router.get('/categories', (req, res) => {
  const stmt = db.prepare(`
    SELECT category, COUNT(*) as count
    FROM custom_modules
    WHERE is_active = 1
    GROUP BY category
    ORDER BY count DESC
  `)
  const categories = stmt.all()

  res.json({
    categories: [
      { name: '全部', count: categories.reduce((sum, c) => sum + c.count, 0) },
      ...categories.map(c => ({ name: c.category, count: c.count }))
    ]
  })
})

/**
 * 获取用户发布的自定义模块列表
 * POST /api/custom-modules/my-modules
 */
router.post('/my-modules',
  [
    body('clientId').isString().trim().isLength({ min: 16, max: 64 }).withMessage('无效的客户端ID'),
    body('page').optional().isInt({ min: 1 }).toInt(),
    body('limit').optional().isInt({ min: 1, max: 50 }).toInt()
  ],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({ error: '参数错误', details: errors.array() })
    }

    const { clientId, page = 1, limit = 24 } = req.body
    const offset = (page - 1) * limit

    const countStmt = db.prepare('SELECT COUNT(*) as total FROM custom_modules WHERE client_id = ? AND is_active = 1')
    const { total } = countStmt.get(clientId)

    const listStmt = db.prepare(`
      SELECT id, name, display_name, description, icon, color, author, category, tags,
        version, node_count, download_count, created_at
      FROM custom_modules
      WHERE client_id = ? AND is_active = 1
      ORDER BY created_at DESC
      LIMIT ? OFFSET ?
    `)
    const modules = listStmt.all(clientId, limit, offset)

    res.json({
      modules: modules.map(m => ({
        ...m,
        tags: m.tags ? m.tags.split(',').filter(Boolean) : []
      })),
      pagination: { page, limit, total, totalPages: Math.ceil(total / limit) }
    })
  }
)

/**
 * 获取单个自定义模块详情（含完整内容）
 * GET /api/custom-modules/:id
 */
router.get('/:id',
  [param('id').isUUID()],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({ error: '无效的模块ID' })
    }

    const stmt = db.prepare(`
      SELECT id, name, display_name, description, icon, color, author, category, tags,
        content, version, node_count, download_count, created_at
      FROM custom_modules
      WHERE id = ? AND is_active = 1
    `)
    const module = stmt.get(req.params.id)

    if (!module) {
      return res.status(404).json({ error: '模块不存在' })
    }

    res.json({
      ...module,
      tags: module.tags ? module.tags.split(',').filter(Boolean) : [],
      content: JSON.parse(module.content)
    })
  }
)

/**
 * 下载自定义模块（增加下载计数，返回完整模块 JSON）
 * POST /api/custom-modules/:id/download
 */
router.post('/:id/download',
  downloadLimiter,
  [param('id').isUUID()],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({ error: '无效的模块ID' })
    }

    const moduleId = req.params.id
    const clientIP = getClientIP(req)

    const checkStmt = db.prepare('SELECT id, content FROM custom_modules WHERE id = ? AND is_active = 1')
    const module = checkStmt.get(moduleId)

    if (!module) {
      return res.status(404).json({ error: '模块不存在' })
    }

    const recentDownload = db.prepare(`
      SELECT id FROM custom_module_download_logs
      WHERE module_id = ? AND ip_address = ?
      AND downloaded_at > datetime('now', '-1 hour')
    `).get(moduleId, clientIP)

    if (!recentDownload) {
      try {
        db.prepare('INSERT INTO custom_module_download_logs (module_id, ip_address) VALUES (?, ?)').run(moduleId, clientIP)
        db.prepare('UPDATE custom_modules SET download_count = download_count + 1 WHERE id = ?').run(moduleId)
      } catch (e) {
        // 忽略重复插入错误
      }
    }

    res.json({
      success: true,
      content: JSON.parse(module.content)
    })
  }
)

/**
 * 发布自定义模块
 * POST /api/custom-modules
 */
router.post('/',
  publishLimiter,
  [
    body('display_name').isString().trim().isLength({ min: 1, max: 50 }).withMessage('显示名称长度应在1-50个字符之间'),
    body('description').optional().isString().trim().isLength({ max: 500 }).withMessage('描述不能超过500个字符'),
    body('author').optional().isString().trim().isLength({ max: 30 }).withMessage('作者名不能超过30个字符'),
    body('category').optional().isString().trim().withMessage('无效的分类'),
    body('tags').optional().isArray({ max: 8 }).withMessage('标签最多8个'),
    body('module').exists().withMessage('缺少模块内容'),
    body('clientId').optional().isString().trim().isLength({ min: 16, max: 64 }).withMessage('无效的客户端ID')
  ],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({ error: '参数验证失败', details: errors.array() })
    }

    const { display_name, description, author, category, tags, module, clientId } = req.body
    const clientIP = getClientIP(req)
    const userAgent = req.get('User-Agent') || ''

    // 校验模块内容
    const validation = validateModuleContent(module)
    if (!validation.valid) {
      return res.status(400).json({ error: validation.error })
    }

    if (category && !ALLOWED_CATEGORIES.includes(category)) {
      return res.status(400).json({ error: '无效的分类' })
    }

    // 计算哈希去重
    const hash = calculateModuleHash(module)
    const existing = db.prepare('SELECT id, display_name, client_id FROM custom_modules WHERE hash = ? AND is_active = 1').get(hash)
    if (existing) {
      // 同一发布者重复发布内容完全相同的模块：视为「无需更新」，幂等返回成功
      if (clientId && existing.client_id === clientId) {
        return res.status(200).json({
          success: true,
          id: existing.id,
          message: '该模块内容未变化，已是最新',
          unchanged: true,
        })
      }
      return res.status(409).json({
        error: '该模块已存在于社区中',
        existingId: existing.id,
        existingName: existing.display_name
      })
    }

    // XSS 过滤
    const safeName = xss(String(module.name || display_name), xssOptions)
    const safeDisplayName = xss(display_name, xssOptions)
    const safeDescription = description ? xss(description, xssOptions) : ''
    const safeAuthor = author ? xss(author, xssOptions) : '匿名'
    const safeTags = Array.isArray(tags) ? tags.map(t => xss(String(t), xssOptions)).slice(0, 8).join(',') : ''
    const safeIcon = module.icon ? String(module.icon).substring(0, 16) : '📦'
    const safeColor = module.color ? String(module.color).substring(0, 16) : '#8B5CF6'
    const version = module.version ? String(module.version).substring(0, 20) : '1.0.0'
    const nodeCount = module.workflow?.nodes?.length || 0

    // 标准化存储内容：完整模块 JSON（供下载导入）
    const storeContent = {
      ...module,
      name: safeName,
      display_name: safeDisplayName,
      description: safeDescription,
      icon: safeIcon,
      color: safeColor,
      category: category || module.category || '其他',
      tags: safeTags ? safeTags.split(',').filter(Boolean) : [],
      author: safeAuthor,
      version
    }

    const id = uuidv4()

    try {
      const insertStmt = db.prepare(`
        INSERT INTO custom_modules
          (id, hash, name, display_name, description, icon, color, category, tags,
           content, author, version, node_count, ip_address, user_agent, client_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `)
      insertStmt.run(
        id, hash, safeName, safeDisplayName, safeDescription, safeIcon, safeColor,
        category || module.category || '其他', safeTags,
        JSON.stringify(storeContent), safeAuthor, version, nodeCount,
        clientIP, userAgent.substring(0, 200), clientId || null
      )

      res.status(201).json({ success: true, id, message: '模块发布成功' })
    } catch (error) {
      console.error('发布自定义模块失败:', error)
      res.status(500).json({ error: '发布失败，请稍后重试' })
    }
  }
)

/**
 * 删除自定义模块（仅发布者可删除）
 * DELETE /api/custom-modules/:id
 */
router.delete('/:id',
  rateLimit({ windowMs: 60 * 60 * 1000, max: 30, message: { error: '操作过于频繁' } }),
  [
    param('id').isUUID(),
    body('clientId').isString().trim().isLength({ min: 16, max: 64 }).withMessage('无效的客户端ID')
  ],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({ error: '参数错误', details: errors.array() })
    }

    const moduleId = req.params.id
    const { clientId } = req.body

    const module = db.prepare('SELECT id, client_id FROM custom_modules WHERE id = ? AND is_active = 1').get(moduleId)
    if (!module) {
      return res.status(404).json({ error: '模块不存在' })
    }
    if (!module.client_id || module.client_id !== clientId) {
      return res.status(403).json({ error: '无权删除此模块' })
    }

    try {
      db.prepare('DELETE FROM custom_module_download_logs WHERE module_id = ?').run(moduleId)
      db.prepare('DELETE FROM custom_modules WHERE id = ?').run(moduleId)
      res.json({ success: true, message: '模块已删除' })
    } catch (error) {
      console.error('删除自定义模块失败:', error)
      res.status(500).json({ error: '删除失败' })
    }
  }
)

/**
 * 更新自己发布的模块元信息（版本更新：名称/描述/分类/标签/版本号）
 * PUT /api/custom-modules/:id
 */
router.put('/:id',
  rateLimit({ windowMs: 60 * 60 * 1000, max: 40, message: { error: '操作过于频繁' } }),
  [
    param('id').isUUID(),
    body('clientId').isString().trim().isLength({ min: 16, max: 64 }),
    body('display_name').optional().isString().trim().isLength({ min: 1, max: 50 }),
    body('description').optional().isString().trim().isLength({ max: 500 }),
    body('category').optional().isString().trim(),
    body('tags').optional().isArray({ max: 8 }),
    body('version').optional().isString().trim().isLength({ max: 20 }),
  ],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({ error: '参数验证失败', details: errors.array() })
    }
    const moduleId = req.params.id
    const { clientId, display_name, description, category, tags, version } = req.body

    const module = db.prepare('SELECT id, client_id, content FROM custom_modules WHERE id = ? AND is_active = 1').get(moduleId)
    if (!module) return res.status(404).json({ error: '模块不存在' })
    if (!module.client_id || module.client_id !== clientId) {
      return res.status(403).json({ error: '无权修改此模块' })
    }
    if (category && !ALLOWED_CATEGORIES.includes(category)) {
      return res.status(400).json({ error: '无效的分类' })
    }

    const updates = []
    const params = []
    let content
    try { content = JSON.parse(module.content) } catch { content = {} }

    if (display_name !== undefined) { updates.push('display_name = ?'); params.push(xss(display_name, xssOptions)); content.display_name = xss(display_name, xssOptions) }
    if (description !== undefined) { updates.push('description = ?'); params.push(xss(description, xssOptions)); content.description = xss(description, xssOptions) }
    if (category !== undefined) { updates.push('category = ?'); params.push(category); content.category = category }
    if (tags !== undefined) {
      const safeTags = tags.map(t => xss(String(t), xssOptions)).slice(0, 8)
      updates.push('tags = ?'); params.push(safeTags.join(','))
      content.tags = safeTags
    }
    if (version !== undefined) { updates.push('version = ?'); params.push(version); content.version = version }

    if (updates.length === 0) return res.status(400).json({ error: '没有要更新的内容' })

    updates.push('content = ?'); params.push(JSON.stringify(content))
    updates.push('updated_at = ?'); params.push(new Date().toISOString())

    try {
      params.push(moduleId)
      db.prepare(`UPDATE custom_modules SET ${updates.join(', ')} WHERE id = ?`).run(...params)
      res.json({ success: true, message: '模块已更新' })
    } catch (error) {
      console.error('更新自定义模块失败:', error)
      res.status(500).json({ error: '更新失败' })
    }
  }
)

/**
 * 获取模块评论 + 评分
 * GET /api/custom-modules/:id/comments
 */
router.get('/:id/comments',
  [param('id').isUUID(), query('page').optional().isInt({ min: 1 }).toInt(), query('clientId').optional().isString()],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) return res.status(400).json({ error: '参数错误' })
    const moduleId = req.params.id
    const page = req.query.page || 1
    const limit = 10
    const offset = (page - 1) * limit
    const clientId = req.query.clientId || ''

    const { total } = db.prepare('SELECT COUNT(*) as total FROM custom_module_comments WHERE module_id = ? AND is_active = 1').get(moduleId)
    const avgRow = db.prepare('SELECT IFNULL(ROUND(AVG(rating),1),0) as avg FROM custom_module_comments WHERE module_id = ? AND is_active = 1 AND rating > 0').get(moduleId)
    const rows = db.prepare(`
      SELECT id, nickname, content, rating, client_id, created_at
      FROM custom_module_comments
      WHERE module_id = ? AND is_active = 1
      ORDER BY created_at DESC
      LIMIT ? OFFSET ?
    `).all(moduleId, limit, offset)

    res.json({
      comments: rows.map(r => ({
        id: r.id, nickname: r.nickname, content: r.content, rating: r.rating,
        created_at: r.created_at, isOwner: !!clientId && r.client_id === clientId,
      })),
      avgRating: avgRow.avg,
      pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
    })
  }
)

/**
 * 发表模块评论 / 评分
 * POST /api/custom-modules/:id/comments
 */
router.post('/:id/comments',
  rateLimit({ windowMs: 60 * 1000, max: 10, message: { error: '评论过于频繁' } }),
  [
    param('id').isUUID(),
    body('content').isString().trim().isLength({ min: 1, max: 500 }),
    body('nickname').optional().isString().trim().isLength({ max: 30 }),
    body('rating').optional().isInt({ min: 0, max: 5 }).toInt(),
    body('clientId').optional().isString().trim().isLength({ min: 16, max: 64 }),
  ],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) return res.status(400).json({ error: '参数验证失败', details: errors.array() })
    const moduleId = req.params.id
    const { content, nickname, rating, clientId } = req.body

    const exists = db.prepare('SELECT id FROM custom_modules WHERE id = ? AND is_active = 1').get(moduleId)
    if (!exists) return res.status(404).json({ error: '模块不存在' })

    try {
      db.prepare(`
        INSERT INTO custom_module_comments (module_id, nickname, content, rating, client_id, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
      `).run(moduleId, xss(nickname || '匿名用户', xssOptions), xss(content, xssOptions), rating || 0, clientId || null, getClientIP(req))
      res.status(201).json({ success: true, message: '评论已发布' })
    } catch (error) {
      res.status(500).json({ error: '发布失败' })
    }
  }
)

/**
 * 删除自己的模块评论
 * DELETE /api/custom-modules/comments/:commentId
 */
router.delete('/comments/:commentId',
  [param('commentId').isInt(), body('clientId').isString().trim().isLength({ min: 16, max: 64 })],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) return res.status(400).json({ error: '参数错误' })
    const commentId = req.params.commentId
    const { clientId } = req.body
    const c = db.prepare('SELECT id, client_id FROM custom_module_comments WHERE id = ? AND is_active = 1').get(commentId)
    if (!c) return res.status(404).json({ error: '评论不存在' })
    if (!c.client_id || c.client_id !== clientId) return res.status(403).json({ error: '无权删除此评论' })
    db.prepare('UPDATE custom_module_comments SET is_active = 0 WHERE id = ?').run(commentId)
    res.json({ success: true })
  }
)

/**
 * 举报模块
 * POST /api/custom-modules/:id/report
 */
router.post('/:id/report',
  rateLimit({ windowMs: 60 * 60 * 1000, max: 5, message: { error: '举报过于频繁' } }),
  [
    param('id').isUUID(),
    body('reason').isIn(['违规内容', '恶意代码', '侵权', '垃圾信息', '其他']),
    body('description').optional().isString().trim().isLength({ max: 200 }),
  ],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) return res.status(400).json({ error: '参数错误', details: errors.array() })
    const moduleId = req.params.id
    const { reason, description } = req.body
    const exists = db.prepare('SELECT id FROM custom_modules WHERE id = ? AND is_active = 1').get(moduleId)
    if (!exists) return res.status(404).json({ error: '模块不存在' })
    try {
      db.prepare('INSERT INTO custom_module_reports (module_id, reason, description, ip_address) VALUES (?, ?, ?, ?)')
        .run(moduleId, reason, description || '', getClientIP(req))
      res.json({ success: true, message: '举报已提交' })
    } catch (error) {
      res.status(500).json({ error: '提交失败' })
    }
  }
)

export default router
