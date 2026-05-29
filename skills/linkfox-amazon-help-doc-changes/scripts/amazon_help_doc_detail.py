#!/usr/bin/env python3
"""
Amazon Help Doc Change Detail - LinkFox Skill
调用 amazon/helpDocDetail 接口，按变更记录 ID 查看单篇帮助文档变更的完整信息
（AI 变更摘要 + 具体改动点 + 最新文档全文，Markdown）。
入参 id 来自 amazon_help_doc_changes.py 列表响应中的 data[].id 字段。

Usage:
  python amazon_help_doc_detail.py '{"id": 35}'
"""

import json
import os
import sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


API_URL = "https://tool-gateway.linkfox.com/amazon/helpDocDetail"


def get_api_key():
    """从环境变量读取 API Key，缺失时给出友好提示。"""
    key = os.environ.get("LINKFOXAGENT_API_KEY")
    if not key:
        print(
            "API Key not configured. Please complete authorization first:\n"
            "1. Visit https://yxgb3sicy7.feishu.cn/wiki/GIkkweGghiyzkqkRXQKc2n0Tnre to obtain your Key\n"
            "2. Set the environment variable: export LINKFOXAGENT_API_KEY=your-key-here",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def call_api(params: dict) -> dict:
    """调用工具网关接口。"""
    api_key = get_api_key()
    data = json.dumps(params).encode("utf-8")

    req = Request(
        API_URL,
        data=data,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
            "User-Agent": "LinkFox-Skill/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
        if isinstance(result, dict) and "errcode" in result and result["errcode"] != 200:
            print(
                f"Business error: errcode={result['errcode']}, errmsg={result.get('errmsg', '')}",
                file=sys.stderr,
            )
        return result
    except HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        try:
            parsed = json.loads(body) if body else None
        except (json.JSONDecodeError, ValueError):
            parsed = None
        if isinstance(parsed, dict) and "errcode" in parsed:
            return parsed
        errmsg = f"HTTP {e.code}: {e.reason}"
        if body:
            errmsg += f" - {body}"
        return {"errcode": e.code, "errmsg": errmsg}
    except URLError as e:
        return {"errcode": -1, "errmsg": f"Connection failed: {e.reason}"}


def main():
    if len(sys.argv) < 2:
        print("Usage: amazon_help_doc_detail.py '<JSON parameters>'", file=sys.stderr)
        print('Example: amazon_help_doc_detail.py \'{"id": 35}\'', file=sys.stderr)
        sys.exit(1)

    try:
        params = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"Invalid parameter format: {e}", file=sys.stderr)
        sys.exit(1)

    result = call_api(params)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
