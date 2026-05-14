# 沃师傅竞品搜索 API

## 概述

搜索沃尔玛平台的竞品数据，支持多种筛选条件，返回解码后的产品信息。

## API Endpoint

```
POST /api/v1/product/search
```

**注意**: 使用 POST 方法，参数通过 JSON body 传递（不是 URL 查询参数）

## 请求参数

**重要说明**:
- `product_id` 和 `keyword` 为**互斥参数**
- 如果提供了 `product_id`，则其他所有筛选参数（keyword, is_wfs, min/max_sales 等）都将被忽略
- 使用 `product_id` 时，API 会直接返回该产品的详细信息

### 可选参数

| 参数名 | 类型 | 说明 | 示例 | 默认值 |
|--------|------|------|------|--------|
| keyword | string | 搜索关键词 | "iphone" | - |
| product_id | string | 产品 WID（与 keyword 互斥） | "297407634" | - |
| is_wfs | boolean | 是否只搜索 WFS 商品 | true | false |
| min_sales_volume | integer | 最小销量 | 4000 | 无 |
| max_sales_volume | integer | 最大销量 | 90000 | 无 |
| min_sales_amount | integer | 最小销售额 | 200 | 无 |
| max_sales_amount | integer | 最大销售额 | 800 | 无 |
| min_number_of_reviews | integer | 最小评论数 | 50 | 无 |
| max_number_of_reviews | integer | 最大评论数 | 100 | 无 |
| min_average_rating | float | 最低评分（1-5） | 1.0 | 无 |
| max_average_rating | float | 最高评分（1-5） | 5.0 | 无 |
| min_price | float | 最低价格 | 1.0 | 无 |
| max_price | float | 最高价格 | 10.0 | 无 |
| seller_name | string | 卖家名称 | "ERIC-EXPRESS" | 无 |
| brand | string | 品牌 | "Simyoung" | 无 |
| page | integer | 页码（从1开始） | 1 | 1 |
| pageSize | integer | 每页数量 | 50 | 50 |

## 请求示例

### 1. 按关键词搜索（基本搜索）

```json
{
  "keyword": "iphone",
  "is_wfs": true,
  "min_sales_volume": 4000,
  "max_sales_volume": 90000,
  "page": 1,
  "pageSize": 10
}
```

### 2. 按产品 ID 查询（其他参数将被忽略）

```json
{
  "product_id": "297407634"
}
```

**注意**: 使用 `product_id` 时，其他所有筛选参数都会被忽略，API 直接返回该产品的详细信息。

### 3. 综合筛选（使用所有参数）

```json
{
  "keyword": "iphone case",
  "seller_name": "ERIC-EXPRESS",
  "brand": "Simyoung",
  "is_wfs": true,
  "min_sales_volume": 200,
  "max_sales_volume": 800,
  "min_sales_amount": 200,
  "max_sales_amount": 800,
  "min_number_of_reviews": 50,
  "max_number_of_reviews": 100,
  "min_average_rating": 1.0,
  "max_average_rating": 5.0,
  "min_price": 1.0,
  "max_price": 10.0,
  "page": 1,
  "pageSize": 10
}
```

## 响应格式

### 成功响应

```json
{
  "code": 1,
  "msg": "成功",
  "data": {
    "list": [
      {
        "product_id": "B0ABCD1234",
        "title": "产品标题",
        "additional_offer_count": "Ȓ",
        "number_of_reviews": "ȓ",
        "price": "$ȒȓȐȔȘ",
        "rating": "ȗȐȔ",
        "sellers": [
          {
            "display_name": "ȟȬȣȝ-ȟȲȪȬȟȭȭ",
            "name": "ȭȽɁɍɃɉɂȻ ȣɂȷȐ",
            "seller_rating": "ȘȔȐȖ",
            "seller_reviews": "ȒȚȔȜȓȿ+"
          }
        ],
        "sales_trends": [
          {
            "sales_amount": {
              "label": "$ȓȒȒȑȐȕȿ+",
              "value": 2110400
            },
            "sales_volume": {
              "label": "ȒȚȘȐȑȿ+",
              "value": 197000
            },
            "month_sales_growth": "ȖȐȒȿ+",
            "gross_profit": "$ȖȚȚȚȿ+",
            "gross_profit_margin": "ȓȖȐȑ%"
          }
        ]
      }
    ],
    "total": 100,
    "page": 1,
    "pageSize": 10
  }
}
```

### 解码后的数据

所有编码字符会自动解码：

```json
{
  "code": 1,
  "msg": "成功",
  "data": {
    "list": [
      {
        "product_id": "B0ABCD1234",
        "title": "产品标题",
        "additional_offer_count": "1",
        "number_of_reviews": "2",
        "price": "$12.37",
        "rating": "6.3",
        "sellers": [
          {
            "display_name": "ERIC-EXPRESS",
            "name": "Simyoung Inc.",
            "seller_rating": "73.5",
            "seller_reviews": "193.2k+"
          }
        ],
        "sales_trends": [
          {
            "sales_amount": {
              "label": "$2110.4k+",
              "value": 2110400
            },
            "sales_volume": {
              "label": "197.0k+",
              "value": 197000
            },
            "month_sales_growth": "5.1k+",
            "gross_profit": "$5999k+",
            "gross_profit_margin": "25.0%"
          }
        ]
      }
    ],
    "total": 100,
    "page": 1,
    "pageSize": 10
  }
}
```

## 字段说明

### 产品字段

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| product_id | string | 产品 ID | "B0ABCD1234" |
| title | string | 产品标题 | "iPhone 15 Case..." |
| additional_offer_count | string | 额外供应商数量 | "1" |
| number_of_reviews | string | 评论数 | "2" |
| price | string | 价格 | "$12.37" |
| rating | string | 评分 | "4.5" |

