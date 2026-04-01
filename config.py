"""
配置文件 - 清华大学校园网自动重连
"""

# ==================== 登录信息 ====================
# 校园网用户名
USERNAME = "your_username_here"
# 校园网密码
PASSWORD = "your_password_here"

# ==================== 服务器配置 ====================
# 认证服务器（支持 auth4/auth6）- 可自动检测
AUTH_SERVERS = [
    "auth4.tsinghua.edu.cn",
    "auth6.tsinghua.edu.cn",
]
# 设置为 None 启用自动检测，或手动指定如 "auth6.tsinghua.edu.cn"
AUTH_SERVER = None

# ac_id - 接入控制ID（必填）
# 请在浏览器中访问 login.tsinghua.edu.cn，从重定向后的 URL 中获取
# 例如: https://auth4.tsinghua.edu.cn/srun_portal_pc?ac_id=222
AC_ID = "your_ac_id_here"

# ==================== 网络检测配置 ====================
# 检测间隔（秒）
CHECK_INTERVAL = 10

# 用于检测网络连通性的地址
PING_HOSTS = [
    ("8.8.8.8", 1),      # Google DNS
    ("2001:4860:4860::8888", 1),  # Google DNS IPv6
]

# 检测 URL（判断是否需要登录）
CHECK_URL = "http://www.tsinghua.edu.cn"
LOGIN_CHECK_URL = "http://ipv4.icanhazip.com"

# ==================== 日志配置 ====================
LOG_FILE = "campus_net.log"
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# ==================== Windows 服务配置 ====================
SERVICE_NAME = "CampusNetReconnect"
SERVICE_DISPLAY_NAME = "清华大学校园网自动重连"
SERVICE_DESCRIPTION = "当检测到校园网断线时，自动重新登录校园网"