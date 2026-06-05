# TikTok Shop 店铺授权 API Reference

本文档描述 **TikTok 授权与店铺/令牌管理** 相关的 API，覆盖 **TikTok Shop 小店（`appType=erp`）** 与 **TikTok 视频号 / 带货内容（`appType=creator`）** 两类授权。底层经 LinkFox 网关转发至紫鸟开放平台 `tiktok-auth` 接口。业务数据调用（商品/订单/财务等）通过开发者代理 `/tiktokShop/developerProxy` 完成，不在本 skill 范围内。

> **视频号授权**：将 `appType` 设为 `creator` 即为授权 TikTok 视频号；该授权在查询令牌（`storeTokens`）、刷新令牌（`refreshToken`）时也须保持 `appType=creator`，与小店（`erp`）授权相互独立。

## Calling Conventions

- **Base URL**: `https://tool-gateway.linkfox.com`（默认；可用环境变量 `TIKTOK_SHOP_API_BASE_URL` 覆盖）
- **Request Method**: 所有接口均为 POST
- **Content-Type**: `application/json`
- **Authentication**: Header `Authorization: <api_key>`，API key 读取环境变量 `LINKFOXAGENT_API_KEY`（未配置时，请提示用户向系统管理员获取）
- **User-Agent**: `LinkFox-Skill/1.0`
- **超时**: 60s
- **用户鉴权**: 以下接口均需 LinkFox 用户 Token（用户身份来自上下文）；OAuth 回调端点不在本 skill 内。

## API Endpoints

### 1. Get Authorization URL

**Endpoint**: `/tiktokShop/authorizeUrl`

**Request Parameters** (JSON):

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| shopName | string | No | - | 店铺名称（展示用，最长 256） |
| region | string | No | `global` | 地区：`global` / `us`（美国站传 `us`） |
| appType | string | No | `erp` | 应用类型：`erp`=TikTok Shop 小店；`creator`=TikTok 视频号（带货内容）；`affiliate`=联盟。**授权视频号时传 `creator`** |

**Response**:

```json
{
  "authorizeUrl": "https://services.tiktokshop.com/open/authorize?service_id=xxx&state=abc123"
}
```

> 授权 URL 有效期约 1 小时；每次授权须重新获取。用户完成授权后，紫鸟将 Token 推送到系统回调端点并自动落库，回调属于系统内部流程，不作为本 skill 的用户调用接口。

---

### 2. List Authorized Stores

**Endpoint**: `/tiktokShop/authorizedStores`

**Request Parameters**: 无（使用当前用户上下文）。

**Response**:

```json
{
  "stores": [
    {
      "openId": "7010736057180325637",
      "sellerName": "Test Shop",
      "sellerBaseRegion": "ID",
      "appType": "erp",
      "region": "global"
    }
  ],
  "total": 1
}
```

**stores[] 字段**

| Field | Type | Description |
|-------|------|-------------|
| openId | string | 卖家唯一标识 |
| sellerName | string | 店铺名称 |
| sellerBaseRegion | string | 店铺所在区域（如 ID） |
| appType | string | 应用类型 |
| region | string | 授权 region（global / us 等） |

---

### 3. Query Store Tokens

**Endpoint**: `/tiktokShop/storeTokens`

按 `openId` + `appType` 读取当前用户已绑定授权在库中的令牌，**不调用**紫鸟刷新接口。

**Request Parameters** (JSON):

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| openId | string | **Yes** | - | 卖家 open_id |
| appType | string | No | `erp` | `erp`=小店 / `creator`=视频号 / `affiliate`，须与授权时一致 |

**Response**:

```json
{
  "authRecordId": 1,
  "openId": "7010736057180325637",
  "appType": "erp",
  "accessToken": "TTP_Fw8rBwAAAA...",
  "refreshToken": "TTP_NTUxZTNh...",
  "accessTokenExpireIn": 1660556783,
  "refreshTokenExpireIn": 1691487031
}
```

| Field | Type | Description |
|-------|------|-------------|
| authRecordId | integer | 授权主表 ID |
| openId | string | open_id |
| appType | string | 应用类型 |
| accessToken | string | access_token |
| refreshToken | string | refresh_token |
| accessTokenExpireIn | integer | access_token 过期 Unix 时间戳 |
| refreshTokenExpireIn | integer | refresh_token 过期 Unix 时间戳 |