### 卖家字段

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| display_name | string | 显示名称 | "ERIC-EXPRESS" |
| name | string | 公司名称 | "Simyoung Inc." |
| seller_rating | string | 卖家评分 | "95.5" |
| seller_reviews | string | 卖家评论数 | "10k+" |

### 销售数据字段

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| sales_amount.label | string | 销售额标签 | "$2110.4k+" |
| sales_amount.value | number | 销售额数值 | 2110400 |
| sales_volume.label | string | 销量标签 | "197.0k+" |
| sales_volume.value | number | 销量数值 | 197000 |
| month_sales_growth | string | 月销量增长 | "5.1k+" |
| gross_profit | string | 毛利 | "$500k+" |
| gross_profit_margin | string | 毛利率 | "25.0%" |

## 错误响应

```json
{
  "code": 1001,
  "msg": "参数错误",
  "data": null
}
```

## 编码规则

沃师傅使用 Unicode 字符编码数据：

| 类型 | Unicode 范围 | 解码公式 | 示例 |
|------|-------------|---------|------|
| 大写字母 A-Z | 539-564 | chr(65 + 码点 - 539) | ȟ(543) → E |
| 小写字母 a-z | 565-590 | chr(97 + 码点 - 565) | ɉ(585) → u |
| 数字 0-9 | 529-538 | 码点 - 529 | ȓ(531) → 2 |
| 小数点 | 528 | "." | Ȑ(528) → . |

## 使用示例

### Python

```python
from scripts.wmtwin_search_competitors import WMTwinCompetitorSearch

client = WMTwinCompetitorSearch(phone="15625238480")

# 基本搜索
results = client.search_competitors(
    keyword="iphone",
    is_wfs=True,
    min_sales_volume=4000,
    max_sales_volume=90000,
    page=1,
    page_size=10
)

# 综合筛选（使用多个参数）
results = client.search_competitors(
    keyword="iphone case",
    seller_name="ERIC-EXPRESS",
    brand="Simyoung",
    is_wfs=True,
    min_sales_volume=200,
    max_sales_volume=800,
    min_sales_amount=200,
    max_sales_amount=800,
    min_number_of_reviews=50,
    max_number_of_reviews=100,
    min_average_rating=1.0,
    max_average_rating=5.0,
    min_price=1.0,
    max_price=10.0,
    page=1,
    page_size=10
)

# 数据已自动解码
for product in results['data']['list']:
    print(f"产品: {product['title']}")
    print(f"价格: {product['price']}")
    print(f"卖家: {product['sellers'][0]['display_name']}")
    print(f"销量: {product['sales_trends'][0]['sales_volume']['label']}")
```

### 命令行

```bash
# 基本搜索
python3 scripts/wmtwin_search_competitors.py --keyword "iphone" --phone 15625238480

# 完整参数（综合筛选）
python3 scripts/wmtwin_search_competitors.py \
    --keyword "iphone case" \
    --phone 15625238480 \
    --seller-name "ERIC-EXPRESS" \
    --brand "Simyoung" \
    --is-wfs \
    --min-sales 200 \
    --max-sales 800 \
    --min-sales-amount 200 \
    --max-sales-amount 800 \
    --min-reviews 50 \
    --max-reviews 100 \
    --min-rating 1.0 \
    --max-rating 5.0 \
    --min-price 1.0 \
    --max-price 10.0 \
    --page 1 \
    --page-size 10 \
    -o results.json
```

## 注意事项

1. **请求方法**: 必须使用 POST 方法，参数放在 JSON body 中（不是 URL 查询参数）
2. **API 端点**: 使用 `/api/v1/product/search`（单数 product，不是 products）
3. **参数互斥规则**:
   - ⚠️ **重要**: `product_id` 和 `keyword` 互斥
   - 如果提供了 `product_id`，所有其他筛选参数都将被忽略
   - 使用 `product_id` 直接查询单个产品，使用 `keyword` 进行搜索筛选
4. **自动解码**: 所有编码字符会自动解码为真实数据
5. **需要登录**: 调用此 API 前需要先登录
6. **分页**: 通过 page 和 pageSize 参数控制分页
7. **筛选条件**: 可组合使用多个筛选条件（仅在使用 keyword 时有效）
8. **参数类型**:
   - 整数参数: min_sales_volume, max_sales_volume, min_sales_amount, max_sales_amount, min_number_of_reviews, max_number_of_reviews
   - 浮点数参数: min_average_rating, max_average_rating, min_price, max_price
   - 字符串参数: keyword, seller_name, brand
   - 布尔参数: is_wfs

## 常见筛选场景

### 按产品 ID 精确查询
查询指定产品的详细信息：
```json
{
  "product_id": "297407634"
}
```
**说明**: 此方式忽略所有其他筛选参数，直接返回该产品的完整信息。

### 按销量筛选
适用于找中等销量产品（避免竞争激烈的爆款）：
```json
{
  "keyword": "iphone case",
  "min_sales_volume": 200,
  "max_sales_volume": 800
}
```

### 按评论和评分筛选
找到有一定销量基础且评价不错的产品：
```json
{
  "keyword": "phone charger",
  "min_number_of_reviews": 50,
  "max_number_of_reviews": 100,
  "min_average_rating": 4.0
}
```

### 按价格区间筛选
找特定价格带的产品：
```json
{
  "keyword": "phone accessories",
  "min_price": 5.0,
  "max_price": 20.0
}
```

### 按卖家/品牌筛选
分析特定竞争对手的产品：
```json
{
  "keyword": "iphone case",
  "seller_name": "ERIC-EXPRESS",
  "brand": "Simyoung"
}
```
