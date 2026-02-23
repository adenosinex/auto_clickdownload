import os
import time
import requests
import mss
import pyautogui

# --- 配置区 ---
SERVER_URL = "http://15x4.zin6.dpdns.org:5010/api/find_target" 
DOWNLOAD_DIR = r"\\One\d\downloadD" 
CHECK_INTERVAL = 10

IDLE_CONFIRM_TIMES = 2     # 需要连续几次确认无下载
IDLE_CONFIRM_INTERVAL = 5  # 确认期间的等待间隔(秒)

# --------------
import os
import time

def is_active_downloading(directory):
    """
    使用 os.walk 递归检查所有层级的 .qkdownloading 文件。
    """
    if not os.path.exists(directory):
        print(f"[错误] 目录不存在: {directory}")
        return False
    
    five_minutes_ago = time.time() - 300
    
    try:
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith('.qkdownloading'):
                    filepath = os.path.join(root, filename)
                    try:
                        if os.path.getmtime(filepath) > five_minutes_ago:
                            rel_path = os.path.relpath(filepath, directory)
                            print(f"[状态] 活跃下载中: {rel_path}")
                            return True
                    except OSError:
                        continue  # 跳过无法访问的文件
    except PermissionError:
        print(f"[警告] 无权限访问: {directory}")
    except Exception as e:
        print(f"[系统] 扫描出错: {e}")
    
    return False
def find_and_click(target_img=None, target_text=None,click=True):
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
            response = requests.post(SERVER_URL, files=files, data=data, timeout=20)
            
        result = response.json()
        if not click:
            return result.get('found')
        
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
    idle_count = 0
    while True:
        if is_active_downloading(DOWNLOAD_DIR):
            if idle_count > 0:
                print("[状态] 虚惊一场，属于任务切换间隙，下载仍在继续。")
            
            # 只要检测到在下载，立刻把计数器清零，安心挂机
            idle_count = 0 
            time.sleep(CHECK_INTERVAL)
            continue
            
        # =========================================
        # 核心防抖逻辑：没检测到下载，先别急着去点屏幕
        # =========================================
        idle_count += 1
        if idle_count <= IDLE_CONFIRM_TIMES:
            print(f"[防抖] 未检测到下载。可能是任务切换或合并中，等待二次确认... ({idle_count}/{IDLE_CONFIRM_TIMES})")
            time.sleep(IDLE_CONFIRM_INTERVAL) # 等待 5 秒后再查一次
            continue # 跳过下面的点击逻辑，重新进入 while 循环检查
            
        # =========================================
        # 真正确认空闲：连续 N 次都没在下载
        # =========================================
        idle_count = 0 # 触发操作前，记得把计数器清零
        print("\n[逻辑] 确认当前真无活跃下载，开始分析 UI 状态...")
        
            
        
        # 状态 2：尝试寻找并点击“下载”按钮
        # 优先匹配 templates/btn_download.png，如果匹配失败，去屏幕上找“下载”这两个字
        if not find_and_click(target_img='btn_download', target_text='高速下载',click=False):
            find_and_click(target_img='btn_get', target_text='并复制')
        time.sleep(3)
        if find_and_click(target_img='btn_download', target_text='高速下载'):
            print("[逻辑] 已启动新下载任务。")
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