返回的 `accessToken` 可交给开发者代理（`/tiktokShop/developerProxy`）用于调用 TikTok Shop 开放接口。

---

### 4. Refresh Token

**Endpoint**: `/tiktokShop/refreshToken`

从库中读取 `refresh_token`，调用紫鸟刷新接口续签令牌并回写数据库。

**Request Parameters** (JSON):

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| openId | string | **Yes** | - | 卖家 open_id |
| appType | string | No | `erp` | 须与授权时一致（视频号授权传 `creator`） |

**Response**:

```json
{
  "authRecordId": 1,
  "accessToken": "TTP_Fw8rBwAAAA...",
  "refreshToken": "TTP_NTUxZTNh...",
  "accessTokenExpireIn": 1660556783,
  "refreshTokenExpireIn": 1691487031,
  "message": "刷新成功并已更新数据库"
}
```

> `refresh_token` 过期后须重新走 **`/tiktokShop/authorizeUrl`** 授权流程。

---

## Error Codes

| errcode | 含义 | 建议动作 |
|---------|------|----------|
| 1002 | 参数校验失败 / 未登录（如缺少 openId、path 非法） | 检查必填参数与认证 |
| 1003 | 上游（紫鸟）服务或网络异常 | 稍后重试，检查网络与白名单 |
| 1004 | 授权记录不存在或不属于当前用户、缺少 refresh_token | 核对 openId/appType 或重新授权 |
| 1005 | 开发者代理 path 未在白名单（仅 developerProxy 相关） | 使用白名单内的 path 前缀 |

**Error Response Example**:

```json
{
  "errcode": 1002,
  "errmsg": "Missing required parameter: openId"
}
```

---

## curl Examples

### Get Authorization URL

```bash
# 授权 TikTok Shop 小店
curl -X POST https://tool-gateway.linkfox.com/tiktokShop/authorizeUrl \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"shopName": "My Shop", "region": "us", "appType": "erp"}'

# 授权 TikTok 视频号（appType=creator）
curl -X POST https://tool-gateway.linkfox.com/tiktokShop/authorizeUrl \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"shopName": "My Channels", "region": "global", "appType": "creator"}'
```

### List Authorized Stores

```bash
curl -X POST https://tool-gateway.linkfox.com/tiktokShop/authorizedStores \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Query Store Tokens

```bash
curl -X POST https://tool-gateway.linkfox.com/tiktokShop/storeTokens \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"openId": "7010736057180325637", "appType": "erp"}'
```

### Refresh Token

```bash
curl -X POST https://tool-gateway.linkfox.com/tiktokShop/refreshToken \
  -H "Authorization: $LINKFOXAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"openId": "7010736057180325637", "appType": "erp"}'
```

---

## Feedback API

> 本接口与上面的工具 API **是不同 base URL**，请勿混用。

- **POST** `https://skill-api.linkfox.com/api/v1/public/feedback`
- **Content-Type**: `application/json`

```json
{
  "skillName": "linkfox-tiktok-auth",
  "sentiment": "POSITIVE",
  "category": "OTHER",
  "content": "Authorization flow worked smoothly, user was satisfied."
}
```

**Field rules**:
- `skillName`: 使用本 skill 的 YAML frontmatter `name`
- `sentiment`: `POSITIVE` / `NEUTRAL` / `NEGATIVE`
- `category`: `BUG` / `COMPLAINT` / `SUGGESTION` / `OTHER`
- `content`: 用户说的话、实际发生了什么、为什么是问题或赞赏

---

## Important Notes

1. **Token 安全**：不要打印完整 accessToken/refreshToken，仅展示前 10 字符掩码。
2. **过期判断**：`accessTokenExpireIn` / `refreshTokenExpireIn` 为绝对 Unix 时间戳，与当前时间比较判断是否过期。
3. **appType 一致**：查询/刷新令牌的 `appType` 必须与授权时一致。
4. **用户隔离**：所有 API 都强制用户级访问控制。
5. **回调白名单**：系统回调 URL 与调用 IP 必须在授权提供方（紫鸟）处加白名单。
