import logging
import yaml
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.utils.request import Request
from config.configration import Config
from openai import APIConnectionError, APIError, AuthenticationError, OpenAI

# 配置日志记录
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]  # 输出到终端
)
logger = logging.getLogger()
# 获取 DeepSeek 配置信息


# 定义 /start 命令的处理函数
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    update.message.reply_text(f"Hello! Your user ID is {user_id}, and chat ID is {chat_id}")
    logger.info(f"Start command received from User ID: {user_id}, Chat ID: {chat_id}")

# 定义接收消 息的处理函数
def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    chat_type = update.message.chat.type  # 获取消息的聊天类型
    message_text = update.message.text  # 获取用户的消息内容

    if chat_type == 'private':
        logger.info(f"Received private message from User ID: {user_id}, Chat ID: {chat_id}")
    #   update.message.reply_text(f"Received your private message. User ID: {user_id}, Chat ID: {chat_id}")
    elif chat_type in ['group', 'supergroup']:
        logger.info(f"Received group message from User ID: {user_id}, Group ID: {chat_id}, Message: {update.message.text}")
        # update.message.reply_text(f"Received your message in the group. User ID: {user_id}, Group ID: {chat_id}")
    else:
        logger.warning(f"Unknown chat type: {chat_type}")




def main():
    # 加载配置
    config = Config()
    # 填入你的 bot token
    token = '7626771486:AAFkl7Niv9cohzgJICkA5mjQS2PbvCCb-YU'
    request = Request(proxy_url='http://127.0.0.1:7890')
    # 创建 Updater 对象并指定 token
    updater = Updater(token=token, request_kwargs={'proxy_url': 'http://127.0.0.1:7890'})
    # 获取调度器并添加处理程序
    dispatcher = updater.dispatcher
    # 添加一个处理 /start 命令的处理器
    dispatcher.add_handler(CommandHandler("start", start))
    # 添加处理文本消息的处理器
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    # 启动机器人
    updater.start_polling()
    # 运行直到程序被停止
    updater.idle()


if __name__ == '__main__':
    main()
