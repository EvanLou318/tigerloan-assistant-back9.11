// ==================== AI Mock Provider ====================
// 模拟实现：OCR / ASR / LLM 结构化提取 / 匹配引擎 / 助理意图识别
// 返回结构与前端原型 mock 完全一致；切换到真实服务时前端无需任何改动
// （真实服务见 real.js，通过环境变量 AI_PROVIDER=real 切换）

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

// ---------- OCR：各材料类型 ----------

export async function ocrIdCard() {
  await delay(2500)
  return {
    success: true,
    data: {
      name: '张明',
      idNumber: '310115199201011234',
      gender: '男',
      age: 34,
      city: '上海',
      ethnicity: '汉',
      birthDate: '1992-01-01',
      address: '上海市浦东新区张江路100号',
      issueAuthority: '上海市公安局浦东分局',
      validFrom: '2020-01-01',
      validTo: '2040-01-01',
    },
    confidence: 0.99,
    source: '身份证正面+反面',
  }
}

export async function ocrBankStatement() {
  await delay(3000)
  return {
    success: true,
    data: {
      bank: '招商银行',
      monthlyAvgIncome: 15320,
      monthlyAvgExpense: 8500,
      dailyAvgBalance: 42000,
      period: '近6个月',
      largeTransactions: [
        { date: '2026-07-15', amount: 50000, type: '转入', note: '大额交易' },
        { date: '2026-06-20', amount: 30000, type: '转出', note: '大额交易' },
      ],
      lateNightTransactions: [],
      stability: '良好',
    },
    confidence: 0.95,
    source: '银行流水PDF',
  }
}

export async function ocrCreditReport() {
  await delay(3500)
  return {
    success: true,
    data: {
      queryCount1m: 2,
      queryCount3m: 5,
      queryCount6m: 8,
      queryCount12m: 15,
      maxOverdueMonths: 0,
      maxOverdueAmount: 0,
      currentOverdue: '无',
      totalDebt: 80000,
      loanBalance: 50000,
      creditCardUsed: 30000,
      creditCardTotal: 60000,
      creditCardUsage: 50,
      guaranteeBalance: 0,
    },
    confidence: 0.92,
    source: '央行征信报告',
  }
}

export async function ocrIncomeProof() {
  await delay(2500)
  return {
    success: true,
    data: {
      employer: '上海某科技有限公司',
      position: '产品经理',
      monthlyIncome: 15320,
      incomeSource: '工资代发',
      companyPhone: '021-88886666',
    },
    confidence: 0.93,
    source: '收入证明',
  }
}

export async function ocrSocialSecurity() {
  await delay(2800)
  return {
    success: true,
    data: {
      employer: '上海某科技有限公司',
      housingFundBase: 3500,
      socialSecurityBase: 12000,
      housingFundMonths: 36,
      socialSecurityMonths: 42,
    },
    confidence: 0.91,
    source: '社保公积金截图',
  }
}

export async function ocrProperty() {
  await delay(3000)
  return {
    success: true,
    data: {
      propertyValue: 280,
      propertyArea: 89.5,
      propertyAddress: '上海市浦东新区张江路100号',
      hasMortgage: false,
      mortgageBalance: 0,
    },
    confidence: 0.87,
    source: '房产证',
  }
}

export async function ocrBusinessLicense() {
  await delay(2600)
  return {
    success: true,
    data: {
      employer: '上海某科技有限公司',
      position: '法定代表人',
      businessType: '有限责任公司',
      registeredCapital: 500,
      establishDate: '2015-03-12',
      businessStatus: '存续',
    },
    confidence: 0.94,
    source: '营业执照',
  }
}

// ---------- ASR：语音转文字 ----------

export async function asr(text = null) {
  await delay(2000)
  const defaultText = '张三，男，32岁，在上海某科技公司做产品经理，月收入一万五，公积金基数3500，名下在浦东有套房值280万没有贷款，还有一辆车值15万，征信良好没有逾期，近三个月查询5次，想贷20万'
  return {
    success: true,
    text: text || defaultText,
    duration: 15,
    language: '普通话',
  }
}

