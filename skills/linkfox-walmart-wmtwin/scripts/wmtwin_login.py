#!/usr/bin/env python3
"""
沃师傅(WMTwin) API工具
自动化登录与API调用
"""

import os
import sys
import json
import base64
import requests
from datetime import datetime

# RSA加密
try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_v1_5
except ImportError:
    print("请安装: pip install pycryptodome")
    sys.exit(1)

# 配置
BASE_URL = "https://www.wmtwin.com"
API_BASE = f"{BASE_URL}/api/v1"
SESSION_DIR = "/tmp/linkfox_wmtwin_sessions"

# RSA公钥
PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDEICVdtxqOCBwHN9a/+YxeXz/B
ZGfduADPfV9dUTW+hGVpIcXU6kBkUdlhVPPdO6n7irK7dxD56m1xG1EmV2RICsvy
W2Y7JVyRRVhun92urbw7TtBcMCCB5SzLI+x1LBUr98SMkMNRQxcnYPkrPj0qGI4v
MC52dJ7z3n6aMf3XoQIDAQAB
-----END PUBLIC KEY-----"""


def encrypt_password(password):
    """RSA加密密码"""
    public_key = RSA.import_key(PUBLIC_KEY)
    cipher = PKCS1_v1_5.new(public_key)
    encrypted_bytes = cipher.encrypt(password.encode('utf-8'))
    return base64.b64encode(encrypted_bytes).decode('utf-8')


def is_success(result):
    """判断API响应是否成功（沃师傅的code: 1表示成功）"""
    return result.get('code') in [0, 1] and result.get('msg') in ['成功', '操作成功']


def create_session():
    """创建新的requests session"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    })
    return session


def save_session(session, phone):
    """保存session到文件"""
    try:
        os.makedirs(SESSION_DIR, exist_ok=True)
        session_file = f'{SESSION_DIR}/{phone}.json'

        # 处理重复cookie
        cookies_dict = {}
        for cookie in session.cookies:
            cookies_dict[cookie.name] = cookie.value

        session_data = {
            'cookies': cookies_dict,
            'headers': dict(session.headers),
            'saved_at': datetime.now().isoformat()
        }

        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        return True
    except Exception as e:
        print(f"⚠️  保存session失败: {e}")
        return False


def load_session(phone):
    """加载已保存的session"""
    session_file = f'{SESSION_DIR}/{phone}.json'

    if not os.path.exists(session_file):
        return None

    try:
        with open(session_file, 'r') as f:
            session_data = json.load(f)

        session = create_session()

        # 恢复cookies
        for name, value in session_data.get('cookies', {}).items():
            session.cookies.set(name, value)

        # 恢复headers
        session.headers.update(session_data.get('headers', {}))

        return session
    except Exception as e:
        print(f"⚠️  加载session失败: {e}")
        return None


def login_step1_password(phone, password):
    """步骤1: 尝试密码登录"""
    session = create_session()
    encrypted_pwd = encrypt_password(password)

    try:
        response = session.post(
            f'{API_BASE}/auth/login',
            json={'phone': phone, 'password': encrypted_pwd},
            timeout=10
        )
        result = response.json()

        if is_success(result):
            return 'success', session, None
        elif result.get('code') == 1101:
            return 'need_sms', session, result.get('msg')
        else:
            return 'error', None, result.get('msg')

    except Exception as e:
        return 'error', None, str(e)


def login_step2_get_captcha(session):
    """步骤2: 获取图形验证码"""
    try:
        response = session.get(f'{API_BASE}/auth/captcha', timeout=10)
        result = response.json()

        if result.get('code') in [0, 1]:
            captcha_base64 = result.get('data', {}).get('b64', '')
            if 'base64,' in captcha_base64:
                captcha_base64 = captcha_base64.split('base64,')[1]

            # 保存验证码图片
            captcha_path = '/tmp/linkfox_wmtwin_captcha.png'
            with open(captcha_path, 'wb') as f:
                f.write(base64.b64decode(captcha_base64))

            return 'success', captcha_path, captcha_base64
        else:
            return 'error', None, result.get('msg')

    except Exception as e:
        return 'error', None, str(e)


def login_step3_send_sms(session, phone, captcha_answer):
    """步骤3: 发送短信验证码"""
    try:
        response = session.post(
            f'{API_BASE}/auth/sms-code',
            json={
                'phone': phone,
                'captcha': str(captcha_answer),
                'scene': 2
            },
            timeout=10
        )
        result = response.json()

        if is_success(result):
            return 'success', result.get('data')
        else:
            return 'error', result.get('msg')

    except Exception as e:
        return 'error', str(e)


