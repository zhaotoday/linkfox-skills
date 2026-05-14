# 沃师傅(WMTwin) API Reference

## Base URL

```
https://www.wmtwin.com/api/v1
```

## Authentication

All authentication APIs are under `/api/v1/auth/` path.

## Response Format

### Success Response

```json
{
  "code": 1,           // 注意：1表示成功！
  "msg": "成功",
  "data": {...}
}
```

### Error Response

```json
{
  "code": <error_code>,
  "msg": "错误描述",
  "data": null
}
```

### Determining Success

```python
def is_success(result):
    return result.get('code') in [0, 1] and result.get('msg') in ['成功', '操作成功']
```

## Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 1 | Success | Process normally |
| 0 | Success (alternative) | Process normally |
| 1101 | Environment anomaly, SMS login required | Switch to SMS login flow |
| 1008 | CAPTCHA error | Get new CAPTCHA |
| 1020 | SMS code error | Verify SMS code or resend |

## API Endpoints

### 1. Password Login

**POST** `/api/v1/auth/login`

尝试使用密码登录。如果环境正常，可以直接登录成功；如果环境异常（code: 1101），需要切换到短信验证码登录流程。

#### Request

```json
{
  "phone": "13699998888",
  "password": "RSA加密后的密码(Base64格式)"
}
```

**Password Encryption**:
- Algorithm: RSA 1024-bit + PKCS1 v1.5
- Encoding: Base64
- See SKILL.md for encryption example

#### Response (Success)

```json
{
  "code": 1,
  "msg": "成功",
  "data": true
}
```

#### Response (Need SMS)

```json
{
  "code": 1101,
  "msg": "环境异常，请使用手机验证码登录",
  "data": null
}
```

**Set-Cookie**: Session cookies will be set in response headers

---

### 2. Get Graphical CAPTCHA

**GET** `/api/v1/auth/captcha`

获取图形验证码。返回base64编码的PNG图片。

#### Request

No parameters required.

#### Response

```json
{
  "code": 1,
  "msg": "成功",
  "data": {
    "b64": "data:image/png;base64,iVBORw0KGgo..."
  }
}
```

**CAPTCHA Type**: Simple math expression (e.g., "3 × 8 = ?", "12 + 2 = ?" )

**Usage**:
1. Extract base64 data: `split('base64,')[1]`
2. Decode and save as PNG image
3. Display to user for manual input
4. Use answer in next step (send SMS code)

---

### 3. Send SMS Verification Code

**POST** `/api/v1/auth/sms-code`

发送短信验证码。需要提供图形验证码的答案。

#### Request

```json
{
  "phone": "13699998888",
  "captcha": "24",
  "scene": 2
}
```

**Parameters**:
- `phone` (string, required): 手机号
- `captcha` (string, required): 图形验证码的答案
- `scene` (integer, required): 场景代码，登录场景使用 `2`

#### Response (Success)

```json
{
  "code": 1,
  "msg": "成功",
  "data": "短信已发至您的手机，有效时间30分钟，请及时使用"
}
```

#### Response (CAPTCHA Error)

```json
{
  "code": 1008,
  "msg": "验证码错误",
  "data": null
}
```

**Note**: SMS code is valid for 30 minutes

---

### 4. SMS Code Login

**POST** `/api/v1/auth/sms-login`

使用短信验证码完成登录。

#### Request

```json
{
  "phone": "13699998888",
  "smsCode": "123456",
  "referrerCode": "",
  "source": "baidu"
}
```

**Parameters**:
- `phone` (string, required): 手机号
- `smsCode` (string, required): 短信验证码
- `referrerCode` (string, optional): 推荐码，可以为空
- `source` (string, optional): 来源标识，默认 "baidu"

#### Response (Success)

```json
{
  "code": 1,
  "msg": "成功",
  "data": true
}
```

#### Response (SMS Code Error)

```json
{
  "code": 1020,
  "msg": "短信验证码错误",
  "data": null
}
```

**Set-Cookie**: Session cookies will be set in response headers upon successful login

---

## Cookie Management

### Cookie Structure

沃师傅可能返回多个同名cookie（例如 `wal`），需要特殊处理：

