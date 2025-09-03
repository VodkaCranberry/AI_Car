#!/usr/bin/python
# -*- coding: utf-8 -*-
import zmq
import cv2
import numpy as np
import json
import subprocess
import psutil

import time, os, sys
# 使用相对导入，移除脆弱的sys.path修改
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from log_info import logger
from tools import get_yaml

def get_path_relative(*args):
    local_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(local_dir, *args)


def get_zmp_client(port):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    res = socket.connect(f"tcp://127.0.0.1:{port}")
    # print(res)
    return socket

def get_python_processes():

    # print("----------")
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower() and len(proc.info['cmdline']) > 1 and len(proc.info['cmdline'][1]) < 100:
                info = [proc.info['pid'], proc.info['cmdline'][1]]
                python_processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return python_processes
    # for process in python_processes:
    #     print(f"PID: {process['pid']}, Name: {process['name']}, Cmdline: {process['cmdline']}")
    # print("    ")

class Bbox:
    def __init__(self, box=None, rect=None, size=[640, 480]) -> None:
        self.size = np.array(size) / 2
        self.size_concat = np.concatenate((self.size, self.size))

        if box is not None:
            box_np = np.array(box)
            # 如果所有值的绝对值都小于1，表示归一化
            # np.abs(box_np, out=box_np)
            if (np.abs(box_np) < 2).all():
                self.box_normalise = box_np
                self.box = self.denormalise(box_np, self.size)
                # print(self.box)
            else:
                self.box = box_np
                self.box_normalise = self.normalise(box_np, self.size)
            self.rect = self.box_to_rect(self.box, self.size)
        elif rect is not None:
            self.rect = np.array(rect)
            self.box = self.rect_to_box(self.rect, self.size)
            self.box_normalise = self.normalise(self.box, self.size)

    def get_rect(self):
        return self.rect

    def get_box(self):
        return self.box

    @staticmethod
    def normalise(box, size):
        return box / np.concatenate((size, size))

    @staticmethod
    # 去归一化
    def denormalise(box_nor, size):
        return (box_nor * np.concatenate((size, size))).astype(np.int32)

    @staticmethod
    def rect_to_box(rect, size):
        pt_tl = rect[:2]
        pt_br = rect[2:]
        pt_center = (pt_tl + pt_br) / 2 - size
        box_wd = pt_br - pt_tl
        return np.concatenate((pt_center, box_wd)).astype(np.int32)

    @staticmethod
    def box_to_rect(box, size):
        pt_center = box[:2]
        box_wd = box[2:]
        pt_tl = (size + pt_center - box_wd / 2).astype(np.int32)
        pt_br = (size + pt_center + box_wd / 2).astype(np.int32)
        # print(pt_tl, pt_br)
        rect = np.concatenate((pt_tl, pt_br))
        # 限制最大最小值
        max_size = np.concatenate((size, size))*2
        # print(max_size)
        np.clip(rect, 0, max_size, out=rect)
        return rect

