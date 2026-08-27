<template>
  <div class="page-container">
    <van-nav-bar title="客户档案" left-arrow @click-left="$router.back()">
      <template #right>
        <span class="nav-edit-btn" @click="openEdit">
          <van-icon name="edit" size="14" /> 编辑
        </span>
      </template>
    </van-nav-bar>

    <div v-if="customer" class="detail-page">
      <!-- 客户头部 -->
      <div class="customer-header">
        <div class="header-top">
          <div class="customer-avatar" :class="customer.gender">
            {{ customer.name.charAt(0) }}
          </div>
          <div class="header-info">
            <div class="header-name">{{ customer.name }}</div>
            <div class="header-tags">
              <span class="tag">{{ customer.age || '--' }}岁</span>
              <span class="tag">{{ customer.gender }}</span>
              <span class="tag">{{ customer.maritalStatus || '未填写' }}</span>
              <span class="tag source-tag">{{ sourceLabel }}</span>
            </div>
          </div>
          <div class="risk-badge" :class="riskLevel">
            {{ riskText }}
          </div>
        </div>

        <!-- 资料完整度 -->
        <div class="completeness-bar">
          <div class="completeness-top">
            <span class="completeness-label">
              <van-icon name="records" size="13" color="#3B82F6" />
              资料完整度
            </span>
            <span class="completeness-num">{{ completeness }}%</span>
          </div>
          <div class="completeness-track">
            <div class="completeness-fill" :style="{ width: completeness + '%' }"></div>
          </div>
          <p v-if="missingMaterials.length > 0" class="missing-tip" @click="$router.push(`/customers/${customer.id}/materials`)">
            待补充：{{ missingMaterials.join('、') }} <van-icon name="arrow" size="10" />
          </p>
          <p v-else class="missing-tip done">资料已齐全，可以放心匹配产品</p>
        </div>

        <div class="header-stats">
          <div class="stat">
            <span class="stat-label">月收入</span>
            <span class="stat-value">{{ formatMoney(customer.monthlyIncome) }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat">
            <span class="stat-label">总负债</span>
            <span class="stat-value" :class="{ warn: customer.totalDebt > 100000 }">{{ formatMoney(customer.totalDebt) }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat">
            <span class="stat-label">负债率</span>
            <span class="stat-value" :class="getDebtRatioClass">{{ debtRatio }}%</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat">
            <span class="stat-label">逾期</span>
            <span class="stat-value" :class="{ warn: customer.maxOverdueMonths > 0 }">{{ customer.maxOverdueMonths }}月</span>
          </div>
        </div>
      </div>

      <!-- 补充资料入口 -->
      <div class="material-entry" @click="$router.push(`/customers/${customer.id}/materials`)">
        <div class="entry-icon">
          <van-icon name="add-o" size="18" color="#3B82F6" />
        </div>
        <div class="entry-text">
          <div class="entry-title">补充客户资料</div>
          <div class="entry-desc">拍照 / 上传 / 语音口述，AI 自动提取并合并到档案</div>
        </div>
        <van-icon name="arrow" size="16" color="#94A3B8" />
      </div>

      <!-- 材料列表 -->
      <div class="section">
        <div class="section-header">
          <span class="section-title">已录入材料</span>
          <span class="section-extra">{{ customer.materials.length }}份</span>
        </div>
        <div class="material-list">
          <div class="material-item" v-for="mat in customer.materials" :key="mat.id" @click="openMaterial(mat)">
            <div class="mat-icon">
              <van-icon name="description" size="16" color="#3B82F6" />
            </div>
            <div class="mat-info">
              <div class="mat-name">{{ mat.type }}</div>
              <div class="mat-time">{{ mat.time }} · {{ mat.fieldCount || '--' }}项字段</div>
            </div>
            <div class="mat-confidence" :class="{ low: mat.confidence < 0.85 }">
              {{ Math.round(mat.confidence * 100) }}%
            </div>
          </div>
          <div v-if="customer.materials.length === 0" class="material-empty">
            <van-icon name="description" size="28" color="#94A3B8" />
            <p>暂无材料，点击上方「补充客户资料」录入身份证、流水等材料</p>
          </div>
        </div>
      </div>

      <!-- 详细信息分组 -->
      <div class="section" v-for="group in infoGroups" :key="group.title">
        <div class="section-header" @click="toggleGroup(group.key)">
          <span class="section-title">{{ group.title }}</span>
          <van-icon :name="expandedGroups[group.key] ? 'arrow-up' : 'arrow-down'" size="14" color="#475569" />
        </div>
        <div v-show="expandedGroups[group.key]" class="info-list">
          <div class="info-row" v-for="field in group.fields" :key="field.key">
            <span class="info-label">{{ field.label }}</span>
            <span class="info-value" :class="field.class">{{ field.value }}</span>
            <span class="info-source" v-if="field.source" @click="showSource(field)">
              <van-icon name="search" size="12" color="#06B6D4" />
            </span>
          </div>
        </div>
      </div>

      <!-- 关联日程 -->
      <div class="section">
        <div class="section-header">
          <span class="section-title">关联日程</span>
          <div class="section-actions">
            <span
              class="sch-add-btn"
              @click="$router.push(`/schedules/create?customerId=${customer.id}&customerName=${encodeURIComponent(customer.name)}`)"
            >
              <van-icon name="plus" size="12" /> 新建日程
            </span>
            <span class="section-extra" v-if="upcomingSchedules.length > 0" @click="$router.push('/schedules')">全部 ›</span>
          </div>
        </div>
        <div class="sch-list" v-if="upcomingSchedules.length > 0">
          <div class="sch-item" v-for="sch in upcomingSchedules" :key="sch.id" @click="$router.push('/schedules')">
            <div class="sch-time" :class="`prio-${sch.priority}`">
              <div class="sch-clock">{{ formatSchTime(sch.startTime) }}</div>
              <div class="sch-prio">{{ sch.priority }}</div>
            </div>
            <div class="sch-info">
              <div class="sch-title">{{ sch.title }}</div>
              <div class="sch-meta">
                <span v-if="sch.location">📍 {{ sch.location }}</span>
                <span v-if="sch.reminderTime">⏰ 提醒已设</span>
              </div>
            </div>
            <van-icon name="arrow" size="14" color="#94A3B8" />
          </div>
        </div>
        <div class="sch-empty" v-else>
          <span class="sch-empty-text">暂无针对该客户的日程</span>
          <van-button
            size="small"
            round
            type="primary"
            plain
            @click="$router.push(`/schedules/create?customerId=${customer.id}&customerName=${encodeURIComponent(customer.name)}`)"
          >
            <van-icon name="plus" /> 为 TA 安排日程
          </van-button>
        </div>
      </div>

      <!-- 推演历史 -->
      <div class="section" v-if="simulations.length > 0">
        <div class="section-header">
          <span class="section-title">推演记录</span>
          <span class="section-extra">{{ simulations.length }}条</span>
        </div>
        <div class="sim-list">
          <div class="sim-item" v-for="sim in simulations" :key="sim.id" @click="$router.push(`/customers/${customer.id}/simulation?load=${sim.id}`)">
            <div class="sim-time">{{ sim.createdAt }}</div>
            <div class="sim-adjustments">
              <span v-for="(adj, key) in sim.adjustments" :key="key" class="adjust-tag">
                {{ fieldLabels[key] || key }}: {{ adj.old }} → {{ adj.new }}
              </span>
            </div>
            <div class="sim-result">
              <span class="sim-approved">准入{{ sim.matchResult.approved.length }}</span>
              <span class="sim-rejected">拒贷{{ sim.matchResult.rejected.length }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部操作 -->
      <div class="action-bar">
        <van-button plain round @click="$router.push(`/customers/${customer.id}/simulation`)">
          场景推演
        </van-button>
        <van-button round type="primary" @click="$router.push(`/customers/${customer.id}/match`)">
          <van-icon name="search" /> 匹配产品
        </van-button>
      </div>
    </div>

    <!-- 溯源弹窗 -->
    <van-popup v-model:show="showSourcePopup" position="center" round :style="{ width: '85%' }">
      <div class="source-popup">
        <div class="source-title">材料溯源</div>
        <div class="source-content">
          <div class="source-field">
            <span class="source-label">字段</span>
            <span class="source-value">{{ currentSourceField?.label }}</span>
          </div>
          <div class="source-field">
            <span class="source-label">当前值</span>
            <span class="source-value">{{ currentSourceField?.value }}</span>
          </div>
          <div class="source-field">
            <span class="source-label">来源</span>
            <span class="source-value">{{ currentSourceField?.source }}</span>
          </div>
          <div class="source-preview">
            <div class="preview-placeholder">
              <van-icon name="photo-o" size="32" color="#94A3B8" />
              <span>原始材料截图</span>
            </div>
          </div>
        </div>
        <van-button block round type="primary" @click="showSourcePopup = false" style="margin-top: 16px;">
          关闭
        </van-button>
      </div>
    </van-popup>

    <!-- 材料查看弹层 -->
    <van-popup v-model:show="showMaterialViewer" position="bottom" round :style="{ height: '72%' }">
      <div class="mat-viewer" v-if="activeMaterial">
        <div class="mv-header">
          <div class="mv-title">
            <van-icon name="description" size="16" color="#3B82F6" />
            <span>{{ activeMaterial.type }}</span>
          </div>
          <div class="mv-conf" :class="{ low: activeMaterial.confidence < 0.85 }">
            AI 置信度 {{ Math.round(activeMaterial.confidence * 100) }}%
          </div>
        </div>

        <!-- 模拟材料预览 -->
        <div class="mv-preview">
          <div class="mv-preview-icon">
            <van-icon :name="activeMaterial.source === 'photo' ? 'photo-o' : (activeMaterial.source === 'voice' ? 'volume-o' : 'orders-o')" size="36" color="#3B82F6" />
          </div>
          <div class="mv-preview-name">{{ activeMaterial.type }}（演示数据）</div>
          <div class="mv-fields">
            <div class="mv-field" v-for="f in materialPreviewFields" :key="f.label">
              <span class="mv-label">{{ f.label }}</span>
              <span class="mv-value">{{ f.value }}</span>
            </div>
          </div>
        </div>

        <!-- 元信息 -->
        <div class="mv-meta">
          <div class="mv-meta-row">
            <span class="mv-meta-label">录入方式</span>
            <span class="mv-meta-value">{{ sourceText(activeMaterial.source) }}</span>
          </div>
          <div class="mv-meta-row">
            <span class="mv-meta-label">录入时间</span>
            <span class="mv-meta-value">{{ activeMaterial.time }}</span>
          </div>
          <div class="mv-meta-row">
            <span class="mv-meta-label">材料编号</span>
            <span class="mv-meta-value">{{ activeMaterial.id }}</span>
          </div>
        </div>

        <div class="mv-actions">
          <van-button plain round block @click="openMatTypeEdit">编辑类型</van-button>
          <van-button plain round block type="danger" @click="confirmRemoveMaterial">删除材料</van-button>
          <van-button round block type="primary" @click="showMaterialViewer = false">关闭</van-button>
        </div>
      </div>
    </van-popup>

    <!-- 编辑客户信息弹层（全字段分组编辑） -->
    <van-popup v-model:show="showEditPopup" position="bottom" round :style="{ height: '88%' }">
      <div class="edit-popup" v-if="customer">
        <div class="ep-header">
          <span class="ep-title">编辑客户信息</span>
          <van-icon name="cross" size="18" color="#94A3B8" @click="showEditPopup = false" />
        </div>

        <div class="ep-form">
          <!-- 基础信息 -->
          <div class="ep-group-title">基础信息</div>
          <div class="ep-grid">
            <div class="ep-field span2">
              <span class="ep-label">姓名 <i class="req">*</i></span>
              <van-field v-model="editForm.name" placeholder="客户姓名" class="ep-input" />
            </div>
            <div class="ep-field span2">
              <span class="ep-label">手机号 <i class="req">*</i></span>
              <van-field v-model="editForm.phone" type="tel" maxlength="11" placeholder="客户手机号" class="ep-input" />
            </div>
            <div class="ep-field">
              <span class="ep-label">性别</span>
              <div class="ep-chips">
                <span class="ep-chip" :class="{ active: editForm.gender === g }" v-for="g in ['男', '女']" :key="g" @click="editForm.gender = g">{{ g }}</span>
              </div>
            </div>
            <div class="ep-field">
              <span class="ep-label">年龄</span>
              <van-field v-model="editForm.age" type="digit" placeholder="如 32" class="ep-input" />
            </div>
            <div class="ep-field span2">
              <span class="ep-label">所在城市</span>
              <van-field v-model="editForm.city" placeholder="如 上海" class="ep-input" />
            </div>
            <div class="ep-field">
              <span class="ep-label">婚姻状况</span>
              <div class="ep-chips">
                <span class="ep-chip" :class="{ active: editForm.maritalStatus === m }" v-for="m in ['已婚', '未婚', '离异']" :key="m" @click="editForm.maritalStatus = m">{{ m }}</span>
              </div>
            </div>
            <div class="ep-field">
              <span class="ep-label">学历</span>
              <div class="ep-chips">
                <span class="ep-chip" :class="{ active: editForm.education === e }" v-for="e in ['高中', '大专', '本科', '硕士+']" :key="e" @click="editForm.education = e">{{ e }}</span>
              </div>
            </div>
          </div>

          <!-- 收入信息 -->
          <div class="ep-group-title">收入信息 <em>万元/月</em></div>
          <div class="ep-grid">
            <div class="ep-field">
              <span class="ep-label">月均收入</span>
              <van-field v-model="editForm.monthlyIncome" type="number" placeholder="如 2.5" class="ep-input" />
            </div>
            <div class="ep-field">
              <span class="ep-label">公积金基数</span>
              <van-field v-model="editForm.housingFundBase" type="number" placeholder="如 0.8" class="ep-input" />
            </div>
            <div class="ep-field span2">
              <span class="ep-label">工作单位</span>
              <van-field v-model="editForm.employer" placeholder="如 上海某科技公司" class="ep-input" />
            </div>
            <div class="ep-field span2">
              <span class="ep-label">职位</span>
              <van-field v-model="editForm.position" placeholder="如 产品经理" class="ep-input" />
            </div>
          </div>

          <!-- 负债与征信 -->
          <div class="ep-group-title">负债与征信</div>
          <div class="ep-grid">
            <div class="ep-field">
              <span class="ep-label">总负债（万元）</span>
              <van-field v-model="editForm.totalDebt" type="number" placeholder="如 12" class="ep-input" />
            </div>
            <div class="ep-field">
              <span class="ep-label">信用卡使用率（%）</span>
              <van-field v-model="editForm.creditCardUsage" type="digit" placeholder="如 45" class="ep-input" />
            </div>
            <div class="ep-field">
              <span class="ep-label">近1月查询（次）</span>
              <van-field v-model="editForm.queryCount1m" type="digit" placeholder="如 1" class="ep-input" />
            </div>
            <div class="ep-field">
              <span class="ep-label">近3月查询（次）</span>
              <van-field v-model="editForm.queryCount3m" type="digit" placeholder="如 3" class="ep-input" />
            </div>
            <div class="ep-field">
              <span class="ep-label">近6月查询（次）</span>
              <van-field v-model="editForm.queryCount6m" type="digit" placeholder="如 5" class="ep-input" />
            </div>
            <div class="ep-field">
              <span class="ep-label">最长逾期（月）</span>
              <van-field v-model="editForm.maxOverdueMonths" type="digit" placeholder="0 表示无逾期" class="ep-input" />
            </div>
          </div>

          <!-- 资产信息 -->
          <div class="ep-group-title">资产信息 <em>万元</em></div>
          <div class="ep-grid">
            <div class="ep-field">
              <span class="ep-label">房产价值</span>
              <van-field v-model="editForm.propertyValue" type="number" placeholder="如 320" class="ep-input" />
            </div>
            <div class="ep-field">
              <span class="ep-label">是否有抵押</span>
              <div class="ep-chips">
                <span class="ep-chip" :class="{ active: editForm.hasMortgage === true }" @click="editForm.hasMortgage = true">是</span>
                <span class="ep-chip" :class="{ active: editForm.hasMortgage === false }" @click="editForm.hasMortgage = false">否</span>
              </div>
            </div>
            <div class="ep-field">
              <span class="ep-label">车辆价值</span>
              <van-field v-model="editForm.carValue" type="number" placeholder="如 15" class="ep-input" />
            </div>
            <div class="ep-field">
              <span class="ep-label">期望额度</span>
              <van-field v-model="editForm.expectedAmount" type="number" placeholder="如 20" class="ep-input" />
            </div>
          </div>

          <!-- 客户来源 -->
          <div class="ep-group-title">客户来源</div>
          <div class="ep-grid">
            <div class="ep-field span2">
              <div class="ep-chips wrap">
                <span class="ep-chip" :class="{ active: editForm.source === s.key }" v-for="s in editSources" :key="s.key" @click="editForm.source = s.key">{{ s.name }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="ep-actions">
          <van-button plain round block @click="showEditPopup = false">取消</van-button>
          <van-button round block type="primary" :loading="savingEdit" loading-text="保存中..." @click="saveEdit">保存修改</van-button>
        </div>
      </div>
    </van-popup>

    <!-- 材料类型编辑弹层 -->
    <van-popup v-model:show="showMatTypeEdit" position="center" round :style="{ width: '85%' }">
      <div class="mat-type-popup" v-if="activeMaterial">
        <div class="mtp-title">修改材料类型</div>
        <p class="mtp-desc">AI 识别有误时可手动更正类型</p>
        <div class="mtp-chips">
          <span class="mtp-chip" :class="{ active: matTypeDraft === t }" v-for="t in materialTypes" :key="t" @click="matTypeDraft = t">{{ t }}</span>
        </div>
        <div class="mtp-actions">
          <van-button plain round block @click="showMatTypeEdit = false">取消</van-button>
          <van-button round block type="primary" @click="confirmMatType">确认修改</van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast, showConfirmDialog } from 'vant'
import { useCustomerStore } from '../../stores/customer'
import { useScheduleStore } from '../../stores/schedule'

const route = useRoute()
const router = useRouter()
const store = useCustomerStore()
const scheduleStore = useScheduleStore()

// 数据加载（覆盖直接刷新详情页的场景）
onMounted(async () => {
  try {
    await store.loadCustomers()
    await store.loadSimulations(route.params.id)
    await scheduleStore.loadSchedules()
  } catch (e) { /* 拦截器已提示 */ }
})

const customer = computed(() => store.getCustomerById(route.params.id))
const simulations = computed(() => store.getSimulationsByCustomerId(route.params.id))

// 该客户的未来未完成日程（按开始时间升序）
const upcomingSchedules = computed(() => {
  if (!customer.value) return []
  const now = new Date()
  return scheduleStore.schedules
    .filter((s) => s.customerId === customer.value.id && !s.done && new Date(s.startTime) >= now)
    .sort((a, b) => new Date(a.startTime) - new Date(b.startTime))
})

function formatSchTime(iso) {
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const expandedGroups = reactive({
  basic: true,
  income: true,
  debt: true,
  asset: true,
  credit: false,
})

const showSourcePopup = ref(false)
const currentSourceField = ref(null)

/* ===== 材料查看 ===== */
const showMaterialViewer = ref(false)
const activeMaterial = ref(null)

function openMaterial(mat) {
  activeMaterial.value = mat
  showMaterialViewer.value = true
}

function sourceText(s) {
  const map = { upload: '文件上传', photo: '现场拍照', voice: '语音口述' }
  return map[s] || '文件上传'
}

const materialPreviewFields = computed(() => {
  const mat = activeMaterial.value
  const c = customer.value || {}
  if (!mat) return []
  const map = {
    '身份证': [
      { label: '姓名', value: c.name || '--' },
      { label: '身份证号', value: c.idCard || '--' },
      { label: '签发机关', value: '上海市公安局浦东分局' },
      { label: '有效期限', value: '2020.06.15 - 2040.06.15' },
    ],
    '工资流水': [
      { label: '月均收入', value: c.monthlyIncome ? formatMoney(c.monthlyIncome) : '--' },
      { label: '发薪单位', value: c.employer || '--' },
      { label: '流水月份', value: '近 6 个月' },
      { label: '账户余额', value: '87,300 元' },
    ],
    '征信报告': [
      { label: '征信评分', value: '680 分（良好）' },
      { label: '逾期记录', value: (c.maxOverdueMonths || 0) > 0 ? `最长逾期 ${c.maxOverdueMonths} 个月` : '无逾期' },
      { label: '近3月查询', value: `${c.queryCount3m || 0} 次` },
      { label: '授信总额', value: formatMoney(c.totalDebt || 0) },
    ],
    '营业执照': [
      { label: '企业名称', value: c.employer || '--' },
      { label: '统一社会信用代码', value: '9131***********XK' },
      { label: '成立日期', value: '2018-03-12' },
      { label: '经营范围', value: '软件开发、技术服务' },
    ],
  }
  return map[mat.type] || [
    { label: '文件类型', value: mat.type },
    { label: '录入时间', value: mat.time },
  ]
})

/* ===== 编辑客户信息（全字段分组编辑） ===== */
const showEditPopup = ref(false)
const savingEdit = ref(false)

const editSources = [
  { key: 'friend', name: '朋友介绍' },
  { key: 'telemarketing', name: '电话营销' },
  { key: 'walkin', name: '门店进件' },
  { key: 'online', name: '线上渠道' },
  { key: 'referral', name: '老客转介绍' },
  { key: 'other', name: '其他' },
]

// 元 → 万元字符串（用于表单展示，如 25000 → "2.5"）
const yuanToWan = (v) => (v ? String(+(v / 10000).toFixed(2)) : '')
// 万元字符串 → 元（如 "2.5" → 25000；空值 → null）
const wanToYuan = (v) => (v === '' || v == null ? null : Math.round(parseFloat(v) * 10000))
// 数字字段：空 → null，否则 Number
const toNum = (v) => (v === '' || v == null ? null : Number(v))

const editForm = reactive({
  name: '',
  phone: '',
  gender: '',
  age: '',
  city: '',
  maritalStatus: '',
  education: '',
  monthlyIncome: '',
  housingFundBase: '',
  employer: '',
  position: '',
  totalDebt: '',
  creditCardUsage: '',
  queryCount1m: '',
  queryCount3m: '',
  queryCount6m: '',
  maxOverdueMonths: '',
  propertyValue: '',
  hasMortgage: null,
  carValue: '',
  expectedAmount: '',
  source: '',
})

function openEdit() {
  const c = customer.value
  if (!c) return
  editForm.name = c.name || ''
  editForm.phone = c.phone || ''
  editForm.gender = c.gender || ''
  editForm.age = c.age != null ? String(c.age) : ''
  editForm.city = c.city || ''
  editForm.maritalStatus = c.maritalStatus || ''
  editForm.education = c.education || ''
  editForm.monthlyIncome = yuanToWan(c.monthlyIncome)
  editForm.housingFundBase = yuanToWan(c.housingFundBase)
  editForm.employer = c.employer || ''
  editForm.position = c.position || ''
  editForm.totalDebt = yuanToWan(c.totalDebt)
  editForm.creditCardUsage = c.creditCardUsage != null ? String(c.creditCardUsage) : ''
  editForm.queryCount1m = c.queryCount1m != null ? String(c.queryCount1m) : ''
  editForm.queryCount3m = c.queryCount3m != null ? String(c.queryCount3m) : ''
  editForm.queryCount6m = c.queryCount6m != null ? String(c.queryCount6m) : ''
  editForm.maxOverdueMonths = c.maxOverdueMonths != null ? String(c.maxOverdueMonths) : ''
  editForm.propertyValue = c.propertyValue != null ? String(c.propertyValue) : ''
  editForm.hasMortgage = c.hasMortgage != null ? !!c.hasMortgage : null
  editForm.carValue = c.carValue != null ? String(c.carValue) : ''
  editForm.expectedAmount = c.expectedAmount != null ? String(c.expectedAmount) : ''
  editForm.source = c.source || ''
  showEditPopup.value = true
}

function saveEdit() {
  if (!editForm.name.trim()) {
    showToast('请输入客户姓名')
    return
  }
  // 演示数据允许脱敏手机号（如 138****6688），生产环境应强校验
  const raw = editForm.phone.replace(/[*\s-]/g, '')
  if (!/^1[3-9]\d{9}$/.test(raw)) {
    showToast('手机号格式不正确')
    return
  }
  savingEdit.value = true
  setTimeout(() => {
    store.updateCustomer(customer.value.id, {
      name: editForm.name.trim(),
      phone: editForm.phone,
      gender: editForm.gender || '男',
      age: toNum(editForm.age),
      city: editForm.city,
      maritalStatus: editForm.maritalStatus,
      education: editForm.education,
      monthlyIncome: wanToYuan(editForm.monthlyIncome),
      housingFundBase: wanToYuan(editForm.housingFundBase),
      employer: editForm.employer,
      position: editForm.position,
      totalDebt: wanToYuan(editForm.totalDebt),
      creditCardUsage: toNum(editForm.creditCardUsage),
      queryCount1m: toNum(editForm.queryCount1m),
      queryCount3m: toNum(editForm.queryCount3m),
      queryCount6m: toNum(editForm.queryCount6m),
      maxOverdueMonths: toNum(editForm.maxOverdueMonths) || 0,
      propertyValue: toNum(editForm.propertyValue),
      hasMortgage: editForm.hasMortgage,
      carValue: toNum(editForm.carValue),
      expectedAmount: toNum(editForm.expectedAmount),
      source: editForm.source || 'other',
    })
    savingEdit.value = false
    showEditPopup.value = false
    showSuccessToast('已保存')
  }, 400)
}

/* ===== 材料编辑 / 删除 ===== */
const materialTypes = ['身份证', '工资流水', '银行流水', '征信报告', '营业执照', '房产证', '行驶证', '其他']
const showMatTypeEdit = ref(false)
const matTypeDraft = ref('')

function openMatTypeEdit() {
  matTypeDraft.value = activeMaterial.value?.type || ''
  showMatTypeEdit.value = true
}

function confirmMatType() {
  if (!matTypeDraft.value) {
    showToast('请选择材料类型')
    return
  }
  store.updateMaterialType(customer.value.id, activeMaterial.value.id, matTypeDraft.value)
  showMatTypeEdit.value = false
  showMaterialViewer.value = false
  showSuccessToast('材料类型已更正')
}

function confirmRemoveMaterial() {
  showConfirmDialog({
    title: '删除材料',
    message: `确定删除「${activeMaterial.value?.type}」吗？删除后可通过补充资料重新录入。`,
    confirmButtonText: '删除',
    confirmButtonColor: '#EF4444',
  })
    .then(() => {
      store.removeMaterial(customer.value.id, activeMaterial.value.id)
      showMaterialViewer.value = false
      showSuccessToast('材料已删除')
    })
    .catch(() => {})
}

const fieldLabels = {
  monthlyIncome: '月收入',
  totalDebt: '总负债',
  queryCount3m: '近3月查询',
  housingFundBase: '公积金基数',
  propertyValue: '房产价值',
}

function toggleGroup(key) {
  expandedGroups[key] = !expandedGroups[key]
}

function formatMoney(val) {
  if (val >= 10000) return (val / 10000).toFixed(1) + '万'
  return val + '元'
}

const debtRatio = computed(() => {
  if (!customer.value || !customer.value.monthlyIncome) return 0
  return ((customer.value.totalDebt / (customer.value.monthlyIncome * 12)) * 100).toFixed(1)
})

const getDebtRatioClass = computed(() => {
  const ratio = parseFloat(debtRatio.value)
  if (ratio > 50) return 'warn'
  if (ratio > 30) return 'caution'
  return ''
})

const riskLevel = computed(() => {
  if (!customer.value) return ''
  const c = customer.value
  if (c.maxOverdueMonths > 0 || c.queryCount3m > 8 || c.totalDebt > 100000) return 'high'
  if (c.queryCount3m > 6 || c.creditCardUsage > 60) return 'medium'
  return 'low'
})

const riskText = computed(() => {
  const map = { high: '高风险', medium: '中风险', low: '低风险' }
  return map[riskLevel.value] || ''
})

// ==================== 资料完整度 ====================
const sourceMap = {
  friend: '朋友介绍',
  telemarketing: '电话营销',
  walkin: '门店进件',
  online: '线上渠道',
  referral: '老客转介绍',
  other: '其他',
}

const sourceLabel = computed(() => {
  if (!customer.value) return ''
  return sourceMap[customer.value.source] || '朋友介绍'
})

// 关键字段权重：基础信息 + 收入 + 负债征信 + 资产
const completenessFields = [
  { key: 'idCard', label: '身份证', weight: 20 },
  { key: 'monthlyIncome', label: '收入信息', weight: 20 },
  { key: 'totalDebt', label: '负债信息', weight: 20 },
  { key: 'queryCount3m', label: '征信查询', weight: 15 },
  { key: 'housingFundBase', label: '公积金', weight: 15 },
  { key: 'propertyValue', label: '资产信息', weight: 10 },
]

const completeness = computed(() => {
  if (!customer.value) return 0
  const c = customer.value
  let score = 0
  for (const f of completenessFields) {
    const val = c[f.key]
    if (val !== undefined && val !== null && val !== '' && val !== 0) {
      score += f.weight
    }
  }
  return score
})

const missingMaterials = computed(() => {
  if (!customer.value) return []
  const c = customer.value
  const missing = []
  for (const f of completenessFields) {
    const val = c[f.key]
    if (val === undefined || val === null || val === '' || val === 0) {
      missing.push(f.label)
    }
  }
  return missing
})

const infoGroups = computed(() => {
  if (!customer.value) return []
  const c = customer.value
  return [
    {
      title: '基础信息',
      key: 'basic',
      fields: [
        { label: '姓名', value: c.name, source: c.sourceName || '建档录入' },
        { label: '手机号', value: c.phone, source: '建档录入' },
        { label: '年龄', value: c.age ? c.age + '岁' : '未填写', source: '身份证OCR' },
        { label: '性别', value: c.gender || '未填写', source: '身份证OCR' },
        { label: '所在城市', value: c.city || '未填写', source: '身份证OCR' },
        { label: '婚姻状况', value: c.maritalStatus || '未填写', source: '语音口述' },
        { label: '学历', value: c.education || '未填写', source: '语音口述' },
      ],
    },
    {
      title: '收入信息',
      key: 'income',
      fields: [
        { label: '月均收入', value: c.monthlyIncome ? formatMoney(c.monthlyIncome) : '未填写', source: '银行流水OCR', class: c.monthlyIncome >= 10000 ? 'good' : '' },
        { label: '公积金基数', value: c.housingFundBase ? formatMoney(c.housingFundBase) : '未填写', source: '社保公积金OCR' },
        { label: '工作单位', value: c.employer || '未填写', source: '语音口述' },
        { label: '职位', value: c.position || '未填写', source: '语音口述' },
      ],
    },
    {
      title: '负债与征信',
      key: 'credit',
      fields: [
        { label: '总负债', value: c.totalDebt ? formatMoney(c.totalDebt) : '未填写', source: '征信报告OCR', class: c.totalDebt > 100000 ? 'warn' : '' },
        { label: '信用卡使用率', value: c.creditCardUsage ? c.creditCardUsage + '%' : '未填写', source: '征信报告OCR', class: c.creditCardUsage > 60 ? 'warn' : '' },
        { label: '近1月查询', value: c.queryCount1m ? c.queryCount1m + '次' : '未填写', source: '征信报告OCR', class: c.queryCount1m > 3 ? 'caution' : '' },
        { label: '近3月查询', value: c.queryCount3m ? c.queryCount3m + '次' : '未填写', source: '征信报告OCR', class: c.queryCount3m > 6 ? 'warn' : '' },
        { label: '近6月查询', value: c.queryCount6m ? c.queryCount6m + '次' : '未填写', source: '征信报告OCR' },
        { label: '最长逾期', value: c.maxOverdueMonths ? c.maxOverdueMonths + '月' : '无', source: '征信报告OCR', class: c.maxOverdueMonths > 0 ? 'warn' : '' },
      ],
    },
    {
      title: '资产信息',
      key: 'asset',
      fields: [
        { label: '房产价值', value: c.propertyValue ? c.propertyValue + '万' : '未填写', source: '房产证OCR' },
        { label: '是否有抵押', value: c.hasMortgage ? '是' : '否', source: '房产证OCR' },
        { label: '车辆价值', value: c.carValue ? c.carValue + '万' : '未填写', source: '语音口述' },
        { label: '期望额度', value: c.expectedAmount ? c.expectedAmount + '万' : '未填写', source: '语音口述' },
      ],
    },
  ]
})

function showSource(field) {
  currentSourceField.value = field
  showSourcePopup.value = true
}
</script>

<style scoped>
.detail-page {
  padding-bottom: 80px;
}

/* 客户头部 */
.customer-header {
  background: var(--bg-card);
  padding: 16px;
  border-bottom: none;
  position: relative;
  overflow: hidden;
}

.customer-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--gradient-primary);
}

.header-top {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
}

.customer-avatar {
  width: 50px;
  height: 50px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
}

.customer-avatar.男 {
  background: var(--primary-container);
  color: var(--on-primary-container);
  border: none;
}

.customer-avatar.女 {
  background: var(--danger-container);
  color: var(--on-danger-container);
  border: none;
}

.header-info {
  flex: 1;
  min-width: 0;
}

.header-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.header-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--surface-container-high);
  color: var(--text-secondary);
  border-radius: 8px;
  border: none;
}