// ---------- LLM：结构化提取 ----------

export async function extractFromVoice(text) {
  await delay(2000)
  return {
    success: true,
    data: {
      name: '张三',
      gender: '男',
      age: 32,
      city: '上海',
      employer: '某科技公司',
      position: '产品经理',
      monthlyIncome: 15000,
      housingFundBase: 3500,
      propertyValue: 280,
      hasMortgage: false,
      carValue: 15,
      creditOverdue: false,
      queryCount3m: 5,
      expectedAmount: 20,
    },
    confidence: 0.88,
    source: '语音口述',
  }
}

export async function extractCustomerFromVoice(text) {
  await delay(2200)
  return {
    success: true,
    transcript: text,
    recognizedTypes: ['客户基本信息', '收入信息'],
    summary: '已自动识别 2 类资料，共提取 10 个字段',
    confidence: 0.9,
    source: '语音口述',
    data: {
      name: { value: '张三', confidence: 0.98 },
      phone: { value: '13812345678', confidence: 0.96 },
      gender: { value: '男', confidence: 0.99 },
      age: { value: 32, confidence: 0.97 },
      city: { value: '上海', confidence: 0.92 },
      occupation: { value: '产品经理', confidence: 0.86 },
      source: { value: 'friend', confidence: 0.82 },
      remark: { value: '朋友介绍，意向信用贷 20 万，重点关注利率和放款速度', confidence: 0.8 },
      employer: { value: '某科技公司', confidence: 0.88 },
      monthlyIncome: { value: 15000, confidence: 0.9 },
    },
  }
}

export async function extractProduct(rawText) {
  await delay(2500)
  return {
    success: true,
    data: {
      productName: '建设银行公积金贷',
      institution: '建设银行',
      minRate: 3.45,
      maxRate: 5.6,
      minAmount: 5,
      maxAmount: 50,
      loanTerm: '6-60个月',
      repaymentMethod: '等额本息/先息后本',
      conditions: '公积金连续缴存≥12个月；基数≥3000元；征信无当前逾期',
    },
    confidence: 0.9,
  }
}

export async function extractSchedule(text) {
  await delay(800)
  const lower = text || ''
  const has = (k) => lower.includes(k)

  const title = text ? text.slice(0, 20).replace(/[,。.!！?？;；]/g, '').trim() : ''

  // 时间
  let startTime = new Date()
  startTime.setHours(startTime.getHours() + 1, 0, 0, 0)
  const timeMatch = text && text.match(/(上午|下午|早上|晚上)?\s*(\d{1,2})[点时:：](\d{1,2})?\s*分?/)
  if (timeMatch) {
    let h = parseInt(timeMatch[2])
    if (timeMatch[1] === '下午' || timeMatch[1] === '晚上') h = (h < 12 ? h + 12 : h)
    const m = parseInt(timeMatch[3] || 0)
    const d = new Date()
    d.setHours(h, m, 0, 0)
    if (d < new Date()) d.setDate(d.getDate() + 1)
    startTime = d
  }

  // 优先级
  let priority = 'P1'
  if (has('紧急') || has('马上') || has('立刻') || has('重要')) priority = 'P0'
  if (has('不急') || has('有空') || has('抽空') || has('随便')) priority = 'P2'

  // 类型
  let type = 'task'
  if (has('电话') || has('回电') || has('拨打')) type = 'call'
  if (has('见') || has('面谈') || has('会议') || has('会面')) type = 'meeting'

  // 客户（简单识别）
  let customerName = ''
  const nameMatch = text && text.match(/与([一-龥]{2,4})[见面谈通话]/)
  if (nameMatch) customerName = nameMatch[1]

  return {
    data: {
      title: title || '新日程',
      startTime: startTime.toISOString(),
      endTime: new Date(startTime.getTime() + 60 * 60 * 1000).toISOString(),
      priority,
      type,
      location: has('电话') ? '电话' : (has('公司') ? '客户公司' : ''),
      remark: text,
      customerName,
      source: 'ai',
    },
    confidence: 0.86,
  }
}

