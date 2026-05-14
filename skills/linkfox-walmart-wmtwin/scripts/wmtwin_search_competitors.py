#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沃师傅竞品搜索工具

功能：搜索沃尔玛竞品，支持多种筛选条件
自动检查登录状态，未登录时引导用户登录
"""

import os
import sys
import requests
import json
import argparse
from typing import Dict, List, Optional, Any

# 导入登录模块
try:
    from wmtwin_login import load_session, save_session, create_session
    from wmtwin_login import login_step1_password, login_step2_get_captcha
    from wmtwin_login import login_step3_send_sms, login_step4_sms_login
    from wmtwin_login import is_success as is_api_success
    HAVE_LOGIN_MODULE = True
except ImportError:
    HAVE_LOGIN_MODULE = False
    print("⚠️  未找到 wmtwin_login.py，部分功能不可用")

# 导入解码模块
try:
    from wmtwin_complete_decoder import decode_json
    HAVE_DECODER = True
except ImportError:
    HAVE_DECODER = False
    print("⚠️  未找到 wmtwin_complete_decoder.py，数据将不会自动解码")


class WMTwinCompetitorSearch:
    """沃师傅竞品搜索客户端（带自动登录）"""

    def __init__(self, base_url: str = 'https://www.wmtwin.com', phone: str = None):
        """
        初始化搜索客户端

        Args:
            base_url: API 基础 URL
            phone: 手机号（用于加载 session）
        """
        self.base_url = base_url
        self.phone = phone
        self.session = None
        self.logged_in = False

        # 如果提供了手机号，尝试加载 session
        if phone and HAVE_LOGIN_MODULE:
            self._load_session_for_phone(phone)

    def _load_session_for_phone(self, phone: str):
        """加载指定手机号的 session"""
        session = load_session(phone)
        if session:
            self.session = session
            self.logged_in = True
            print(f"✓ 已加载 {phone} 的登录状态")
        else:
            print(f"⚠️  未找到 {phone} 的登录信息")
            self.session = create_session()
            self.logged_in = False

    def ensure_logged_in(self, phone: str = None, password: str = None) -> bool:
        """
        确保已登录，如果未登录则引导用户登录

        Args:
            phone: 手机号
            password: 密码

        Returns:
            是否已登录
        """
        if not HAVE_LOGIN_MODULE:
            print("❌ 登录功能不可用，缺少 wmtwin_login.py")
            return False

        # 如果已登录，直接返回
        if self.logged_in:
            return True

        # 如果没有提供手机号，提示用户
        if not phone:
            phone = self.phone
            if not phone:
                print("\n" + "="*80)
                print("需要登录才能搜索竞品")
                print("="*80)
                print("\n请提供登录信息：")
                phone = input("手机号: ").strip()
                if not phone:
                    print("❌ 未提供手机号，无法登录")
                    return False

        # 尝试加载已有的 session
        self.phone = phone
        session = load_session(phone)
        if session:
            self.session = session
            self.logged_in = True
            print(f"✓ 已加载 {phone} 的登录状态")
            return True

        # 需要登录
        print(f"\n未找到 {phone} 的登录信息，开始登录流程...\n")

        # 如果没有密码，询问用户
        if not password:
            import getpass
            password = getpass.getpass("密码: ")
            if not password:
                print("❌ 未提供密码，无法登录")
                return False

        # 执行登录流程
        return self._do_login(phone, password)

    def _do_login(self, phone: str, password: str) -> bool:
        """
        执行完整的登录流程

        Args:
            phone: 手机号
            password: 密码

        Returns:
            是否登录成功
        """
        print("\n" + "="*80)
        print("开始登录流程")
        print("="*80 + "\n")

        # 步骤1: 尝试密码登录
        print("步骤 1/4: 尝试密码登录...")
        status, session, msg = login_step1_password(phone, password)

        if status == 'success':
            self.session = session
            self.logged_in = True
            save_session(session, phone)
            print("✓ 密码登录成功！")
            return True

        elif status == 'need_sms':
            print(f"⚠️  {msg}")
            print("需要短信验证码登录\n")
            self.session = session

        else:
            print(f"❌ 登录失败: {msg}")
            return False

        # 步骤2: 获取图形验证码
        print("步骤 2/4: 获取图形验证码...")
        status, captcha_path, captcha_b64 = login_step2_get_captcha(self.session)

        if status != 'success':
            print(f"❌ 获取验证码失败: {captcha_path}")
            return False

        print(f"✓ 验证码已保存到: {captcha_path}")
        print("\n请查看验证码图片并输入答案")

        # 尝试自动打开图片（macOS）
        try:
            os.system(f'open {captcha_path}')
        except:
            pass

        captcha_answer = input("\n验证码答案: ").strip()
        if not captcha_answer:
            print("❌ 未提供验证码答案")
            return False

        # 步骤3: 发送短信验证码
        print("\n步骤 3/4: 发送短信验证码...")
        status, data = login_step3_send_sms(self.session, phone, captcha_answer)

        if status != 'success':
            print(f"❌ 发送短信失败: {data}")
            print("可能是验证码错误，请重试")
            return False

        print(f"✓ 短信已发送到 {phone}")

        # 步骤4: 短信验证码登录
        sms_code = input("\n短信验证码: ").strip()
        if not sms_code:
            print("❌ 未提供短信验证码")
            return False

        print("\n步骤 4/4: 验证短信验证码...")
        status, session = login_step4_sms_login(self.session, phone, sms_code)

        if status != 'success':
            print(f"❌ 登录失败: {session}")
            return False

        # 登录成功
        self.session = session
        self.logged_in = True
        save_session(session, phone)

        print("\n" + "="*80)
        print("✓ 登录成功！")
        print("="*80 + "\n")

        return True

    def search_competitors(
        self,
        keyword: str = None,
        product_id: str = None,
        is_wfs: Optional[bool] = None,
        min_sales_volume: Optional[int] = None,
        max_sales_volume: Optional[int] = None,
        min_sales_amount: Optional[int] = None,
        max_sales_amount: Optional[int] = None,
        min_number_of_reviews: Optional[int] = None,
        max_number_of_reviews: Optional[int] = None,
        min_average_rating: Optional[float] = None,
        max_average_rating: Optional[float] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        seller_name: Optional[str] = None,
        brand: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        phone: str = None,
        password: str = None,
        **extra_params
    ) -> Dict:
        """
        搜索竞品（自动检查登录）

        Args:
            keyword: 搜索关键词（与 product_id 互斥）
            product_id: 产品 WID（与 keyword 互斥，如果提供则忽略其他筛选参数）
            is_wfs: 是否 WFS（Walmart Fulfillment Services）
            min_sales_volume: 最小销量
            max_sales_volume: 最大销量
            min_sales_amount: 最小销售额
            max_sales_amount: 最大销售额
            min_number_of_reviews: 最小评论数
            max_number_of_reviews: 最大评论数
            min_average_rating: 最低评分
            max_average_rating: 最高评分
            min_price: 最低价格
            max_price: 最高价格
            seller_name: 卖家名称
            brand: 品牌
            page: 页码（从1开始）
            page_size: 每页数量
            phone: 手机号（用于登录）
            password: 密码（用于登录）
            **extra_params: 其他额外参数

        Returns:
            解码后的搜索结果
        """
        # 确保已登录
        if not self.ensure_logged_in(phone, password):
            return {
                'error': 'not_logged_in',
                'success': False,
                'message': '未登录，无法搜索'
            }

        # 构建请求参数
        # 注意：product_id 和 keyword 互斥，如果提供 product_id 则忽略其他筛选参数
        if product_id:
            params = {
                'product_id': product_id
            }
        else:
            params = {
                'page': page,
                'pageSize': page_size,
            }

            # keyword 是必需的（当不使用 product_id 时）
            if keyword:
                params['keyword'] = keyword

            # 添加可选参数
            if is_wfs is not None:
                params['is_wfs'] = is_wfs

            if min_sales_volume is not None:
                params['min_sales_volume'] = min_sales_volume

            if max_sales_volume is not None:
                params['max_sales_volume'] = max_sales_volume

            if min_sales_amount is not None:
                params['min_sales_amount'] = min_sales_amount

            if max_sales_amount is not None:
                params['max_sales_amount'] = max_sales_amount

            if min_number_of_reviews is not None:
                params['min_number_of_reviews'] = min_number_of_reviews

            if max_number_of_reviews is not None:
                params['max_number_of_reviews'] = max_number_of_reviews

            if min_average_rating is not None:
                params['min_average_rating'] = min_average_rating

            if max_average_rating is not None:
                params['max_average_rating'] = max_average_rating

            if min_price is not None:
                params['min_price'] = min_price

            if max_price is not None:
                params['max_price'] = max_price

            if seller_name is not None:
                params['seller_name'] = seller_name

            if brand is not None:
                params['brand'] = brand

            # 添加额外参数
            params.update(extra_params)

        # 发送请求 - 使用 POST 方法和正确的端点
        endpoint = '/api/v1/product/search'  # 正确的端点（单数形式）
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.post(url, json=params, timeout=30)  # 使用 POST 和 json 参数

            # 检查是否需要重新登录
            if response.status_code == 401:
                print("⚠️  登录已过期，需要重新登录")
                self.logged_in = False

                # 尝试重新登录
                if self.ensure_logged_in(self.phone, password):
                    # 重试请求
                    response = self.session.post(url, json=params, timeout=30)
                else:
                    return {
                        'error': 'login_expired',
                        'success': False,
                        'message': '登录已过期，请重新登录'
                    }

            response.raise_for_status()

            # 解析 JSON
            data = response.json()

            # 自动解码所有编码字符串
            if HAVE_DECODER:
                decoded_data = decode_json(data)
            else:
                decoded_data = data

            return decoded_data

        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'success': False,
                'message': f'请求失败: {e}'
            }

    def search_from_params(self, params: Dict, phone: str = None, password: str = None) -> Dict:
        """
        从参数字典搜索（自动检查登录）

        Args:
            params: 参数字典，例如 {"keyword": "iphone", "is_wfs": true, ...}
            phone: 手机号（用于登录）
            password: 密码（用于登录）

        Returns:
            解码后的搜索结果
        """
        keyword = params.pop('keyword', '')
        if not keyword:
            return {
                'error': 'keyword is required',
                'success': False
            }

        return self.search_competitors(keyword=keyword, phone=phone, password=password, **params)

    def search_multiple_pages(
        self,
        total_count: int,
        keyword: str = None,
        product_id: str = None,
        phone: str = None,
        password: str = None,
        **search_params
    ) -> Dict:
        """
        自动查询多页数据直到达到指定数量

        Args:
            total_count: 需要获取的总数据量
            keyword: 搜索关键词
            product_id: 产品ID
            phone: 手机号
            password: 密码
            **search_params: 其他搜索参数

        Returns:
            合并后的搜索结果
        """
        all_products = []
        page = 1
        page_size = search_params.get('page_size', 50)  # 默认每页50条

        # 如果用户指定的page_size小于50，使用用户指定的值
        if 'page_size' in search_params and search_params['page_size'] < 50:
            page_size = search_params['page_size']
        else:
            # 否则使用最大值50来减少请求次数
            page_size = 50
            search_params['page_size'] = page_size

        print(f"🔍 自动分页查询中（目标: {total_count}条，每页: {page_size}条）...\n")

        while len(all_products) < total_count:
            # 计算本次需要查询的数量
            remaining = total_count - len(all_products)
            current_page_size = min(page_size, remaining)

            print(f"📄 正在查询第 {page} 页（已获取: {len(all_products)}/{total_count}）...")

            # 查询当前页
            result = self.search_competitors(
                keyword=keyword,
                product_id=product_id,
                page=page,
                page_size=current_page_size,
                phone=phone,
                password=password,
                **{k: v for k, v in search_params.items() if k not in ['page', 'page_size']}
            )

            # 检查是否成功
            if not result.get('success', True) or 'error' in result:
                print(f"❌ 第 {page} 页查询失败: {result.get('message', result.get('error', 'Unknown error'))}")
                break

            # 获取产品列表
            products = result.get('data', {}).get('list', [])

            if not products:
                print(f"✓ 第 {page} 页无数据，查询结束")
                break

            all_products.extend(products)
            print(f"✓ 第 {page} 页获取 {len(products)} 条数据")

            # 检查是否还有下一页
            has_next = result.get('data', {}).get('hasNext', False)
            if not has_next:
                print(f"✓ 已到最后一页，查询结束")
                break

            # 如果已经达到目标数量，停止查询
            if len(all_products) >= total_count:
                break

            page += 1

        # 截取到指定数量
        all_products = all_products[:total_count]

        print(f"\n✓ 分页查询完成！共获取 {len(all_products)} 条数据")

        # 构建合并后的结果
        merged_result = {
            'data': {
                'list': all_products,
                'page': 1,
                'pageSize': len(all_products),
                'hasNext': False,
                'total_pages': page
            },
            'success': True,
            'message': f'成功获取 {len(all_products)} 条数据（共 {page} 页）'
        }

        return merged_result

    def mock_search(self, **params) -> Dict:
        """
        模拟搜索（用于演示和测试，不需要登录）

        返回模拟的数据结构，格式与 a.json 相同
        """
        keyword = params.get('keyword', 'iphone')
        page = params.get('page', 1)
        page_size = params.get('pageSize', 10)

        # 模拟数据（与 a.json 结构相同）
        mock_data = {
            "data": {
                "list": [
                    {
                        "product_id": f"B0MOCK{i:04d}",
                        "title": f"Mock Product {i} for {keyword}",
                        "additional_offer_count": "Ȓ",
                        "number_of_reviews": "ȓ",
                        "sellers": [{
                            "display_name": "ȟȬȣȝ-ȟȲȪȬȟȭȭ",
                            "name": "ȭȽɁɍɃɉɂȻ ȣɂȷȐ",
                            "seller_rating": "ȘȔȐȖ",
                            "seller_reviews": "ȒȚȔȜȓȿ+"
                        }],
                        "sales_trends": [{
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
                        }],
                        "price": "$ȒȓȐȔȘ",
                        "rating": "ȗȐȔ"
                    }
                    for i in range(1, min(page_size + 1, 11))
                ],
                "total": 100,
                "page": page,
                "pageSize": page_size
            },
            "success": True,
            "message": "搜索成功（模拟数据）"
        }

        # 解码模拟数据
        if self.decoder:
            return self.decoder.decode_json(mock_data, decode_all=True)
        else:
            return mock_data


def format_product_info(product: Dict, index: int = 1) -> str:
    """
    格式化产品信息

    Args:
        product: 产品数据
        index: 序号

    Returns:
        格式化的字符串
    """
    lines = []
    lines.append(f"\n{'='*80}")
    lines.append(f"产品 #{index}: {product.get('product_id', 'N/A')}")
    lines.append(f"{'='*80}")
    lines.append(f"标题: {product.get('title', 'N/A')}")
    lines.append(f"价格: {product.get('price', 'N/A')}")
    lines.append(f"评分: {product.get('rating', 'N/A')}")
    lines.append(f"评论数: {product.get('number_of_reviews', 'N/A')}")
    lines.append(f"供应商数: {product.get('additional_offer_count', 'N/A')}")

    # 卖家信息
    if product.get('sellers'):
        seller = product['sellers'][0]
        lines.append(f"\n卖家信息:")
        lines.append(f"  名称: {seller.get('display_name', 'N/A')}")
        lines.append(f"  公司: {seller.get('name', 'N/A')}")
        lines.append(f"  评分: {seller.get('seller_rating', 'N/A')}")
        lines.append(f"  评论数: {seller.get('seller_reviews', 'N/A')}")

    # 销售数据
    if product.get('sales_trends'):
        trend = product['sales_trends'][0]
        lines.append(f"\n销售数据（最新）:")
        lines.append(f"  销售额: {trend['sales_amount'].get('label', 'N/A')}")
        lines.append(f"  销量: {trend['sales_volume'].get('label', 'N/A')}")
        lines.append(f"  月增长: {trend.get('month_sales_growth', 'N/A')}")
        lines.append(f"  毛利: {trend.get('gross_profit', 'N/A')}")
        lines.append(f"  毛利率: {trend.get('gross_profit_margin', 'N/A')}")

    return '\n'.join(lines)


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='沃师傅竞品搜索工具（自动登录）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 搜索（自动检查登录，需要时会提示登录）
  python3 wmtwin_search_competitors.py --keyword iphone

  # 提供手机号（自动加载已有登录）
  python3 wmtwin_search_competitors.py --keyword iphone --phone 15659922174

  # 完整参数（如未登录会自动引导登录）
  python3 wmtwin_search_competitors.py \
      --keyword iphone \
      --phone 15659922174 \
      --is-wfs \
      --min-sales 4000 \
      --max-sales 90000

  # 模拟模式（无需登录）
  python3 wmtwin_search_competitors.py --keyword iphone --mock
        """
    )

    parser.add_argument(
        '--keyword',
        help='搜索关键词（与 --product-id 互斥）'
    )
    parser.add_argument(
        '--product-id',
        help='产品 WID（与 --keyword 互斥，如果提供则忽略其他筛选参数）'
    )
    parser.add_argument(
        '--phone',
        help='手机号（用于加载/创建登录）'
    )
    parser.add_argument(
        '--password',
        help='密码（不推荐在命令行中使用，会提示输入）'
    )
    parser.add_argument(
        '--is-wfs',
        action='store_true',
        help='只搜索 WFS 商品'
    )
    parser.add_argument(
        '--min-sales',
        type=int,
        help='最小销量'
    )
    parser.add_argument(
        '--max-sales',
        type=int,
        help='最大销量'
    )
    parser.add_argument(
        '--min-sales-amount',
        type=int,
        help='最小销售额'
    )
    parser.add_argument(
        '--max-sales-amount',
        type=int,
        help='最大销售额'
    )
    parser.add_argument(
        '--min-reviews',
        type=int,
        help='最小评论数'
    )
    parser.add_argument(
        '--max-reviews',
        type=int,
        help='最大评论数'
    )
    parser.add_argument(
        '--min-rating',
        type=float,
        help='最低评分'
    )
    parser.add_argument(
        '--max-rating',
        type=float,
        help='最高评分'
    )
    parser.add_argument(
        '--min-price',
        type=float,
        help='最低价格'
    )
    parser.add_argument(
        '--max-price',
        type=float,
        help='最高价格'
    )
    parser.add_argument(
        '--seller-name',
        help='卖家名称'
    )
    parser.add_argument(
        '--brand',
        help='品牌'
    )
    parser.add_argument(
        '--page',
        type=int,
        default=1,
        help='页码（默认: 1）'
    )
    parser.add_argument(
        '--page-size',
        type=int,
        default=10,
        help='每页数量（默认: 10）'
    )
    parser.add_argument(
        '--from-json',
        metavar='FILE',
        help='从 JSON 文件读取搜索参数'
    )
    parser.add_argument(
        '-o', '--output',
        metavar='FILE',
        help='保存结果到文件'
    )
    parser.add_argument(
        '--mock',
        action='store_true',
        help='使用模拟模式（演示/测试用，无需登录）'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'text'],
        default='text',
        help='输出格式（默认: text）'
    )

    args = parser.parse_args()

    # 创建搜索客户端
    client = WMTwinCompetitorSearch(phone=args.phone)

    # 准备参数
    if args.from_json:
        # 从 JSON 文件读取
        with open(args.from_json, 'r', encoding='utf-8') as f:
            params = json.load(f)
    else:
        # 从命令行参数构建
        # product_id 和 keyword 互斥检查
        if args.product_id:
            params = {
                'product_id': args.product_id
            }
        else:
            if not args.keyword and not args.mock:
                parser.error('--keyword or --product-id is required (or use --mock)')

            params = {
                'keyword': args.keyword or 'iphone',
                'page': args.page,
                'pageSize': args.page_size,
            }

            if args.is_wfs:
                params['is_wfs'] = True

            if args.min_sales is not None:
                params['min_sales_volume'] = args.min_sales

            if args.max_sales is not None:
                params['max_sales_volume'] = args.max_sales

            if args.min_sales_amount is not None:
                params['min_sales_amount'] = args.min_sales_amount

            if args.max_sales_amount is not None:
                params['max_sales_amount'] = args.max_sales_amount

            if args.min_reviews is not None:
                params['min_number_of_reviews'] = args.min_reviews

            if args.max_reviews is not None:
                params['max_number_of_reviews'] = args.max_reviews

            if args.min_rating is not None:
                params['min_average_rating'] = args.min_rating

            if args.max_rating is not None:
                params['max_average_rating'] = args.max_rating

            if args.min_price is not None:
                params['min_price'] = args.min_price

            if args.max_price is not None:
                params['max_price'] = args.max_price

            if args.seller_name is not None:
                params['seller_name'] = args.seller_name

            if args.brand is not None:
                params['brand'] = args.brand

    # 执行搜索
    print(f"搜索参数: {json.dumps(params, ensure_ascii=False, indent=2)}\n")

    # 判断是否需要自动分页
    MAX_PAGE_SIZE = 50  # API单页最大限制
    requested_page_size = params.get('pageSize', 10)
    use_auto_paging = requested_page_size > MAX_PAGE_SIZE and params.get('page', 1) == 1

    if args.mock:
        print("⚠️  使用模拟模式（无需登录）\n")
        results = client.mock_search(**params)
        raw_results = results  # 模拟模式没有原始数据
    elif use_auto_paging:
        # 自动分页模式
        print(f"💡 检测到请求数量 ({requested_page_size}) 大于单页限制 ({MAX_PAGE_SIZE})，自动启用分页查询\n")

        # 准备搜索参数
        search_params = {k: v for k, v in params.items() if k not in ['keyword', 'product_id', 'page', 'pageSize']}

        # 获取原始结果（未解码）
        original_have_decoder = HAVE_DECODER
        globals()['HAVE_DECODER'] = False
        raw_results = client.search_multiple_pages(
            total_count=requested_page_size,
            keyword=params.get('keyword'),
            product_id=params.get('product_id'),
            phone=args.phone,
            password=args.password,
            **search_params
        )
        globals()['HAVE_DECODER'] = original_have_decoder

        # 检查是否成功
        if not raw_results.get('success', True):
            print(f"❌ 搜索失败: {raw_results.get('message', raw_results.get('error', 'Unknown error'))}")
            return

        # 保存原始文件（如果指定了输出文件）
        if args.output:
            raw_file = args.output.replace('.json', '_raw.json') if args.output.endswith('.json') else args.output + '_raw.json'
            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(raw_results, f, ensure_ascii=False, indent=2)
            print(f"✓ 原始数据已保存到: {raw_file}")

        # 解码数据
        if HAVE_DECODER:
            print("🔄 解码数据中...")
            results = decode_json(raw_results)
            print("✓ 数据解码完成")
        else:
            results = raw_results
            print("⚠️  解码器不可用，使用原始数据")
    else:
        # 单页查询模式
        print("🔍 搜索中...\n")

        # 获取原始结果（未解码）
        # 临时禁用解码，先获取原始数据
        original_have_decoder = HAVE_DECODER
        globals()['HAVE_DECODER'] = False
        raw_results = client.search_from_params(params, phone=args.phone, password=args.password)
        globals()['HAVE_DECODER'] = original_have_decoder

        # 检查是否成功
        if not raw_results.get('success', True):
            print(f"❌ 搜索失败: {raw_results.get('message', raw_results.get('error', 'Unknown error'))}")
            return

        # 保存原始文件（如果指定了输出文件）
        if args.output:
            raw_file = args.output.replace('.json', '_raw.json') if args.output.endswith('.json') else args.output + '_raw.json'
            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(raw_results, f, ensure_ascii=False, indent=2)
            print(f"✓ 原始数据已保存到: {raw_file}")

        # 解码数据
        if HAVE_DECODER:
            print("🔄 解码数据中...")
            results = decode_json(raw_results)
            print("✓ 数据解码完成")
        else:
            results = raw_results
            print("⚠️  解码器不可用，使用原始数据")

    # 处理解码后的结果
    if not results.get('success', True):
        print(f"❌ 处理失败: {results.get('message', results.get('error', 'Unknown error'))}")
        return

    # 输出结果
    if args.format == 'json':
        # JSON 格式
        output = json.dumps(results, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✓ 解码后的数据已保存到: {args.output}")
        else:
            print(output)
    else:
        # 文本格式
        data = results.get('data', {})
        products = data.get('list', [])
        total = data.get('total', 0)
        page = data.get('page', 1)
        page_size = data.get('pageSize', 10)

        print(f"✓ 搜索成功")
        print(f"  总结果数: {total}")
        print(f"  当前页: {page}")
        print(f"  每页数量: {page_size}")
        print(f"  返回产品数: {len(products)}")

        # 显示产品列表
        for i, product in enumerate(products, 1):
            print(format_product_info(product, i))

        # 保存到文件
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n✓ 解码后的完整结果已保存到: {args.output}")


if __name__ == '__main__':
    main()
