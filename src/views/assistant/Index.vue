<template>
  <div class="page-container assistant-page">
    <van-nav-bar title="AI 助理" left-arrow @click-left="$router.back()" />

    <!-- AI 头部 -->
    <div class="ai-hero">
      <div class="ai-avatar">
        <AppIcon name="sparkles" :size="24" color="var(--color-primary)" />
      </div>
      <div class="ai-hero-text">
        <div class="ai-name">小智 · 展业助理</div>
        <div class="ai-status"><span class="dot"></span>在线 · 随时响应</div>
      </div>
    </div>

    <!-- 消息流 -->
    <div class="chat-body" ref="chatBody">
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="msg-row"
        :class="msg.role"
      >
        <div v-if="msg.role === 'ai'" class="msg-avatar">智</div>
        <div class="bubble" :class="msg.role">
          <!-- 文本内容 -->
          <div class="msg-text" v-html="renderText(msg.text)"></div>

          <!-- 客户卡片 -->
          <div v-if="msg.card?.type === 'customer'" class="card-box">
            <div class="cb-title"><AppIcon name="user" :size="14" color="var(--color-primary)" /> {{ msg.card.data.name }}</div>
            <div class="cb-row"><span>手机号</span><b>{{ msg.card.data.phone }}</b></div>
            <div class="cb-row"><span>月收入</span><b>{{ fmtAmt(msg.card.data.monthlyIncome) }}</b></div>
            <div class="cb-row"><span>负债</span><b>{{ fmtAmt(msg.card.data.totalDebt) }}</b></div>
          </div>

          <!-- 客户新建确认卡 -->
          <div v-if="msg.card?.type === 'customer_create'" class="card-box">
            <div class="cb-title"><AppIcon name="user-plus" :size="14" color="var(--color-primary)" /> 新建客户</div>
            <div class="cb-row"><span>姓名</span><b>{{ msg.card.data.name }}</b></div>
            <div class="cb-row"><span>手机号</span><b>{{ msg.card.data.phone }}</b></div>
          </div>

          <!-- 资料更新确认卡 -->
          <div v-if="msg.card?.type === 'customer_update'" class="card-box">
            <div class="cb-title"><AppIcon name="edit" :size="14" color="#2563EB" /> 更新客户资料</div>
            <div class="cb-row"><span>客户</span><b>{{ msg.card.data.name }}</b></div>
            <div class="cb-row">
              <span>{{ msg.card.data.fieldLabel }}</span>
              <b class="changed">{{ msg.card.data.oldVal }} → {{ msg.card.data.value }}</b>
            </div>
          </div>

          <!-- 产品确认卡 -->
          <div v-if="msg.card?.type === 'product_create'" class="card-box">
            <div class="cb-title"><AppIcon name="file-plus" :size="14" color="var(--color-primary)" /> 录入产品</div>
            <div class="cb-row"><span>产品名</span><b>{{ msg.card.data.productName || '待补充' }}</b></div>
            <div class="cb-row"><span>机构</span><b>{{ msg.card.data.institution || '待补充' }}</b></div>
            <div class="cb-row" v-if="msg.card.data.minRate"><span>最低利率</span><b>{{ msg.card.data.minRate }}%</b></div>
            <div class="cb-row" v-if="msg.card.data.maxAmount"><span>最高额度</span><b>{{ msg.card.data.maxAmount }}万</b></div>
          </div>

          <!-- 日程确认卡 -->
          <div v-if="msg.card?.type === 'schedule_create'" class="card-box">
            <div class="cb-title"><AppIcon name="calendar-plus" :size="14" color="var(--color-primary)" /> 新建日程</div>
            <div class="cb-row"><span>标题</span><b>{{ msg.card.data.title }}</b></div>
            <div class="cb-row"><span>时间</span><b>{{ fmtDT(msg.card.data.startTime) }}</b></div>
            <div class="cb-row" v-if="msg.card.data.customerName"><span>关联客户</span><b>{{ msg.card.data.customerName }}</b></div>
            <div class="cb-row" v-if="msg.card.data.location"><span>地点</span><b>{{ msg.card.data.location }}</b></div>
          </div>

          <!-- 日程列表卡 -->
          <div v-if="msg.card?.type === 'schedule_list'" class="card-box">
            <div class="cb-title"><AppIcon name="calendar" :size="14" color="var(--color-primary)" /> {{ msg.card.data.label }}</div>
            <div v-for="s in msg.card.data.list" :key="s.id" class="cb-line">
              <span class="cb-time" :class="`p-${s.priority}`">{{ fmtDT(s.startTime) }}</span>
              <span class="cb-text">{{ s.title }}</span>
            </div>
            <div v-if="msg.card.data.list.length === 0" class="cb-empty">暂无日程安排</div>
          </div>

          <!-- 产品列表卡 -->
          <div v-if="msg.card?.type === 'product_list'" class="card-box">
            <div class="cb-title"><AppIcon name="grid" :size="14" color="var(--color-primary)" /> 产品库（{{ msg.card.data.total }}）</div>
            <div v-for="p in msg.card.data.list" :key="p.id" class="cb-line">
              <span class="cb-text">{{ p.productName }}</span>
              <span class="cb-rate">{{ p.minRate }}%~{{ p.maxRate }}%{{ p.rateType === 'monthly' ? ' /月' : '' }}</span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div v-if="msg.pending" class="card-actions">
            <van-button size="small" plain round @click="confirmAction(msg)">确认执行</van-button>
            <van-button size="small" plain round @click="cancelAction(msg)">取消</van-button>
          </div>
          <div v-if="msg.done" class="card-done">✓ 已执行</div>

          <!-- 跳转链接 -->
          <div v-if="msg.link" class="card-link" @click="$router.push(msg.link.to)">
            {{ msg.link.label }} ›
          </div>
        </div>
      </div>

      <!-- typing -->
      <div v-if="thinking" class="msg-row ai">
        <div class="msg-avatar">智</div>
        <div class="bubble ai typing">
          <span class="t-dot"></span><span class="t-dot"></span><span class="t-dot"></span>
        </div>
      </div>
    </div>

    <!-- 快捷指令 -->
    <div class="quick-chips">
      <span v-for="q in quickCommands" :key="q" class="chip" @click="send(q)">{{ q }}</span>
    </div>

    <!-- 输入栏 -->
    <div class="input-bar">
      <van-field
        v-model="inputText"
        placeholder="告诉我你要做什么…"
        class="input-field"
        :border="false"
        @keyup.enter="send()"
      >
        <template #right-icon>
          <span style="display: inline-flex; align-items: center;">
            <VoiceMic label="指令内容" sample="帮我筛选适合公积金信用贷的客户" @confirm="inputText = $event" />
          </span>
        </template>
      </van-field>
      <div class="send-btn" :class="{ active: inputText.trim() }" @click="send()">
        <AppIcon name="chevron-up" :size="18" color="#FFFFFF" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { assistantReply } from '../../api/ai'
