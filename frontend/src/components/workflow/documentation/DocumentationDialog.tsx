import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { X, ChevronRight, BookOpen, ArrowUp, Search, Download, FileDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { documents } from './documents'
import { documentContents } from './contents'
import { MarkdownRenderer } from './MarkdownRenderer'
import type { DocumentationDialogProps } from './types'
import { pinyinMatch } from '@/lib/pinyin'
import { DialogPortal } from '@/components/ui/dialog-portal'

export function DocumentationDialog({ isOpen, onClose }: DocumentationDialogProps) {
  const [selectedDoc, setSelectedDoc] = useState('getting-started')
  const [showScrollTop, setShowScrollTop] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Array<{docId: string, title: string, heading: string, level: number, matches: string[]}>>([])
  const [isSearching, setIsSearching] = useState(false)
  const [highlightKeyword, setHighlightKeyword] = useState('')
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)
  
  // 切换文档时滚动到顶部
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = 0
      setShowScrollTop(false)
    }
  }, [selectedDoc])

  // 监听滚动显示返回顶部按钮
  const handleScroll = () => {
    if (scrollContainerRef.current) {
      setShowScrollTop(scrollContainerRef.current.scrollTop > 300)
    }
  }

  const scrollToTop = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  // 搜索功能 - 支持三级标题搜索
  const handleSearch = (query: string) => {
    setSearchQuery(query)
    
    if (!query.trim()) {
      setSearchResults([])
      setIsSearching(false)
      setHighlightKeyword('')
      return
    }
    
    setIsSearching(true)
    setHighlightKeyword(query.trim())
    const results: Array<{docId: string, title: string, heading: string, level: number, matches: string[]}> = []
    const queryLower = query.toLowerCase()
    
    for (const doc of documents) {
      const content = documentContents[doc.id] || ''
      const lines = content.split('\n')
      
      // 提取所有标题（一级、二级、三级）
      const headings: Array<{text: string, level: number, lineIndex: number}> = []
      lines.forEach((line, index) => {
        const h1Match = line.match(/^# (.+)/)
        const h2Match = line.match(/^## (.+)/)
        const h3Match = line.match(/^### (.+)/)
        
        if (h1Match) headings.push({text: h1Match[1], level: 1, lineIndex: index})
        else if (h2Match) headings.push({text: h2Match[1], level: 2, lineIndex: index})
        else if (h3Match) headings.push({text: h3Match[1], level: 3, lineIndex: index})
      })
      
      // 搜索每个标题及其内容
      headings.forEach((heading, idx) => {
        const nextHeadingIndex = idx < headings.length - 1 ? headings[idx + 1].lineIndex : lines.length
        const sectionContent = lines.slice(heading.lineIndex, nextHeadingIndex).join('\n')
        const sectionLower = sectionContent.toLowerCase()
        const headingLower = heading.text.toLowerCase()
        
        // 检查标题或内容是否匹配
        const headingMatch = headingLower.includes(queryLower) || pinyinMatch(heading.text, query)
        const contentMatch = sectionLower.includes(queryLower)
        
        if (headingMatch || contentMatch) {
          const matches: string[] = []
          
          if (contentMatch) {
            // 提取匹配的上下文（最多3个）
            let searchIndex = 0
            let matchCount = 0
            while (searchIndex < sectionLower.length && matchCount < 3) {
              const index = sectionLower.indexOf(queryLower, searchIndex)
              if (index === -1) break
              
              // 提取前后50个字符作为上下文
              const start = Math.max(0, index - 30)
              const end = Math.min(sectionContent.length, index + query.length + 50)
              let context = sectionContent.slice(start, end)
              
              // 清理markdown标记
              context = context.replace(/[#*`\[\]()]/g, '').replace(/\n/g, ' ').trim()
              if (start > 0) context = '...' + context
              if (end < sectionContent.length) context = context + '...'
              
              matches.push(context)
              searchIndex = index + query.length
              matchCount++
            }
          }
          
          results.push({
            docId: doc.id,
            title: doc.title,
            heading: heading.text,
            level: heading.level,
            matches
          })
        }
      })
      
      // 如果文档标题或描述匹配，但没有具体标题匹配，添加文档级别的结果
      const titleLower = doc.title.toLowerCase()
      const descLower = doc.description.toLowerCase()
      const titleMatch = titleLower.includes(queryLower) || pinyinMatch(doc.title, query)
      const descMatch = descLower.includes(queryLower) || pinyinMatch(doc.description, query)
      
      if ((titleMatch || descMatch) && !results.some(r => r.docId === doc.id)) {
        results.push({
          docId: doc.id,
          title: doc.title,
          heading: doc.title,
          level: 0,
          matches: [doc.description]
        })
      }
    }
    
    setSearchResults(results)
  }

  // 清除搜索
  const clearSearch = () => {
    setSearchQuery('')
    setSearchResults([])
    setIsSearching(false)
    setHighlightKeyword('')
    searchInputRef.current?.focus()
  }

  // 选择搜索结果 - 保持搜索状态
  const selectSearchResult = (docId: string) => {
    setSelectedDoc(docId)
    // 不清除搜索状态，保持高亮
  }
  
  // 下载当前文档
  const handleDownloadCurrent = () => {
    const doc = documents.find(d => d.id === selectedDoc)
    if (!doc) return
    
    const content = documentContents[selectedDoc] || ''
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${doc.title.replace(/[🚀⚡📊🧠💡🌐📝🔧🎯📁🔍]/g, '').trim()}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
  
  // 下载全部文档
  const handleDownloadAll = () => {
    let allContent = '# WebRPA 教学文档\n\n'
    allContent += '> 本文档包含 WebRPA 的完整使用指南\n\n'
    allContent += '---\n\n'
    
    documents.forEach((doc, index) => {
      const content = documentContents[doc.id] || ''
      allContent += `\n\n# ${index + 1}. ${doc.title}\n\n`
      allContent += `> ${doc.description}\n\n`
      allContent += content
      allContent += '\n\n---\n\n'
    })
    
    const blob = new Blob([allContent], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'WebRPA完整教学文档.md'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
  
  if (!isOpen) return null
  
  const content = documentContents[selectedDoc] || ''
  const currentDoc = documents.find(d => d.id === selectedDoc)
  
  return (
    <DialogPortal>
    <AnimatePresence>
      <motion.div
        key="doc-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        className="fixed inset-0 bg-[hsl(217_45%_15%_/_0.55)] backdrop-blur-[3px] flex items-center justify-center p-4"
        style={{ zIndex: 2147483646 }}
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 8 }}
          transition={{ type: 'spring', stiffness: 380, damping: 28 }}
          className="modern-dialog w-full max-w-5xl h-[88vh] flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
        <div className="modern-dialog-header">
          <div className="modern-dialog-header-icon modern-dialog-header-icon-info">
            <BookOpen className="w-5 h-5" strokeWidth={2.2} />
          </div>
          <div className="flex-1">
            <h2 className="modern-dialog-title">教学文档</h2>
            <div className="modern-dialog-subtitle">
              共 <span className="text-[hsl(var(--brand-700))] font-bold">{documents.length}</span> 篇 · 内置全文搜索
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <Button
              variant="tonal"
              size="icon-sm"
              onClick={handleDownloadCurrent}
              title={`下载当前文档：${currentDoc?.title}`}
            >
              <FileDown className="w-3.5 h-3.5" />
            </Button>
            <Button
              variant="tonal-success"
              size="icon-sm"
              onClick={handleDownloadAll}
              title="下载全部文档为一个文件"
            >
              <Download className="w-3.5 h-3.5" />
            </Button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-[7px] text-[hsl(var(--slate-500))] hover:bg-[hsl(var(--danger-50))] hover:text-[hsl(var(--danger-600))] hover:border-[hsl(var(--danger-500)/0.3)] border border-transparent transition-all duration-150 active:scale-90"
              title="关闭"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden">
          <div className="w-72 border-r border-[hsl(var(--border))] bg-[hsl(var(--slate-50)/0.5)] flex flex-col">
            {/* 搜索框 */}
            <div className="p-3 border-b border-[hsl(var(--border))]">
              <div className="relative group">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[hsl(var(--muted-foreground))] group-focus-within:text-[hsl(var(--brand-600))] transition-colors duration-150" />
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  placeholder="搜索文档内容..."
                  className="w-full pl-8 pr-7 h-8 text-[12px] border border-[hsl(var(--slate-200))] bg-[hsl(var(--card))] rounded-[8px] shadow-[inset_0_1px_2px_rgb(15_23_42_/_0.04)] focus:outline-none focus:border-[hsl(var(--brand-500))] focus:ring-2 focus:ring-[hsl(var(--brand-500)/0.18)] transition-all duration-150"
                />
                {searchQuery && (
                  <button
                    onClick={clearSearch}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded hover:bg-[hsl(var(--danger-50))] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--danger-600))] transition-all active:scale-90"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            {/* 搜索结果或文档目录 */}
            <div className="flex-1 p-2.5 overflow-y-auto">
              {isSearching && searchResults.length > 0 ? (
                <>
                  <div className="text-[10px] uppercase tracking-wider font-semibold text-[hsl(var(--muted-foreground))] mb-2 flex items-center gap-1.5">
                    <Search className="w-2.5 h-2.5" />
                    搜索结果
                    <span className="badge badge-brand !py-0">{searchResults.length}</span>
                  </div>
                  <div className="space-y-1">
                    {searchResults.map((result, idx) => (
                      <button
                        key={`${result.docId}-${idx}`}
                        className="w-full text-left p-2 rounded-[8px] hover:bg-[hsl(var(--brand-50))] border border-transparent hover:border-[hsl(var(--brand-500)/0.3)] transition-all duration-150 hover:translate-x-0.5"
                        onClick={() => selectSearchResult(result.docId)}
                      >
                        <div className="text-[10px] text-[hsl(var(--muted-foreground))] mb-0.5 truncate">{result.title}</div>
                        <div className="text-[12px] font-medium text-[hsl(var(--slate-800))] flex items-center gap-1">
                          {result.level === 1 && <span className="text-[hsl(var(--brand-600))] font-mono">#</span>}
                          {result.level === 2 && <span className="text-[hsl(var(--success-600))] font-mono">##</span>}
                          {result.level === 3 && <span className="text-[hsl(var(--warning-600))] font-mono">###</span>}
                          <span className="truncate">{result.heading}</span>
                        </div>
                        {result.matches.length > 0 && (
                          <div className="text-[11px] text-[hsl(var(--muted-foreground))] mt-1 line-clamp-2">
                            {result.matches[0]}
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                </>
              ) : isSearching && searchQuery ? (
                <div className="empty-state !py-10">
                  <div className="empty-state-icon !w-12 !h-12">
                    <Search className="w-5 h-5" />
                  </div>
                  <div className="empty-state-title !text-[13px]">未找到相关内容</div>
                  <div className="empty-state-desc !text-[11px]">试试其他关键词</div>
                </div>
              ) : (
                <>
                  <div className="text-[10px] uppercase tracking-wider font-semibold text-[hsl(var(--muted-foreground))] mb-2 flex items-center gap-1.5">
                    <BookOpen className="w-2.5 h-2.5" />
                    文档目录
                    <span className="badge badge-default !py-0">{documents.length}</span>
                  </div>
                  <div className="space-y-1">
                    {documents.map((doc) => {
                      const Icon = doc.icon
                      const isActive = selectedDoc === doc.id
                      return (
                        <button
                          key={doc.id}
                          className={cn(
                            'w-full flex items-center gap-2 px-2 py-2 rounded-[8px] text-left transition-[background-color,color,border-color,box-shadow] duration-150 ease-out border',
                            isActive
                              ? '!bg-[hsl(var(--brand-600))] !text-white !border-[hsl(var(--brand-700))] shadow-brand-glow'
                              : '!bg-transparent !text-[hsl(var(--slate-700))] !border-transparent hover:!bg-[hsl(var(--card))] hover:!border-[hsl(var(--border))] hover:shadow-xs'
                          )}
                          onClick={() => {
                            setSelectedDoc(doc.id)
                          }}
                        >
                          <span className={cn(
                            'icon-chip !w-7 !h-7',
                            isActive ? '!bg-white/20 !text-white !border-white/30' : 'icon-chip-slate'
                          )}>
                            <Icon className="w-3.5 h-3.5" />
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="text-[12.5px] font-semibold truncate">{doc.title}</div>
                            <div className={cn('text-[10.5px] truncate mt-0.5', isActive ? 'text-white/80' : 'text-[hsl(var(--muted-foreground))]')}>{doc.description}</div>
                          </div>
                          {isActive && <ChevronRight className="w-3.5 h-3.5 shrink-0 text-white" />}
                        </button>
                      )
                    })}
                  </div>
                </>
              )}
            </div>
            <div className="px-4 py-2.5 border-t border-[hsl(var(--border))] text-[10px] text-[hsl(var(--muted-foreground))] text-center shrink-0 bg-[hsl(var(--card)/0.5)]">
              © {new Date().getFullYear()} 青云制作_彭明航 版权所有
            </div>
          </div>

          <div className="flex-1 relative bg-[hsl(var(--card))]">
            <div
              ref={scrollContainerRef}
              onScroll={handleScroll}
              className="h-full overflow-y-auto"
            >
              <div className="px-8 py-7 max-w-3xl">
                <MarkdownRenderer content={content} highlightKeyword={highlightKeyword} />
              </div>
            </div>

            {/* 返回顶部按钮 */}
            {showScrollTop && (
              <button
                onClick={scrollToTop}
                className="fab absolute bottom-6 right-6 !w-10 !h-10 animate-fade-in-up"
                title="返回顶部"
              >
                <ArrowUp className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
    </DialogPortal>
  )
}
