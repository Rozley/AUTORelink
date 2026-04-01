"""
网络状态检测模块
"""

import socket
import subprocess
import time
from typing import Tuple

import requests

import config


def ping_host(host: str, timeout: int = 3) -> Tuple[bool, str]:
    """
    Ping 指定主机检测网络

    Args:
        host: 主机地址（IP 或域名）
        timeout: 超时时间（秒）

    Returns:
        (是否成功, 错误信息)
    """
    try:
        # Windows 使用 -n，Unix 使用 -c
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout * 1000), host],
            capture_output=True,
            timeout=timeout + 1
        )

        if result.returncode == 0:
            return True, ""
        else:
            return False, "Ping 超时"

    except subprocess.TimeoutExpired:
        return False, "Ping 超时"
    except FileNotFoundError:
        return False, "ping 命令不存在"
    except Exception as e:
        return False, str(e)


def check_tcp_port(host: str, port: int, timeout: int = 3) -> Tuple[bool, str]:
    """
    检测 TCP 端口是否可达

    Args:
        host: 主机地址
        port: 端口号
        timeout: 超时时间

    Returns:
        (是否可达, 错误信息)
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            return True, ""
        else:
            return False, f"端口 {port} 不可达"

    except socket.timeout:
        return False, "连接超时"
    except Exception as e:
        return False, str(e)


def check_http(url: str, timeout: int = 5) -> Tuple[bool, str]:
    """
    通过 HTTP 请求检测网络

    Args:
        url: 检测 URL
        timeout: 超时时间

    Returns:
        (是否成功, 错误信息)
    """
    try:
        # 不使用代理
        response = requests.get(
            url,
            timeout=timeout,
            proxies={"http": None, "https": None},
            allow_redirects=True
        )

        if response.status_code in (200, 301, 302):
            return True, ""
        else:
            return False, f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "请求超时"
    except requests.exceptions.ConnectionError:
        return False, "连接失败"
    except Exception as e:
        return False, str(e)


def is_network_connected() -> Tuple[bool, str]:
    """
    综合检测网络是否连接

    Returns:
        (是否连接, 状态描述)
    """
    # 方法1: 检测 HTTP 请求（最可靠）
    for url in [config.CHECK_URL, "http://www.baidu.com"]:
        success, msg = check_http(url, timeout=5)
        if success:
            return True, "网络正常"

    # 方法2: Ping 检测
    for host, _ in config.PING_HOSTS:
        success, msg = ping_host(host, timeout=3)
        if success:
            return True, "网络正常"

    # 方法3: 检测特定端口
    for host, port in [("auth4.tsinghua.edu.cn", 443), ("auth6.tsinghua.edu.cn", 443)]:
        success, msg = check_tcp_port(host, port, timeout=3)
        if success:
            return True, "网络正常"

    return False, "网络断开"


def is_campus_net_connected() -> Tuple[bool, str]:
    """
    检测是否已连接校园网（需要登录的那种）

    Returns:
        (是否连接, 状态描述)
    """
    # 尝试访问需要登录才会重定向页面的 URL
    # 如果能直接访问说明已经登录，否则会跳转到登录页

    # 校园网登录后的典型特征：可以访问校外网络（使用国内可访问的网站）
    success, msg = check_http("https://www.baidu.com", timeout=5)
    if success:
        return True, "已连接校园网"

    # 如果访问 Google 失败，检查是否是校园网限制还是完全断网
    success2, _ = check_http("http://www.tsinghua.edu.cn", timeout=5)
    if success2:
        return False, "需要重新登录校园网"

    return False, "网络完全断开"


def monitor_network(callback=None, interval: int = None):
    """
    持续监控网络状态

    Args:
        callback: 网络状态变化时的回调函数 (is_connected: bool, message: str) -> None
        interval: 检测间隔（秒），默认使用 config.CHECK_INTERVAL
    """
    if interval is None:
        interval = config.CHECK_INTERVAL

    last_state = None

    while True:
        connected, message = is_campus_net_connected()

        # 状态变化时触发回调
        if connected != last_state:
            last_state = connected
            if callback:
                callback(connected, message)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 状态变化: {message}")

        time.sleep(interval)


if __name__ == "__main__":
    # 测试网络检测
    print("正在检测网络状态...")

    connected, message = is_network_connected()
    print(f"网络状态: {message}")

    connected, message = is_campus_net_connected()
    print(f"校园网状态: {message}")