.tag.source-tag {
  background: var(--primary-container);
  color: var(--on-primary-container);
  border: none;
}

/* 资料完整度 */
.completeness-bar {
  background: var(--bg-input);
  border: none;
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  margin-bottom: 16px;
}

.completeness-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.completeness-label {
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.completeness-num {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-primary);
  font-family: 'DIN', sans-serif;
}

.completeness-track {
  height: 6px;
  background: var(--bg-base);
  border-radius: 3px;
  overflow: hidden;
}

.completeness-fill {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: 3px;
  transition: width 0.5s ease;
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.5);
}

.missing-tip {
  font-size: 11px;
  color: var(--color-warning);
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 2px;
  cursor: pointer;
}

.missing-tip.done {
  color: var(--color-success);
}

/* 补充资料入口 */
.material-entry {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 16px 0;
  padding: 14px 16px;
  background: var(--primary-container);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.material-entry:active {
  transform: scale(0.98);
}

.entry-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(59, 130, 246, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.entry-text {
  flex: 1;
  min-width: 0;
}

.entry-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.entry-desc {
  font-size: 11px;
  color: var(--text-tertiary);
}

/* 材料空态 */
.material-empty {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 28px 16px;
  background: var(--surface-container-low);
  border: none;
  border-radius: var(--radius-sm);
}

.material-empty p {
  font-size: 12px;
  color: var(--text-tertiary);
  text-align: center;
  line-height: 1.5;
}

.risk-badge {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 600;
  flex-shrink: 0;
}

.risk-badge.high {
  background: var(--danger-container);
  color: var(--on-danger-container);
  border: none;
}

.risk-badge.medium {
  background: var(--warning-container);
  color: var(--on-warning-container);
  border: none;
}

.risk-badge.low {
  background: var(--success-container);
  color: var(--on-success-container);
  border: none;
}

.header-stats {
  display: flex;
  align-items: center;
  padding: 12px 0 0;
}

.stat {
  flex: 1;
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 11px;
  color: var(--text-tertiary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'DIN', sans-serif;
}

.stat-value.warn {
  color: var(--color-warning);
}

.stat-value.caution {
  color: var(--color-secondary);
}

.stat-value.good {
  color: var(--color-success);
}

.stat-divider {
  width: 1px;
  height: 28px;
  background: var(--surface-container-high);
}

/* Section */
.section {
  padding: 0 16px;
  margin-top: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding: 0 4px;
  cursor: pointer;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  position: relative;
  padding-left: 10px;
}

.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 14px;
  border-radius: 2px;
  background: var(--gradient-primary);
}

.section-extra {
  font-size: 12px;
  color: var(--text-tertiary);
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sch-add-btn {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 4px 12px;
  background: var(--primary-container);
  color: var(--on-primary-container);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
}

.sch-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 18px 16px;
  background: var(--surface-container-low);
  border-radius: var(--radius-sm);
}

.sch-empty-text {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 材料列表 */
.material-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.material-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-card);
  border: none;
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  cursor: pointer;
}

.mat-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-container);
}

