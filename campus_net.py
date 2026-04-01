"""
校园网登录核心模块 - 清华大学 Srun 认证
"""

import base64
import hashlib
import hmac
import json
import random
import re
import time
from typing import Optional

import requests

import config
import x_encode


class CampusNetLogin:
    """清华大学校园网登录类"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        self.challenge: Optional[str] = None
        self.ipv6: Optional[str] = None

    def get_local_ip(self) -> Optional[str]:
        """获取本地 IP 地址（优先 IPv4）"""
        # 方法1: 从认证服务器获取（最准确 - 服务器看到的 IP）
        ip = self._get_ip_from_auth_server()
        if ip:
            return ip

        # 方法2: 从网络接口获取
        ip = self._get_ip_from_interface()
        if ip:
            return ip

        return None

    def _get_ip_from_auth_server(self) -> Optional[str]:
        """从认证服务器获取客户端 IP"""
        try:
            timestamp = int(time.time() * 1000)
            callback = f"jQuery{timestamp}_{random.randint(1000000000, 9999999999)}"

            params = {
                "callback": callback,
                "username": "probe",  # 探测用户
                "ip": "",  # 空 IP，让服务器返回客户端 IP
                "_": timestamp,
            }

            auth_server = getattr(config, 'AUTH_SERVER', None) or 'auth4.tsinghua.edu.cn'
            url = f"https://{auth_server}/cgi-bin/get_challenge"
            response = self.session.get(url, params=params, timeout=10)

            # 从响应中提取 IP
            match = re.search(r'"client_ip"\s*:\s*"([^"]+)"', response.text)
            if match:
                return match.group(1)

        except Exception:
            pass

        return None

    def _get_ip_from_interface(self) -> Optional[str]:
        """从本地网络接口获取 IP 地址（优先 IPv4）"""
        try:
            import subprocess
            # 使用 ipconfig 获取 IP 地址
            result = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                timeout=10
            )

            if result.returncode == 0:
                try:
                    output = result.stdout.decode('gbk')
                except UnicodeDecodeError:
                    try:
                        output = result.stdout.decode('utf-8')
                    except UnicodeDecodeError:
                        output = result.stdout.decode('latin1', errors='replace')

                # 查找 IPv4 地址（通常在 "IPv4 地址" 或 "IPv4 Address" 行）
                # 格式如: 192.168.1.100
                ipv4_pattern = r'IPv4[^:]*:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                for line in output.split('\n'):
                    match = re.search(ipv4_pattern, line)
                    if match:
                        ip = match.group(1)
                        # 排除 127.0.0.1
                        if ip != '127.0.0.1':
                            return ip

        except Exception as e:
            print(f"获取本地 IP 失败: {e}")

        return None

    def get_local_ipv6(self) -> Optional[str]:
        """获取本地 IPv6 地址（从网络接口）- 保留此方法以备后用"""
        # 方法1: 从本地网络接口获取
        ipv6 = self._get_ipv6_from_interface()
        if ipv6:
            return ipv6

        # 方法2: 从认证服务器获取（有时候服务器会返回客户端IP）
        ipv6 = self._get_ipv6_from_auth_server()
        if ipv6:
            return ipv6

        return None

    def _get_ipv6_from_interface(self) -> Optional[str]:
        """从本地网络接口获取 IPv6 地址"""
        try:
            import subprocess
            import re
            # 使用 netsh 获取 IPv6 地址
            result = subprocess.run(
                ["netsh", "interface", "ipv6", "show", "address"],
                capture_output=True,
                timeout=10
            )

            if result.returncode == 0:
                # Windows 控制台可能是 gbk 编码，尝试解码
                try:
                    output = result.stdout.decode('gbk')
                except UnicodeDecodeError:
                    try:
                        output = result.stdout.decode('utf-8')
                    except UnicodeDecodeError:
                        output = result.stdout.decode('latin1', errors='replace')

                # 使用正则表达式在每行中查找 IPv6 地址
                # 匹配 2402: 开头的全局单播地址，排除 fe80: 链路本地地址
                ipv6_pattern = r'(?<![0-9a-fA-F:])(2402:[0-9a-fA-F:]+[0-9a-fA-F]{1,4})(?![0-9a-fA-F:])'

                for line in output.split('\n'):
                    match = re.search(ipv6_pattern, line)
                    if match:
                        ipv6 = match.group(1)
                        # 进一步验证：排除包含 % 的地址
                        if '%' not in ipv6 and not ipv6.startswith('fe80:'):
                            return ipv6

        except Exception as e:
            print(f"获取本地 IPv6 失败: {e}")

        return None

    def _get_ipv6_from_auth_server(self) -> Optional[str]:
        """从认证服务器获取客户端 IP（通过 get_challenge 响应）"""
        try:
            # 使用一个假的用户名获取挑战，服务器会返回客户端 IP
            timestamp = int(time.time() * 1000)
            callback = f"jQuery{timestamp}_{random.randint(1000000000, 9999999999)}"

            params = {
                "callback": callback,
                "username": "probe",  # 探测用户
                "ip": "",  # 空 IP，让服务器返回客户端 IP
                "_": timestamp,
            }

            url = f"https://{config.AUTH_SERVER}/cgi-bin/get_challenge"
            response = self.session.get(url, params=params, timeout=10)

            # 从响应中提取 IP
            match = re.search(r'"client_ip"\s*:\s*"([^"]+)"', response.text)
            if match:
                return match.group(1)

            # 尝试其他可能的字段名
            match = re.search(r'"ip"\s*:\s*"([^"]+)"', response.text)
            if match:
                ip = match.group(1)
                if self._is_valid_ipv6(ip):
                    return ip

        except Exception:
            pass

        return None

    def _is_valid_ipv6(self, ip: str) -> bool:
        """验证是否为有效的 IPv6 地址"""
        if not ip:
            return False
        pattern = r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$"
        return bool(re.match(pattern, ip))

    def detect_server_config(self) -> tuple[Optional[str], Optional[str]]:
        """
        从重定向获取认证服务器和 AC_ID

        Returns:
            (auth_server, ac_id) 元组，失败返回 (None, None)
        """
        try:
            # 使用不带 cookie 的干净 session 检测（不登录状态下的重定向）
            import requests
            clean_session = requests.Session()
            clean_session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            })

            # 访问 login.tsinghua.edu.cn，强制触发重定向到认证服务器
            response = clean_session.get(
                "http://login.tsinghua.edu.cn/",
                timeout=10,
                allow_redirects=True
            )

            final_url = response.url
            print(f"重定向后 URL: {final_url}")

            # 从 URL 中提取 auth_server 和 ac_id
            # 格式: https://auth4.tsinghua.edu.cn/srun_portal_pc?ac_id=222&...
            auth_match = re.search(r'https?://([^/]+)/', final_url)
            ac_id_match = re.search(r'ac_id=(\d+)', final_url)

            auth_server = auth_match.group(1) if auth_match else None
            ac_id = ac_id_match.group(1) if ac_id_match else None

            if auth_server and ac_id:
                print(f"自动检测: auth_server={auth_server}, ac_id={ac_id}")
                return auth_server, ac_id

        except Exception as e:
            print(f"自动检测服务器配置失败: {e}")

        return None, None

    def get_challenge(self, username: str, ip: str, auth_server: str = None) -> Optional[str]:
        """
        从认证服务器获取挑战字符串

        Args:
            username: 用户名
            ip: IPv6 地址
            auth_server: 认证服务器（可选，默认使用config中的值）

        Returns:
            挑战字符串，失败返回 None
        """
        if auth_server is None:
            auth_server = getattr(config, 'AUTH_SERVER', None) or 'auth6.tsinghua.edu.cn'

        timestamp = int(time.time() * 1000)
        callback = f"jQuery{timestamp}_{random.randint(1000000000, 9999999999)}"

        params = {
            "callback": callback,
            "username": username,
            "ip": ip,
            "_": timestamp,
        }

        url = f"https://{auth_server}/cgi-bin/get_challenge"

        try:
            response = self.session.get(url, params=params, timeout=10)
            response_text = response.text

            # 解析 JSONP 响应: jQueryxxxxx({...})
            match = re.search(r'jQuery\d+_\d+\((.+)\)', response_text)
            if match:
                data = json.loads(match.group(1))
                if data.get("res") == "ok":
                    return data.get("challenge")

            # 尝试直接解析 JSON
            data = response.json()
            if data.get("res") == "ok":
                return data.get("challenge")

        except Exception as e:
            print(f"获取挑战失败: {e}")

        return None

    def get_challenge_with_ip(self, username: str, auth_server: str, session=None) -> tuple[Optional[str], Optional[str]]:
        """
        从认证服务器获取挑战字符串和客户端IP

        Args:
            username: 用户名
            auth_server: 认证服务器
            session: 可选的 session，不提供则使用 self.session

        Returns:
            (挑战字符串, 客户端IP) 元组，失败返回 (None, None)
        """
        if session is None:
            session = self.session

        timestamp = int(time.time() * 1000)
        callback = f"jQuery{timestamp}_{random.randint(1000000000, 9999999999)}"

        params = {
            "callback": callback,
            "username": username,
            "ip": "",  # 空 IP，让服务器返回客户端 IP
            "_": timestamp,
        }

        url = f"https://{auth_server}/cgi-bin/get_challenge"

        try:
            response = session.get(url, params=params, timeout=10)
            response_text = response.text

            # 解析 JSONP 响应: jQueryxxxxx({...})
            match = re.search(r'jQuery\d+_\d+\((.+)\)', response_text)
            if match:
                data = json.loads(match.group(1))
                if data.get("res") == "ok":
                    return data.get("challenge"), data.get("client_ip")

            # 尝试直接解析 JSON
            data = response.json()
            if data.get("res") == "ok":
                return data.get("challenge"), data.get("client_ip")

        except Exception as e:
            print(f"获取挑战失败: {e}")

        return None, None

    def _encrypt_password(self, challenge: str, password: str) -> str:
        """
        使用挑战字符串加密密码 (HMAC-MD5)

        根据 md5.js v2.10.0: md5(password, token) = HMAC-MD5(key=token, message=password)

        Args:
            challenge: 挑战字符串 (token)
            password: 原始密码

        Returns:
            加密后的密码，格式: {MD5}xxxx
        """
        # md5(password, challenge) = HMAC-MD5(key=challenge, message=password)
        hmac_md5 = hmac.new(challenge.encode('utf-8'), password.encode('utf-8'), hashlib.md5).hexdigest()
        return f"{{MD5}}{hmac_md5}"

    def _calc_info(self, challenge: str, username: str, password: str, ip: str, ac_id: str) -> str:
        """
        计算 info 字段（使用 x_encode 加密）

        Args:
            challenge: 挑战字符串
            username: 用户名
            password: 原始密码
            ip: IP 地址
            ac_id: 接入控制ID

        Returns:
            Base64 编码的加密信息，带 {SRBX1} 前缀
        """
        # 构建 JSON 数据（注意：不包含 mac 字段）
        info_data = {
            "username": username,
            "password": password,
            "ip": ip,
            "acid": ac_id,
            "enc_ver": "srun_bx1",
        }

        # 使用 x_encode 加密
        info_json = json.dumps(info_data, separators=(',', ':'))
        encrypted = x_encode.x_encode(info_json, challenge)

        # 使用自定义 base64 编码（与浏览器相同）
        encoded = x_encode.custom_base64_encode(encrypted)
        return f"{{SRBX1}}{encoded}"

    def _calc_chksum(self, challenge: str, username: str, encrypted_password: str,
                     info: str, ip: str, ac_id: str) -> str:
        """
        计算校验和

        Args:
            challenge: 挑战字符串
            username: 用户名
            encrypted_password: 加密后的密码，格式 {MD5}xxxx
            info: info 字段
            ip: IPv6 地址
            ac_id: 接入控制ID

        Returns:
            校验和字符串
        """
        # 构建校验字符串 - token (challenge) 插入在每个字段之前
        # JavaScript格式: token + username + token + hmd5 + token + acid + token + ip + token + n + token + type + token + info
        # 注意：hmd5是原始HMAC-MD5值（不含{MD5}前缀）
        n = "200"
        type_ = "1"

        # 提取原始HMAC-MD5值（去掉{MD5}前缀）
        hmd5 = encrypted_password[5:] if encrypted_password.startswith('{MD5}') else encrypted_password

        chkstr = f"{challenge}{username}"
        chkstr += f"{challenge}{hmd5}"
        chkstr += f"{challenge}{ac_id}"
        chkstr += f"{challenge}{ip}"
        chkstr += f"{challenge}{n}"
        chkstr += f"{challenge}{type_}"
        chkstr += f"{challenge}{info}"

        return hashlib.sha1(chkstr.encode('utf-8')).hexdigest()

    def login(self, username: str, password: str, ip: str) -> bool:
        """
        执行校园网登录

        Args:
            username: 用户名
            password: 密码
            ip: IP 地址

        Returns:
            登录成功返回 True，失败返回 False
        """
        self.ipv6 = ip  # 保留兼容性

        # 使用新的 session 避免 cookie 冲突问题
        login_session = requests.Session()
        login_session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })

        # 认证服务器列表（按优先级排序）
        auth_servers = ["auth6.tsinghua.edu.cn", "auth4.tsinghua.edu.cn"]

        # 从配置获取手动指定的服务器
        configured_server = getattr(config, 'AUTH_SERVER', None)
        if configured_server:
            # 如果手动指定了服务器，优先使用它
            auth_servers = [configured_server] + [s for s in auth_servers if s != configured_server]

        # 尝试自动检测
        print("正在自动检测服务器配置...")
        detected_server, detected_ac_id = self.detect_server_config()
        if detected_server:
            # 将检测到的服务器放到最优先位置
            auth_servers = [detected_server] + [s for s in auth_servers if s != detected_server]

        # ac_id 必须配置
        default_ac_id = getattr(config, 'AC_ID', None)
        if not default_ac_id:
            print("错误: config.py 中未配置 AC_ID")
            print("请在浏览器中访问 http://login.tsinghua.edu.cn/")
            print("登录后会重定向到认证页面，从 URL 中获取 ac_id 值")
            print("例如: https://auth4.tsinghua.edu.cn/srun_portal_pc?ac_id=222")
            return False

        # 尝试每个服务器
        for auth_server in auth_servers:
            print(f"\n{'='*50}")
            print(f"尝试服务器: {auth_server}")
            print(f"{'='*50}")

            # 获取新的挑战（每个服务器需要新的挑战）
            # 使用空 IP 让服务器返回它看到的客户端 IP
            challenge, server_ip = self.get_challenge_with_ip(username, auth_server, login_session)
            if not challenge:
                print(f"获取挑战失败，跳过此服务器")
                continue

            self.challenge = challenge
            print(f"获取挑战成功: {challenge}")
            print(f"服务器返回的客户端 IP: {server_ip}")

            # 加密密码
            encrypted_password = self._encrypt_password(challenge, password)
            print(f"密码加密完成: {encrypted_password}")

            # 只使用用户配置的 ac_id
            ac_ids_to_try = [default_ac_id]

            for try_ac_id in ac_ids_to_try:
                print(f"\n尝试使用 ac_id={try_ac_id} 登录...")

                # 计算 info 和 chksum（使用服务器返回的 IP）
                info = self._calc_info(challenge, username, password, server_ip, try_ac_id)
                chksum = self._calc_chksum(challenge, username, encrypted_password, info, server_ip, try_ac_id)

                # 构建登录请求
                timestamp = int(time.time() * 1000)
                callback = f"jQuery{timestamp}_{random.randint(1000000000, 9999999999)}"

                params = {
                    "callback": callback,
                    "action": "login",
                    "username": username,
                    "password": encrypted_password,
                    "os": "Windows 10",
                    "name": "Windows",
                    "double_stack": "0",
                    "chksum": chksum,
                    "info": info,
                    "ac_id": try_ac_id,
                    "ip": server_ip,
                    "n": "200",
                    "type": "1",
                    "_": timestamp,
                }

                url = f"https://{auth_server}/cgi-bin/srun_portal"

                try:
                    print(f"URL: {url}")

                    response = login_session.get(url, params=params, timeout=15)
                    response_text = response.text

                    print(f"响应: {response_text[:500]}")

                    # 解析响应
                    match = re.search(r'jQuery\d+_\d+\((.+)\)', response_text)
                    if match:
                        data = json.loads(match.group(1))
                        if data.get("res") == "ok":
                            print("登录成功!")
                            return True
                        else:
                            error_msg = data.get("error_msg") or data.get("error") or "未知错误"
                            print(f"ac_id={try_ac_id} 登录失败: {error_msg}")
                            # 继续尝试下一个 ac_id
                            continue

                    print(f"ac_id={try_ac_id} 登录失败: {response_text[:200]}")

                except Exception as e:
                    print(f"ac_id={try_ac_id} 登录异常: {e}")

            print(f"服务器 {auth_server} 所有 ac_id 都尝试完毕")

        print(f"\n所有服务器都尝试完毕，登录失败")
        return False

    def logout(self, username: str, ipv6: str) -> bool:
        """
        登出校园网

        Args:
            username: 用户名
            ipv6: IPv6 地址

        Returns:
            登出成功返回 True，失败返回 False
        """
        timestamp = int(time.time() * 1000)
        callback = f"jQuery{timestamp}_{random.randint(1000000000, 9999999999)}"

        params = {
            "callback": callback,
            "action": "logout",
            "username": username,
            "ip": ipv6,
            "_": timestamp,
        }

        url = f"https://{config.AUTH_SERVER}/cgi-bin/srun_portal"

        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            return data.get("res") == "ok"
        except Exception as e:
            print(f"登出失败: {e}")
            return False


def test_login():
    """测试登录功能"""
    import config

    login = CampusNetLogin()

    # 获取本地 IP
    ip = login.get_local_ip()
    if not ip:
        print("无法获取本地 IP 地址")
        return

    print(f"当前 IP: {ip}")

    # 执行登录
    success = login.login(config.USERNAME, config.PASSWORD, ip)
    print(f"登录结果: {'成功' if success else '失败'}")


if __name__ == "__main__":
    test_login()
