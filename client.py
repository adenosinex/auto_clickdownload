# client.py (四肢)
import os
import time
import requests
import mss
import pyautogui
import yaml
import shutil

CONFIG_FILE = "config.yaml"
MANAGED_DIR = "templates"

def generate_default_yaml():
    """生成默认的配置文件"""
    default_config = {
        "system": {
            "server_url": "http://15x4.zin6.dpdns.org:5010/api/find_target",
            "download_dir": r"\\One\d\downloadD",
            "check_interval": 10,
            "idle_confirm_times": 2,
            "idle_confirm_interval": 5,
            "debug_mode": True  # 新增：默认开启调试模式方便首次测试
        },
        "tasks": [
            {
                "name": "高速下载操作",
                "target_text": "高速下载",
                "image_path": "templates/btn_download.png"
            },
            {
                "name": "获取并复制操作",
                "target_text": "并复制",
                "image_path": "templates/btn_get.png"
            }
        ]
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, allow_unicode=True, sort_keys=False)
    print(f"[系统] 已生成默认配置文件 {CONFIG_FILE}！")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        generate_default_yaml()
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def verify_and_manage_templates(tasks):
    os.makedirs(MANAGED_DIR, exist_ok=True)
    print(f"\n[系统] 开始校验并管理模板文件 (统一目录: {MANAGED_DIR}/)...")
    
    for task in tasks:
        original_path = task.get('image_path', '')
        if not original_path:
            continue

        if not os.path.exists(original_path):
            print(f"  [警告] 任务 [{task.get('name')}] 配置的图片不存在: {original_path}")
            continue

        filename = os.path.basename(original_path)
        managed_path = os.path.join(MANAGED_DIR, filename)

        if os.path.abspath(original_path) != os.path.abspath(managed_path):
            try:
                shutil.copy2(original_path, managed_path)
                print(f"  [文件管理] 已将外部图片归档: {filename} -> {MANAGED_DIR}/")
            except Exception as e:
                print(f"  [错误] 复制文件失败 {original_path}: {e}")
                continue

        task['image_path'] = managed_path
        print(f"  [就绪] 任务 [{task.get('name')}] 图像模板已确认挂载: {managed_path}")
        
    print("[系统] 模板文件校验与管理完毕！\n")
    return tasks

def is_active_downloading(directory):
    if not os.path.exists(directory):
        return False
    five_minutes_ago = time.time() - 300
    try:
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith('.qkdownloading'):
                    filepath = os.path.join(root, filename)
                    try:
                        if os.path.getmtime(filepath) > five_minutes_ago:
                            return True
                    except OSError:
                        continue
    except Exception:
        pass
    return False

def find_and_click(server_url, task_conf):
    screenshot_path = "temp_screen.png"
    task_name = task_conf.get('name', '未命名任务')
    target_text = task_conf.get('target_text', '')
    image_path = task_conf.get('image_path', '')
    
    with mss.mss() as sct:
        sct.shot(mon=1, output=screenshot_path)
    
    f_screen = None
    f_template = None
    
    try:
        f_screen = open(screenshot_path, 'rb')
        files = {'screenshot': ('screen.png', f_screen, 'image/png')}
        data = {}
        
        if target_text:
            data['target_text'] = target_text
            
        if image_path and os.path.exists(image_path):
            f_template = open(image_path, 'rb')
            files['template'] = ('template.png', f_template, 'image/png')
            
        response = requests.post(server_url, files=files, data=data, timeout=20)
        result = response.json()
        
        if result.get('found'):
            x, y = result['x'], result['y']
            method = result.get('method', '未知')
            print(f"[动作] 成功锁定 [{task_name}] ({method}模式) -> 坐标 ({x}, {y})，执行点击！")
            pyautogui.moveTo(x, y, duration=0.2)
            pyautogui.click()
            time.sleep(2) 
            return True
        return False
        
    except Exception as e:
        print(f"[网络错误] 请求服务器失败: {e}")
        return False
    finally:
        if f_screen: f_screen.close()
        if f_template: f_template.close()
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
def is_active_downloading(directory):
    if not os.path.exists(directory):
        return False
    five_minutes_ago = time.time() - 300
    
    # === 优化：限制局域网 I/O 深度，仅扫描表层及第一级子目录 ===
    try:
        # 只取当前目录下的文件和第一级子文件夹
        with os.scandir(directory) as it:
            for entry in it:
                # 如果表层直接有下载文件
                if entry.is_file() and entry.name.endswith('.qkdownloading'):
                    if entry.stat().st_mtime > five_minutes_ago:
                        return True
                
                # 如果是文件夹，往里面找一层就够了，坚决不往深了挖
                elif entry.is_dir():
                    try:
                        with os.scandir(entry.path) as sub_it:
                            for sub_entry in sub_it:
                                if sub_entry.is_file() and sub_entry.name.endswith('.qkdownloading'):
                                    if sub_entry.stat().st_mtime > five_minutes_ago:
                                        return True
                    except Exception:
                        continue # 子目录没权限或报错就跳过
    except Exception:
        pass
    return False

def main_loop():
    config = load_config()
    sys_conf = config['system']
    tasks = verify_and_manage_templates(config.get('tasks', []))
    
    debug_mode = sys_conf.get('debug_mode', False)
    
    if debug_mode:
        print("=== 🛠️ 调试模式 (DEBUG MODE) 已开启 🛠️ ===")
        print("[调试] 已绕过下载检测与防抖等待，将全速测试视觉识别逻辑！")
    else:
        print("=== 🚀 分布式双擎自动化下载终端 (YAML灵动版) 已启动 ===")
        
    idle_count = 0
    scan_count = 0 # 新增：用于防刷屏的心跳计数器
    
    while True:
        if not debug_mode:
            # 加入扫描提示，让你知道它在干活
            if scan_count % 6 == 0:  # 大约每分钟打印一次，防刷屏
                print(f"[{time.strftime('%H:%M:%S')}] 🔍 正在探测网络目录状态...")
            scan_count += 1
            
            if is_active_downloading(sys_conf['download_dir']):
                if idle_count > 0:
                    print("[状态] 虚惊一场，属于任务切换间隙，下载仍在继续。")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] 📥 发现活跃下载任务，继续安心挂机 zZ...")
                idle_count = 0 
                time.sleep(sys_conf['check_interval'])
                continue
                
            idle_count += 1
            if idle_count <= sys_conf['idle_confirm_times']:
                print(f"[防抖] 未检测到下载... 等待二次确认 ({idle_count}/{sys_conf['idle_confirm_times']})")
                time.sleep(sys_conf['idle_confirm_interval'])
                continue
                
            idle_count = 0 
            scan_count = 0
            print(f"\n[{time.strftime('%H:%M:%S')}] 🚨 确认当前真无活跃下载，开始依据 YAML 扫描屏幕 UI...")
        else:
            print(f"\n[{time.strftime('%H:%M:%S')}] 🛠️ [调试] 正在扫描屏幕目标...")
        
        # 核心点击逻辑
        action_taken = False
        for task in tasks:
            if find_and_click(sys_conf['server_url'], task):
                print(f"[逻辑] 已触发任务节点: {task.get('name')}")
                action_taken = True
                # break
                
        if not action_taken:
            print("[逻辑] 当前画面未命中任何 YAML 定义的目标，盲等中。")
            
        time.sleep(2 if debug_mode else sys_conf['check_interval'])

if __name__ == "__main__":
    pyautogui.FAILSAFE = True 
    main_loop()