.mat-icon.add {
  background: var(--bg-input);
}

.mat-info {
  min-width: 0;
}

.mat-name {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.mat-time {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.mat-confidence {
  font-size: 11px;
  color: var(--color-primary);
  font-family: 'DIN', sans-serif;
}

.mat-confidence.low {
  color: var(--color-warning);
}

/* ===== navbar 编辑按钮 ===== */
.nav-edit-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 4px 12px;
  background: var(--primary-container);
  color: var(--on-primary-container);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
}

/* ===== 材料查看弹层 ===== */
.mat-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow-y: auto;
  box-sizing: border-box;
}

.mv-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.mv-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.mv-conf {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--success-container);
  color: var(--on-success-container);
  font-weight: 500;
}

.mv-conf.low {
  background: var(--warning-container);
  color: var(--on-warning-container);
}

.mv-preview {
  background: var(--surface-container-low);
  border-radius: var(--radius-md);
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 14px;
}

.mv-preview-icon {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  background: var(--primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}

.mv-preview-name {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.mv-fields {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.mv-field {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 4px;
  border-bottom: none;
}

.mv-field + .mv-field {
  border-top: 1px solid var(--surface-container-high);
}

.mv-label {
  font-size: 13px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.mv-value {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
  text-align: right;
}

.mv-meta {
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 6px 16px;
  margin-bottom: 16px;
}

.mv-meta-row {
  display: flex;
  justify-content: space-between;
  padding: 9px 0;
}

.mv-meta-row + .mv-meta-row {
  border-top: 1px solid var(--surface-container-high);
}

.mv-meta-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.mv-meta-value {
  font-size: 12px;
  color: var(--text-secondary);
}

.mv-actions {
  margin-top: auto;
  display: flex;
  gap: 8px;
}

.mv-actions .van-button {
  flex: 1;
}

/* ===== 编辑客户信息弹层 ===== */
.edit-popup {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
  box-sizing: border-box;
}

.ep-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.ep-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.ep-form {
  flex: 1;
  overflow-y: auto;
}

.ep-group-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  padding: 10px 4px 8px;
  position: relative;
  padding-left: 12px;
}

.ep-group-title::before {
  content: '';
  position: absolute;
  left: 2px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 13px;
  border-radius: 2px;
  background: var(--gradient-primary);
}

.ep-group-title em {
  font-style: normal;
  font-size: 11px;
  font-weight: 400;
  color: var(--text-tertiary);
  margin-left: 6px;
}

.ep-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: 10px;
}

.ep-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}

.ep-field.span2 {
  grid-column: span 2;
}

.ep-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  padding-left: 2px;
}

