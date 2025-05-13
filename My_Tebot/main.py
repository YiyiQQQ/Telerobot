import signal
from argparse import ArgumentParser
from config.configration import Config
from Robot.constants import  ChatType
from Robot.robot import Robot


def main(chat_type: int):
    config = Config()

    def handler(sig, frame):
        print("终止信号接收，准备退出...")
        exit(0)

    signal.signal(signal.SIGINT, handler)

    robot = Robot(config, chat_type)
    robot.LOG.info("🚀 TelegramBot 启动成功...")

    robot.sendTextMsg("🤖 机器人启动成功！", chat_id=config.telegram["admin_id"])
    robot.enableReceivingMsg()

    # 定时任务（保持不变）
    robot.onEveryTime("07:00", lambda: robot.sendTextMsg("🌤 天气预报（假装）", chat_id=config.telegram["admin_id"]))
    robot.onEveryTime("16:30", lambda: robot.sendTextMsg("📋 提醒：请填写日报", chat_id=config.telegram["admin_id"]))

    robot.keepRunningAndBlockProcess()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-c', type=int, default=0, help=f'选择模型参数序号: {ChatType.help_hint()}')
    args = parser.parse_args()
    main(args.c)
