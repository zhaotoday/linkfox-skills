# 亚马逊卖家政策新闻 API 参考

本 skill 封装两个串联接口：**政策新闻列表**（`amazon/policyNews`）与**新闻详情**（`amazon/newsDetail`）。先用列表接口拿到新闻 `id`，再用详情接口获取完整正文。

## 调用规范

- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOXAGENT_API_KEY` 读取（如未配置，提示用户前往 https://yxgb3sicy7.feishu.cn/wiki/GIkkweGghiyzkqkRXQKc2n0Tnre 申请）
- **业务成功判定**：HTTP 状态码通常为 200，业务成功与否以响应体 `errcode` 字段为准（`errcode = 200` 成功，其他值为业务错误，`errmsg` 给出原因）

---

## 一、政策新闻列表

- **请求地址**：`https://tool-gateway.linkfox.com/amazon/policyNews`
- **脚本**：`scripts/amazon_policy_news.py`

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| site | string | 是 | 亚马逊站点代码（大写），默认 `US`。可选值：US/JP/UK/AU/BE/BR/CA/EG/FR/DE/IN/IT/MX/NL/PL/SA/SG/ES/SE/TR/AE/ZA/IE |
| keyword | string | 否 | 标题模糊匹配关键词（不区分大小写，最大长度 1000） |
| publishedAtGte | string | 否 | 发布时间下界（含），格式 `yyyy-MM-dd HH:mm:ss`。未传默认近 3 个月起；最多可查近 1 年（早于该范围将报错） |
| publishedAtLte | string | 否 | 发布时间上界（含），格式 `yyyy-MM-dd HH:mm:ss`。未传默认当前时间 |
| page | integer | 否 | 页码，从 1 开始，默认 `1` |
| pageSize | integer | 否 | 每页条数，默认 `20`，取值范围 1-100 |

### 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| errcode | integer | 网关响应码（200 成功） |
| code | string | 业务响应码（"200" 成功） |
| msg / errmsg | string | 提示信息 |
| total | integer | 本次返回的条数 |
| type | string | 渲染样式，固定 `tableListWorkbenches` |
| data | array | 新闻列表（见下表） |

#### data 新闻对象字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 新闻 ID（用作 `amazon/newsDetail` 入参） |
| title | string | 新闻标题 |
| site | string | 站点代码（大写，如 US/UK/DE） |
| categoryName | string | 类目名称（未识别返 null，当前仅「Policy and Compliance」政策与合规） |
| publishedAt | string | 发布时间（北京时间），格式 `yyyy-MM-dd HH:mm:ss` |
| url | string | 详情页 URL（Seller Central 原文链接） |
| contentSnippet | string | 预览摘要，前约 300 字纯文本 |

### curl 示例

```bash
curl -X POST https://tool-gateway.linkfox.com/amazon/policyNews \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"site": "US", "keyword": "FBA", "pageSize": 20}'
```

---

## 二、新闻详情

- **请求地址**：`https://tool-gateway.linkfox.com/amazon/newsDetail`
- **脚本**：`scripts/amazon_news_detail.py`

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 新闻文章 ID，来自政策新闻列表响应的 `data[].id` |
| site | string | 否 | 亚马逊站点代码（大写），传入与来源新闻一致的站点，默认 `US`；取值同列表接口 |

### 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| errcode | integer | 网关响应码（200 成功） |
| errmsg | string | 提示信息 |
| type | string | 响应类型，固定 `stdoutWorkbenches`（前端按 Markdown 渲染 stdout） |
| stdout | string | 新闻完整正文（Markdown）。开头附带标题、站点、类目、发布时间、原文链接等元信息 |

### curl 示例

```bash
curl -X POST https://tool-gateway.linkfox.com/amazon/newsDetail \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"id": "QVRWUERLSUtYMERFUiNHOTZRODY5N1pXWU1DR0I3", "site": "US"}'
```

> `site` 建议与拉取该新闻时的列表站点一致；`id` 为定位新闻的主键。

---

## 错误码

| errcode | 含义 | 处理建议 |
|---------|------|----------|
| 200 | 成功 | 正常解析业务字段 |
| 401 | 认证失败 | 检查请求头 `Authorization` 是否正确携带 API Key |
| 4007 | 新闻不存在 | 传入的 `id` 无效或不存在，请用列表接口重新获取有效 `id` |
| 其他非 200 值 | 业务异常 | 参考 `errmsg` 字段获取具体错误原因 |

错误响应示例（详情接口传入无效 id）：

```json
{
    "errcode": 4007,
    "errmsg": "未找到该新闻文章。"
}
```

---

## Feedback API

> This endpoint is **separate** from the tool API above. Do not mix the two base URLs.

- **POST** `https://skill-api.linkfox.com/api/v1/public/feedback`
- **Content-Type:** `application/json`

```json
{
  "skillName": "linkfox-amazon-policy-news",
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