// ---------- 匹配引擎 ----------
// 通用规则：解析产品「准入条件」文本中的规则并对客户画像逐条校验
// （不绑定具体产品 ID，用户新录入的产品同样可参与匹配）

const RULE_PARSERS = [
  {
    // 年龄22-55周岁
    regex: /年龄(\d+)\s*[-~至]\s*(\d+)\s*周岁/,
    build: (m) => ({
      condition: `年龄${m[1]}-${m[2]}周岁`,
      check: (c) => c.age >= Number(m[1]) && c.age <= Number(m[2]),
      reason: (c) => `年龄${c.age}周岁（要求${m[1]}-${m[2]}周岁） ✓`,
      failValue: (c) => `${c.age}周岁`,
    }),
  },
  {
    // 月收入≥5000元
    regex: /月收入[≥>=]+\s*(\d+)\s*元/,
    build: (m) => ({
      condition: `月收入≥${m[1]}元`,
      check: (c) => (c.monthlyIncome || 0) >= Number(m[1]),
      reason: (c) => `月收入${c.monthlyIncome}元≥${m[1]}元 ✓`,
      failValue: (c) => `${c.monthlyIncome || 0}元`,
      suggestion: '月收入未达标，建议提供共同还款人或选择额度较低产品',
    }),
  },
  {
    // 近3个月查询≤6次
    regex: /近3个月查询[≤<=]+\s*(\d+)\s*次/,
    build: (m) => ({
      condition: `近3个月查询≤${m[1]}次`,
      check: (c) => (c.queryCount3m || 0) <= Number(m[1]),
      reason: (c) => `近3个月查询${c.queryCount3m}次≤${m[1]}次 ✓`,
      failValue: (c) => `${c.queryCount3m || 0}次`,
      suggestion: (c) => `近3个月查询${c.queryCount3m}次，超过要求${m[1]}次，建议等待${Math.max(1, Math.ceil(((c.queryCount3m || 0) - Number(m[1])) / 2))}个月后再申请`,
    }),
  },
  {
    // 公积金基数≥3000元
    regex: /基数[≥>=]+\s*(\d+)\s*元/,
    build: (m) => ({
      condition: `公积金基数≥${m[1]}元`,
      check: (c) => (c.housingFundBase || 0) >= Number(m[1]),
      reason: (c) => `公积金基数${c.housingFundBase}元≥${m[1]}元 ✓`,
      failValue: (c) => `${c.housingFundBase || 0}元`,
      suggestion: '建议补充公积金缴存记录或选择其他产品',
    }),
  },
  {
    // 征信无当前逾期
    regex: /征信无当前逾期/,
    build: () => ({
      condition: '征信无当前逾期',
      check: (c) => (c.maxOverdueMonths || 0) === 0,
      reason: () => '征信无当前逾期 ✓',
      failValue: (c) => `逾期${c.maxOverdueMonths}个月`,
      suggestion: (c) => `当前逾期${c.maxOverdueMonths}个月，建议先结清逾期款项`,
    }),
  },
  {
    // 负债率≤50%
    regex: /负债率[≤<=]+\s*(\d+)\s*%/,
    build: (m) => ({
      condition: `负债率≤${m[1]}%`,
      check: (c) => {
        const income = c.monthlyIncome || 0
        if (income <= 0) return false
        return (c.totalDebt || 0) / (income * 12) * 100 <= Number(m[1])
      },
      reason: (c) => `负债率${((c.totalDebt || 0) / ((c.monthlyIncome || 1) * 12) * 100).toFixed(1)}%≤${m[1]}% ✓`,
      failValue: (c) => `${((c.totalDebt || 0) / ((c.monthlyIncome || 1) * 12) * 100).toFixed(1)}%`,
      suggestion: (c) => `当前负债率${((c.totalDebt || 0) / ((c.monthlyIncome || 1) * 12) * 100).toFixed(1)}%，建议降低负债到${m[1]}%以下`,
    }),
  },
]

