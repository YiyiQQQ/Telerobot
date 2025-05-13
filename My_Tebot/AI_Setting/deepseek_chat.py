#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
import sys
import os
import httpx
from openai import OpenAI, APIConnectionError, APIError, AuthenticationError
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.configration import Config


class DeepSeekChat:
    def __init__(self, conf: dict) -> None:
        self.api_key = conf.get("api_key")
        self.api_url = conf.get("api_url")
        self.model = conf.get("model", "deepseek-chat")
        self.proxy = conf.get("proxy")
        self.prompt = conf.get("prompt", "")

        self.max_tokens = conf.get("max_tokens", 4096)
        self.temperature = conf.get("temperature", 1.0)
        self.top_p = conf.get("top_p", 1.0)
        self.presence_penalty = conf.get("presence_penalty", 0.0)
        self.frequency_penalty = conf.get("frequency_penalty", 0.0)
        self.reasoning_effort = conf.get("reasoning_effort", None)

        self.reasoning_enabled = conf.get("enable_reasoning", False) and (self.model == "deepseek-reasoner")
        self.reasoning_visible = conf.get("show_reasoning", False) and self.reasoning_enabled

        # 禁止使用不支持的参数
        for banned_param in ["logprobs", "top_logprobs"]:
            if banned_param in conf:
                raise ValueError(f"❌ 配置中含有不被支持的参数：{banned_param}")

        self.LOG = logging.getLogger("DeepSeekChat")
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_url)

        self.system_prompt = {"role": "system", "content": self.prompt}

        self.conversations = {}

    def __repr__(self):
        return "DeepSeekChat"

    @staticmethod
    def is_valid(conf: dict) -> bool:
        return bool(conf and conf.get("key") and conf.get("prompt"))

    def get_reply(self, user_input: str, user_id: str) -> str:
        
        cmd = user_input.strip().lower()

        commands = {
            "#开启思维链": lambda: "⚙️ 配置文件中已设定是否启用思维链。",
            "#enable reasoning": lambda: "⚙️ Reasoning is controlled by config file and cannot be changed at runtime.",
            "#关闭思维链": lambda: "⚙️ 配置文件中已设定是否启用思维链。",
            "#disable reasoning": lambda: "⚙️ Reasoning is controlled by config file and cannot be changed at runtime.",
            "#显示思维链": lambda: "⚙️ 显示状态由配置文件决定。",
            "#show reasoning": lambda: "⚙️ Visibility is controlled by config file.",
            "#隐藏思维链": lambda: "⚙️ 显示状态由配置文件决定。",
            "#hide reasoning": lambda: "⚙️ Visibility is controlled by config file.",
        }

        if cmd in commands:
            return commands[cmd]()


        # 初始化对话上下文
        if user_id not in self.conversations:
            self.conversations[user_id] = []
            if self.system_prompt["content"]:
                self.conversations[user_id].append(self.system_prompt)

        self.conversations[user_id].append({"role": "user", "content": user_input})

        try:
            messages = self.conversations[user_id]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                stream=False,
                temperature=self.temperature,
                top_p=self.top_p,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty,
                # reasoning_effort=self.reasoning_effort,  # 等官方支持后再启用
            )


            message = response.choices[0].message
            answer = message.content

            # 若开启思维链，拼接推理信息
            if self.reasoning_enabled and hasattr(message, "reasoning_content"):
                reasoning = getattr(message, "reasoning_content", "")
                if self.reasoning_visible and reasoning:
                    answer = f"🧠 推理过程：\n{reasoning}\n\n💡 最终回答：\n{message.content}"

            # 添加回答到上下文
            self.conversations[user_id].append({"role": "assistant", "content": message.content})

            # 限制对话上下文长度
            max_len = 30
            if len(self.conversations[user_id]) > max_len:
                system_msg = self.conversations[user_id][0] if self.conversations[user_id][0]["role"] == "system" else None
                self.conversations[user_id] = ([system_msg] if system_msg else []) + self.conversations[user_id][-max_len:]
            return answer

        except (APIConnectionError, APIError, AuthenticationError) as e:
            self.LOG.error(f"DeepSeek API 错误：{e}")
            return f"❌ DeepSeek API 错误：{e}"
        except Exception as e:
            self.LOG.error(f"未知错误：{e}")
            return "❗ 发生未知错误，请稍后重试"


# 示例运行
if __name__ == "__main__":
    config = Config().deepseek

    if not config:
        print("未找到 DeepSeek 配置")
        exit(0)

    bot = DeepSeekChat(config)

    while True:
        try:
            question = input("你：")
            start = datetime.now()
            reply = bot.get_reply(question, "user123")
            print("AI：", reply)
            print(f"⏱️耗时：{round((datetime.now() - start).total_seconds(), 2)}s\n")
        except KeyboardInterrupt:
            break
