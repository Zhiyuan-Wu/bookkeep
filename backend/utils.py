"""
工具函数
"""

import hashlib
import json
from typing import Dict, Any, Optional
from backend.config import TAX_RATE


def hash_password(password: str) -> str:
    """
    对密码进行哈希处理
    
    Args:
        password: 原始密码
        
    Returns:
        str: 哈希后的密码
        
    使用样例:
        hashed = hash_password("mypassword")
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """
    验证密码
    
    Args:
        password: 原始密码
        password_hash: 哈希后的密码
        
    Returns:
        bool: 密码是否正确
        
    使用样例:
        if verify_password("mypassword", stored_hash):
            print("密码正确")
    """
    return hash_password(password) == password_hash


def parse_order_content(content: str) -> list:
    """
    解析订单内容JSON字符串
    
    Args:
        content: JSON字符串
        
    Returns:
        list: 订单项列表
        
    使用样例:
        items = parse_order_content('{"items": [...]}')
    """
    try:
        data = json.loads(content)
        return data.get("items", [])
    except (json.JSONDecodeError, AttributeError):
        return []


def format_order_content(items: list) -> str:
    """
    将订单项列表格式化为JSON字符串
    
    Args:
        items: 订单项列表
        
    Returns:
        str: JSON字符串
        
    使用样例:
        content = format_order_content([{"product_id": 1, "quantity": 2}])
    """
    return json.dumps({"items": items}, ensure_ascii=False)


def calculate_order_totals(items: list, include_internal: bool = True) -> Dict[str, float]:
    """
    计算订单总价
    
    Args:
        items: 订单项列表
        include_internal: 是否包含内部价格
        
    Returns:
        dict: 包含总内部价格和总含税价格的字典
        
    使用样例:
        totals = calculate_order_totals(items, include_internal=True)
        print(totals["total_internal_price"])
    """
    total_internal = 0.0
    total_tax_included = 0.0
    
    for item in items:
        if isinstance(item, dict):
            muted = item.get("muted", False)
            if muted:
                continue
            quantity = item.get("quantity", 1)
            if include_internal and "internal_price" in item:
                total_internal += (item.get("internal_price", 0) or 0) * quantity
            total_tax_included += item.get("tax_included_price", 0) * quantity
    
    return {
        "total_internal_price": total_internal,
        "total_tax_included_price": total_tax_included
    }


def calculate_tax(total_tax_included: float, total_internal: float) -> float:
    """
    计算税额
    
    Args:
        total_tax_included: 总含税价格
        total_internal: 总内部价格
        
    Returns:
        float: 税额
        
    使用样例:
        tax = calculate_tax(1000, 800)
    """
    return (total_tax_included - total_internal) * TAX_RATE


def remove_internal_price_from_items(items: list) -> list:
    """
    从订单项列表中移除内部价格字段（用于厂家用户）
    
    Args:
        items: 订单项列表
        
    Returns:
        list: 移除内部价格后的订单项列表
        
    使用样例:
        safe_items = remove_internal_price_from_items(items)
    """
    result = []
    for item in items:
        if isinstance(item, dict):
            safe_item = {k: v for k, v in item.items() if k != "internal_price"}
            result.append(safe_item)
        else:
            result.append(item)
    return result

