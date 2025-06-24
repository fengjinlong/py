import itchat
import time
import random
from itchat.content import *


# 登录微信
itchat.auto_login(hotReload=True)

# 设置目标好友的信息（可以使用备注名、昵称或微信号）
TARGET_FRIEND_NAME = "张广朋"  # 替换为你想聊天的好友名称

# 找到特定好友
def get_target_friend():
    # 尝试通过备注名查找
    friends = itchat.search_friends(remarkName=TARGET_FRIEND_NAME)
    if not friends:
        # 如果备注名没找到，尝试通过昵称查找
        friends = itchat.search_friends(nickName=TARGET_FRIEND_NAME)
    
    if friends:
        return friends[0]['UserName']
    else:
        print(f"未找到名为 {TARGET_FRIEND_NAME} 的好友")
        return None

# 获取目标好友的UserName
target_friend_username = get_target_friend()

# 一些回复内容
chat_responses = {
    "你好": ["你好啊！", "Hello！", "你好，最近怎么样？"],
    "在吗": ["在的，有什么事吗？", "我在呢，找我有事？", "嗯，我在的"],
    "忙吗": ["不忙，有什么事？", "还好，你呢？", "刚忙完，正好空闲"],
    "吃了吗": ["还没呢，你呢？", "刚吃完，你呢？", "准备去吃，你要一起吗？"],
}

# 通用回复（当没有匹配到关键词时使用）
default_responses = [
    "嗯，我在听",
    "继续说...",
    "有意思，然后呢？",
    "好的，我明白了",
    "哈哈，真有趣"
]

# 主动发起聊天的消息
initial_messages = [
    "嘿，在干嘛呢？",
    "今天过得怎么样？",
    "有空聊聊天吗？",
    "最近好吗？",
    "有什么新鲜事？"
]

# 注册文本消息处理函数
@itchat.msg_register([TEXT])
def reply_to_specific_friend(msg):
    # 只处理来自目标好友的消息
    if msg['FromUserName'] == target_friend_username:
        print(f"收到 {TARGET_FRIEND_NAME} 的消息: {msg['Text']}")
        
        # 根据关键词选择回复
        for keyword, responses in chat_responses.items():
            if keyword in msg['Text']:
                reply = random.choice(responses)
                time.sleep(random.uniform(1, 3))  # 随机延迟，模拟真人
                return reply
        
        # 如果没有匹配的关键词，使用默认回复
        reply = random.choice(default_responses)
        time.sleep(random.uniform(1, 3))
        return reply

# 主动发起聊天功能
def initiate_chat():
    if target_friend_username:
        message = random.choice(initial_messages)
        print(f"向 {TARGET_FRIEND_NAME} 发送消息: {message}")
        itchat.send(message, target_friend_username)

# 启动脚本
if __name__ == '__main__':
    if target_friend_username:
        print(f"已找到目标好友: {TARGET_FRIEND_NAME}")
        print("是否要主动发起聊天? (y/n)")
        choice = input().strip().lower()
        if choice == 'y':
            initiate_chat()
        
        print("自动聊天脚本运行中，按Ctrl+C停止")
        try:
            itchat.run()
        except KeyboardInterrupt:
            print("脚本已停止")
            itchat.logout()
    else:
        print("未能找到目标好友，脚本退出")
