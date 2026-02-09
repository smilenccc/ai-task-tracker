#!/usr/bin/env python3
"""
Android WebSocket 整合測試腳本
用於驗證 ws://157.180.126.133:8200/chat 連線
"""

import asyncio
import websockets
import json
import sys


async def test_websocket():
    """測試 WebSocket 連線和訊息交換"""
    uri = "ws://157.180.126.133:8200/chat"
    
    print("🧪 OpenClaw WebSocket 測試")
    print("=" * 60)
    print(f"📡 連接到: {uri}\n")
    
    try:
        async with websockets.connect(uri, timeout=10) as websocket:
            print("✅ WebSocket 連線成功！\n")
            
            # 發送測試訊息
            test_message = {
                "type": "message",
                "content": "你好！這是測試訊息，請簡短回覆。"
            }
            
            print(f"📤 發送測試訊息:")
            print(f"   {json.dumps(test_message, ensure_ascii=False)}\n")
            
            await websocket.send(json.dumps(test_message))
            
            print("⏳ 等待回覆...\n")
            
            # 接收回覆
            message_count = 0
            got_reply = False
            
            while message_count < 10:
                try:
                    response = await asyncio.wait_for(
                        websocket.recv(), 
                        timeout=30.0
                    )
                    
                    message_count += 1
                    data = json.loads(response)
                    msg_type = data.get('type', 'unknown')
                    
                    print(f"📥 訊息 #{message_count} [類型: {msg_type}]")
                    
                    if data.get('content'):
                        content = data['content']
                        # 限制顯示長度
                        if len(content) > 200:
                            content = content[:200] + "..."
                        print(f"   內容: {content}")
                    
                    if data.get('error'):
                        print(f"   ⚠️ 錯誤: {data['error']}")
                    
                    print()
                    
                    # 收到 AI 回覆
                    if msg_type == 'reply' and message_count > 1:
                        print("=" * 60)
                        print("🎉 測試成功！收到 OpenClaw 回覆！")
                        print("=" * 60)
                        got_reply = True
                        break
                
                except asyncio.TimeoutError:
                    print("⏱️ 30秒超時，未收到更多訊息")
                    break
            
            if not got_reply:
                print("=" * 60)
                print("❌ 測試失敗：沒有收到 AI 回覆")
                print(f"   共收到 {message_count} 則訊息")
                print("=" * 60)
                sys.exit(1)
    
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket 錯誤: {e}")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ 未預期的錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("\n")
    asyncio.run(test_websocket())
    print("\n")