export async function match(customer, products) {
  await delay(3000)
  const results = { approved: [], rejected: [] }

  for (const product of products) {
    if (product.status !== 'active') continue

    const reasons = []
    const failedConditions = []

    // 从准入条件文本解析规则
    const conditions = product.conditions || ''
    const rules = []
    for (const parser of RULE_PARSERS) {
      const m = conditions.match(parser.regex)
      if (m) rules.push(parser.build(m))
    }

    for (const rule of rules) {
      if (rule.check(customer)) {
        reasons.push(rule.reason(customer))
      } else {
        failedConditions.push({
          condition: rule.condition,
          value: rule.failValue(customer),
          ...(rule.suggestion ? { suggestion: typeof rule.suggestion === 'function' ? rule.suggestion(customer) : rule.suggestion } : {}),
        })
      }
    }

    // 无可解析规则的产品：默认通过（模拟宽松准入）
    if (rules.length === 0) {
      reasons.push('暂无冲突的准入条件')
    }

    if (failedConditions.length === 0) {
      results.approved.push({
        productId: product.id,
        productName: product.productName,
        institution: product.institution,
        minRate: product.minRate,
        maxRate: product.maxRate,
        maxAmount: product.maxAmount,
        loanTerm: product.loanTerm,
        reasons,
      })
    } else {
      results.rejected.push({
        productId: product.id,
        productName: product.productName,
        institution: product.institution,
        failedConditions,
      })
    }
  }

  // 准入产品按利率从低到高；拒贷按不满足条件数量从少到多
  results.approved.sort((a, b) => a.minRate - b.minRate)
  results.rejected.sort((a, b) => a.failedConditions.length - b.failedConditions.length)

  return results
}

// ---------- AI 助理：意图识别（NLU 层，不执行读写） ----------

