import os
import time
import requests
import mss
import pyautogui

# --- 配置区 ---
SERVER_URL = "http://15x4.zin6.dpdns.org:5010/api/find_target" 
DOWNLOAD_DIR = r"\\One\d\downloadD" 
CHECK_INTERVAL = 10 
# --------------

def is_active_downloading(directory):
    # (此函数保持与之前完全一致，检查 .qkdownloading 的修改时间)
    if not os.path.exists(directory): return False
    current_time = time.time()
    five_minutes_ago = current_time - (5 * 60)
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.endswith('.qkdownloading'):
                    if entry.stat().st_mtime > five_minutes_ago:
                        print(f"[状态] 活跃下载中: {entry.name}")
                        return True
    except Exception as e: print(f"[系统] 扫描出错: {e}")
    return False
 
def find_and_click(target_name):
    """
    通用寻图点击函数：截取屏幕，请求服务器寻找 target_name，如果找到则点击并返回 True。
    """
    screenshot_path = "temp_screen.png"
    
    # 1. 极速截图
    with mss.mss() as sct:
        sct.shot(mon=1, output=screenshot_path)
    
    try:
        # 2. 发送截图和 target_name 给服务器
        with open(screenshot_path, 'rb') as f:
            files = {'screenshot': ('screen.png', f, 'image/png')}
            data = {'target_name': target_name}
            response = requests.post(SERVER_URL, files=files, data=data, timeout=5)
            
        result = response.json()
        
        # 3. 解析结果并执行点击
        if result.get('found'):
            x, y = result['x'], result['y']
            print(f"[动作] 成功点击目标 [{target_name}] -> 坐标 ({x}, {y})")
            pyautogui.moveTo(x, y, duration=0.2)
            pyautogui.click()
            time.sleep(2) # 给软件UI反应的时间
            return True
        else:
            return False
            
    except Exception as e:
        print(f"[网络错误] 请求失败: {e}")
        return False
    finally:
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

def main_loop():
    print("=== 高级自动化下载终端已启动 ===")
    while True:
        if is_active_downloading(DOWNLOAD_DIR):
            # 状态 1：正常下载中，挂机等待
            time.sleep(CHECK_INTERVAL)
            continue
            
        print("\n[逻辑] 当前无活跃下载，开始分析 UI 状态...")
        
        # 状态 2：尝试寻找并点击正常的“下载”按钮
        if find_and_click('btn_download'):
            print("[逻辑] 已启动新下载任务。")
            time.sleep(CHECK_INTERVAL)
            continue
            
        find_and_click('btn_get')
            
        # 状态 5：什么都没找到，盲等
        print("[逻辑] 当前画面无已知操作目标，等待下一次检查。")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    pyautogui.FAILSAFE = True 
    main_loop()