def login_step4_sms_login(session, phone, sms_code):
    """步骤4: 短信验证码登录"""
    try:
        response = session.post(
            f'{API_BASE}/auth/sms-login',
            json={
                'phone': phone,
                'smsCode': sms_code,
                'referrerCode': '',
                'source': 'baidu'
            },
            timeout=10
        )
        result = response.json()

        if is_success(result):
            return 'success', session
        else:
            return 'error', result.get('msg')

    except Exception as e:
        return 'error', str(e)


def auto_login(phone, password, captcha_answer=None, sms_code=None):
    """
    自动登录（完整流程）

    返回: (status, session_or_message)
        - ('success', session): 登录成功
        - ('need_captcha', captcha_path): 需要图形验证码
        - ('need_sms', message): 需要短信验证码
        - ('error', message): 错误
    """
    print(f"🔐 登录沃师傅账号: {phone}")
    print()

    # 步骤1: 密码登录
    print("📝 [1/4] 尝试密码登录...")
    status, session, msg = login_step1_password(phone, password)

    if status == 'success':
        print("✅ 密码登录成功！")
        save_session(session, phone)
        return ('success', session)
    elif status == 'error':
        print(f"❌ 密码登录失败: {msg}")
        return ('error', msg)

    print(f"⚠️  {msg}")
    print()

    # 步骤2: 获取验证码
    print("🖼️  [2/4] 获取图形验证码...")
    status, captcha_path, captcha_base64 = login_step2_get_captcha(session)

    if status == 'error':
        print(f"❌ 获取验证码失败: {captcha_path}")
        return ('error', captcha_path)

    print(f"✅ 验证码已保存: {captcha_path}")

    if not captcha_answer:
        print()
        print("=" * 70)
        print("📸 需要图形验证码")
        print("=" * 70)

        # 保存临时session
        temp_file = '/tmp/linkfox_wmtwin_temp.json'
        with open(temp_file, 'w') as f:
            cookies_dict = {}
            for cookie in session.cookies:
                cookies_dict[cookie.name] = cookie.value
            json.dump({
                'cookies': cookies_dict,
                'headers': dict(session.headers),
                'phone': phone,
                'captcha_base64': captcha_base64
            }, f)

        return ('need_captcha', captcha_path)

    # 步骤3: 发送短信
    print()
    print(f"📲 [3/4] 发送短信验证码... (图形验证码: {captcha_answer})")
    status, msg = login_step3_send_sms(session, phone, captcha_answer)

    if status == 'error':
        print(f"❌ 发送失败: {msg}")
        return ('error', msg)

    print(f"✅ {msg}")

    if not sms_code:
        print()
        print("=" * 70)
        print("📱 需要短信验证码")
        print("=" * 70)

        # 更新临时session
        temp_file = '/tmp/linkfox_wmtwin_temp.json'
        with open(temp_file, 'w') as f:
            cookies_dict = {}
            for cookie in session.cookies:
                cookies_dict[cookie.name] = cookie.value
            json.dump({
                'cookies': cookies_dict,
                'headers': dict(session.headers),
                'phone': phone
            }, f)

        return ('need_sms', '请查看手机短信')

    # 步骤4: 短信登录
    print()
    print(f"📱 [4/4] 短信验证码登录... (验证码: {sms_code})")
    status, result = login_step4_sms_login(session, phone, sms_code)

    if status == 'error':
        print(f"❌ 登录失败: {result}")
        return ('error', result)

    print()
    print("=" * 70)
    print("🎉 登录成功！")
    print("=" * 70)

    if save_session(result, phone):
        print(f"💾 Session已保存: {SESSION_DIR}/{phone}.json")

    # 清理临时文件
    temp_file = '/tmp/linkfox_wmtwin_temp.json'
    if os.path.exists(temp_file):
        os.remove(temp_file)

    return ('success', result)


