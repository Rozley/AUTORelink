# AUTORelink

清华大学校园网自动重连工具 for Windows

当检测到校园网断线时，自动重新登录 Tsinghua Campus Network（Srun4000 认证）。

## 功能特性

- 自动检测网络断开并重连
- 支持 IPv6 认证
- 支持 auth4 / auth6 双栈自动切换
- 支持开机自启动（Task Scheduler）
- 配置简单，无需复杂设置

## 环境要求

- Windows 10/11
- Python 3.8+
- 清华大学校园网账号

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置账号

编辑 `config.py`，填入你的校园网用户名和密码：

```python
USERNAME = "your-username"
PASSWORD = "your-password"
```

### 3. 配置 AC_ID

AC_ID 需要手动获取（每位用户可能不同）：

1. 断开校园网登录
2. 在浏览器访问 `http://login.tsinghua.edu.cn/`
3. 观察重定向后的 URL，格式类似：
   ```
   https://auth4.tsinghua.edu.cn/srun_portal_pc?ac_id=222
   ```
4. 将 `ac_id=222` 中的数字填入 `config.py`：
   ```python
   AC_ID = "222"
   ```

也可以运行 `python test_ac_id.py` 自动检测。

### 4. 运行

**命令行模式：**

```bash
python main.py
```

**设置开机自启动（后台运行）：**

```bash
# 以管理员身份运行
python setup_autostart.py install
```

开机自启动相关命令：

```bash
python setup_autostart.py status     # 查看状态
python setup_autostart.py remove      # 移除开机自启动
```

## 工作原理

```
检测网络 ──> 断开？ ──> 获取 Challenge Token
                        │
                        v
                   加密密码 (HMAC-MD5)
                        │
                        v
                   加密登录信息 (x_encode + 自定义 Base64)
                        │
                        v
                   发送认证请求到 /cgi-bin/srun_portal
                        │
                        v
                   成功？ ──> 继续监控
```

### x_encode 算法

x_encode 是 Srun4000 认证使用的 TEA-like 分组密码，由 JavaScript 版本移植而来，包含以下关键修复：

- 无符号右移操作符 (`>>>`) 的正确模拟
- JavaScript 与 Python 运算符优先级差异处理
- Latin1 字符编码确保二进制数据不损坏
- 与浏览器一致的自定义 Base64 字母表

详见 [x_encode.py](x_encode.py) 源码注释。

## 项目结构

```
AUTORelink/
├── main.py              # 主程序入口，监控循环
├── campus_net.py        # Srun 认证核心逻辑
├── detector.py          # 网络状态检测
├── x_encode.py          # 加密算法实现
├── config.py            # 配置文件
├── setup_autostart.py   # 开机自启动设置脚本
├── test_ac_id.py        # AC_ID 检测工具
└── requirements.txt     # 依赖
```

## 配置说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `USERNAME` | 校园网用户名 | 必填 |
| `PASSWORD` | 校园网密码 | 必填 |
| `AC_ID` | 接入控制 ID | 必填（需手动获取）|
| `AUTH_SERVER` | 认证服务器，设为 `None` 自动检测 | `None` |
| `CHECK_INTERVAL` | 网络检测间隔（秒） | `30` |
| `LOG_FILE` | 日志文件路径 | `campus_net.log` |
| `LOG_LEVEL` | 日志级别 | `INFO` |


## License

MIT