import VoiceMic from '../../components/VoiceMic.vue'
import { useCustomerStore } from '../../stores/customer'
import { useProductStore } from '../../stores/product'
import { useScheduleStore } from '../../stores/schedule'

const router = useRouter()
const customerStore = useCustomerStore()
const productStore = useProductStore()
const scheduleStore = useScheduleStore()

const inputText = ref('')
const thinking = ref(false)
const chatBody = ref(null)
let msgId = 0

const quickCommands = [
  '明天有什么日程',
  '查张志远的档案',
  '新增客户 王芳 13900139000',
  '更新张志远的月收入为2万',
  '录入产品 平安薪易贷 利率4%起',
  '明天下午3点与张总面谈',
  '有哪些产品',
]

const messages = ref([])

function pushMsg(role, text, extra = {}) {
  messages.value.push({ id: ++msgId, role, text, ...extra })
  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    chatBody.value?.scrollTo({ top: chatBody.value.scrollHeight, behavior: 'smooth' })
  })
}

function renderText(text) {
  return (text || '').replace(/\n/g, '<br/>')
}

function fmtAmt(val) {
  if (!val) return '-'
  return val >= 10000 ? (val / 10000).toFixed(1) + '万' : val + '元'
}

function fmtDT(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function send(preset) {
  const text = (preset || inputText.value).trim()
  if (!text || thinking.value) return
  inputText.value = ''
  pushMsg('user', text)
  thinking.value = true

  const result = await assistantReply(text)
  thinking.value = false

  switch (result.intent) {
    case 'customer_create':
      handleCustomerCreate(result.entities)
      break
    case 'customer_update':
      handleCustomerUpdate(result.entities, result.reply)
      break
    case 'product_create':
      handleProductCreate(result.entities)
      break
    case 'schedule_create':
      handleScheduleCreate(result.entities, result.reply)
      break
    case 'query_customer':
      handleQueryCustomer(result.entities)
      break
    case 'query_schedule':
      handleQuerySchedule(result.entities)
      break
    case 'query_product':
      handleQueryProduct()
      break
    case 'query_match':
      handleQueryMatch(result.entities)
      break
    default:
      pushMsg('ai', result.reply)
  }
}

/* ============ 客户新增 ============ */
function handleCustomerCreate(e) {
  if (!e.name || !e.phone) {
    pushMsg('ai', '新建客户需要姓名和手机号，例如："新增客户 张三 13800138000"')
    return
  }
  const exists = customerStore.customers.find((c) => c.phone === e.phone)
  if (exists) {
    pushMsg('ai', `手机号 ${e.phone} 已有档案（客户「${exists.name}」），直接为你打开：`, {
      link: { label: '查看客户档案', to: `/customers/${exists.id}` },
    })
    return
  }
  pushMsg('ai', '好的，已识别客户信息，将创建档案：', {
    card: { type: 'customer_create', data: e },
    pending: true,
    action: { type: 'customer_create', payload: e },
  })
}

/* ============ 资料更新 ============ */
function handleCustomerUpdate(e, reply) {
  // 找客户：按姓名或手机号
  let target = null
  if (e.phone) target = customerStore.customers.find((c) => c.phone === e.phone)
  if (!target && e.name) {
    target = customerStore.customers.find((c) => c.name === e.name || c.name.includes(e.name))
  }
  if (!target) {
    pushMsg('ai', `没有找到${e.name ? `「${e.name}」` : '该'}的客户档案。请先确认客户姓名，或从客户列表中选择：`, {
      link: { label: '打开客户列表', to: '/customers' },
    })
    return
  }
  if (e.value === '' || e.value === 0 || e.value === '0') {
    pushMsg('ai', `${reply.replace('请确认：', '')}请同时告诉我新的数值，例如："更新${target.name}的月收入为2万"`)
    return
  }
  const oldVal = target[e.field]
  pushMsg('ai', `收到，将更新客户「${target.name}」的${e.fieldLabel}：`, {
    card: { type: 'customer_update', data: { ...e, name: target.name, oldVal: oldVal ?? '未填写' } },
    pending: true,
    action: { type: 'customer_update', payload: { id: target.id, field: e.field, value: e.value } },
  })
}

/* ============ 产品录入 ============ */
function handleProductCreate(e) {
  if (!e.productName && !e.institution) {
    pushMsg('ai', '录入产品请提供产品名，例如："录入产品 平安薪易贷 利率4%起 额度30万"')
    return
  }
  pushMsg('ai', '已解析产品信息，将录入产品库：', {
    card: { type: 'product_create', data: e },
    pending: true,
    action: { type: 'product_create', payload: e },
  })
}

/* ============ 日程创建 ============ */
function handleScheduleCreate(e, reply) {
  // 关联客户匹配
  let customerName = e.customerName || ''
  let customerId = null
  if (customerName) {
    const matched = customerStore.customers.find(
      (c) => c.name === customerName || c.name.includes(customerName)
    )
    if (matched) {
      customerId = matched.id
      customerName = matched.name
    }
  }
  const payload = { ...e, customerId, customerName }
  pushMsg('ai', reply, {
    card: { type: 'schedule_create', data: payload },
    pending: true,
    action: { type: 'schedule_create', payload },
  })
}

/* ============ 查询 ============ */
function handleQueryCustomer(e) {
  const kw = (e.name || e.phone || '').trim()
  const list = customerStore.customers.filter(
    (c) => c.name.includes(kw) || c.phone.includes(kw) || (c.employer || '').includes(kw)
  )
  if (list.length === 0) {
    pushMsg('ai', `没有找到「${kw}」相关的客户。`, { link: { label: '新建客户', to: '/customers/create' } })
    return
  }
  const c = list[0]
  pushMsg('ai', list.length > 1 ? `找到 ${list.length} 位相关客户，最匹配的是：` : '已找到客户档案：', {
    card: { type: 'customer', data: c },
    link: { label: '查看完整档案', to: `/customers/${c.id}` },
  })
}

function handleQuerySchedule(e) {
  const scope = e.scope || 'upcoming'
  let list = []
  let label = ''
  const now = new Date()
  const dayStart = new Date(now)
  dayStart.setHours(0, 0, 0, 0)
  if (scope === 'today') {
    const dayEnd = new Date(dayStart.getTime() + 86400000)
    list = scheduleStore.schedules.filter((s) => {
      const t = new Date(s.startTime)
      return t >= dayStart && t < dayEnd && !s.done
    })
    label = '今日日程'
  } else if (scope === 'tomorrow') {
    const tStart = new Date(dayStart.getTime() + 86400000)
    const tEnd = new Date(dayStart.getTime() + 172800000)
    list = scheduleStore.schedules.filter((s) => {
      const t = new Date(s.startTime)
      return t >= tStart && t < tEnd && !s.done
    })
    label = '明日日程'
  } else {
    list = scheduleStore.schedules.filter((s) => !s.done && new Date(s.startTime) >= now)
    label = '未来日程'
  }
  list.sort((a, b) => new Date(a.startTime) - new Date(b.startTime))
  pushMsg('ai', `${label}共 ${list.length} 项：`, {
    card: { type: 'schedule_list', data: { list: list.slice(0, 5), label } },
    link: { label: '打开日程计划', to: '/schedules' },
  })
}

function handleQueryProduct() {
  const list = productStore.products.slice(0, 5)
  pushMsg('ai', `产品库共 ${productStore.products.length} 个产品（启用 ${productStore.activeCount} 个）：`, {
    card: { type: 'product_list', data: { list, total: productStore.products.length } },
    link: { label: '打开产品库', to: '/products' },
  })
}

function handleQueryMatch(e) {
  const c = customerStore.customers.find((x) => x.name === e.name || x.name.includes(e.name))
  if (!c) {
    pushMsg('ai', `没有找到客户「${e.name}」的档案。`, { link: { label: '打开客户列表', to: '/customers' } })
    return
  }
  pushMsg('ai', `已定位客户「${c.name}」，正在为你打开 AI 匹配：`, {
    link: { label: '立即匹配', to: `/customers/${c.id}/match` },
  })
}

/* ============ 确认/取消 ============ */
function confirmAction(msg) {
  const { type, payload } = msg.action
  if (type === 'customer_create') {
    const c = customerStore.addCustomer({
      name: payload.name,
      phone: payload.phone,
      source: 'ai',
      remark: '由 AI 助理创建',
    })
    msg.link = { label: '查看新档案', to: `/customers/${c.id}` }
  } else if (type === 'customer_update') {
    customerStore.mergeCustomerFields(payload.id, { [payload.field]: payload.value })
    const c = customerStore.getCustomerById(payload.id)
    msg.link = { label: '查看客户档案', to: `/customers/${payload.id}` }
    if (c) msg.text = `已更新客户「${c.name}」的档案字段。`
  } else if (type === 'product_create') {
    const p = productStore.addProduct({
      productName: payload.productName || '未命名产品',
      institution: payload.institution || '待补充',
      minRate: Number(payload.minRate) || 0,
      maxRate: Number(payload.minRate ? payload.minRate + 2 : 5) || 5,
      minAmount: 1,
      maxAmount: Number(payload.maxAmount) || 30,
      loanTerm: '12-36个月',
      repaymentMethod: '等额本息',
      conditions: '由 AI 助理录入，待补充完整准入条件',
      source: 'ai',
    })
    msg.link = { label: '查看产品', to: `/products/${p.id}` }
  } else if (type === 'schedule_create') {
    const s = scheduleStore.addSchedule({
      title: payload.title,
      startTime: payload.startTime,
      endTime: payload.endTime,
      reminderTime: new Date(new Date(payload.startTime).getTime() - 15 * 60000).toISOString(),
      priority: payload.priority || 'P1',
      type: payload.type || 'task',
      location: payload.location || '',
      remark: `AI 助理创建：${payload.rawText || payload.remark || ''}`,
      customerId: payload.customerId || null,
      customerName: payload.customerName || '',
      source: 'ai',
    })
    msg.link = { label: '查看日程', to: '/schedules' }
  }
  msg.pending = false
  msg.done = true
  scrollToBottom()
}

function cancelAction(msg) {
  msg.pending = false
  msg.text = '好的，已取消该操作。'
  scrollToBottom()
}

onMounted(() => {
  pushMsg('ai', '你好，我是小智\n你可以直接用一句话让我完成展业工作：新增客户、更新资料、录入产品、创建日程，或者随时查询信息。')
})
</script>

<style scoped>
.assistant-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-base);
}

