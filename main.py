"""
清华大学校园网自动重连 - 主程序

功能：
1. 监控网络状态
2. 检测到断线后自动重连
"""

import sys
import os
import subprocess

# 确保当前目录在 Python 路径中
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

import logging
import time
from datetime import datetime
from typing import Optional

import config
import campus_net
import detector


def disable_proxy():
    """关闭系统代理/VPN，确保认证请求直连校园网"""
    try:
        # 重置 WinHTTP 代理设置
        subprocess.run(
            ["netsh", "winhttp", "reset", "proxy"],
            capture_output=True,
            timeout=10
        )
        # 关闭 Windows 代理设置
        subprocess.run(
            ["netsh", "interface", "set", "proxy", "disable"],
            capture_output=True,
            timeout=10
        )
        print(f"[{datetime.now()}] 已关闭代理/VPN")
    except Exception as e:
        print(f"[{datetime.now()}] 关闭代理失败: {e}")

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="[%(asctime)s] %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


class CampusNetReconnect:
    """校园网自动重连服务"""

    def __init__(self):
        self.login_client = None  # 延迟初始化
        self.is_running = False
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        self.disconnect_threshold = 2  # 连续2次检测到断网才认为真的断了
        self.connected_confirm_threshold = 2  # 连续2次检测到联网才认为真的恢复了
        self.disconnected_count = 0  # 连续断开次数
        self.connected_count = 0  # 连续连接次数

    def _ensure_login_client(self):
        """延迟创建登录客户端"""
        if self.login_client is None:
            self.login_client = campus_net.CampusNetLogin()

    def get_current_ipv6(self) -> Optional[str]:
        """获取当前 IPv6 地址"""
        self._ensure_login_client()
        return self.login_client.get_local_ipv6()

    def reconnect(self) -> bool:
        """尝试重新连接校园网"""
        print(f"[{datetime.now()}] 开始重连...")

        # 获取当前 IPv6
        ipv6 = self.get_current_ipv6()
        if not ipv6:
            print(f"[{datetime.now()}] 无法获取 IPv6 地址")
            return False

        print(f"[{datetime.now()}] 当前 IPv6: {ipv6}")

        # 执行登录
        success = self.login_client.login(
            config.USERNAME,
            config.PASSWORD,
            ipv6
        )

        if success:
            self.consecutive_failures = 0
            return True
        else:
            self.consecutive_failures += 1
            print(f"[{datetime.now()}] 重连失败 (第 {self.consecutive_failures} 次)")
            return False

    def on_network_disconnected(self):
        """网络断开时的处理"""
        print(f"[{datetime.now()}] 检测到网络断开，正在尝试重连...")

        # 关闭代理后再尝试重连
        disable_proxy()

        # 多次重试
        for attempt in range(1, self.max_consecutive_failures + 1):
            print(f"[{datetime.now()}] 重连尝试 {attempt}/{self.max_consecutive_failures}")

            if self.reconnect():
                return True

            # 重连失败后等待一下再试
            if attempt < self.max_consecutive_failures:
                time.sleep(5)

        print(f"[{datetime.now()}] 重连失败，请检查网络或配置")
        return False

    def on_network_connected(self):
        """网络恢复时的处理"""
        self.consecutive_failures = 0
        print(f"[{datetime.now()}] 网络已恢复")

    def network_callback(self, is_connected: bool, message: str):
        """网络状态变化的回调"""
        if is_connected:
            self.on_network_connected()
        else:
            self.on_network_disconnected()

    def run(self):
        """运行监控服务"""
        print(f"[{datetime.now()}] 清华大学校园网自动重连服务启动")
        print(f"[{datetime.now()}] 用户名: {config.USERNAME}")
        print(f"[{datetime.now()}] 认证服务器: {config.AUTH_SERVER}")
        print(f"[{datetime.now()}] 检测间隔: {config.CHECK_INTERVAL} 秒")
        print(f"[{datetime.now()}] 日志文件: {config.LOG_FILE}")

        self.is_running = True
        self.disconnected_count = 0
        self.connected_count = 0

        while self.is_running:
            try:
                connected, message = detector.is_campus_net_connected()

                # 防抖逻辑：避免网络状态频繁波动
                if connected:
                    self.connected_count += 1
                    self.disconnected_count = 0
                    if self.connected_count >= self.connected_confirm_threshold:
                        if self.consecutive_failures > 0 or self.disconnected_count > 0:
                            self.on_network_connected()
                        self.consecutive_failures = 0
                else:
                    self.disconnected_count += 1
                    self.connected_count = 0
                    if self.disconnected_count >= self.disconnect_threshold:
                        self.on_network_disconnected()

                # 等待下次检测
                for _ in range(config.CHECK_INTERVAL):
                    if not self.is_running:
                        break
                    time.sleep(1)

            except KeyboardInterrupt:
                print(f"\n[{datetime.now()}] 收到退出信号，正在停止...")
                self.stop()
                break
            except Exception as e:
                logger.error(f"监控异常: {e}")
                time.sleep(5)

        print(f"[{datetime.now()}] 服务已停止")

    def stop(self):
        """停止服务"""
        self.is_running = False
        self.disconnected_count = 0
        self.connected_count = 0


def main():
    """命令行入口"""
    service = CampusNetReconnect()
    service.run()


if __name__ == "__main__":
    main()
