# 亚马逊帮助文档变更监控 API 参考

本 skill 封装两个串联接口：**帮助文档变更列表**（`amazon/helpDocChanges`）与**变更详情**（`amazon/helpDocDetail`）。先用列表接口拿到变更记录 `id`，再用详情接口获取「AI 变更摘要 + 具体改动点 + 最新文档全文」。

## 调用规范

- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOXAGENT_API_KEY` 读取（如未配置，提示用户前往 https://yxgb3sicy7.feishu.cn/wiki/GIkkweGghiyzkqkRXQKc2n0Tnre 申请）
- **业务成功判定**：HTTP 状态码通常为 200，业务成功与否以响应体 `errcode` 字段为准（`errcode = 200` 成功，其他值为业务错误，`errmsg` 给出原因）

---

## 一、帮助文档变更列表

- **请求地址**：`https://tool-gateway.linkfox.com/amazon/helpDocChanges`
- **脚本**：`scripts/amazon_help_doc_changes.py`

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 文档标题模糊匹配关键词（不区分大小写，最大长度 1000） |
| changedAtGte | string | 否 | 变更发生时间下界（含），格式 `yyyy-MM-dd HH:mm:ss`。未传默认近 3 个月起 |
| changedAtLte | string | 否 | 变更发生时间上界（含），格式 `yyyy-MM-dd HH:mm:ss`。未传默认当前时间 |
| page | integer | 否 | 页码，从 1 开始，默认 `1` |
| pageSize | integer | 否 | 每页条数，默认 `20`，取值范围 1-100 |

> 无必填参数；不传任何参数即返回近 3 个月的有价值变更。

### 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| errcode | integer | 网关响应码（200 成功） |
| code | string | 业务响应码（"200" 成功） |
| msg / errmsg | string | 提示信息（成功为 ok） |
| total | integer | 本次返回的条数 |
| type | string | 渲染样式，固定 `tableListWorkbenches` |
| data | array | 变更记录列表，按变更时间倒序（见下表） |

#### data 变更记录字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 变更记录 ID（用作 `amazon/helpDocDetail` 入参） |
| title | string | 文档标题 |
| breadcrumb | string | 目录路径，从根到当前节点用 ` > ` 拼接 |
| summary | string | AI 生成的中文变更摘要（1-3 句），概括本次变更对卖家的意义 |
| changedAt | string | 变更检测时间，格式 `yyyy-MM-dd HH:mm:ss` |
| url | string | 详情页 URL（Seller Central 帮助中心原文链接） |

### curl 示例

```bash
curl -X POST https://tool-gateway.linkfox.com/amazon/helpDocChanges \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "FBA", "pageSize": 20}'
```

---

## 二、变更详情

- **请求地址**：`https://tool-gateway.linkfox.com/amazon/helpDocDetail`
- **脚本**：`scripts/amazon_help_doc_detail.py`

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 变更记录 ID（≥1），来自变更列表响应的 `data[].id` |

### 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| errcode | integer | 网关响应码（200 成功） |
| errmsg | string | 提示信息 |
| type | string | 响应类型，固定 `stdoutWorkbenches`（前端按 Markdown 渲染 stdout） |
| stdout | string | 变更详情 + 最新文档全文（Markdown）。含变更摘要、变更时间、Locale、目录路径、原文链接与文档正文 |

### curl 示例

```bash
curl -X POST https://tool-gateway.linkfox.com/amazon/helpDocDetail \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"id": 35}'
```

---

## 错误码

| errcode | 含义 | 处理建议 |
|---------|------|----------|
| 200 | 成功 | 正常解析业务字段 |
| 401 | 认证失败 | 检查请求头 `Authorization` 是否正确携带 API Key |
| 其他非 200 值 | 业务异常 | 参考 `errmsg` 字段获取具体错误原因（如 `id` 无效，请用列表接口重新获取） |

错误响应示例：

```json
{
    "errcode": 401,
    "errmsg": "authorized error"
}
```

---

## Feedback API

> This endpoint is **separate** from the tool API above. Do not mix the two base URLs.

- **POST** `https://skill-api.linkfox.com/api/v1/public/feedback`
- **Content-Type:** `application/json`

```json
{
  "skillName": "linkfox-amazon-help-doc-changes",
  "sentiment": "POSITIVE",
  "category": "OTHER",
  "content": "Results were accurate, user was satisfied."
}
```

**Field rules:**
- `skillName`: Use this skill's `name` from the YAML frontmatter
- `sentiment`: Choose ONE — `POSITIVE` (praise), `NEUTRAL` (suggestion without emotion), `NEGATIVE` (complaint or error)
- `category`: Choose ONE — `BUG` (malfunction or wrong data), `COMPLAINT` (user dissatisfaction), `SUGGESTION` (improvement idea), `OTHER`
- `content`: Include what the user said or intended, what actually happened, and why it is a problem or praise
