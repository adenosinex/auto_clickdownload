from flask import Flask, request, jsonify
import cv2
import numpy as np
import os
from rapidocr_onnxruntime import RapidOCR

app = Flask(__name__)

# --- 初始化 1：加载模板图库 ---
TEMPLATES_DIR = 'templates'
templates_db = {}
if os.path.exists(TEMPLATES_DIR):
    for filename in os.listdir(TEMPLATES_DIR):
        if filename.endswith('.png') or filename.endswith('.PNG'):
            name = filename.split('.')[0]
            path = os.path.join(TEMPLATES_DIR, filename)
            img = cv2.imread(path, 0)
            if img is not None:
                h, w = img.shape
                templates_db[name] = {'image': img, 'w': w, 'h': h}
                print(f"[图库] 成功加载模板图片: {name}.png")

# 初始化改为：
print("[系统] 正在加载 RapidOCR 极速识别模型...")
engine = RapidOCR()
print("[系统] OCR 模型加载完毕！")


@app.route('/api/find_target', methods=['POST'])
def find_target():
    if 'screenshot' not in request.files:
        return jsonify({'error': '未收到截图'}), 400
        
    target_img = request.form.get('target_img')   # 期望的图片模板名
    target_text = request.form.get('target_text') # 期望寻找的文字
    
    # 接收截图并解码为内存数组
    file = request.files['screenshot']
    in_memory_file = file.read()
    nparr = np.frombuffer(in_memory_file, np.uint8)
    
    # 彩色图留给 OCR 用，转换为灰度图给 OpenCV 用
    img_color = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
   
  # ==========================================
    # 引擎 1：精确图像匹配 (OpenCV 彩色模式)
    # ==========================================
    if target_img and target_img in templates_db:
        target_data = templates_db[target_img]
        template = target_data['image']
        w, h = target_data['w'], target_data['h']
        
        # 【新增：终极防崩溃装甲 - 强制统一通道数】
        # 1. 确保模板图 (template) 是标准 3 通道 BGR 彩色图
        if len(template.shape) == 2: 
            template = cv2.cvtColor(template, cv2.COLOR_GRAY2BGR)
        elif len(template.shape) == 3 and template.shape[2] == 4: 
            template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
            
        # 2. 确保客户端截图 (img_color) 也是标准 3 通道 BGR
        if len(img_color.shape) == 2:
            img_color = cv2.cvtColor(img_color, cv2.COLOR_GRAY2BGR)
        elif len(img_color.shape) == 3 and img_color.shape[2] == 4:
            img_color = cv2.cvtColor(img_color, cv2.COLOR_BGRA2BGR)

        # 3. 尺寸防御：防止极端情况下截图比模板还小导致崩溃
        if img_color.shape[0] < template.shape[0] or img_color.shape[1] < template.shape[1]:
            print(f"[引擎1失效] 截图尺寸小于模板尺寸，无法匹配。")
        else:
            # 此时两张图格式绝对一致，放心匹配
            res = cv2.matchTemplate(img_color, template, cv2.TM_CCOEFF_NORMED)
            threshold = 0.6
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            if max_val >= threshold:
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                print(f"[命中] 彩色图片 '{target_img}' 匹配成功！(置信度: {max_val:.2f})")
                return jsonify({'found': True, 'x': center_x, 'y': center_y, 'method': 'image'})
            else:
                print(f"[降级] 图片 '{target_img}' 匹配失败 (置信度 {max_val:.2f} < 0.8)，准备切换至 OCR...")
    elif target_img:
        print(f"[降级] 图库中不存在 '{target_img}.png'，准备切换至 OCR...")
    cv2.imwrite("debug_screen.png", img_color)  # 调试用：保存接收到的截图
# ==========================================
    # 引擎 2：鲁棒文字识别 (rapidOCR 灰度模式)
    # ==========================================
    if target_text:
        print(f"[OCR] 正在扫描文字，寻找: '{target_text}' ...")
        
        # RapidOCR 接受 numpy 数组，直接传 img_color 即可
        # 返回格式：[[[左上, 右上, 右下, 左下], '文字', 置信度], ...]
        result, _ = engine(img_color)
        
        if result:
            for bbox, text, conf in result:
                if target_text in text:
                    # 解析坐标 (取对角线计算中心点)
                    top_left = bbox[0]
                    bottom_right = bbox[2]
                    center_x = int((top_left[0] + bottom_right[0]) / 2)
                    center_y = int((top_left[1] + bottom_right[1]) / 2)
                    
                    print(f"[命中] 文字 '{text}' 识别成功！(置信度: {conf:.2f})")
                    return jsonify({'found': True, 'x': center_x, 'y': center_y, 'method': 'ocr'})
                
        print(f"[失效] 屏幕上未找到包含 '{target_text}' 的文字。")
   
    return jsonify({'found': False})

if __name__ == '__main__':
    # 你指定的端口 5010
    app.run(host='0.0.0.0', port=5010, debug=True)