export async function assistantReply(text) {
  await delay(900 + Math.random() * 600)
  const t = (text || '').trim()
  const has = (...kws) => kws.some((k) => t.includes(k))

  // ---------- 实体提取 ----------
  const phoneMatch = t.match(/1[3-9]\d{9}/)
  const rateMatch = t.match(/(\d+(?:\.\d+)?)\s*%/)
  const amountMatch = t.match(/(\d+(?:\.\d+)?)\s*(万|k|K|千|元)/)
  let name = ''
  const n1 = t.match(/客户[\s:：]*([\u4e00-\u9fa5]{2,4})/)
  const n2 = t.match(/(?:叫|姓名是?|联系)([\u4e00-\u9fa5]{2,4})/)
  const n3 = t.match(/([\u4e00-\u9fa5]{2,4})的/)
  if (n1) name = n1[1]
  else if (n2) name = n2[1]
  else if (n3) name = n3[1]
  // 金额归一化为元
  let amount = 0
  if (amountMatch) {
    const v = parseFloat(amountMatch[1])
    const unit = amountMatch[2]
    amount = unit === '万' ? v * 10000 : unit === '元' ? v : v * 1000
  }

  // ---------- 意图：日程创建 ----------
  if (has('日程', '提醒我', '安排', '约了', '见面', '面谈', '回访') && has('新建', '创建', '添加', '安排', '提醒', '明天', '后天', '下午', '上午', '晚上')) {
    const ai = await extractSchedule(t)
    return {
      intent: 'schedule_create',
      entities: { ...ai.data, rawText: t },
      reply: '好的，我已为你解析出以下日程安排，请确认：',
    }
  }

  // ---------- 意图：资料更新 ----------
  if (has('更新', '修改', '改成') && has('资料', '档案', '月收入', '收入', '负债', '公积金', '收入', '房产', '职业', '单位')) {
    const fieldMap = [
      { kws: ['月收入', '月均收入', '收入'], key: 'monthlyIncome', label: '月均收入' },
      { kws: ['负债', '欠款'], key: 'totalDebt', label: '总负债' },
      { kws: ['公积金基数', '公积金'], key: 'housingFundBase', label: '公积金基数' },
      { kws: ['房产价值', '房产'], key: 'propertyValue', label: '房产价值(万)' },
      { kws: ['工作单位', '单位', '雇主'], key: 'employer', label: '工作单位' },
      { kws: ['职业', '职位'], key: 'occupation', label: '职业' },
    ]
    const field = fieldMap.find((f) => has(...f.kws))
    if (field) {
      const value = field.key === 'propertyValue' && amountMatch ? parseFloat(amountMatch[1]) : amount || (n2 ? t.slice(t.indexOf(n2[1]) + n2[1].length).trim() : '')
      return {
        intent: 'customer_update',
        entities: { name, phone: phoneMatch?.[0] || '', field: field.key, fieldLabel: field.label, value, rawText: t },
        reply: name
          ? `收到，准备更新客户「${name}」的${field.label}，请确认：`
          : `收到，准备更新客户档案的${field.label}。请告诉我客户姓名，或从下面选择：`,
      }
    }
  }

  // ---------- 意图：客户新增 ----------
  if (has('新增客户', '新建客户', '添加客户', '录入客户', '客户建档')) {
    return {
      intent: 'customer_create',
      entities: { name, phone: phoneMatch?.[0] || '', rawText: t },
      reply: phoneMatch
        ? '好的，已识别客户信息，将创建档案：'
        : '好的，请提供客户姓名和手机号，例如："新增客户 张三 13800138000"',
    }
  }
  if (has('新增', '新建', '添加') && phoneMatch && name) {
    return {
      intent: 'customer_create',
      entities: { name, phone: phoneMatch[0], rawText: t },
      reply: '好的，已识别客户信息，将创建档案：',
    }
  }

  // ---------- 意图：产品录入/更新 ----------
  if (has('录入产品', '新增产品', '添加产品', '上新产品')) {
    return {
      intent: 'product_create',
      entities: {
        productName: (t.match(/(?:产品|录入)[:：\s]*([\u4e00-\u9fa5A-Za-z0-9]{2,15}贷)/) || [])[1] || '',
        institution: (t.match(/([\u4e00-\u9fa5]{2,6})(?:银行|金融|消费金融)/) || [])[0] || '',
        minRate: rateMatch ? parseFloat(rateMatch[1]) : '',
        maxAmount: amountMatch ? parseFloat(amountMatch[1]) : '',
        rawText: t,
      },
      reply: '已解析产品信息，将录入产品库，请确认：',
    }
  }
  if (has('更新产品', '修改产品') && rateMatch) {
    return {
      intent: 'product_update',
      entities: { rate: parseFloat(rateMatch[1]), rawText: t },
      reply: '收到，将更新产品利率信息，请确认：',
    }
  }

  // ---------- 意图：查询 ----------
  if (has('日程') && has('什么', '哪些', '几', '安排', '明天', '今天', '查看', '看看')) {
    return {
      intent: 'query_schedule',
      entities: { scope: has('明天') ? 'tomorrow' : has('今天') ? 'today' : 'upcoming' },
      reply: '',
    }
  }
  if (has('查', '搜索', '找', '看看', '档案', '资料') && (name || phoneMatch) && !has('更新', '修改')) {
    return {
      intent: 'query_customer',
      entities: { name, phone: phoneMatch?.[0] || '' },
      reply: '',
    }
  }
  if (has('产品') && has('哪些', '什么', '多少', '列表', '利率', '额度')) {
    return {
      intent: 'query_product',
      entities: {},
      reply: '',
    }
  }
  if (has('匹配', '推荐') && name) {
    return {
      intent: 'query_match',
      entities: { name },
      reply: '',
    }
  }

  // ---------- 兜底 ----------
  return {
    intent: 'unknown',
    entities: {},
    reply: '我可以帮你完成这些事：\n· 客户：新增客户 张三 13800138000\n· 资料：更新张三的月收入为2万\n· 产品：录入产品 招行闪电贷 利率3.5%起\n· 日程：明天下午3点与张总面谈\n· 查询：张三的档案 / 明天有什么日程 / 有哪些产品',
  }
}

// ---------- Provider 导出 ----------

export const mockProvider = {
  name: 'mock',
  ocrIdCard,
  ocrBankStatement,
  ocrCreditReport,
  ocrIncomeProof,
  ocrSocialSecurity,
  ocrProperty,
  ocrBusinessLicense,
  asr,
  extractFromVoice,
  extractCustomerFromVoice,
  extractProduct,
  extractSchedule,
  match,
  assistantReply,
}
