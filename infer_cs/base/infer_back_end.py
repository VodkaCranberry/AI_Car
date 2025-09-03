# --*-- coding: utf-8 --*--
# infer_back_end.py

import zmq, json, cv2
import numpy as np
from threading import Thread
from infer_front import ClintInterface
import time, os, sys
# 使用相对导入，移除脆弱的sys.path修改
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ..tools import get_yaml
def get_path_relative(*args):
    local_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(local_dir, *args)

class InferServer:
    def __init__(self):
        # 导入推理客户端的配置
        # configs = ClintInterface.configs
        configs = get_yaml(get_path_relative('infer.yaml'))['infer_cfg']

        self.flag_infer_initok = False

        self.flag_end = False
        # 开启对应的线程和服务
        self.threads_list = []
        self.server_dict = {}

        # self.lane_server = self.get_server(5001)
        for conf in configs:
            # 创建获取zmq服务
            server = self.get_server(conf['port'])
            self.server_dict[conf['name']] = server
            # 创建线程
            # thread_tmp = Thread(target=eval('self.'+conf['name']+'_process'))
            # 带参数线程，此处参数为各种推理模型
            thread_tmp = Thread(target=self.process_demo, args=(conf['name'],))
            # thread_tmp = Thread(target=self.lane_process)
            thread_tmp.daemon = True
            thread_tmp.start()
            # 添加进程
            self.threads_list.append(thread_tmp)

        from paddle_jetson import YoloeInfer, LaneInfer, OCRReco, HummanAtrr, MotHuman
        # 创建推理模型
        self.infer_dict = {}
        for conf in configs:
            # 创建推理模型, eval字符转为对象
            # print(*conf['model'])
            infer_tmp = eval(conf['infer_type'])(*conf['model'])
            self.infer_dict[conf['name']] = infer_tmp

        # 创建推理模型
        # self.lane_infer = LaneInfer()
        # self.front_infer = YoloInfer("front_model2") # "trt_fp32")
        # self.task_infer = YoloInfer("task_model3") # "trt_fp32")
        # self.ocr_infer = OCRReco()
        # self.humattr_infer = HummanAtrr()
        # self.mot_infer = MotHuman()

        # 新建一个空白图片，用于预先图片推理
        img = np.zeros((240, 240, 3), np.uint8)
        # 预加载推理几张图片，刚开始推理时速度慢，会有卡顿
        for i in range(3):
            for conf in configs:
                infer_tmp = self.infer_dict[conf['name']]
                infer_tmp(img)
        print("infer init ok")

        self.flag_infer_initok = True


    def get_server(self, port):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind(f"tcp://127.0.0.1:{port}")
        return socket

    def process_demo(self, name):

        print(time.strftime("%Y-%m-%d %H:%M:%S"), "{} process start".format(name))
        server:zmq.Socket = self.server_dict[name]
        # 预先准备好推理函数，避免在循环中重复查找和创建
        infer_func = self.infer_dict[name]

        while True:
            if self.flag_end:
                return

            parts = server.recv_multipart()
            head = parts[0]
            res = []

            if head == b"ATATA":
                if self.flag_infer_initok:
                    res = True
                else:
                    res = False
            elif head == b"image" or head == b"image_compressed":
                img = None
                if head == b"image":
                    # 从元数据和原始字节中重建numpy数组，无解码开销
                    metadata = json.loads(parts[1])
                    img = np.frombuffer(parts[2], dtype=np.dtype(metadata['dtype'])).reshape(metadata['shape'])
                elif head == b"image_compressed":
                    # 从压缩数据中解码图像
                    img_encoded = np.frombuffer(parts[1], dtype=np.uint8)
                    img = cv2.imdecode(img_encoded, cv2.IMREAD_COLOR)

                if img is not None and self.flag_infer_initok:
                    # 直接调用预先准备好的函数
                    res = infer_func(img, True)

            json_data = json.dumps(res)
            json_data = bytes(json_data, encoding='utf-8')
            server.send(json_data)

    def close(self):
        print("closing...")
        self.flag_end = True
        for thread in self.threads_list:
            # 等待结束
            thread.join()
            # 关闭
            thread.close()

def main():
    infer_back = InferServer()

    while True:
        try:
            time.sleep(1)
        except Exception as e:
            print(e)
            break
    time.sleep(0.1)
    infer_back.close()

if __name__ == "__main__":
    main()
