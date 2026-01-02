"""
邮件发送工具
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Optional, List
from backend.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    SMTP_FROM_EMAIL, SMTP_FROM_NAME, SMTP_USE_TLS
)
from backend.logger import get_logger

logger = get_logger(__name__)


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    发送邮件
    
    Args:
        to_email: 收件人邮箱
        subject: 邮件主题
        html_content: HTML格式的邮件内容
        text_content: 纯文本格式的邮件内容（可选）
        
    Returns:
        bool: 是否发送成功
        
    使用样例:
        send_email(
            "user@example.com",
            "订单通知",
            "<h1>您的订单已确认</h1>"
        )
    """
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("邮件服务器未配置，跳过邮件发送")
        return False
    
    try:
        # 创建邮件对象
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')
        
        # 添加文本内容
        if text_content:
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(text_part)
        
        # 添加HTML内容
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 连接SMTP服务器并发送
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        
        logger.info(f"邮件发送成功: {to_email}, 主题: {subject}")
        return True
        
    except Exception as e:
        if "\\x00\\x00\\x00" not in str(e):
            logger.error(f"邮件发送失败: {e}", exc_info=True)
            return False
        return True


def send_order_notification(
    to_email: str,
    to_name: str,
    order_id: int,
    order_status: str,
    supplier_name: Optional[str] = None,
    order_summary: Optional[str] = None
) -> bool:
    """
    发送订单通知邮件
    
    Args:
        to_email: 收件人邮箱
        to_name: 收件人名称
        order_id: 订单ID
        order_status: 订单状态
        supplier_name: 厂家名称（可选）
        order_summary: 订单摘要（可选）
        
    Returns:
        bool: 是否发送成功
    """
    status_text = {
        "暂存": "已创建",
        "发起": "已发起",
        "确认": "已确认",
        "无效": "已标记为无效"
    }.get(order_status, order_status)
    
    subject = f"订单通知 - 订单 #{order_id} {status_text}"
    
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #4472C4;">订单通知</h2>
            <p>尊敬的 {to_name}，</p>
            <p>您的订单状态已更新：</p>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>订单编号：</strong>#{order_id}</p>
                <p><strong>订单状态：</strong>{status_text}</p>
                {f'<p><strong>厂家：</strong>{supplier_name}</p>' if supplier_name else ''}
                {f'<p><strong>订单摘要：</strong>{order_summary}</p>' if order_summary else ''}
            </div>
            <p>请登录系统查看订单详情。</p>
            <p>此邮件由系统自动发送，请勿回复。</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">报价及记账系统</p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
订单通知

尊敬的 {to_name}，

您的订单状态已更新：

订单编号：#{order_id}
订单状态：{status_text}
{f'厂家：{supplier_name}' if supplier_name else ''}
{f'订单摘要：{order_summary}' if order_summary else ''}

请登录系统查看订单详情。

此邮件由系统自动发送，请勿回复。

报价及记账系统
    """
    
    return send_email(to_email, subject, html_content, text_content)


def send_service_notification(
    to_email: str,
    to_name: str,
    service_id: int,
    service_status: str,
    supplier_name: Optional[str] = None,
    service_content: Optional[str] = None,
    service_amount: Optional[float] = None
) -> bool:
    """
    发送服务记录通知邮件
    
    Args:
        to_email: 收件人邮箱
        to_name: 收件人名称
        service_id: 服务记录ID
        service_status: 服务状态
        supplier_name: 厂家名称（可选）
        service_content: 服务内容（可选）
        service_amount: 服务金额（可选）
        
    Returns:
        bool: 是否发送成功
    """
    status_text = {
        "暂存": "已创建",
        "发起": "已发起",
        "确认": "已确认",
        "无效": "已标记为无效"
    }.get(service_status, service_status)
    
    subject = f"服务记录通知 - 服务记录 #{service_id} {status_text}"
    
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #4472C4;">服务记录通知</h2>
            <p>尊敬的 {to_name}，</p>
            <p>服务记录状态已更新：</p>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>服务记录编号：</strong>#{service_id}</p>
                <p><strong>服务状态：</strong>{status_text}</p>
                {f'<p><strong>厂家：</strong>{supplier_name}</p>' if supplier_name else ''}
                {f'<p><strong>服务内容：</strong>{service_content}</p>' if service_content else ''}
                {f'<p><strong>服务金额：</strong>¥{service_amount:.2f}</p>' if service_amount is not None else ''}
            </div>
            <p>请登录系统查看服务记录详情。</p>
            <p>此邮件由系统自动发送，请勿回复。</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">报价及记账系统</p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
服务记录通知

尊敬的 {to_name}，

服务记录状态已更新：

服务记录编号：#{service_id}
服务状态：{status_text}
{f'厂家：{supplier_name}' if supplier_name else ''}
{f'服务内容：{service_content}' if service_content else ''}
{f'服务金额：¥{service_amount:.2f}' if service_amount is not None else ''}

请登录系统查看服务记录详情。

此邮件由系统自动发送，请勿回复。

报价及记账系统
    """
    
    return send_email(to_email, subject, html_content, text_content)

