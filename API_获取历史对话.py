"""
调用API回答问题
"""
import requests
from dateutil.parser import parse
from datetime import datetime
import pandas as pd

# API配置
url = "https://agent-x-pre.maas.com.cn/v1/conversations"
headers = {
    "Authorization": "Bearer app-SNoEbaibC7p0LHKMpJx2WX5f"  # 替换为实际的API密钥
}
params = {
    "user": "zhenyu",  # 用户标识，需保证在应用内唯一
    "limit": 20        # 每次请求返回的记录数
}

def run(url, headers, params):
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


def main():
    result = run(url, headers, params)
    # 将JSON数据转换为DataFrame
    df = pd.DataFrame(result)
    # 将'created_at'列转换为datetime类型
    df['created_at'] = pd.to_datetime(df['created_at'])     
    # 保存DataFrame到Excel文件
    df.to_excel('./result/conversations.xlsx', index=False)
    print("数据已成功保存到 'conversations.xlsx' 文件中。")

if __name__ == "__main__":
    main()
