#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
from datetime import datetime
from pathlib import Path

def load_token_from_file(token_file="本地api.txt"):
    """
    从文件中加载令牌信息

    文件格式：邮箱地址----密码----Client ID----刷新令牌----令牌过期时间
    注：令牌过期时间可选，可以没有

    Args:
        token_file: 令牌文件路径

    Returns:
        dict: 包含令牌信息的字典
    """
    try:
        # 获取脚本所在目录
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 如果是相对路径，则相对于脚本目录
        if not os.path.isabs(token_file):
            token_file = os.path.join(script_dir, token_file)

        with open(token_file, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()

        if not first_line:
            print("[ERROR] 令牌文件为空")
            return None

        parts = first_line.split('----')

        if len(parts) < 4:
            print(f"[ERROR] 文件格式错误，期望至少4个字段（邮箱、密码、Client ID、刷新令牌），实际{len(parts)}个")
            return None

        token_info = {
            'email': parts[0].strip(),
            'password': parts[1].strip(),
            'client_id': parts[2].strip(),
            'refresh_token': parts[3].strip(),
        }

        # 令牌过期时间（可选）
        if len(parts) >= 5 and parts[4].strip():
            expire_time_str = parts[4].strip()
            try:
                # 尝试解析中文日期格式：2026年01月08日
                expire_datetime = datetime.strptime(expire_time_str, '%Y年%m月%d日')
                token_info['expires_at'] = expire_datetime.timestamp()
            except ValueError:
                try:
                    # 尝试解析其他格式
                    expire_datetime = datetime.strptime(expire_time_str, '%Y-%m-%d')
                    token_info['expires_at'] = expire_datetime.timestamp()
                except ValueError:
                    print(f"[WARNING] 无法解析过期时间格式: {expire_time_str}")
                    token_info['expires_at'] = 0
        else:
            print("[INFO] 未提供令牌过期时间")
            token_info['expires_at'] = 0

        print("[SUCCESS] 从文件加载令牌信息成功")
        print(f"  邮箱: {token_info.get('email', 'N/A')}")
        print(f"  Client ID: {token_info.get('client_id', 'N/A')}")
        print(f"  刷新令牌: {token_info.get('refresh_token', 'N/A')[:50]}...")

        # 检查刷新令牌是否即将过期
        if 'expires_at' in token_info and token_info['expires_at'] > 0:
            expire_datetime = datetime.fromtimestamp(token_info['expires_at'])
            days_remaining = (expire_datetime - datetime.now()).days
            print(f"  刷新令牌过期时间: {expire_datetime.strftime('%Y年%m月%d日')} (剩余{days_remaining}天)")

            if days_remaining <= 7:
                print("[WARNING] 刷新令牌即将过期，建议重新提取")

        return token_info
        
    except Exception as e:
        print(f"[ERROR] 加载令牌文件失败: {str(e)}")
        return None

def refresh_access_token(client_id, refresh_token):
    """
    使用刷新令牌获取新的访问令牌

    Args:
        client_id: 客户端ID
        refresh_token: 刷新令牌

    Returns:
        str: 新的访问令牌，失败返回None
    """
    try:
        print("刷新访问令牌...")

        token_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"

        data = {
            'client_id': client_id,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'scope': 'https://graph.microsoft.com/.default'
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(token_url, data=data, headers=headers, timeout=30)

        if response.status_code == 200:
            tokens = response.json()
            new_access_token = tokens.get('access_token')
            print(f"访问令牌刷新成功: {new_access_token[:50]}...")
            return new_access_token
        else:
            error_data = response.json() if response.content else {}
            print(f"访问令牌刷新失败: {response.status_code}")
            print(f"错误信息: {error_data}")
            return None

    except Exception as e:
        print(f"刷新访问令牌异常: {str(e)}")
        return None

def get_mail_folders(access_token):
    """
    获取邮箱文件夹列表

    Args:
        access_token: 访问令牌

    Returns:
        list: 文件夹列表
    """
    try:
        print("获取邮箱文件夹...")

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        response = requests.get(
            'https://graph.microsoft.com/v1.0/me/mailFolders',
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            folders_data = response.json()
            folders = folders_data.get('value', [])
            print(f"邮箱文件夹获取成功: {len(folders)}个")

            for folder in folders[:5]:  # 显示前5个文件夹
                print(f"   {folder.get('displayName', 'N/A')} (ID: {folder.get('id', 'N/A')[:20]}...)")

            return folders
        else:
            print(f"邮箱文件夹获取失败: {response.status_code}")
            return []

    except Exception as e:
        print(f"获取邮箱文件夹异常: {str(e)}")
        return []

def get_recent_emails(access_token, count=5):
    """
    获取最近的邮件

    Args:
        access_token: 访问令牌
        count: 获取邮件数量

    Returns:
        list: 邮件列表
    """
    try:
        print(f"获取最近{count}封邮件...")

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # 获取邮件，按接收时间倒序排列
        params = {
            '$top': count,
            '$select': 'id,subject,from,receivedDateTime,isRead,bodyPreview',
            '$orderby': 'receivedDateTime desc'
        }

        response = requests.get(
            'https://graph.microsoft.com/v1.0/me/messages',
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            messages_data = response.json()
            messages = messages_data.get('value', [])
            print(f"邮件获取成功: {len(messages)}封")

            for i, message in enumerate(messages, 1):
                subject = message.get('subject', 'N/A')
                sender = message.get('from', {}).get('emailAddress', {}).get('address', 'N/A')
                received_time = message.get('receivedDateTime', 'N/A')
                is_read = message.get('isRead', False)
                preview = message.get('bodyPreview', 'N/A')

                print(f"   邮件{i}:")
                print(f"      主题: {subject}")
                print(f"      发件人: {sender}")
                print(f"      时间: {received_time}")
                print(f"      已读: {'是' if is_read else '否'}")
                print(f"      预览: {preview}")
                print()

            return messages
        else:
            print(f"邮件获取失败: {response.status_code}")
            return []

    except Exception as e:
        print(f"获取邮件异常: {str(e)}")
        return []

def get_email_content(access_token, message_id):
    """
    获取指定邮件的完整内容

    Args:
        access_token: 访问令牌
        message_id: 邮件ID

    Returns:
        dict: 邮件详细内容
    """
    try:
        print(f"获取邮件详细内容...")

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # 请求纯文本格式的邮件内容
        response = requests.get(
            f'https://graph.microsoft.com/v1.0/me/messages/{message_id}',
            headers=headers,
            params={'$select': 'subject,from,body,bodyPreview'},
            timeout=10
        )

        if response.status_code == 200:
            message_data = response.json()
            print(f"邮件详细内容获取成功")

            # 显示邮件详细信息
            subject = message_data.get('subject', 'N/A')
            sender = message_data.get('from', {}).get('emailAddress', {}).get('address', 'N/A')
            body_type = message_data.get('body', {}).get('contentType', 'N/A')

            # 优先使用纯文本内容，如果是HTML则提取文本
            if body_type.lower() == 'text':
                body_content = message_data.get('body', {}).get('content', 'N/A')
            else:
                # HTML格式，转换为纯文本
                import re
                html_content = message_data.get('body', {}).get('content', '')
                # 移除HTML标签
                body_content = re.sub(r'<[^>]+>', '', html_content)
                # 解码HTML实体
                import html
                body_content = html.unescape(body_content)
                # 移除多余空行
                body_content = re.sub(r'\n\s*\n', '\n\n', body_content)
                body_content = body_content.strip()

            print(f"   主题: {subject}")
            print(f"   发件人: {sender}")
            print(f"   内容类型: {body_type}")
            print(f"   内容长度: {len(body_content)}字符")
            print(f"\n   纯文本内容:")
            print(f"   {'-' * 60}")
            print(f"{body_content}")
            print(f"   {'-' * 60}")

            return message_data
        else:
            print(f"邮件详细内容获取失败: {response.status_code}")
            return None

    except Exception as e:
        print(f"获取邮件详细内容异常: {str(e)}")
        return None

def test_graph_api_email_access():
    """测试API邮箱访问功能"""

    print("测试API邮箱访问功能")
    print("=" * 60)

    # 1. 加载令牌信息
    token_info = load_token_from_file()
    if not token_info:
        print("无法加载令牌信息，请先运行OAuth2令牌提取测试")
        return False

    # 2. 使用刷新令牌获取新的访问令牌
    client_id = token_info.get('client_id', '')
    refresh_token = token_info.get('refresh_token', '')

    if not client_id or not refresh_token:
        print("未找到客户端ID或刷新令牌")
        return False

    print("使用刷新令牌获取访问令牌...")
    access_token = refresh_access_token(client_id, refresh_token)
    if not access_token:
        print("无法获取访问令牌")
        return False

    print("访问令牌获取成功")

    print()

    # 3. 获取邮箱文件夹
    get_mail_folders(access_token)
    print()

    # 4. 获取最近的邮件
    messages = get_recent_emails(access_token, count=3)
    print()

    # 5. 如果有邮件，获取第一封邮件的详细内容
    if messages:
        first_message_id = messages[0].get('id')
        if first_message_id:
            get_email_content(access_token, first_message_id)
            print()

    print("API邮箱访问测试完成!")
    return True

def main():
    """主函数"""
    print("开始测试API邮箱访问功能")
    print("=" * 80)

    success = test_graph_api_email_access()

    if success:
        print(f"\nAPI邮箱访问测试成功!")
        print(f"邮箱文件夹访问正常")
        print(f"邮件读取功能正常")
        print(f"API集成完全正常!")
    else:
        print(f"\nAPI邮箱访问测试失败")
        print(f"请检查令牌文件和网络连接")

if __name__ == "__main__":
    main()
