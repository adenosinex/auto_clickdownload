# server.py (大脑)
from flask import Flask, request, jsonify
import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR

app = Flask(__name__)

print("[系统] 正在加载 RapidOCR 极速识别模型...")
engine = RapidOCR()
print("[系统] OCR 模型加载完毕！")

@app.route('/api/find_target', methods=['POST'])
def find_target():
    if 'screenshot' not in request.files:
        return jsonify({'error': '未收到截图'}), 400
        
    target_text = request.form.get('target_text') # 期望寻找的文字
    
    # 1. 接收截图并解码为标准 BGR 彩色矩阵
    file_screen = request.files['screenshot']
    img_color = cv2.imdecode(np.frombuffer(file_screen.read(), np.uint8), cv2.IMREAD_COLOR)
    
    # ==========================================
    # 引擎 1：精确图像匹配 (接收客户端传来的模板图片)
    # ==========================================
    if 'template' in request.files:
        file_template = request.files['template']
        # imdecode 读取时通过 IMREAD_COLOR 直接统一为3通道，省去了原先繁琐的通道防御代码
        template_color = cv2.imdecode(np.frombuffer(file_template.read(), np.uint8), cv2.IMREAD_COLOR)
        
        if template_color is not None:
            # 尺寸防御：防止截图比模板还小导致崩溃
            if img_color.shape[0] < template_color.shape[0] or img_color.shape[1] < template_color.shape[1]:
                print(f"[引擎1失效] 截图尺寸小于模板尺寸，无法匹配。")
            else:
                res = cv2.matchTemplate(img_color, template_color, cv2.TM_CCOEFF_NORMED)
                threshold = 0.6
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                
                if max_val >= threshold:
                    h, w = template_color.shape[:2]
                    center_x = max_loc[0] + w // 2
                    center_y = max_loc[1] + h // 2
                    print(f"[命中] -{target_text} 客户端模板图片匹配成功！(置信度: {max_val:.2f})")
                    return jsonify({'found': True, 'x': center_x, 'y': center_y, 'method': 'image'})
                else:
                    print(f"[降级] 图片匹配失败 (置信度 {max_val:.2f} < {threshold})，准备切换至 OCR...")

    # ==========================================
    # 引擎 2：鲁棒文字识别 (RapidOCR)
    # ==========================================
    if target_text:
        print(f"[OCR] 正在扫描文字，寻找: '{target_text}' ...")
        result, _ = engine(img_color)
        
        if result:
            for bbox, text, conf in result:
                if target_text in text:
                    top_left, _, bottom_right, _ = bbox
                    center_x = int((top_left[0] + bottom_right[0]) / 2)
                    center_y = int((top_left[1] + bottom_right[1]) / 2)
                    
                    print(f"[命中] 文字 '{text}' 识别成功！(置信度: {conf:.2f})")
                    return jsonify({'found': True, 'x': center_x, 'y': center_y, 'method': 'ocr'})
                    
        print(f"[失效] 屏幕上未找到包含 '{target_text}' 的文字。")
   
    return jsonify({'found': False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True)