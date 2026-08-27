# 智贷助手（tigerloan-assistant）

面向贷款经理的 AI 辅助展业平台。前端为 Vue3 + Vant 4 移动端应用，后端为 Express + SQLite API 服务，AI 能力（OCR / ASR / LLM / 匹配引擎）通过 Provider 抽象层接入——当前使用 Mock 实现（逻辑完整、带模拟延迟），未来配置真实服务 Key 后一行环境变量即可切换，前端零改动。

## 技术架构

```
loan-assistant/
├── src/                    # 前端（Vue3 + Vant4 + Pinia + Vue Router）
│   ├── api/                # axios 封装 + 各模块 API（/api 代理到后端）
│   ├── stores/             # Pinia 状态（数据全部来自后端接口）
│   ├── views/              # 页面
│   └── mock/data.js        # （已退役，仅留档）
├── server/                 # 后端（Express + better-sqlite3 + JWT）
│   ├── index.js            # 入口：CORS / 静态 uploads / 路由挂载
│   ├── db.js               # SQLite 建表 + 行映射
│   ├── seed.js             # 首次启动自动播种演示数据
│   ├── middleware/auth.js  # JWT 鉴权
│   ├── routes/             # auth / products / customers / schedules / dashboard / ai
│   ├── services/ai/        # AI Provider 抽象层（mock.js / real.js / index.js）
│   └── data/               # SQLite 数据库文件（git 忽略）
└── scripts/                # CDP 截图 / e2e 验证脚本
```

## 快速启动

```bash
npm install

# 终端 1：启动后端（端口 3001，首次启动自动建库+播种）
npm run server

# 终端 2：启动前端（端口 5173，/api 自动代理到 3001）
npm run dev
```

访问 http://localhost:5173

**测试账号**：`13800138000` / `abc123`

### 一键同时启动

```bash
npm run dev:all
```

## 接口一览

| 模块 | 接口 |
|------|------|
| 认证 | `POST /api/auth/login`、`POST /api/auth/change-password` |
| 产品库 | `GET/POST /api/products`、`GET/PUT/DELETE /api/products/:id`、`PATCH /api/products/:id/status` |
| 客户360 | `GET/POST /api/customers`、`GET/PUT/DELETE /api/customers/:id`、材料增删改 `…/materials`、推演记录 `…/simulations` |
| 日程 | `GET/POST /api/schedules`、`PATCH /api/schedules/:id/done`、`DELETE /api/schedules/:id` |
| 仪表盘 | `GET /api/dashboard` |
| AI 能力 | `POST /api/ai/ocr/:type`、`POST /api/ai/asr`、`POST /api/ai/extract/*`、`POST /api/ai/match`、`POST /api/ai/assistant` |

统一响应格式：`{ success: true, data }` / `{ success: false, message }`；除登录外全部需要 `Authorization: Bearer <token>`。

## AI Provider：未来如何接入真实服务

后端通过 `AI_PROVIDER` 环境变量选择实现（默认 `mock`）：

```bash
# .env 或环境变量
AI_PROVIDER=real
```

真实服务在 `server/services/ai/real.js` 中对接，预留的配置位：

| 能力 | 需要的 Key（未来提供） | 配置位置 |
|------|------------------------|----------|
| OCR（身份证/流水/征信等 7 类） | OCR 服务 API Key | `real.js#ocrIdCard` 等 |
| ASR 语音转写 | ASR 服务 API Key | `real.js#asr` |
| LLM 结构化提取 / 匹配 / 助理 | 大模型 API Key | `real.js#extractXxx / match / assistantReply` |

Mock 实现保留完整的业务语义（字段置信度、准入/拒贷规则引擎、模拟延迟），切换 Provider 后前端与接口契约完全不变。

## 数据持久化

SQLite 数据库位于 `server/data/app.db`，首次启动自动播种（3 产品种子为 5+、客户 3 名、日程若干）。删除该文件并重启即可重置演示数据。

## Git 忽略

`server/data/`（数据库）、`server/uploads/`（上传文件）、`node_modules/`、`dist/` 均不入库。
