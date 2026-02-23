pip install flask opencv-python numpy rapidocr_onnxruntime
 
client
pip install mss requests pyautogui

# 🚀 分布式双擎自动化下载终端 (Dual-Engine Download RPA)

本项目是一个专为复杂网络环境和虚拟机（VM）挂机设计的**分布式机器人流程自动化（RPA）系统**。采用“控制端（大脑）”与“执行端（四肢）”分离的 C/S 架构，旨在实现 24/7 无人值守的自动化下载任务流。



## ✨ 核心需求与实现目标

根据业务场景，本项目成功实现了以下核心定制需求：
1. **分布式跨平台执行**：Win11 物理机（AMD 8845HS）作为服务端提供算力，Win10 局域网虚拟机作为客户端负责轻量级挂机与点击。
2. **极速状态监控机制**：针对局域网共享路径 (`\\One\d\downloadD`) 进行深度 I/O 优化。仅扫描表层及“最近5分钟内有修改”的子文件夹，寻找 `.qkdownloading` 后缀，极大地降低了网络扫描的延迟和卡顿。
3. **混合双擎视觉定位**：
   * **引擎 1 (主)**：基于 OpenCV 的彩色模板精确匹配，速度极快（<20ms）。
   * **引擎 2 (备)**：基于 EasyOCR 的全屏文字识别。当 UI 更新、图片失效或变形时，自动无缝降级为文字查找（如寻找“下载”、“获取”），保证任务永不中断。
4. **高鲁棒性防御**：内置图像通道数强制转换防御（解决 `cv2.matchTemplate` 崩溃问题），以及 OCR 动态图像缩放机制（解决纯 CPU 运算导致的 `Read timed out` 请求超时问题）。

---

## 📂 项目结构

```text
auto_download_rpa/
│
├── server/                    # 部署于 Win11 宿主机 (大脑)
│   ├── server.py              # Flask 服务端主程序 (提供视觉 API)
│   └── templates/             # 存放 OpenCV 匹配所需的彩色截图库
│       ├── btn_download.png   # "下载" 按钮截图
│       └── btn_get.png        # "获取" 按钮截图
│
└── client/                    # 部署于 Win10 虚拟机 (四肢)
    └── client.py              # 客户端主程序 (状态机轮询、截图、模拟点击)


    pip install   rapidocr_onnxruntime opencv-python