.ep-label .req {
  color: var(--color-danger);
  font-style: normal;
}

.ep-input {
  background: var(--bg-card);
  border-radius: var(--radius-sm);
}

.ep-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.ep-chips.wrap {
  gap: 10px;
}

.ep-chip {
  flex: 1;
  min-width: 56px;
  text-align: center;
  padding: 9px 0;
  background: var(--surface-container-low);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.ep-chips.wrap .ep-chip {
  flex: 0 0 auto;
  padding: 9px 14px;
}

.ep-chip.active {
  background: var(--primary-container);
  color: var(--on-primary-container);
  font-weight: 600;
}

.ep-actions {
  display: flex;
  gap: 12px;
  padding-top: 12px;
}

/* ===== 材料类型编辑弹层 ===== */
.mat-type-popup {
  padding: 20px 16px;
}

.mtp-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
}

.mtp-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  text-align: center;
  margin: 6px 0 16px;
}

.mtp-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  margin-bottom: 18px;
}

.mtp-chip {
  padding: 8px 16px;
  background: var(--surface-container-low);
  border-radius: 999px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.mtp-chip.active {
  background: var(--primary-container);
  color: var(--on-primary-container);
  font-weight: 600;
}

.mtp-actions {
  display: flex;
  gap: 12px;
}


/* 信息列表 */
.info-list {
  background: var(--bg-card);
  border: none;
  border-radius: var(--radius-md);
  overflow: hidden;
}

.info-row {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: none;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  width: 90px;
  font-size: 14px;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.info-value {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.info-value.warn {
  color: var(--color-warning);
}

.info-value.caution {
  color: var(--color-secondary);
}

.info-value.good {
  color: var(--color-success);
}

.info-source {
  padding: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
}

/* 关联日程 */
.sch-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sch-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-card);
  border: none;
  border-radius: var(--radius-md);
  padding: 12px;
  cursor: pointer;
}

.sch-time {
  width: 62px;
  flex-shrink: 0;
  text-align: center;
  border-radius: 8px;
  padding: 5px 4px;
  background: var(--primary-container);
}

.sch-time.prio-P0 { background: var(--danger-container); }
.sch-time.prio-P2 { background: var(--surface-container-high); }

.sch-clock {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
}

.sch-prio {
  font-size: 11px;
  color: var(--text-tertiary);
}

.sch-info { flex: 1; min-width: 0; }

.sch-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 3px;
}

.sch-meta {
  font-size: 11px;
  color: var(--text-tertiary);
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* 推演历史 */
.sim-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sim-item {
  background: var(--bg-card);
  border: none;
  border-radius: var(--radius-sm);
  padding: 12px;
  cursor: pointer;
}

.sim-time {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 6px;
}

.sim-adjustments {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
}

.adjust-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--secondary-container);
  color: var(--on-secondary-container);
  border-radius: 8px;
  border: none;
}

.sim-result {
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.sim-approved {
  color: var(--color-success);
}

.sim-rejected {
  color: var(--color-danger);
}

/* 操作栏 */
.action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  background: var(--bg-card);
  border-top: none;
}

.action-bar .van-button {
  flex: 1;
}

/* 溯源弹窗 */
.source-popup {
  padding: 20px;
}

.source-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
  margin-bottom: 16px;
}

.source-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.source-field {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  padding: 8px 12px;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
}

.source-label {
  color: var(--text-tertiary);
}

.source-value {
  color: var(--text-primary);
  font-weight: 500;
}

.source-preview {
  margin-top: 8px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: var(--bg-input);
}

.preview-placeholder {
  height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>