/* AI 头部 */
.ai-hero {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 12px 16px;
  padding: 14px 16px;
  background: var(--surface-container-lowest);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  box-shadow: var(--shadow-card);
}
.ai-avatar {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: var(--primary-container);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}
.ai-name { font-size: 16px; font-weight: 700; }
.ai-status { font-size: 11px; color: var(--text-secondary); display: flex; align-items: center; gap: 4px; margin-top: 2px; }
.dot { width: 5px; height: 5px; border-radius: 50%; background: var(--color-success); }

/* 消息流 */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.msg-row { display: flex; gap: 8px; }
.msg-row.user { justify-content: flex-end; }

.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: var(--primary-container);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
}
.bubble.ai {
  background: var(--surface-container);
  color: var(--text-primary);
  border: none;
  border-top-left-radius: 4px;
  box-shadow: var(--shadow-1);
}
.bubble.user {
  background: var(--color-primary);
  color: #fff;
  border-top-right-radius: 4px;
}

.msg-text { white-space: pre-wrap; word-break: break-word; }

/* typing */
.bubble.typing { display: flex; gap: 4px; align-items: center; padding: 14px 16px; }
.t-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--text-tertiary);
  animation: blink 1.2s infinite;
}
.t-dot:nth-child(2) { animation-delay: 0.2s; }
.t-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }

