import { Label } from '@/components/ui/label'
import { VariableInput } from '@/components/ui/variable-input'
import { SelectNative as Select } from '@/components/ui/select-native'
import { useWorkflowStore, type NodeData } from '@/store/workflowStore'

interface ConfigProps {
  data: NodeData
  onChange: (key: string, value: unknown) => void
  renderSelectorInput?: (id: string, label: string, placeholder: string) => React.JSX.Element
}

// 条件判断配置
export function ConditionConfig({ data, onChange }: ConfigProps) {
  const conditionType = (data.conditionType as string) || 'variable'
  const operator = (data.operator as string) || '=='

  // 需要右值的运算符
  const needsRightValue = !['isEmpty', 'isNotEmpty'].includes(operator)

  return (
    <div className="space-y-4">
      {/* 判断类型 */}
      <div className="space-y-2">
        <Label htmlFor="conditionType">判断类型</Label>
        <Select
          id="conditionType"
          value={conditionType}
          onChange={(e) => onChange('conditionType', e.target.value)}
        >
          <option value="variable">变量比较</option>
          <option value="boolean">布尔判断</option>
          <option value="logic">逻辑运算（与/或/非）</option>
          <option value="element_exists">元素存在判断</option>
          <option value="element_visible">元素可见判断</option>
        </Select>
      </div>

      {/* 变量比较 */}
      {conditionType === 'variable' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="leftValue">左值</Label>
            <VariableInput
              value={(data.leftValue as string) || ''}
              onChange={(v) => onChange('leftValue', v)}
              placeholder="输入变量 {变量名} 或字面量"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="operator">运算符</Label>
            <Select
              id="operator"
              value={operator}
              onChange={(e) => onChange('operator', e.target.value)}
            >
              <option value="==">等于 (==)</option>
              <option value="!=">不等于 (!=)</option>
              <option value=">">大于 (&gt;)</option>
              <option value="<">小于 (&lt;)</option>
              <option value=">=">大于等于 (&gt;=)</option>
              <option value="<=">小于等于 (&lt;=)</option>
              <option value="contains">包含</option>
              <option value="not_contains">不包含</option>
              <option value="startswith">开头是</option>
              <option value="endswith">结尾是</option>
              <option value="in">在列表中</option>
              <option value="not_in">不在列表中</option>
              <option value="isEmpty">为空</option>
              <option value="isNotEmpty">不为空</option>
            </Select>
          </div>
          {needsRightValue && (
            <div className="space-y-2">
              <Label htmlFor="rightValue">右值</Label>
              <VariableInput
                value={(data.rightValue as string) || ''}
                onChange={(v) => onChange('rightValue', v)}
                placeholder="输入变量 {变量名} 或字面量"
              />
            </div>
          )}
        </>
      )}

      {/* 布尔判断 */}
      {conditionType === 'boolean' && (
        <div className="space-y-2">
          <Label htmlFor="leftValue">变量</Label>
          <VariableInput
            value={(data.leftValue as string) || ''}
            onChange={(v) => onChange('leftValue', v)}
            placeholder="输入变量 {变量名}，判断是否为真"
          />
          <p className="text-xs text-muted-foreground">
            真值：true、1、非空字符串、非空列表；假值：false、0、空字符串、null
          </p>
        </div>
      )}

      {/* 逻辑运算 */}
      {conditionType === 'logic' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="logicOperator">逻辑运算符</Label>
            <Select
              id="logicOperator"
              value={(data.logicOperator as string) || 'and'}
              onChange={(e) => onChange('logicOperator', e.target.value)}
            >
              <option value="and">与（AND）—— 两个条件都为真</option>
              <option value="or">或（OR）—— 任一条件为真</option>
              <option value="not">非（NOT）—— 对条件取反</option>
            </Select>
          </div>
          {(data.logicOperator as string) !== 'not' ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="condition1">条件1</Label>
                <VariableInput
                  value={(data.condition1 as string) || ''}
                  onChange={(v) => onChange('condition1', v)}
                  placeholder="输入变量 {变量名} 或表达式"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="condition2">条件2</Label>
                <VariableInput
                  value={(data.condition2 as string) || ''}
                  onChange={(v) => onChange('condition2', v)}
                  placeholder="输入变量 {变量名} 或表达式"
                />
              </div>
            </>
          ) : (
            <div className="space-y-2">
              <Label htmlFor="condition">条件</Label>
              <VariableInput
                value={(data.condition as string) || ''}
                onChange={(v) => onChange('condition', v)}
                placeholder="输入变量 {变量名} 或表达式，取反"
              />
            </div>
          )}
        </>
      )}

      {/* 元素存在/可见判断 */}
      {(conditionType === 'element_exists' || conditionType === 'element_visible') && (
        <div className="space-y-2">
          <Label htmlFor="leftValue">元素选择器</Label>
          <VariableInput
            value={(data.leftValue as string) || ''}
            onChange={(v) => onChange('leftValue', v)}
            placeholder="输入 CSS 选择器或 XPath"
          />
        </div>
      )}
    </div>
  )
}

