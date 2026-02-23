import time
import cv2
import os

# 检查测试图片是否存在
img_path = 'debug_screen.png'
if not os.path.exists(img_path):
    print(f"❌ 找不到测试图片 '{img_path}'，请先放一张截图在同目录下！")
    exit()

print(f"正在读取图片: {img_path}")
img = cv2.imread(img_path)

print("\n" + "="*50)
print(" 🥊 第一回合：EasyOCR (PyTorch 引擎)")
print("="*50)
try:
    import easyocr
    
    # 1. 测试模型加载时间
    t0 = time.time()
    # 第一次运行可能会下载模型，忽略第一次的加载时间
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)
    t1 = time.time()
    print(f"[加载耗时] EasyOCR 模型载入: {t1 - t0:.3f} 秒")
    
    # 2. 测试推理时间
    t2 = time.time()
    result_easy = reader.readtext(img)
    t3 = time.time()
    print(f"[推理耗时] EasyOCR 识别全屏: {t3 - t2:.3f} 秒")
    
    # 3. 打印结果 (只打印置信度大于 0.5 的)
    print("\n[识别结果提取]:")
    for bbox, text, conf in result_easy:
        if conf > 0.5:
            print(f"  - 文字: '{text}' (置信度: {conf:.2f})")
            
except Exception as e:
    print(f"EasyOCR 运行报错: {e}")


print("\n" + "="*50)
print(" 🥊 第二回合：RapidOCR (ONNXRuntime 引擎)")
print("="*50)
try:
    from rapidocr_onnxruntime import RapidOCR
    
    # 1. 测试模型加载时间
    t4 = time.time()
    engine = RapidOCR()
    t5 = time.time()
    print(f"[加载耗时] RapidOCR 模型载入: {t5 - t4:.3f} 秒")
    
    # 2. 测试推理时间
    t6 = time.time()
    result_rapid, _ = engine(img)
    t7 = time.time()
    print(f"[推理耗时] RapidOCR 识别全屏: {t7 - t6:.3f} 秒")
    
    # 3. 打印结果
    print("\n[识别结果提取]:")
    if result_rapid:
        for bbox, text, conf in result_rapid:
            # RapidOCR 返回的 confidence 可能是字符串，处理一下
            conf_val = float(conf)
            if conf_val > 0.5:
                print(f"  - 文字: '{text}' (置信度: {conf_val:.2f})")
    else:
        print("  - 未识别到任何文字。")
        
except Exception as e:
    print(f"RapidOCR 运行报错: {e}")

print("\n" + "="*50)
print(" 🎉 测试结束！请对比上面的 [推理耗时] 和 [识别结果提取]")