def continue_login(captcha_answer=None, sms_code=None):
    """继续未完成的登录流程"""
    temp_file = '/tmp/linkfox_wmtwin_temp.json'

    if not os.path.exists(temp_file):
        return ('error', '没有未完成的登录流程')

    with open(temp_file, 'r') as f:
        temp_data = json.load(f)

    session = create_session()
    for name, value in temp_data['cookies'].items():
        session.cookies.set(name, value)
    session.headers.update(temp_data['headers'])

    phone = temp_data['phone']

    if captcha_answer and not sms_code:
        # 发送短信
        print(f"📲 发送短信验证码... (图形验证码: {captcha_answer})")
        status, msg = login_step3_send_sms(session, phone, captcha_answer)

        if status == 'error':
            print(f"❌ 发送失败: {msg}")
            return ('error', msg)

        print(f"✅ {msg}")
        print()
        print("=" * 70)
        print("📱 请查看手机短信，然后输入验证码")
        print("=" * 70)

        # 更新临时session
        with open(temp_file, 'w') as f:
            cookies_dict = {}
            for cookie in session.cookies:
                cookies_dict[cookie.name] = cookie.value
            json.dump({
                'cookies': cookies_dict,
                'headers': dict(session.headers),
                'phone': phone
            }, f)

        return ('need_sms', '请输入短信验证码')

    elif sms_code:
        # 完成登录
        print(f"📱 短信验证码登录... (验证码: {sms_code})")
        status, result = login_step4_sms_login(session, phone, sms_code)

        if status == 'error':
            print(f"❌ 登录失败: {result}")
            return ('error', result)

        print()
        print("=" * 70)
        print("🎉 登录成功！")
        print("=" * 70)

        if save_session(result, phone):
            print(f"💾 Session已保存: {SESSION_DIR}/{phone}.json")

        # 清理临时文件
        os.remove(temp_file)

        return ('success', result)

    return ('error', '参数错误')


def call_api(phone, endpoint, method='GET', data=None, password=None):
    """
    调用沃师傅API（自动处理登录）

    参数:
        phone: 手机号
        endpoint: API端点（如 /user/info）
        method: GET/POST/PUT/DELETE
        data: 请求数据
        password: 密码（首次登录需要）
    """
    # 加载session
    session = load_session(phone)

    # 如果没有session，需要登录
    if not session:
        if not password:
            return {'error': '未登录，需要提供密码'}

        status, result = auto_login(phone, password)
        if status != 'success':
            return {'error': f'登录失败: {result}'}
        session = result

    # 调用API
    url = f'{API_BASE}{endpoint}'

    try:
        if method.upper() == 'GET':
            response = session.get(url, timeout=30)
        elif method.upper() == 'POST':
            response = session.post(url, json=data, timeout=30)
        elif method.upper() == 'PUT':
            response = session.put(url, json=data, timeout=30)
        elif method.upper() == 'DELETE':
            response = session.delete(url, timeout=30)
        else:
            return {'error': f'不支持的方法: {method}'}

        return response.json()

    except Exception as e:
        return {'error': str(e)}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("沃师傅API工具")
        print()
        print("命令:")
        print("  login <手机号> <密码> [图形验证码] [短信验证码]")
        print("  continue <图形验证码>  或  continue sms <短信验证码>")
        print("  api <手机号> <端点> [方法] [数据JSON]")
        print("  check <手机号>")
        print()
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'login':
        if len(sys.argv) < 4:
            print("用法: login <手机号> <密码> [图形验证码] [短信验证码]")
            sys.exit(1)

        phone = sys.argv[2]
        password = sys.argv[3]
        captcha = sys.argv[4] if len(sys.argv) > 4 else None
        sms = sys.argv[5] if len(sys.argv) > 5 else None

        status, result = auto_login(phone, password, captcha, sms)
        print()
        print(f"状态: {status}")

    elif cmd == 'continue':
        if len(sys.argv) < 3:
            print("用法: continue <图形验证码>  或  continue sms <短信验证码>")
            sys.exit(1)

        if sys.argv[2] == 'sms':
            sms = sys.argv[3] if len(sys.argv) > 3 else None
            status, result = continue_login(sms_code=sms)
        else:
            captcha = sys.argv[2]
            status, result = continue_login(captcha_answer=captcha)

        print()
        print(f"状态: {status}")

    elif cmd == 'api':
        if len(sys.argv) < 4:
            print("用法: api <手机号> <端点> [方法] [数据JSON]")
            sys.exit(1)

        phone = sys.argv[2]
        endpoint = sys.argv[3]
        method = sys.argv[4] if len(sys.argv) > 4 else 'GET'
        data = json.loads(sys.argv[5]) if len(sys.argv) > 5 else None

        result = call_api(phone, endpoint, method, data)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == 'check':
        if len(sys.argv) < 3:
            print("用法: check <手机号>")
            sys.exit(1)

        phone = sys.argv[2]
        session = load_session(phone)

        if session:
            print(f"✅ {phone} 已登录")
        else:
            print(f"❌ {phone} 未登录")

    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)