// 循环配置
export function LoopConfig({ data, onChange }: ConfigProps) {
  const loopType = (data.loopType as string) || 'count'
  
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="loopType">循环类型</Label>
        <Select
          id="loopType"
          value={loopType}
          onChange={(e) => onChange('loopType', e.target.value)}
        >
          <option value="count">计数循环</option>
          <option value="range">范围循环</option>
          <option value="while">条件循环</option>
        </Select>
      </div>
      
      {loopType === 'count' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="loopCount">循环次数</Label>
            <VariableInput
              value={(data.loopCount as string) || ''}
              onChange={(v) => onChange('loopCount', v)}
              placeholder="输入循环次数或变量"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="indexVariable">索引变量名</Label>
            <VariableInput
              value={(data.indexVariable as string) || 'i'}
              onChange={(v) => onChange('indexVariable', v)}
              placeholder="索引变量名（默认：i）"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="step">步长</Label>
            <VariableInput
              value={(data.step as string) || '1'}
              onChange={(v) => onChange('step', v)}
              placeholder="每次循环的增量（默认：1）"
            />
          </div>
        </>
      )}
      
      {loopType === 'range' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="startValue">起始值</Label>
            <VariableInput
              value={(data.startValue as string) || '0'}
              onChange={(v) => onChange('startValue', v)}
              placeholder="循环起始值（默认：0）"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="endValue">结束值</Label>
            <VariableInput
              value={(data.endValue as string) || ''}
              onChange={(v) => onChange('endValue', v)}
              placeholder="循环结束值（不包含）"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="step">步长</Label>
            <VariableInput
              value={(data.step as string) || '1'}
              onChange={(v) => onChange('step', v)}
              placeholder="每次循环的增量（默认：1）"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="indexVariable">循环变量名</Label>
            <VariableInput
              value={(data.indexVariable as string) || 'i'}
              onChange={(v) => onChange('indexVariable', v)}
              placeholder="循环变量名（默认：i）"
            />
          </div>
        </>
      )}
      
      {loopType === 'while' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="condition">循环条件</Label>
            <VariableInput
              value={(data.condition as string) || ''}
              onChange={(v) => onChange('condition', v)}
              placeholder="输入循环条件表达式"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="maxIterations">最大迭代次数</Label>
            <VariableInput
              value={(data.maxIterations as string) || '1000'}
              onChange={(v) => onChange('maxIterations', v)}
              placeholder="防止无限循环的最大次数（默认：1000）"
            />
          </div>
        </>
      )}
      
      {/* 高级配置 */}
      <div className="space-y-2">
        <Label htmlFor="timeout">超时时间（秒）</Label>
        <VariableInput
          value={String(data.timeout || '0')}
          onChange={(v) => onChange('timeout', v)}
          placeholder="0 表示不限制超时，当前模块建议: 0秒"
        />
        <p className="text-xs text-muted-foreground">
          0 表示不限制超时，当前模块建议: 0秒
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="onTimeout">运行超时后</Label>
        <Select
          id="onTimeout"
          value={(data.onTimeout as string) || 'retry'}
          onChange={(e) => onChange('onTimeout', e.target.value)}
        >
          <option value="retry">重试</option>
          <option value="skip">跳过</option>
          <option value="stop">停止</option>
        </Select>
      </div>
    </div>
  )
}

