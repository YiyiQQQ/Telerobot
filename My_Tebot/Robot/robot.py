import logging
from threading import Thread
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from datetime import datetime
from time import sleep
from AI_Setting.deepseek_chat import DeepSeekChat
from config.configration import Config
import yaml 

class Robot:
    def __init__(self, config, chat_type: int):
        config1 = Config().deepseek
        self.config = config
        self.chat_type = chat_type
        self.token = self.config.telegram["bot_token"]
        self.proxy_url = self.config.telegram.get("proxy_url", None)

        
        self.chatbot = DeepSeekChat(config1)# 日志设置
        logging.basicConfig(level=logging.INFO)
        self.LOG = logging.getLogger("TelegramRobot")
       
        self.deepseek_enabled = False  # 默认关闭 DeepSeek 聊天

        # 从 YAML 文件加载白名单
        self.load_whitelist()
        
        
        # 初始化 bot
        self.updater = Updater(
            token=self.token,
            request_kwargs={"proxy_url": self.proxy_url} if self.proxy_url else {}
        )
        self.dispatcher = self.updater.dispatcher

        # 注册消息处理器
        self._register_handlers()

        # 存储定时任务
        self.jobs = []

    def _register_handlers(self):
        self.dispatcher.add_handler(CommandHandler("start", self._on_start))
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self._on_message))
        self.dispatcher.add_handler(CommandHandler("deepseek_on", self._on_deepseek_on))
        self.dispatcher.add_handler(CommandHandler("deepseek_off", self._on_deepseek_off))

    def load_whitelist(self):
        """加载用户和群聊白名单"""
        with open(r"E:\WeChatFerry_proj\Telerobot\My_Tebot\config\config.yaml", "r", encoding="utf-8") as file:
            whitelist_data = yaml.safe_load(file)

        self.whitelist = whitelist_data.get("user_whitelist", [])
        self.whitelist_groups = whitelist_data.get("group_whitelist", [])
    def _on_deepseek_on(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        if chat_id not in self.whitelist_groups:
            update.message.reply_text("🚫 该群聊没有权限使用这个 Bot。")
            return

        if user_id not in self.whitelist:
            update.message.reply_text("🚫 你没有权限启用聊天功能。")
            return

        self.deepseek_enabled = True
        update.message.reply_text("✅ DeepSeek 聊天模式已启用！可以发送消息让 AI 回复。")
        self.LOG.info(f"用户 {user_id} 在群聊 {chat_id} 启用了 DeepSeek 聊天。")

    def _on_deepseek_off(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        if chat_id not in self.whitelist_groups:
            update.message.reply_text("🚫 该群聊没有权限使用这个 Bot。")
            return

        if user_id not in self.whitelist:
            update.message.reply_text("🚫 你没有权限关闭聊天功能。")
            return

        self.deepseek_enabled = False
        update.message.reply_text("❎ DeepSeek 聊天模式已关闭。")
        self.LOG.info(f"用户 {user_id} 在群聊 {chat_id} 关闭了 DeepSeek 聊天。")
    def _on_start(self, update: Update, context: CallbackContext):
        instructions = (
            "📘 可用命令列表：\n"
            "/start - 显示指令说明\n"
            "/deepseek_on - 启用 DeepSeek 聊天模式\n"
            "/deepseek_off - 关闭 DeepSeek 聊天模式\n"
            "直接发送文本（在启用聊天模式时）可触发 AI 回复"
        )
        update.message.reply_text(instructions)
    def _on_message(self, update: Update, context: CallbackContext):
        msg = update.message.text
        chat_id = update.message.chat.id
        user_id = update.effective_user.id

        if chat_id not in self.whitelist_groups:
            self.LOG.warning(f"群聊 {chat_id} 不在白名单中，忽略消息。")
            return

        if user_id not in self.whitelist:
            self.LOG.warning(f"用户 {user_id} 不在白名单中，忽略消息。")
            return

        if not self.deepseek_enabled:
            self.LOG.warning("🤖 当前未启用 DeepSeek 聊天功能，发送 /deepseek_on 以启用。")
            return

        self.LOG.info(f"收到消息：{msg}")
        self.processMsg(chat_id, msg)

    def processMsg(self, chat_id: int, msg: str):
        try:
            # 使用 DeepSeekChat 获取回复
            reply = self.chatbot.get_reply(msg, str(chat_id))  # 注意 user_id 用 chat_id 字符串化即可
        except Exception as e:
            reply = f"❗ 出错了：{e}"

        self.sendTextMsg(reply, chat_id)

    def sendTextMsg(self, msg: str, chat_id: int):
        self.updater.bot.send_message(chat_id=chat_id, text=msg)

    def enableReceivingMsg(self):
        self.LOG.info("开始监听消息...")
        self.updater.start_polling()

    def onEveryTime(self, time_str: str, func, *args, **kwargs):
        def job_loop():
            while True:
                now = datetime.now().strftime("%H:%M")
                if now == time_str:
                    self.LOG.info(f"定时任务执行：{func.__name__}")
                    try:
                        func(*args, **kwargs)
                    except Exception as e:
                        self.LOG.error(f"任务执行错误: {e}")
                    sleep(60)
                sleep(5)

        Thread(target=job_loop, daemon=True).start()

    def keepRunningAndBlockProcess(self):
        self.updater.idle()
