#!/usr/bin/env python3
"""测试API key是否有效"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from openai import OpenAI
from utils.config import API_KEY, API_BASE_URL

def test_api_key():
    """测试API key是否有效"""
    print("=" * 80)
    print("🔑 API Key 测试")
    print("=" * 80)
    print(f"API_BASE_URL: {API_BASE_URL}")
    print(f"API_KEY: {API_KEY[:20]}...{API_KEY[-10:]}")
    print("=" * 80)
    
    try:
        client = OpenAI(
            api_key=API_KEY,
            base_url=API_BASE_URL
        )
        
        print("\n📡 发送测试请求...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Hello! Please reply with 'OK' if you receive this message."}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        print("\n✅ API调用成功！")
        print(f"📨 响应: {response.choices[0].message.content}")
        print(f"💰 Token使用: {response.usage.total_tokens} tokens")
        print("\n" + "=" * 80)
        print("✅ API Key 有效且有余额！")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n❌ API调用失败！")
        print(f"错误信息: {str(e)}")
        print("\n" + "=" * 80)
        print("❌ API Key 可能无效或没有余额！")
        print("=" * 80)
        
        # 尝试解析错误信息
        error_str = str(e).lower()
        if "insufficient" in error_str or "quota" in error_str or "balance" in error_str:
            print("\n💡 提示: 看起来是余额不足的问题")
        elif "invalid" in error_str or "unauthorized" in error_str:
            print("\n💡 提示: 看起来是API Key无效或未授权")
        elif "timeout" in error_str or "connection" in error_str:
            print("\n💡 提示: 看起来是网络连接问题")
        
        return False

if __name__ == "__main__":
    test_api_key()

