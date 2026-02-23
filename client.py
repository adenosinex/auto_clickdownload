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
    """
    高效检查下载状态：
    1. 检查表层文件。
    2. 筛选出最近5分钟内修改过的文件夹，进入内部检查文件。
    """
    if not os.path.exists(directory): 
        print(f"[错误] 目录不存在: {directory}")
        return False
        
    current_time = time.time()
    five_minutes_ago = current_time - (5 * 60)
    
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                # 1. 检查表层的临时文件
                if entry.is_file() and entry.name.endswith('.qkdownloading'):
                    if entry.stat().st_mtime > five_minutes_ago:
                        print(f"[状态] 活跃下载中 (表层): {entry.name}")
                        return True
                        
                # 2. 检查最近 5 分钟内有变动的文件夹
                elif entry.is_dir():
                    if entry.stat().st_mtime > five_minutes_ago:
                        try:
                            with os.scandir(entry.path) as sub_entries:
                                for sub_entry in sub_entries:
                                    if sub_entry.is_file() and sub_entry.name.endswith('.qkdownloading'):
                                        if sub_entry.stat().st_mtime > five_minutes_ago:
                                            print(f"[状态] 活跃下载中 (内部): {entry.name}/{sub_entry.name}")
                                            return True
                        except Exception as e:
                            print(f"[系统] 扫描子文件夹 {entry.name} 出错: {e}")
                            
    except Exception as e: 
        print(f"[系统] 扫描主目录出错: {e}")
        
    return False

def find_and_click(target_img=None, target_text=None):
    """
    双擎寻路点击函数：优先请求服务器寻找 target_img 图片，若无则识别 target_text 文字。
    """
    screenshot_path = "temp_screen.png"
    
    # 1. 极速截图
    with mss.mss() as sct:
        sct.shot(mon=1, output=screenshot_path)
    
    try:
        # 2. 动态打包请求数据
        with open(screenshot_path, 'rb') as f:
            files = {'screenshot': ('screen.png', f, 'image/png')}
            data = {}
            if target_img: data['target_img'] = target_img
            if target_text: data['target_text'] = target_text
            
            # OCR可能耗时稍长，设置10秒超时防卡死
            response = requests.post(SERVER_URL, files=files, data=data, timeout=10)
            
        result = response.json()
        
        # 3. 解析结果并执行点击
        if result.get('found'):
            x, y = result['x'], result['y']
            method = result.get('method', '未知')
            target_name_display = target_img if method == 'image' else target_text
            print(f"[动作] 成功锁定 [{target_name_display}] ({method}模式) -> 坐标 ({x}, {y})，执行点击！")
            pyautogui.moveTo(x, y, duration=0.2)
            pyautogui.click()
            time.sleep(2) # 给软件UI反应的时间
            return True
        else:
            return False
            
    except Exception as e:
        print(f"[网络错误] 请求服务器失败: {e}")
        return False
    finally:
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

def main_loop():
    print("=== 终极混合自动化下载终端 已启动 ===")
    while True:
        if is_active_downloading(DOWNLOAD_DIR):
            # 状态 1：正常下载中，挂机等待
            time.sleep(CHECK_INTERVAL)
            continue
            
        print("\n[逻辑] 当前无活跃下载，开始分析 UI 状态...")
        
        # 状态 2：尝试寻找并点击“下载”按钮
        # 优先匹配 templates/btn_download.png，如果匹配失败，去屏幕上找“下载”这两个字
        if find_and_click(target_img='btn_download', target_text='高速下载'):
            print("[逻辑] 已启动新下载任务。")
            find_and_click(target_img='btn_get', target_text='并复制')
            time.sleep(CHECK_INTERVAL)
            continue
            
        # 状态 3：处理可能存在的获取/确认按钮
        # 优先匹配 templates/btn_get.png，如果匹配失败，去屏幕上找“获取”这两个字
        if find_and_click(target_img='btn_get', target_text='并复制'):
            print("[逻辑] 发现获取按钮，已点击。")
            time.sleep(CHECK_INTERVAL)
            continue
            
        # 状态 4：什么都没找到，盲等
        print("[逻辑] 当前画面无已知操作目标，等待下一次检查。")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # 安全锁：鼠标移到屏幕四角强制中断
    pyautogui.FAILSAFE = True 
    main_loop()