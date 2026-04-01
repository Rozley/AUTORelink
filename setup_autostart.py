"""
设置开机自启动 - 使用 Windows Task Scheduler

使用方法：
1. 以管理员身份运行命令行
2. python setup_autostart.py install    # 安装开机自启动
3. python setup_autostart.py remove     # 移除开机自启动
4. python setup_autostart.py status    # 查看状态
"""

import sys
import os
import subprocess

# 确保当前目录在 Python 路径中
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

import config


TASK_NAME = "CampusNetReconnect"


def create_task():
    """创建开机自启动任务"""
    try:
        # 使用 pythonw.exe 隐藏控制台窗口
        python_exe = sys.executable.replace("python.exe", "pythonw.exe")
        script_path = os.path.abspath("main.py").replace('/', '\\')

        # 使用 schtasks 创建任务
        # /SC ONLOGON 表示登录时启动
        # /RL HIGHEST 表示以最高权限运行
        cmd = [
            "schtasks",
            "/Create",
            "/TN", TASK_NAME,
            "/TR", f'"{python_exe}" "{script_path}"',
            "/SC", "ONLOGON",
            "/RL", "HIGHEST",
            "/F"  # 强制创建（如果已存在则覆盖）
        ]

        print(f"正在创建任务: {TASK_NAME}")
        print(f"命令: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("任务创建成功!")
            return True
        else:
            print(f"任务创建失败: {result.stderr}")
            return False

    except Exception as e:
        print(f"创建任务失败: {e}")
        return False


def delete_task():
    """删除开机自启动任务"""
    try:
        cmd = ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]

        print(f"正在删除任务: {TASK_NAME}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("任务删除成功!")
            return True
        else:
            print(f"任务删除失败: {result.stderr}")
            return False

    except Exception as e:
        print(f"删除任务失败: {e}")
        return False


def show_status():
    """查看任务状态"""
    try:
        cmd = ["schtasks", "/Query", "/TN", TASK_NAME]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"任务状态:")
            print(result.stdout)
            return True
        else:
            print("任务不存在或查询失败")
            return False

    except Exception as e:
        print(f"查询状态失败: {e}")
        return False


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print(f"用法: python {os.path.basename(__file__)} [install|remove|status]")
        print("")
        print("命令:")
        print("  install  - 安装开机自启动（需要管理员权限）")
        print("  remove   - 移除开机自启动")
        print("  status   - 查看任务状态")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "install":
        create_task()
    elif command == "remove":
        delete_task()
    elif command == "status":
        show_status()
    else:
        print(f"未知命令: {command}")
        main()


if __name__ == "__main__":
    main()
