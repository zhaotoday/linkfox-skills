# MPSTATS Ozon 商品搜索 API 参考

## 调用规范

- **请求地址**：`https://tool-gateway.linkfox.com/mpstats/ozon/productSearch`
- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOXAGENT_API_KEY` 读取（如未配置，提示用户前往 https://yxgb3sicy7.feishu.cn/wiki/GIkkweGghiyzkqkRXQKc2n0Tnre 申请）

## 请求参数

POST Body（JSON）。以下字段与工具网关当前登记的「MPSTATS-Ozon-商品搜索」入参 schema 一致（同步日期 2026-04-30）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 四选一 | 俄语搜索关键词，例如 `кроссовки`（跑鞋） |
| productIds | array | 四选一 | Ozon 商品 SKU 列表（整数或字符串） |
| brandNames | array<string> | 四选一 | 品牌名列表（俄语或拉丁拼写） |
| sellerNames | array<string> | 四选一 | 卖家名列表（俄语） |
| startDate | string | 否 | 统计起始日，格式 `YYYY-MM-DD`；留空时按一年前；最晚可选昨日 |
| endDate | string | 否 | 统计结束日，格式 `YYYY-MM-DD`；留空时按昨天；最晚可选昨日 |
| page | integer | 否 | 页码，从 1 开始 |
| pageSize | integer | 否 | 每页条数，1-100，默认 100 |

> **四选一约束**：`keyword` / `productIds` / `brandNames` / `sellerNames` 至少传一个，全部为空时请求会被拒绝。

## 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | 返回码（字符串），`"200"` 表示成功 |
| msg | string | 消息；成功为 `ok`，失败为错误描述 |
| total | integer | 命中总数 |
| products | array | 商品列表（详见下方） |
| columns | array | 渲染列定义 |
| costTime | integer | 接口耗时（毫秒） |
| costToken | integer | 消耗 Token 数量 |
| type | string | 响应类型 |

### products[*] 商品对象字段（39 个）

按官方 outputSchema 定义（`_mpstats_ozon_productSearch`，同步日期 2026-05-06）。该 schema 与 `brandProducts` / `categoryProducts` / `sellerProducts` 共享同一套商品卡结构；本端点以**发现为主**，部分度量字段在运行时可能为 null / 不填充。

**身份与基础信息**

| 字段 | 类型 | 说明 |
|------|------|------|
| productId | integer | SKU ID |
| title | string | 商品名称（俄语） |
| brand | string | 品牌 |
| brandId | integer | 品牌 ID |
| sellerName | string | 卖家名 |
| sellerId | integer | 卖家 ID |
| category | string | 品类路径（俄语，`/` 分隔） |
| nicheName | string | 赛道路径（俄语） |
| nicheId | integer | 赛道 ID |
| country | string | 销售国，Ozon 恒为 `RU` |
| firstDate | string | 上架日期（`yyyy-MM-dd`） |
| imageUrl | string | 主图 URL |
| productPageUrl | string | 商品页 URL |
| sourceTool / sourceType | string | 来源工具 / 数据源标识 |

**价格与货币**

| 字段 | 类型 | 说明 |
|------|------|------|
| price | number | 当前售价 |
| oldPrice | number | 折扣前原价 |
| ozonCardPrice | number | Ozon Card 价（银行卡优惠价） |
| minPrice / maxPrice / averagePrice | number | 统计期内最低价 / 最高价 / 均价 |
| currency | string | 币种符号（`₽` / `$` / `€`） |

**评分与评论**

| 字段 | 类型 | 说明 |
|------|------|------|
| rating | number | 评分，0-5 |
| reviewCount | integer | 评论数 |

**库存与 FBS**

| 字段 | 类型 | 说明 |
|------|------|------|
| balance | integer | 当前库存（件） |
| balanceFbs | integer | FBS 库存（卖家自发货） |
| frozenStocks | integer | 滞销库存 |
| warehousesCount | integer | FBO 分仓数 |
| isFbs | boolean | 是否 FBS 发货 |

**销售与周转**

| 字段 | 类型 | 说明 |
|------|------|------|
| salesPerDay | number | 日均销量（件/日） |
| monthlySalesUnits | integer | 统计期销量（件） |
| monthlySalesRevenue | number | 统计期销售额 |
| lostProfit | number | 损失销售额（缺货等造成） |
| daysInSite | integer | 在售天数（统计期，含缺货日） |
| daysInStock | integer | 有货天数 |
| turnoverDays | number | 周转天数（越小越快） |

**排名与占比**

| 字段 | 类型 | 说明 |
|------|------|------|
| position | integer | 当前查询维度（品类/品牌/卖家/赛道）内排名 |
| categoryPosition | integer | 品类内排名 |
| revenueSharePercent | number | 该 SKU 在当前查询维度的销售额占比，0-100 |

## 错误码

正常情况下，HTTP 状态码为 200，业务成功与否通过 `code` / `errcode` 区分（`200` 成功）。

| errcode | 含义 | 处理建议 |
|---------|------|----------|
| 200 | 成功 | 正常解析 `products` 字段 |
| 401 | 认证失败 | 检查请求头 `Authorization` 是否正确携带 API Key |
| 其他非 200 值 | 业务异常 | 查看 `errmsg` / `msg` 获取具体原因；常见为四选一参数缺失、日期超过昨日、非俄语关键词等 |

## curl 示例

```bash
curl -X POST https://tool-gateway.linkfox.com/mpstats/ozon/productSearch \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "кроссовки",
    "pageSize": 50
  }'
```

## 响应示例（简略）

```json
{
  "code": "200",
  "msg": "ok",
  "total": 8721,
  "products": [
    {
      "productId": 1786874757,
      "title": "Кроссовки мужские ...",
      "brand": "Nike",
      "sellerName": "ООО Ромашка",
      "sellerId": 3628678,
      "imageUrl": "https://...",
      "productPageUrl": "https://www.ozon.ru/product/..."
    }
  ],
  "costToken": 1
}
```

---

## Feedback API

> 该接口与上方工具接口不同，**请勿混用两个基础 URL**。

- **POST** `https://skill-api.linkfox.com/api/v1/public/feedback`
- **Content-Type:** `application/json`

```json
{
  "skillName": "linkfox-mpstats-ozon-product-search",
  "sentiment": "POSITIVE",
  "category": "OTHER",
  "content": "User successfully located Ozon SKUs from a Russian keyword."
}
```

**字段说明：**
- `skillName`：使用本 skill 的 YAML `name`
- `sentiment`：`POSITIVE` / `NEUTRAL` / `NEGATIVE` 三选一
- `category`：`BUG` / `COMPLAINT` / `SUGGESTION` / `OTHER` 四选一
- `content`：用户表达、实际现象、为什么算问题或好评