class ClintInterface:

    def __init__(self, name, local=True):
        self.local = local
        self.configs = get_yaml(get_path_relative('infer.yaml'))['infer_cfg']
        model_cfg = self.get_config(name)
        self.img_size = model_cfg['img_size']

        if self.local:
            logger.info("In local mode, init {}...".format(name))
            # Import inference classes here to avoid circular dependencies if they also use ClintInterface
            from paddle_jetson import YoloeInfer, LaneInfer, OCRReco, HummanAtrr, MotHuman
            # Create the inference instance directly
            self.infer_instance = eval(model_cfg['infer_type'])(*model_cfg['model'])
            # Pre-warm the model
            img = np.zeros((240, 240, 3), np.uint8)
            if self.img_size is not None:
                img = cv2.resize(img, self.img_size)
            self.infer_instance(img)
            logger.info("{} init ok in local mode".format(name))
        else:
            logger.info("{} connecting server...".format(name))
            self.client = self.get_zmp_client(model_cfg['port'])

            infer_back_end_file = "infer_back_end.py"
            # 检查后台程序是否运行, 如果未开启, 则开启
            self.check_back_python(infer_back_end_file)

            flag = False
            while True:
                if self.get_state():
                    if flag:
                        logger.info("")
                    break
                # 输出一个提示信息，不换行
                print('.', end='', flush=True)
                # logger.info(".")
                time.sleep(1)
                flag = True
            # print(self.client)
            # print("连接服务器成功")
            logger.info("{} connect server ok".format(name))

    def check_back_python(self, file_name):
        dir_file = os.path.abspath(os.path.dirname(__file__))
        file_path = os.path.join(dir_file, file_name)
        # print(file_path)
        if not os.path.exists(file_path):
            raise Exception("background script not exist")
        # 获取正在运行的python脚本
        py_lists = get_python_processes()
        for py_iter in py_lists:
            # 检测是否存在后台运行的脚本
            if file_name in py_iter[1]:
                return
        else:
            # 开启后台脚本，后台运行, 忽略输入输出
            # 使用subprocess调用脚本
            logger.info("start {} script, background running, please wait".format(file_name))
            cmd_str = 'python3 ' + file_path + ' &'
            # shell=True告诉subprocess模块在运行命令时使用系统的默认shell。这使得可以像在命令行中一样执行命令，包括使用通配符和其他shell特性
            subprocess.Popen(cmd_str, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            # 这里的> /dev/null 2>&1将标准输出和标准错误都重定向到/dev/null，实现与之前subprocess.Popen相同的效果
            # os.system(cmd_str + " > /dev/null 2>&1")


    def get_config(self, name):
        for conf in self.configs:
            if conf['name'] == name:
                return conf

    @staticmethod
    def get_zmp_client(port):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        res = socket.connect(f"tcp://127.0.0.1:{port}")
        # print(res)
        return socket

    def __call__(self, *args, **kwds):
        return self.get_infer(*args, **kwds)

    def get_state(self):
        data = bytes('ATATA', encoding='utf-8')
        self.client.send(data)
        # 接收服务器数据
        response = self.client.recv()

        # 把bytes转为json
        response = json.loads(response)
        return response

    def get_infer(self, img):
        # 图像预处理
        if self.img_size is not None:
            img = cv2.resize(img, self.img_size)

        if self.local:
            # Directly call the local inference instance
            return self.infer_instance(img)
        else:
            # Use the existing network logic
            # 使用PNG无损压缩图像
            _, img_encoded = cv2.imencode('.png', img)

            # 发送多部分消息：第一部分是信令，第二部分是压缩后的图像数据
            self.client.send_multipart([
                b'image_compressed',
                img_encoded.tobytes()
            ])

            # 接收服务器数据
            response = self.client.recv()

            # 把bytes转为json
            response = json.loads(response)
            return response

def main_client():
    # Create a dummy black image for testing without a camera
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    from camera import Camera
    camera = Camera(3, 640, 480)
    # infer_client = ClintInterface('lane')
    infer_client2 = ClintInterface("ocr")
    infer_client1 = ClintInterface('task')
    # infer_client = ClintInterface('mot')
    # infer_client = ClintInterface('front')
    last_time = time.time()
    while True:
        # Use a cropped version of the dummy image
        img = camera.read()
        dets_ret = infer_client1.get_infer(img)
        print(dets_ret)

        frame_boxes = []
        for det in dets_ret:
            if str(det.label_name) == '0':
                _, _, _, _, x_c, y_c, w, h = det
                H, W = img.shape[:2]

                x1 = int(W * ((1 + x_c) / 2 - w / 2))
                y1 = int(H * ((1 + y_c) / 2 - h / 2))
                x2 = int(W * ((1 + x_c) / 2 + w / 2))
                y2 = int(H * ((1 + y_c) / 2 + h / 2))
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(W, x2), min(H, y2)
                roi = img[y1:y2, x1:x2]
                frame_boxes.append({
                        'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                        'roi': roi
                    })
                print(infer_client2.get_infer(roi))

        # Display the dummy image
        #cv2.imshow("img", img)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

        fps = 1 / (time.time() - last_time)
        last_time = time.time()
        print("fps:", fps)
        time.sleep(1) # Add a delay to avoid flooding the console

    cv2.destroyAllWindows()

def stop_process(py_str):
    py_lists = get_python_processes()
    print(py_lists)
    for py_procees in py_lists:
        pid_id, py_name = py_procees[0], py_procees[1]
        # print(pid_id, py_name)
        if py_str in py_procees[1]:
            psutil.Process(pid_id).terminate()
            print("stop", py_name)
            return


if __name__ == '__main__':
    import argparse
    args = argparse.ArgumentParser()
    args.add_argument('--op', type=str, default="infer")
    args = args.parse_args()
    print(args)
    if args.op == "infer":
        main_client()
    if args.op == "stop":
        stop_process("infer_back_end.py")
