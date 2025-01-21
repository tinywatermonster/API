"""
调用API回答问题
"""
# pip3 install
from openai import OpenAI
import requests, json
import pandas as pd
from tqdm import tqdm
import uuid
import time
import concurrent.futures
import os

# API配置字典
API_CONFIG = {
    "prod": {
        "url": "https://agent-x.maas.com.cn/v1/chat-messages",
        "key": "app-nt84vDhBIhbuWOP0PyYf2FUe",
        "name": "v1.2.0正式版"
    },
    "test": {
        "url": "https://agent-x.maas.com.cn/v1/chat-messages",
        "key": "app-bCdFnfBfNkyn92G857CHK3zJ",
        "name": "测试环境"
    },
    "emotion": {
        "url": "https://agent-x-pre.maas.com.cn/v1/chat-messages",
        "key": "app-lIvakAaUAKcdKtfKrfadbk8H", 
        "name": "情感支持｜v2.4.1｜适配降本提速框架建议"
    },
    "emotionPrd": {
        "url": "https://agent-x.maas.com.cn/v1/chat-messages",
        "key": "app-klj8zDjwYcKxUWkY7HqD00ro", # 
        "name": "0117 情感支持 | v1.5.0"
    }
}

# 选择要使用的环境
current_env = "emotion"
app_url = API_CONFIG[current_env]["url"]
api_key = API_CONFIG[current_env]["key"]

# 前缀，可随意指定，建议按照日期
chatId = time.strftime("%m%d_")

headers = {
    "Authorization": f"Bearer {api_key}", 
    'Content-Type': 'application/json',
}

stop_node_set = set([""])

def run(question, conversation_id="", stream=False):
    url = app_url 
    data = {
        "inputs": {},
        "query": question,
        "response_mode": "streaming",
        "conversation_id": conversation_id,
        "user": "zhenyu", # 多轮问答约束条件：conversation_id+user 用户ID必须要一致。
        "files": []
    }
    if stream:
        paths = []
        res = []
        data["response_mode"] = "streaming"
        response = requests.post(url, json=data, headers=headers, stream=True)
        # 检查响应状态码是否为200
        if response.status_code == 200:
            # 遍历响应体中的每一行
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    # 去除行开头的'data:'，然后解析JSON数据
                    # print(line)
                    chunk = line[6:]
                    try:
                        event_data = json.loads(chunk)
                    except:
                        continue

                    # 输出完成之后再把结果保存在event中
                    if event_data['event'] == "workflow_finished":
                        # print(event_data)
                        res.append(event_data['data']['outputs']['answer'])
                        c_id = event_data['conversation_id']
            # "\n".join(res) 是一个字符串方法，它的作用是：将列表 res 中的所有元素（通常是字符串）连接成一个单独的字符串
            return "\n".join(res), c_id
        else:
            print(f"请求失败，状态码：{response.status_code}")
            return "error", " ", 99999
    else:
        data["response_mode"] = "blocking"
        response = requests.post(url, json=data, headers=headers)
        # 检查响应状态码是否为200
        if response.status_code == 200:
            return response.json()['answer'], ""
        else:
            return "error", ""

def process_excel(excel_path, sheet_name, col_name,file_name):
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    # # 随机采样
    # if sheet_name == "抽样":
    #     df = df[~df['问题'].isna()]
    #     # 按比例随机采样
    #     df = df.sample(frac=0.02, random_state=42)
    #     # 按数量随机采样
    #     df = df.sample(10, random_state=42)
    questions = df[col_name].to_list()
    flag = df['多轮'].to_list()
    last_flag = ''
    answers = []
    c_id = ""

    # 使用单线程处理问题
    for idx, question in tqdm(enumerate(questions), total=len(questions)):
        try:
            # 获取当前行的flag值
            cur_flag = flag[idx]
            # 判断是否为新的对话轮次
            is_new_conversation = pd.isna(cur_flag) or last_flag != cur_flag
            
            if is_new_conversation:
                answer, c_id = run(question, stream=True)
                last_flag = cur_flag
            else:
                answer, _ = run(question, conversation_id=c_id, stream=True)
            answers.append(answer)
        except Exception as exc:
            print(f'{question} 生成了一个异常: {exc}')
            answers.append("错误: 处理失败")

    # 将答案存入新的列中
    df['v1.2.0'] = answers
    # 确保result文件夹存在
    os.makedirs('result', exist_ok=True)
    # 将结果保存在result文件夹下
    df.to_excel(f'result/{file_name}_{chatId}_result.xlsx', index=False)

def main():
    file_name = '情感支持QA测试用例'
    # excel文件夹路径
    excel_path = f'./{file_name}.xlsx'
    # 获取excel文件中的所有sheet名称
    sheet_list = pd.ExcelFile(excel_path).sheet_names
    col_name = '问题'
    process_excel(excel_path, sheet_list[0], col_name, file_name)

if __name__ == "__main__":
    print(os.getcwd())
    main()
