#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沃师傅完整解码器 - 支持所有已知编码范围

编码范围：
1. 312: 小数点 . (新发现 - 偏移量方法)
2. 313-322: 数字 0-9 (偏移量 265)
3. 323: 小数点 . (基数 324系列)
4. 324-333: 数字 0-9 (基数 324)
5. 334-385: 完整字符集 (基数 334)
   - 334-359 (偏移 0-25): 大写字母 A-Z
   - 360-385 (偏移 26-51): 小写字母 a-z
6. 349-374: 小写字母 a-z (偏移量 252) - 新发现
7. 323-348: 大写字母 A-Z (偏移量 258) - 新发现
8. 528-590: 完整字符集 (基数 528) - 文档标准编码
   - 528: 小数点 . (特殊字符)
   - 529-538 (偏移 0-9): 数字 0-9
   - 539-564 (偏移 0-25): 大写字母 A-Z
   - 565-590 (偏移 0-25): 小写字母 a-z

偏移量方法（新发现，优先级最高）：
- 大写字母 A-Z: 码点 - 258 = ASCII码 (65-90)
- 小写字母 a-z: 码点 - 252 = ASCII码 (97-122)
- 数字 0-9: 码点 - 265 = ASCII码 (48-57)
- 小数点: 码点 312 = '.'
"""

import json
import sys
from typing import Any, Dict, List, Union


def decode_wmtwin_char(char: str) -> str:
    """
    解码单个沃师傅编码字符

    优先级：
    1. 偏移量方法（新版，312-374）- 最高优先级
    2. 基数 528 方案（文档标准）
    3. 基数 324/334 方案（旧版API）

    Args:
        char: 单个字符

    Returns:
        解码后的字符
    """
    code = ord(char)

    # === 优先级1: 偏移量方法（新版，最常用）===

    # 小数点 (312)
    if code == 312:
        return '.'

    # 数字 0-9: 偏移量 265 (码点 313-322)
    if 313 <= code <= 322:
        return str(code - 313)

    # 大写字母 A-Z: 偏移量 258 (码点 323-348)
    # 注意: 323 可能是小数点或大写字母 A，这里优先作为 A 处理
    decoded_code = code - 258
    if 65 <= decoded_code <= 90:
        return chr(decoded_code)

    # 小写字母 a-z: 偏移量 252 (码点 349-374)
    decoded_code = code - 252
    if 97 <= decoded_code <= 122:
        return chr(decoded_code)

    # === 优先级2: 基数 528 方案（文档标准）===

    if code == 528:
        return '.'
    elif 529 <= code <= 538:
        return str(code - 529)
    elif 539 <= code <= 564:
        return chr(65 + (code - 539))
    elif 565 <= code <= 590:
        return chr(97 + (code - 565))

    # === 优先级3: 基数 324/334 方案（旧版API，已不常用）===
    # 这些范围已被偏移量方法覆盖，但保留以防万一

    # 未编码字符，保持原样
    return char


def decode_string(s: Any) -> Any:
    """
    解码字符串

    Args:
        s: 输入值（任意类型）

    Returns:
        如果是字符串则解码，否则返回原值
    """
    if not isinstance(s, str):
        return s
    return ''.join(decode_wmtwin_char(c) for c in s)


def decode_json(obj: Any) -> Any:
    """
    递归解码 JSON 对象（处理所有嵌套结构）

    Args:
        obj: JSON 对象（dict, list, str 或其他类型）

    Returns:
        解码后的对象
    """
    if isinstance(obj, dict):
        return {key: decode_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [decode_json(item) for item in obj]
    elif isinstance(obj, str):
        return decode_string(obj)
    else:
        return obj


def decode_json_file(input_file: str, output_file: str = None) -> Dict:
    """
    解码 JSON 文件

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径（可选，不提供则只返回结果）

    Returns:
        解码后的 JSON 数据
    """
    # 读取文件
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 解码
    decoded_data = decode_json(data)

    # 保存（如果提供了输出路径）
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(decoded_data, f, ensure_ascii=False, indent=2)

    return decoded_data


def main():
    """命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(
        description='沃师傅完整解码器 - 解码所有编码字符',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 解码 JSON 文件并保存
  python3 wmtwin_complete_decoder.py input.json -o output.json

  # 解码并输出到标准输出
  python3 wmtwin_complete_decoder.py input.json

  # 从标准输入读取
  cat input.json | python3 wmtwin_complete_decoder.py -

编码范围说明:
  323      : 小数点 .
  324-333  : 数字 0-9
  334-385  : 完整字符集 (A-Z, a-z) - 卖家名称等
  528      : 小数点 . (特殊字符)
  529-538  : 数字 0-9
  539-564  : 大写字母 A-Z
  565-590  : 小写字母 a-z
        """
    )

    parser.add_argument(
        'input',
        help='输入 JSON 文件路径（使用 - 从标准输入读取）'
    )
    parser.add_argument(
        '-o', '--output',
        help='输出文件路径（默认输出到标准输出）'
    )

    args = parser.parse_args()

    # 从标准输入或文件读取
    if args.input == '-':
        json_str = sys.stdin.read()
        data = json.loads(json_str)
    else:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)

    # 解码
    decoded_data = decode_json(data)

    # 输出
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(decoded_data, f, ensure_ascii=False, indent=2)
        print(f"✓ 解码完成: {args.input} -> {args.output}")
    else:
        print(json.dumps(decoded_data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