/* 结构化卡片 */
.card-box {
  margin-top: 8px;
  background: var(--surface-container-low);
  border: none;
  border-radius: 12px;
  padding: 10px 12px;
}
.cb-title { display: flex; align-items: center; gap: 5px; font-size: 13px; font-weight: 700; margin-bottom: 6px; color: var(--text-primary); }
.cb-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  padding: 3px 0;
}
.cb-row span { color: var(--text-tertiary); }
.cb-row b { color: var(--text-primary); font-weight: 600; text-align: right; }
.cb-row b.changed { color: var(--color-primary); }
.cb-line {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  padding: 4px 0;
  border-bottom: none;
}
.cb-line:last-of-type { border-bottom: none; }
.cb-time { color: var(--text-secondary); font-weight: 600; white-space: nowrap; }
.cb-time.p-P0 { color: var(--color-danger); }
.cb-time.p-P1 { color: var(--color-primary); }
.cb-text { color: var(--text-primary); flex: 1; }
.cb-rate { color: var(--color-primary); font-weight: 600; white-space: nowrap; }
.cb-empty { font-size: 12px; color: var(--text-tertiary); padding: 6px 0; }

/* 操作按钮 */
.card-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
.card-done {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-success);
  font-weight: 600;
}
.card-link {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-primary);
  cursor: pointer;
  font-weight: 600;
}

/* 快捷指令 */
.quick-chips {
  display: flex;
  gap: 8px;
  padding: 8px 16px;
  overflow-x: auto;
  white-space: nowrap;
  scrollbar-width: none;
}
.quick-chips::-webkit-scrollbar { display: none; }
.chip {
  font-size: 12px;
  color: var(--on-primary-container);
  background: var(--primary-container);
  border: none;
  padding: 5px 12px;
  border-radius: 999px;
  flex-shrink: 0;
  white-space: nowrap;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}
.chip:active { transform: scale(0.96); }

/* 输入栏 */
.input-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px calc(10px + env(safe-area-inset-bottom));
  background: var(--surface-container-lowest);
  border-top: none;
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.06);
}
.input-field { flex: 1; }
.input-field :deep(.van-field__control) {
  background: var(--bg-input);
  border-radius: 999px;
  padding: 8px 16px;
}
.send-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--gray-300, #CBD5E1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}
.send-btn.active {
  background: var(--color-primary);
  box-shadow: var(--shadow-primary);
}
</style>
