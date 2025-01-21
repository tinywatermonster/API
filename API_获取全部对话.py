"""
调用API回答问题
"""
import requests
from dateutil.parser import parse
from datetime import datetime
import pandas as pd
from tqdm import tqdm

# API配置
url_conv = "https://agent-x.maas.com.cn/v1/conversations"
url_mes = "https://agent-x.maas.com.cn/v1/messages"
headers = {
    "Authorization": "Bearer app-klj8zDjwYcKxUWkY7HqD00ro"  # 替换为实际的API密钥
}

# 参数配置
user = "big"
limit = 20
conversation_id = ''

def get_conversations(url, headers, params):
    all_conversations = []
    has_more = True

    # 发送请求并处理分页
    while has_more:
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # 检查请求是否成功

            data = response.json()
            for conv in data["data"]:
               # 假设 created_at 是Unix时间戳，转换为datetime对象
                created_at_timestamp = conv["created_at"]
                conv["created_at"] = datetime.fromtimestamp(created_at_timestamp)
                if conv["status"] != "normal":
                    print(f"警告：会话 {conv['id']} 状态异常，状态为 {conv['status']}")

            all_conversations.extend(data["data"])
            has_more = data["has_more"]

            if has_more and data["data"]:
                params["last_id"] = data["data"][-1]["id"]  # 更新last_id以获取下一页

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP错误发生: {http_err}")
            break
        except requests.exceptions.RequestException as err:
            print(f"请求错误发生: {err}")
            break
        except ValueError as json_err:
            print(f"JSON解析错误: {json_err}")
            break
    
    return all_conversations

def get_messages(url, headers, params):
    # 发送初始请求
    response = requests.get(url=url, headers=headers, params=params)
    response.raise_for_status()  # 检查请求是否成功
    data = response.json()
    data_list = data['data']
    query_list = []
    answer_list = []
    index_list = []
    create_list = []
    for index, item in enumerate(data_list):
        query_list.append(item['query'])
        answer_list.append(item['answer'])
        index_list.append(index)
        # 转换时间戳
        # created_at_timestamp = item["created_at"]
        item["created_at"] = datetime.fromtimestamp(item["created_at"])
        create_list.append(item['created_at'])
    return index_list, query_list, answer_list, create_list

def main():
    params_conv = {
    "user": user,  # 用户标识，需保证在应用内唯一
    "limit": limit        # 每次请求返回的记录数
    }
    all_conversations = get_conversations(url_conv, headers, params_conv)
    conv_ids = [conv['id'] for conv in all_conversations]
    # print(conv_ids)
    
    index_list = []
    query_list = []
    answer_list = []
    create_list = []
    # 循环开始取对话记录
    for conversation_id in tqdm(conv_ids, desc="Processing conversations"):
        params_mes = {
            'user': user,  # 替换为你的用户标识
            'conversation_id': conversation_id,  # 替换为你的会话ID
            'limit': limit  # 每页请求的记录数
        }
        index, query, answer, create = get_messages(url_mes, headers, params_mes)
        index_list.extend(index)
        query_list.extend(query)
        answer_list.extend(answer)
        create_list.extend(create)
        
    df = pd.DataFrame({
        "序号": index_list,
        "问题": query_list,
        "答案": answer_list,
        "创建时间": create_list
    })
    # 保存DataFrame到Excel文件
    df.to_excel('./result/conversations.xlsx', index=False)

if __name__ == "__main__":
    main()