```python
# 错误方式 (会抛出异常)
cookies = dict(session.cookies)

# 正确方式
cookies_dict = {}
for cookie in session.cookies:
    cookies_dict[cookie.name] = cookie.value  # 自动覆盖同名cookie
```

### Session Cookie

主要session cookie名称: `wal`

Cookie包含加密的会话信息，格式类似：
```
wal=MTc3NzM2NDg4OHxE...（Base64编码的加密数据）
```

---

## Complete Login Flow Example

```python
import requests
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

# 1. 密码登录尝试
session = requests.Session()
encrypted_pwd = encrypt_password("Welcome1")  # RSA加密

response = session.post(
    "https://www.wmtwin.com/api/v1/auth/login",
    json={"phone": "13699998888", "password": encrypted_pwd}
)
result = response.json()

if result['code'] == 1101:
    # 2. 获取图形验证码
    response = session.get("https://www.wmtwin.com/api/v1/auth/captcha")
    captcha_b64 = response.json()['data']['b64'].split('base64,')[1]

    # 保存图片让用户识别
    with open('/tmp/captcha.png', 'wb') as f:
        f.write(base64.b64decode(captcha_b64))

    # 用户提供答案
    captcha_answer = "24"  # 用户输入

    # 3. 发送短信验证码
    response = session.post(
        "https://www.wmtwin.com/api/v1/auth/sms-code",
        json={"phone": "13699998888", "captcha": captcha_answer, "scene": 2}
    )

    # 用户查看手机短信
    sms_code = "123456"  # 用户输入

    # 4. 短信验证码登录
    response = session.post(
        "https://www.wmtwin.com/api/v1/auth/sms-login",
        json={
            "phone": "13699998888",
            "smsCode": sms_code,
            "referrerCode": "",
            "source": "baidu"
        }
    )

    if response.json()['code'] == 1:
        print("登录成功！")
        # session.cookies 现在包含认证cookie
```

---

## Session Storage

### Recommended Storage Format

```json
{
  "cookies": {
    "wal": "encoded_session_token"
  },
  "headers": {
    "User-Agent": "Mozilla/5.0 ...",
    "Content-Type": "application/json",
    "Accept": "application/json"
  },
  "saved_at": "2024-04-28T16:28:08.987745"
}
```

### Session Reuse

```python
import json
import requests

# 加载session
with open('/tmp/linkfox_wmtwin_sessions/13699998888.json', 'r') as f:
    session_data = json.load(f)

session = requests.Session()

# 恢复cookies
for name, value in session_data['cookies'].items():
    session.cookies.set(name, value)

# 恢复headers
session.headers.update(session_data['headers'])

# 现在可以使用session调用其他API
response = session.get('https://www.wmtwin.com/api/v1/user/info')
```

---

## Rate Limiting

- No official rate limit documentation
- Recommended: Don't send SMS codes more than once per minute
- CAPTCHA can be requested multiple times

---

## Common Issues

### Issue 1: Cookie Duplication Error

**Error**: `There are multiple cookies with name, 'wal'`

**Solution**: Use the cookie iteration method shown in Cookie Management section

### Issue 2: Wrong Success Detection

**Error**: API succeeds but code detects it as failure

**Solution**: Check for `code in [0, 1]` instead of just `code == 0`

### Issue 3: SMS Code Expired

**Error**: code 1020 after some delay

**Solution**: SMS codes expire after 30 minutes, request a new one

### Issue 4: CAPTCHA Wrong

**Error**: code 1008 when sending SMS

**Solution**: Get new CAPTCHA and try again - the math expression may have been misread

---

## Security Considerations

1. **Password Encryption**: Always encrypt password with RSA before sending
2. **HTTPS Only**: Never use HTTP for authentication
3. **Session Storage**: Store session securely, don't expose cookies
4. **Session Cleanup**: Delete session files after use or periodically
5. **No Password Storage**: Never store plaintext passwords

---

## Additional Notes

- All timestamps are in ISO 8601 format
- Phone numbers are Chinese mobile numbers (11 digits)
- SMS verification codes are 6 digits
- Graphical CAPTCHA answers are usually integers (math results)
- Session cookies are long-lived but may expire
- Re-authentication required when session expires