// 遍历列表配置
export function ForeachConfig({ data, onChange }: ConfigProps) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="listVariable">列表变量</Label>
        <VariableInput
          value={(data.listVariable as string) || ''}
          onChange={(v) => onChange('listVariable', v)}
          placeholder="输入列表变量名"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="itemVariable">元素变量名</Label>
        <VariableInput
          value={(data.itemVariable as string) || 'item'}
          onChange={(v) => onChange('itemVariable', v)}
          placeholder="元素变量名（默认：item）"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="indexVariable">索引变量名（可选）</Label>
        <VariableInput
          value={(data.indexVariable as string) || ''}
          onChange={(v) => onChange('indexVariable', v)}
          placeholder="索引变量名（可选）"
        />
      </div>
    </div>
  )
}

// 遍历字典配置
export function ForeachDictConfig({ data, onChange }: ConfigProps) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="dictVariable">字典变量</Label>
        <VariableInput
          value={(data.dictVariable as string) || ''}
          onChange={(v) => onChange('dictVariable', v)}
          placeholder="输入字典变量名"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="keyVariable">键变量名</Label>
        <VariableInput
          value={(data.keyVariable as string) || 'key'}
          onChange={(v) => onChange('keyVariable', v)}
          placeholder="键变量名（默认：key）"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="valueVariable">值变量名</Label>
        <VariableInput
          value={(data.valueVariable as string) || 'value'}
          onChange={(v) => onChange('valueVariable', v)}
          placeholder="值变量名（默认：value）"
        />
      </div>
    </div>
  )
}

// 定时任务配置
export function ScheduledTaskConfig({ data, onChange }: ConfigProps) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="cronExpression">Cron表达式</Label>
        <VariableInput
          value={(data.cronExpression as string) || ''}
          onChange={(v) => onChange('cronExpression', v)}
          placeholder="例如：0 0 * * * （每小时执行）"
        />
        <p className="text-xs text-muted-foreground">
          格式：秒 分 时 日 月 周
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="taskName">任务名称</Label>
        <VariableInput
          value={(data.taskName as string) || ''}
          onChange={(v) => onChange('taskName', v)}
          placeholder="输入任务名称"
        />
      </div>
    </div>
  )
}

// 子流程配置
export function SubflowConfig({ data, onChange }: ConfigProps) {
  const nodes = useWorkflowStore((s) => s.nodes)

  // 筛选画布上所有子流程定义节点：
  // 1. groupNode 且 isSubflow=true（分组勾选了「定义为子流程」）
  // 2. subflowHeaderNode（函数头形式的子流程）
  const subflowGroups = nodes.filter(
    (n) =>
      (n.type === 'groupNode' && (n.data as Record<string, unknown>).isSubflow === true) ||
      n.type === 'subflowHeaderNode'
  )

  const selectedId = (data.subflowGroupId as string) || ''

  const handleSelect = (id: string) => {
    const node = subflowGroups.find((n) => n.id === id)
    const name = node
      ? ((node.data as Record<string, unknown>).subflowName as string) || (node.data.label as string) || ''
      : ''
    onChange('subflowGroupId', id)
    onChange('subflowName', name)
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="subflowGroupId">选择子流程</Label>
        {subflowGroups.length === 0 ? (
          <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 p-3 rounded-md">
            画布上暂无子流程。请先在画布上添加「子流程定义」模块，或创建分组后勾选「定义为子流程」。
          </div>
        ) : (
          <Select
            id="subflowGroupId"
            value={selectedId}
            onChange={(e) => handleSelect(e.target.value)}
          >
            <option value="">请选择子流程...</option>
            {subflowGroups.map((n) => {
              const name = ((n.data as Record<string, unknown>).subflowName as string) || (n.data.label as string) || n.id
              const typeLabel = n.type === 'subflowHeaderNode' ? '函数头' : '分组'
              return (
                <option key={n.id} value={n.id}>
                  [{typeLabel}] {name}
                </option>
              )
            })}
          </Select>
        )}
        {selectedId && (
          <p className="text-xs text-muted-foreground">
            已选：{(data.subflowName as string) || selectedId}
          </p>
        )}
      </div>
    </div>
  )
}
