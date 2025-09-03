#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import threading
import os
import platform
import signal
from camera import Camera
import numpy as np
from vehicle import ArmBase, ScreenShow, Key4Btn, Infrared, LedLight,CarBase, Beep
from simple_pid import PID
import difflib
import cv2, math
from task_func import MyTask
from infer_cs import ClintInterface, Bbox
from ernie_bot import ErnieBotWrap, ActionPrompt, HumAttrPrompt,FoodPrompt,TaskAnswerPrompt,IngredientsAnswerAnalysisPrompt
from tools import CountRecord, get_yaml, IndexWrap
import sys, os

# 添加上本地目录
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from log_info import logger

def sellect_program(programs, order, win_order):
    dis_str = ''
    start_index = 0

    start_index = order - win_order
    for i, program in enumerate(programs):
        if i < start_index:
            continue

        now = str(program)
        if i == order:
            now = '>>> ' + now
        else:
            now = str(i+1) + '.' + now
        if len(now) >= 19:
            now = now[:19]
        else:
            now = now + '\n'
        dis_str += now
        if i-start_index == 4:
            break
    return dis_str

def kill_other_python():
    import psutil
    pid_me = os.getpid()
    # logger.info("my pid ", pid_me, type(pid_me))
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower() and len(proc.info['cmdline']) > 1 and len(proc.info['cmdline'][1]) < 30:
                python_processes.append(proc.info)
        # 出现异常的时候捕获 不存在的异常，权限不足的异常， 僵尸进程
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    for process in python_processes:
        # logger.info(f"PID: {process['pid']}, Name: {process['name']}, Cmdline: {process['cmdline']}")
        # logger.info("this", process['pid'], type(process['pid']))
        if int(process['pid']) != pid_me:
            os.kill(int(process['pid']), signal.SIGKILL)
            time.sleep(0.3)

def limit(value, value_range):
    return max(min(value, value_range), 0-value_range)

# 两个pid集合成一个
class PidCal2():
    def __init__(self, cfg_pid_y=None, cfg_pid_angle=None):
        self.pid_y = PID(**cfg_pid_y)
        self.pid_angle = PID(**cfg_pid_angle)

    def get_out(self, error_y, error_angle):
        pid_y_out = self.pid_y(error_y)
        pid_angle_out = self.pid_angle(error_angle)
        return pid_y_out, pid_angle_out

class LanePidCal():
    def __init__(self, cfg_pid_y=None, cfg_pid_angle=None):
        # y_out_limit = 0.7
        # self.pid_y = PID(5, 0, 0)
        # self.pid_y.setpoint = 0
        # self.pid_y.output_limits = (-y_out_limit, y_out_limit)
        # print(cfg_pid_y)
        # print(cfg_pid_angle)
        self.pid_y = PID(**cfg_pid_y)
        # print(self.pid_y)

        angle_out_limit = 1.5
        self.pid_angle = PID(3, 0, 0)
        self.pid_angle.setpoint = 0
        self.pid_angle.output_limits = (-angle_out_limit, angle_out_limit)

    def get_out(self, error_y, error_angle):
        pid_y_out = self.pid_y(error_y)
        pid_angle_out = self.pid_angle(error_angle)
        return pid_y_out, pid_angle_out

class DetPidCal():
    def __init__(self, cfg_pid_y=None, cfg_pid_angle=None):
        y_out_limit = 0.7
        self.pid_y = PID(0.3, 0, 0)
        self.pid_y.setpoint = 0
        self.pid_y.output_limits = (-y_out_limit, y_out_limit)

        angle_out_limit = 1.5
        self.pid_angle = PID(2, 0, 0)
        self.pid_angle.setpoint = 0
        self.pid_angle.output_limits = (-angle_out_limit, angle_out_limit)

    def get_out(self, error_y, error_angle):
        pid_y_out = self.pid_y(error_y)
        pid_angle_out = self.pid_angle(error_angle)
        return pid_y_out, pid_angle_out


class LocatePidCal():
    def __init__(self):
        y_out_limit = 0.3
        self.pid_y = PID(0.5, 0, 0)
        self.pid_y.setpoint = 0
        self.pid_y.output_limits = (-y_out_limit, y_out_limit)

        x_out_limit = 0.3
        self.pid_x = PID(0.5, 0, 0)
        self.pid_x.setpoint = 0
        self.pid_x.output_limits = (-x_out_limit, x_out_limit)

    def set_target(self, x, y):
        self.pid_y.setpoint = y
        self.pid_x.setpoint = x

    def get_out(self, error_x, error_y):
        pid_y_out = self.pid_y(error_y)
        pid_x_out = self.pid_x(error_x)
        return pid_x_out, pid_y_out

class MyCar(CarBase):
    STOP_PARAM = True
    def __init__(self):
        # 调用继承的初始化
        start_time = time.time()
        super(MyCar, self).__init__()
        logger.info("my car init ok {}".format(time.time() - start_time))
        # 任务
        self.task = MyTask()
        # 显示
        self.display = ScreenShow()

        # 获取自己文件所在的目录路径
        self.path_dir = os.path.abspath(os.path.dirname(__file__))
        self.yaml_path = os.path.join(self.path_dir, "config_car.yml")
        # 获取配置
        cfg = get_yaml(self.yaml_path)
        # 根据配置设置sensor
        self.sensor_init(cfg)

        self.car_pid_init(cfg)
        self.ring = Beep()
        self.camera_init(cfg)
        # paddle推理初始化
        self.paddle_infer_init()
        # 文心一言分析初始化
        self.ernie_bot_init()

        # 相关临时变量设置
        # 程序结束标志
        self._stop_flag = False
        # 按键线程结束标志
        self._end_flag = False
        self.thread_key = threading.Thread(target=self.key_thread_func)
        self.thread_key.setDaemon(True)
        self.thread_key.start()

        self.beep()

        self.food_names = []   #以获取的食材名字
        # self.food_names = ["番茄","鸡肉"]
        # self.food_names = ["芹菜","绿叶蔬菜"]
        # self.food_names = ["西红柿","鸡蛋"]
    def beep(self):
        self.ring.rings()
        time.sleep(0.2)

    def sensor_init(self, cfg):
        cfg_sensor = cfg['io']
        # print(cfg_sensor)
        self.key = Key4Btn(cfg_sensor['key'])
        self.light = LedLight(cfg_sensor['light'])
        self.left_sensor = Infrared(cfg_sensor['left_sensor'])
        self.right_sensor = Infrared(cfg_sensor['right_sensor'])

    def car_pid_init(self, cfg):
        # lane_pid_cfg = cfg['lane_pid']
        # self.pid_y = PID(lane_pid_cfg['y'], 0, 0)
        # self.lane_pid = LanePidCal(**cfg['lane_pid'])
        # self.det_pid = DetPidCal(**cfg['det_pid'])
        self.lane_pid = PidCal2(**cfg['lane_pid'])
        self.det_pid = PidCal2(**cfg['det_pid'])

    def camera_init(self, cfg):
        # 初始化前后摄像头设置
        self.cap_front = Camera(cfg['camera']['front'])
        # 侧面摄像头
        self.cap_side = Camera(cfg['camera']['side'])

    def paddle_infer_init(self):
        self.crusie = ClintInterface('lane')
        # 前置左右方向识别
        self.front_det = ClintInterface('front')
        # 任务识别
        self.task_det = ClintInterface('task')
        # ocr识别
        self.ocr_rec = ClintInterface('ocr')
        # 识别为None
        self.last_det = None

    def ernie_bot_init(self):
        # self.bmi_analysis = ErnieBotWrap()
        # self.bmi_analysis.set_promt(str(BmiPrompt()))

        self.action_bot = ErnieBotWrap()
        self.action_bot.set_promt(str(ActionPrompt()))

        #获取食材标签和名字
        self.food_analysis = ErnieBotWrap()
        self.food_analysis.set_promt(str(FoodPrompt()))

        # #获取食材位置
        # self.location_analysis = ErnieBotWrap()
        # self.location_analysis.set_promt(str(LocationPrompt()))

        #
        self.answer_analysis = ErnieBotWrap()
        self.answer_analysis.set_promt(str(TaskAnswerPrompt()))

        self.ingredients_answer_analysis = ErnieBotWrap()
        self.ingredients_answer_analysis.set_promt(str(IngredientsAnswerAnalysisPrompt()))

    @staticmethod
    def get_cfg(path):
        from yaml import load, Loader
        # 把配置文件读取到内存
        with open(path, 'r') as stream:
            yaml_dict = load(stream, Loader=Loader)
        port_list = yaml_dict['port_io']
        # 转化为int
        for port in port_list:
            port['port'] = int(port['port'])
        # print(yaml_dict)

    # 延时函数
    def delay(self, time_hold):
        start_time = time.time()
        while True:
            if self._stop_flag:
                return
            if time.time() - start_time > time_hold:
                break

    # 按键检测线程
    def key_thread_func(self):
        while True:
            if not self._stop_flag:
                if self._end_flag:
                    return
                key_val = self.key.get_key()
                # print(key_val)
                if key_val == 3:
                    self._stop_flag = True
                time.sleep(0.2)
    

    # 根据某个值获取列表中匹配的结果
    @staticmethod
    def get_list_by_val(list, index, val):
        for det in list:
            if det[index] == val:
                return det
        return None

    def move_base(self, sp, end_fuction, stop=STOP_PARAM):
        self.set_velocity(sp[0], sp[1], sp[2])
        while True:
            if self._stop_flag:
                return
            if end_fuction():
                break
            self.set_velocity(sp[0], sp[1], sp[2])
        if stop:
            self.set_velocity(0, 0, 0)


    #  高级移动，按着给定速度进行移动，直到满足条件
    def move_advance(self, sp, value_h=None, value_l=None, times=1, sides=1, dis_out=0.2, stop=STOP_PARAM):
        if value_h is None:
            value_h = 1200
        if value_l is None:
            value_l = 0
        _sensor_usr = self.left_sensor
        if sides == -1:
            _sensor_usr = self.right_sensor
        # 用于检测开始过渡部分的标记
        flag_start = False
        def end_fuction():
            nonlocal flag_start
            val_sensor = _sensor_usr.read()
            # print("val:", val_sensor)
            if val_sensor < value_h and val_sensor > value_l:
                return flag_start
            else:
                flag_start = True
                return False
        for i in range(times):
            self.move_base(sp, end_fuction, stop=False)
        if stop:
            self.stop()


    def move_time(self, sp, dur_time=1, stop=STOP_PARAM):
        end_time = time.time() + dur_time
        end_func = lambda: time.time() > end_time
        self.move_base(sp, end_func, stop)

    def move_distance(self, sp, dis=0.1, stop=STOP_PARAM):
        end_dis = self.get_dis_traveled() + dis
        end_func = lambda: self.get_dis_traveled() > end_dis
        self.move_base(sp, end_func, stop)

    # 计算两个坐标的距离
    def calculation_dis(self, pos_dst, pos_src):
        return math.sqrt((pos_dst[0] - pos_src[0])**2 + (pos_dst[1] - pos_src[1])**2)

    def det2pose(self, det, w_r=0.06):
        # r 真实  v 成像  f 焦点
        # rf 真实到焦点的距离  vf 相到焦点的距离
        vf_dis = 1.445
        x_v, y_v, w_v, h_v = det

        rf_dis = vf_dis * w_r / w_v
        x_r = x_v * rf_dis / vf_dis
        y_r = y_v * rf_dis / vf_dis
        return x_r, y_r, rf_dis

    # 侧面摄像头进行位置定位
    def lane_det_location(self, speed, pts_tar=[[0, 70, 0,  0, 0, 0, 0.70, 0.70]], dis_out=0.05, side=1, time_out=2, det='task', crop_mid=False, threshold=0.01):
        end_time = time.time() + time_out
        infer = self.task_det
        loc_pid = get_yaml(self.yaml_path)["location_pid"]
        pid_x = PID(**loc_pid["pid_x"])
        pid_x.output_limits = (-speed, speed)
        pid_y = PID(**loc_pid["pid_y"])
        pid_y.output_limits = (-0.15, 0.15)
        # pid_w = PID(1.0, 0, 0.00, setpoint=0, output_limits=(-0.15, 0.15))

        # 用于相同记录结果的计数类
        x_count = CountRecord(5)
        dis_count = CountRecord(5)

        out_x = speed
        out_y = 0

        # 此时设置相对初始位置
        # self.set_pos_relative()
        # self.dis_tra_st = self.get_dis_traveled()
        x_st, y_st, _ = self.get_odometry()
        find_tar = False
        tar = []
        for pt_tar in pts_tar:
            # id, 物体宽度，置信度, 归一化bbox[x_c, y_c, w, h]
            tar_id, tar_width, tar_label, tar_score, tar_bbox = pt_tar[0], pt_tar[1], pt_tar[2], pt_tar[3], pt_tar[4:]
            tar_width *= 0.001
            tar_x, tar_y, tar_dis = self.det2pose(tar_bbox, tar_width)
            tar.append([tar_id, tar_width, tar_x, tar_y, tar_dis])
        logger.info("tar x:{} dis:{}".format(tar_x, tar_dis))
        tar_id, tar_width, tar_x, tar_y, tar_dis = tar[0]
        pid_x.setpoint = tar_x
        pid_y.setpoint = tar_dis
        tar_index = 0
        flag_location = False
        while True:
            if self._stop_flag:
                return
            if time.time() > end_time:
                logger.info("time out")
                self.set_velocity(0, 0, 0)
                return False
            _pos_x, _pos_y, _pos_omage = self.get_odometry() # 用来计算距离

            if abs(_pos_x-x_st) > dis_out or abs(_pos_y-y_st) > dis_out:
                if not find_tar:
                    logger.info("task location dis out")
                    self.set_velocity(0, 0, 0)
                    return False
            img_side = self.cap_side.read()
            if crop_mid:
                h, w = img_side.shape[:2]
                roi = img_side[:, w//4 : 3*w//4]          # 中间 1/3
                img_side = cv2.copyMakeBorder(
                    roi, 0, 0, w//4, w//4, cv2.BORDER_CONSTANT, value=0)
            dets_ret = infer(img_side)

            # dets_ret = self.mot_hum(img_side)
            # cv2.imshow("side", img_side)
            # cv2.waitKey(1)

            # 进行排序，此处排列按照自中心由近及远的顺序
            dets_ret.sort(key=lambda x: (x[4])**2 + (x[5])**2)
            print(dets_ret)
            # # 找到最近对应的类别，类别存在第一个位置
            # det = self.get_list_by_val(dets_ret, 2, tar_label)

            # 如果没有，就重新获取
            if len(dets_ret) > 0:
                # print(dets_ret)
                det = dets_ret[0]
                # 结果分解
                det_id, obj_id , det_label, det_score, det_bbox = det[0], det[1], det[2], det[3], det[4:]
                # if find_tar is False:
                # tar_index = 0
                # for tar_pt in tar:
                for index, tar_pt in enumerate(tar):
                    if det_id == tar_pt[0]:
                        tar_index = index
                        tar_id, tar_width, tar_x, tar_y, tar_dis = tar_pt
                        if crop_mid:
                            pass
                            #tar_x = 0
                        pid_x.setpoint = tar_x
                        pid_y.setpoint = tar_dis
                        find_tar = True
                        # print("find tar", tar_id)
                        break
                print(tar_id,det_id)
                if det_id == tar_id:
                    _x, _y, _dis = self.det2pose(det_bbox, tar_width)
                    print(f"当前检测位置: x={_x:.3f}, dis={_dis:.3f}")
                    print(f"目标位置: tar_x={tar_x:.3f}, tar_dis={tar_dis:.3f}")
                    print(f"误差: err_x={_x-tar_x:.3f}, err_dis={_dis-tar_dis:.3f}")
                    out_x = -pid_x(_x) * side
                    out_y = -pid_y(_dis) * side
                    # out_y = pid_y(_dis)
                    # out_y = pid_w(bbox_error[2])
                    # 检测偏差值连续小于阈值时，跳出循环
                    # print(bbox_error)
                    # print("err x:{:.2}, dis:{:.2}, tar x:{:.2}, tar dis:{:.2}".format(_x, _dis, tar_x, tar_dis))
                    print(f"PID输出: out_x={out_x:.3f}, out_y={out_y:.3f}")
                    print(f"side参数: {side}")
                    print("---")
                    flag_x = x_count(abs(_x - tar_x) < threshold)
                    flag_dis = dis_count(abs(_dis - tar_dis) < threshold)
                    if flag_x:
                        out_x = 0
                    if flag_dis:
                        out_y = 0
                    if flag_x and flag_dis:
                        logger.info("location{} ok".format(tar_id))
                        # flag_location = True
                        # 停止
                        self.set_velocity(0, 0, 0)
                        return tar_index

                    #print("out_x:{:.2}, out_y:{:2}".format( out_x, out_y))
            else:
                x_count(False)
                dis_count(False)
            self.set_velocity(out_x, out_y, 0)
    # 侧面摄像头进行位置定位
    def lane_det_location_food_new(self, speed,  pts_tar=[[0, 70, 0,  0, 0, 0, 0.70, 0.70]], dis_out=0.05, side=1, time_out=2, det='task', crop_mid=False, threshold=0.01):
        end_time = time.time() + time_out
        infer = self.task_det
        loc_pid = get_yaml(self.yaml_path)["location_pid"]
        pid_x = PID(**loc_pid["pid_x"])
        pid_x.output_limits = (-speed, speed)
        pid_y = PID(**loc_pid["pid_y"])
        pid_y.output_limits = (-0.15, 0.15)
        # pid_w = PID(1.0, 0, 0.00, setpoint=0, output_limits=(-0.15, 0.15))

        # 用于相同记录结果的计数类
        x_count = CountRecord(5)
        dis_count = CountRecord(5)

        out_x = speed
        out_y = 0

        # 此时设置相对初始位置
        # self.set_pos_relative()
        # self.dis_tra_st = self.get_dis_traveled()
        x_st, y_st, _ = self.get_odometry()
        find_tar = False
        tar = []
        for pt_tar in pts_tar:
            # id, 物体宽度，置信度, 归一化bbox[x_c, y_c, w, h]
            tar_id, tar_width, tar_label, tar_score, tar_bbox = pt_tar[0], pt_tar[1], pt_tar[2], pt_tar[3], pt_tar[4:]
            tar_width *= 0.001
            tar_x, tar_y, tar_dis = self.det2pose(tar_bbox, tar_width)
            tar.append([tar_id, tar_width, tar_x, tar_y, tar_dis])
        logger.info("tar x:{} dis:{}".format(tar_x, tar_dis))
        tar_id, tar_width, tar_x, tar_y, tar_dis = tar[0]
        pid_x.setpoint = tar_x
        pid_y.setpoint = tar_dis
        tar_index = 0
        flag_location = False
        while True:
            if self._stop_flag:
                return
            if time.time() > end_time:
                logger.info("time out")
                self.set_velocity(0, 0, 0)
                return False
            _pos_x, _pos_y, _pos_omage = self.get_odometry() # 用来计算距离

            if abs(_pos_x-x_st) > dis_out or abs(_pos_y-y_st) > dis_out:
                if not find_tar:
                    logger.info("task location dis out")
                    self.set_velocity(0, 0, 0)
                    return False
            img_side = self.cap_side.read()
            if crop_mid:
                h, w = img_side.shape[:2]
                roi = img_side[:, w//4 : 3*w//4]          # 中间 1/3
                img_side = cv2.copyMakeBorder(
                    roi, 0, 0, w//4, w//4, cv2.BORDER_CONSTANT, value=0)
            dets_ret = infer(img_side)

            # dets_ret = self.mot_hum(img_side)
            # cv2.imshow("side", img_side)
            # cv2.waitKey(1)

            # 进行排序，此处排列按照自中心由近及远的顺序
            dets_ret.sort(key=lambda x: (x[4])**2 + (x[5])**2)
            #print(dets_ret)
            # # 找到最近对应的类别，类别存在第一个位置
            # det = self.get_list_by_val(dets_ret, 2, tar_label)
            for i, d in enumerate(dets_ret):
                if d[2] == tar_label:
                    # 将找到的匹配项与第一个元素交换位置
                    dets_ret[0], dets_ret[i] = dets_ret[i], dets_ret[0]
                    break
            #print(dets_ret)
            # 如果没有，就重新获取
            if len(dets_ret) > 0:
                print(dets_ret)
                det = dets_ret[0]
                # 结果分解
                det_id, obj_id , det_label, det_score, det_bbox = det[0], det[1], det[2], det[3], det[4:]
                # if find_tar is False:
                # tar_index = 0
                # for tar_pt in tar:
                for index, tar_pt in enumerate(tar):
                    if det_id == tar_pt[0]:
                        tar_index = index
                        tar_id, tar_width, tar_x, tar_y, tar_dis = tar_pt
                        if crop_mid:
                            pass
                            #tar_x = 0
                        pid_x.setpoint = tar_x
                        pid_y.setpoint = tar_dis
                        find_tar = True
                        # print("find tar", tar_id)
                        break
                #print(tar_id,det_id)
                if det_id == tar_id:
                    _x, _y, _dis = self.det2pose(det_bbox, tar_width)
                    # 添加调试输出
                    print(f"当前检测位置: x={_x:.3f}, dis={_dis:.3f}")
                    print(f"目标位置: tar_x={tar_x:.3f}, tar_dis={tar_dis:.3f}")
                    print(f"误差: err_x={_x-tar_x:.3f}, err_dis={_dis-tar_dis:.3f}")

                    out_x = -pid_x(_x) * side
                    out_y = -pid_y(_dis) * side

                    print(f"PID输出: out_x={out_x:.3f}, out_y={out_y:.3f}")
                    print(f"side参数: {side}")
                    print("---")
                    # out_y = pid_y(_dis)
                    # out_y = pid_w(bbox_error[2])
                    # 检测偏差值连续小于阈值时，跳出循环
                    # print(bbox_error)
                    # print("err x:{:.2}, dis:{:.2}, tar x:{:.2}, tar dis:{:.2}".format(_x, _dis, tar_x, tar_dis))
                    flag_x = x_count(abs(_x - tar_x) < threshold)
                    flag_dis = dis_count(abs(_dis - tar_dis) < threshold)
                    if flag_x:
                        out_x = 0
                    if flag_dis:
                        out_y = 0
                    if flag_x and flag_dis:
                        logger.info("location{} ok".format(tar_id))
                        # flag_location = True
                        # 停止
                        self.set_velocity(0, 0, 0)
                        return tar_index

                    #print("out_x:{:.2}, out_y:{:2}".format( out_x, out_y))
            else:
                x_count(False)
                dis_count(False)
            self.set_velocity(out_x, out_y, 0)


    def lane_det_location_food(self, speed, label, pts_tar=[[0, 70, 0, 0, 0, 0, 0.70, 0.70]], dis_out=0.05, side=1, time_out=2, det='task'):
        end_time = time.time() + time_out

        # 检查推理模块
        infer = self.task_det
        if infer is None:
            raise ValueError("self.task_det 未初始化")

        # 读取 PID 参数
        loc_pid = get_yaml(self.yaml_path)["location_pid"]
        pid_x = PID(**loc_pid["pid_x"])
        pid_x.output_limits = (-speed, speed)
        pid_y = PID(**loc_pid["pid_y"])
        pid_y.output_limits = (-0.15, 0.15)

        # 稳定检测用
        x_count = CountRecord(5)
        dis_count = CountRecord(5)

        out_x = speed
        out_y = 0

        # 起始位置
        x_st, y_st, _ = self.get_odometry()

        # 找目标
        tar = []
        # 保证 pts_tar 是二维结构

        for pt_tar in pts_tar:
            #print("pt_tar:",pt_tar,"pt_tar type:",type(pt_tar))
            #print("pt_tar[2]",pt_tar[2],"label",label)
            if int(pt_tar[2]) == label:
                tar_id, tar_width, tar_label, tar_score, tar_bbox = pt_tar[0], pt_tar[1], pt_tar[2], pt_tar[3], pt_tar[4:]
                tar_width *= 0.001  # 转换单位：mm -> m（若 det2pose 使用米）
                tar_x, tar_y, tar_dis = self.det2pose(tar_bbox, tar_width)
                tar.append([tar_id, tar_width, tar_x, tar_y, tar_dis])
                break

        if len(tar) == 0:
            #print("没有检测到目标食物")
            return False

        # 初始目标设定
        tar_id, tar_width, tar_x, tar_y, tar_dis = tar[0]
        pid_x.setpoint = tar_x
        pid_y.setpoint = tar_dis
        tar_index = 0
        find_tar = False

        while True:
            if self._stop_flag:
                return False

            if time.time() > end_time:
                logger.info("time out")
                self.set_velocity(0, 0, 0)
                return False

            _pos_x, _pos_y, _ = self.get_odometry()
            if abs(_pos_x - x_st) > dis_out or abs(_pos_y - y_st) > dis_out:
                if not find_tar:
                    logger.info("task location dis out")
                    self.set_velocity(0, 0, 0)
                    return False

            img_side = self.cap_side.read()
            dets_ret = infer(img_side)
            if len(dets_ret) > 0:
                matched_det = None
                min_dist = float('inf')
                for det in dets_ret:
                    print("det",det,"det type",type(det))
                    if int(det.label_name) == label:
                        _id, _obj_id, _label, _score, _bbox = det[0], det[1], det[2], det[3], det[4:]
                        _x_tmp, _y_tmp, _dis_tmp = self.det2pose(_bbox, tar_width)
                        err_x = abs(_x_tmp - tar_x)
                        err_dis = abs(_dis_tmp - tar_dis)
                        dist = err_x**2 + err_dis**2
                        if dist < min_dist:
                            min_dist = dist
                            matched_det = det

                if matched_det is not None:
                    det_id, obj_id, det_label, det_score, det_bbox = matched_det[0], matched_det[1], matched_det[2], matched_det[3], matched_det[4:]
                    _x, _y, _dis = self.det2pose(det_bbox, tar_width)

                    out_x = -pid_x(_x) * side
                    out_y = -pid_y(_dis) * side

                    flag_x = x_count(abs(_x - tar_x) < 0.01)
                    flag_dis = dis_count(abs(_dis - tar_dis) < 0.01)

                    if flag_x:
                        out_x = 0
                    if flag_dis:
                        out_y = 0

                    if flag_x and flag_dis:
                        logger.info(f"location {tar_id} ok")
                        self.set_velocity(0, 0, 0)
                        return tar_index
                else:
                    #print("目标未匹配成功")
                    x_count(False)
                    dis_count(False)
            else:
                #print("未检测到目标")
                x_count(False)
                dis_count(False)

            self.set_velocity(out_x, out_y, 0)


    def lane_base(self, speed, end_fuction, stop=STOP_PARAM):
        while True:
            if self._stop_flag:
                return
            image = self.cap_front.read()
            error_y, error_angle = self.crusie(image)
            y_speed, angle_speed = self.lane_pid.get_out(-error_y, -error_angle)
            # print("")
            # print("--------------")
            # print("error:{} angle{}".format(error_y, error_angle))
            # print("y_speed:{}, angle_speed:{}".format(y_speed, angle_speed))
            # speed_dy, angle_speed = process(image)
            self.set_velocity(speed, y_speed, angle_speed)
            if end_fuction():
                break
        if stop:
            self.stop()

    def lane_det_base(self, speed, end_fuction, stop=STOP_PARAM):
        # 初始化速度和角度速度
        y_speed = 0
        angle_speed = 0
        w_r=0.06
        # 无限循环
        while True:
            # 读取前摄像头图像
            image = self.cap_front.read()
            dets_ret = self.front_det(image)
            # 此处检测简单不需要排序
            # dets_ret.sort(key=lambda x: x[4]**2 + (x[5])**2)
            if len(dets_ret)>0:
                det = dets_ret[0]
                det_cls, det_id, det_label, det_score, det_bbox = det[0], det[1], det[2], det[3], det[4:]
                _x, _y, _dis = self.det2pose(det_bbox, w_r)
                # error_y = det_bbox[0]
                # dis_x = 1 - det_bbox[1]
                if end_fuction(_dis):
                    break
                error_angle = _x /_dis
                y_speed, angle_speed = self.det_pid.get_out(_x, error_angle)
                # print("_x:{:.2}, _angle:{:.2}, y_vel:{:.2}, angle_vel:{:.2}, dis{:.2}".format(_x, error_angle, y_speed, angle_speed, _dis))
            self.set_velocity(speed, y_speed, angle_speed)
            # if end_fuction(0):
            #     break
        if stop:
            self.stop()

    def lane_det_time(self, speed, time_dur, stop=STOP_PARAM):
        time_end = time.time() + time_dur
        end_fuction = lambda x: time.time() > time_end
        self.lane_det_base(speed, end_fuction, stop=stop)

    def lane_det_dis2pt(self, speed, dis_end, stop=STOP_PARAM):
        # lambda定义endfunction
        end_fuction = lambda x: x < dis_end and x != 0
        self.lane_det_base(speed, end_fuction, stop=stop)

    def lane_time(self, speed, time_dur, stop=STOP_PARAM):
        time_end = time.time() + time_dur
        end_fuction = lambda: time.time() > time_end
        self.lane_base(speed, end_fuction, stop=stop)

    # 巡航一段路程
    def lane_dis(self, speed, dis_end, stop=STOP_PARAM):
        # lambda重新endfunction
        end_fuction = lambda: self.get_dis_traveled() > dis_end
        self.lane_base(speed, end_fuction, stop=stop)

    def lane_dis_offset(self, speed, dis_hold, stop=STOP_PARAM):
        dis_start = self.get_dis_traveled()
        dis_stop = dis_start + dis_hold
        self.lane_dis(speed, dis_stop, stop=stop)

    def lane_sensor_time(self, speed, value_h=None, value_l=None, litime=1000, sides=1, stop=STOP_PARAM):
        if value_h is None:
            value_h = 1200
        if value_l is None:
            value_l = 0
        _sensor_usr = self.left_sensor
        if sides == -1:
            _sensor_usr = self.right_sensor

        # 使用包装类实现类似引用的效果
        class State:
            def __init__(self):
                self.flag_over_time = False
                self.flag_start = False
                self.te = time.time() + litime

        state = State()

        def end_function():
            val_sensor = _sensor_usr.read()
            if val_sensor < value_h and val_sensor > value_l:
                return state.flag_start
            else:
                state.flag_start = True
                if time.time() > state.te:
                    state.flag_over_time = True
                    return True
                return False

        self.lane_base(speed, end_function, stop=stop)
        return state.flag_over_time
        # 根据需要是否巡航

        #self.lane_dis_offset(speed, dis_offset, stop=stop)

    def lane_sensor(self, speed, value_h=None, value_l=None, dis_offset=0.0, times=1, sides=1, stop=STOP_PARAM):
        if value_h is None:
            value_h = 1200
        if value_l is None:
            value_l = 0
        _sensor_usr = self.left_sensor
        if sides == -1:
            _sensor_usr = self.right_sensor
        # 用于检测开始过渡部分的标记
        flag_start = False
        def end_fuction():
            nonlocal flag_start
            val_sensor = _sensor_usr.read()
            # print("val:", val_sensor)
            # print(val_sensor < value_h and val_sensor > value_l)
            if val_sensor < value_h and val_sensor > value_l:
                #print("已返回")
                return flag_start
            else:
                flag_start = True
                return False

        for i in range(times):
            self.lane_base(speed, end_fuction, stop=stop)
        # 根据需要是否巡航

        #self.lane_dis_offset(speed, dis_offset, stop=stop)

    def get_card_side(self):
        # 检测卡片左右指示
        count_side = CountRecord(3)
        while True:
            if self._stop_flag:
                return
            image = self.cap_front.read()
            dets_ret = self.front_det(image)
            if len(dets_ret) == 0:
                count_side(-1)
                continue
            dets_ret.sort(key=lambda x: -x[3])
            #print(dets_ret)
            det = dets_ret[0]
            det_cls, det_id, det_label, det_score, det_bbox = det[0], det[1], det[2], det[3], det[4:]
            # 联系检测超过3次
            if count_side(det_label):
                if det_label == 'turn_right':
                    return -1
                elif det_label == 'turn_left':
                    return 1

    def get_ocr_whole(self,time_out=3):
        time_stop = time.time() + time_out
        # 简单滤波,三次检测到相同的值，认为稳定并返回
        text_count = CountRecord(3)
        text_out = None
        while True:
            if self._stop_flag:
                return
            if time.time() > time_stop:
                return None
            img = self.cap_side.read()
            text = self.ocr_rec(img)
            #print(response)
            if text is not None:
                text = self.ocr_rec(img)
                #print(text)
                if text_out==None:
                    text_out = text
                else:
                    # 文本相似度比较
                    matcher = difflib.SequenceMatcher(None, text_out, text).ratio()
                    if text_count(matcher > 0.85):
                        return text_out
                    else:
                        text_out = text

    def get_ocr(self, time_out=3):
        time_stop = time.time() + time_out
        # 简单滤波,三次检测到相同的值，认为稳定并返回
        text_count = CountRecord(3)
        text_out = None
        while True:
            if self._stop_flag:
                return
            if time.time() > time_stop:
                return None
            img = self.cap_side.read()
            response = self.task_det(img)
            #print(response)
            if len(response) > 0:
                for det in response:
                    det_cls_id, det_id, det_label, det_score, det_bbox = det[0], det[1], det[2], det[3], det[4:]
                    if det_cls_id == 0:
                        x1, y1, w, h = det_bbox
                        # print(img.shape)
                        # print(x1, y1, w, h)
                        x1 = img.shape[1] * (1+x1) / 2 - img.shape[1] * w / 4
                        x2 = x1 + img.shape[1] * w / 2
                        y1 = img.shape[0] * (1+y1) / 2 - img.shape[0] * w / 4
                        y2 = y1 + img.shape[0] * h / 2
                        x1 = 0 if x1 < 0 else int(x1)
                        x2 = img.shape[1] if x2 > img.shape[1] else int(x2)
                        y1 = 0 if y1 < 0 else int(y1)
                        y2 = img.shape[0] if y2 > img.shape[0] else int(y2)
                        #print(x1, x2, y1, y2)
                        img_txt = img[y1:y2, x1:x2]
                        text = self.ocr_rec(img_txt)
                        #print(text)
                        if text_out==None:
                            text_out = text
                        else:
                            # 文本相似度比较
                            matcher = difflib.SequenceMatcher(None, text_out, text).ratio()
                            if text_count(matcher > 0.85):
                                return text_out
                            else:
                                text_out = text
                            # if matcher > 0.85:
                            #     text_count(T)
                        # print(text)
                        # print(res.bbox)
                        # print(text)
                        # if text_count(text):
                        #     return text

    def get_ocr_food_text(self, time_out=10):
        time_stop = time.time() + time_out
        # 简单滤波,三次检测到相同的值，认为稳定并返回
        text_count = CountRecord(2)
        text_out = None
        while True:
            if self._stop_flag:
                return
            if time.time() > time_stop:
                return None
            img = self.cap_side.read()
            response = self.task_det(img)
           #print(response)
            if len(response) > 0:
                for det in response:
                    det_cls_id, det_id, det_label, det_score, det_bbox = det[0], det[1], det[2], det[3], det[4:]
                    # print(type(det_label))
                    if det_label == '0':
                        x_c, y_c, w, h = det_bbox
                        H, W = img.shape[:2]

                        # print(img.shape)
                        # print(x1, y1, w, h)
                        x1 = int(W * ((1 + x_c) / 2 - w / 2))
                        y1 = int(H * ((1 + y_c) / 2 - h / 2))
                        x2 = int(W * ((1 + x_c) / 2 + w / 2))
                        y2 = int(H * ((1 + y_c) / 2 + h / 2))
                        x1, y1 = max(0, x1), max(0, y1)
                        x2, y2 = min(W, x2), min(H, y2)
                        #print(x1, x2, y1, y2)
                        img_txt = img[y1:y2, x1:x2]
                        text = self.ocr_rec(img_txt)
                        #print("food_text:",text)
                        if text_out==None:
                            text_out = text
                        else:
                            # 文本相似度比较
                            matcher = difflib.SequenceMatcher(None, text_out, text).ratio()
                            if text_count(matcher > 0.7):
                                return text_out
                            else:
                                text_out = text
                            # if matcher > 0.85:
                            #     text_count(T)
                        # print(text)
                        # print(res.bbox)
                        # print(text)
                        # if text_count(text):
                        #     return text

    def get_two_ocr_texts(self, time_out=3):
        time_stop = time.time() + time_out

        while True:
            if self._stop_flag:
                return None
            if time.time() > time_stop:
                return None

            img = self.cap_side.read()
            response = self.task_det(img)

            if len(response) >= 2:
                det_texts = []
                for det in response:
                    det_cls_id, det_id, det_label, det_score, det_bbox = det[0], det[1], det[2], det[3], det[4:]
                    if det_label == '0':
                        x1, y1, w, h = det_bbox
                        x1 = img.shape[1] * (1 + x1) / 2 - img.shape[1] * w / 4
                        x2 = x1 + img.shape[1] * w / 2
                        y1 = img.shape[0] * (1 + y1) / 2 - img.shape[0] * w / 4
                        y2 = y1 + img.shape[0] * h / 2
                        x1 = max(0, int(x1))
                        x2 = min(img.shape[1], int(x2))
                        y1 = max(0, int(y1))
                        y2 = min(img.shape[0], int(y2))
                        img_txt = img[y1:y2, x1:x2]
                        text = self.ocr_rec(img_txt)
                        det_texts.append((y1, text))

                if len(det_texts) >= 2:
                    print(f"检测到的文本框数目为{len(det_texts)}")
                    det_texts.sort(key=lambda x: x[0])
                    # texts = [f"{idx}:{text}" for idx, (_, text) in enumerate(det_texts[:2])]
                    texts = [text for _, text in det_texts[:2]]
                    return texts  # ✅ 返回带序号的文本列表

    def get_ocr_questions(self, time_out=3):
        seen_boxes = set()

        img = self.cap_side.read()
        detections = self.task_det(img)

        frame_boxes = []
        for det in detections:
            if str(det.label_name) == '0':
                _, _, _, _, x_c, y_c, w, h = det
                H, W = img.shape[:2]

                x1 = int(W * ((1 + x_c) / 2 - w / 2))
                y1 = int(H * ((1 + y_c) / 2 - h / 2))
                x2 = int(W * ((1 + x_c) / 2 + w / 2))
                y2 = int(H * ((1 + y_c) / 2 + h / 2))
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(W, x2), min(H, y2)

                box_id = f"{x1},{y1},{x2},{y2}"
                if box_id not in seen_boxes:
                    seen_boxes.add(box_id)
                    roi = img[y1:y2, x1:x2]
                    frame_boxes.append({
                        'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                        'roi': roi
                    })
        #print("len(frame_boxes)",len(frame_boxes))
        #print(frame_boxes)
        if len(frame_boxes) < 5:
            return None

        sorted_boxes = sorted(frame_boxes, key=lambda b: b['y1'])
        question_box = sorted_boxes[0]
        option_boxes = sorted(sorted_boxes[1:5], key=lambda b: b['x1'])
        #print(question_box,option_boxes)
        results = [
            self.ocr_rec(question_box['roi']) or "",
            *[self.ocr_rec(b['roi']) or "" for b in option_boxes]
        ]

        return [str(txt) for txt in results]



    def yiyan_get_bmi(self, text):
        return self.bmi_analysis.get_res_json(text)

    def yiyan_get_actions(self, text):
        return self.action_bot.get_res_json(text)

    def yiyan_get_answer(self, text):
        print("yiyan_get_answer text:", text)
        return self.answer_analysis.get_res_json(text)
    #获取菜品所需要的食材
    def yiyan_get_ingredients_answer(self, text):
        return self.ingredients_answer_analysis.get_res_json(text)

    '''
    用于将食材相关的文本（如OCR识别出来的食材名称）送给大模型（如文心一言）进行分析
    返回结构化的结果（如食材的label、类别等）。
    '''
    def yiyan_get_food(self, text):     #text通常是OCR识别出来的食材名称
        """Safely call food_analysis; 当 text 为空时直接返回空 dict，避免 NoneType 触发 len() 错误。"""
        if not text:    #如果text为空，则返回空字典
            logger.warning("yiyan_get_food: 接收到空文本，跳过大模型解析")
            return {}
        return self.food_analysis.get_res_json(text)  #如果text不为空，则调用food_analysis.get_res_json(text)，返回结构化的结果
        #结构化的结果，指的是有明确字段和层次的数据，通常以字典（dict）、JSON、表格等形式返回，而不是一大段没有格式的自然语言文本。

    def yiyan_get_ingredients_location(self, img , text):
        # 若同时缺失输入直接返回空 dict
        if img is None and text is None:
            logger.warning("yiyan_get_ingredients_location: 接收到空图像和文本，跳过大模型解析")
            return {}

        # OpenCV 读取的图像是 numpy.ndarray，需转为 PIL.Image 才能被文心一言接口接受
        if img is not None and isinstance(img, np.ndarray):
            from PIL import Image
            # BGR → RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)

        return self.location_analysis.get_res_json_from_img(img, text)



    def debug(self):
        # self.arm.arm_init()
        # self.set_xyz_relative(0, 100, 60, 0.5)
        while True:
            if self._stop_flag:
                return
            image = self.cap_front.read()
            res = self.crusie(image)
            det_front = self.front_det(image)
            error = res[0]
            angle = res[1]
            image = self.cap_side.read()
            det_task = self.task_det(image)
            # det_hum = self.mot_hum(image)

            logger.info("")
            logger.info("--------------")
            logger.info("error:{} angle{}".format(error, angle))
            logger.info("front:{}".format(det_front))
            det_task.sort(key=lambda x: (x[4])**2 + (x[5])**2)
            logger.info("task:{}".format(det_task))
            # logger.inf
            if len(det_task) > 0:
                for det in det_task:

                    dis = self.det2pose(det[4:])
                    logger.info("det:{} dis:{}".format(det, dis))
                # logger.info("hum_det:{}".format(det_hum))
                # logger.info("left:{} right:{}".format(self.left_sensor.read(), self.right_sensor.read()))
                # self.delay(0.5)
            # self.det2pose(det_task[4:])
            # logger.info("hum_det:{}".format(det_hum))
            logger.info("left:{} right:{}".format(self.left_sensor.read(), self.right_sensor.read()))
            self.delay(1)

    def walk_lane_test(self):
        end_function = lambda: True
        self.lane_base(0.3, end_function, stop=self.STOP_PARAM)

    def close(self):
        self._stop_flag = False
        self._end_flag = True
        self.thread_key.join()
        self.cap_front.close()
        self.cap_side.close()
        # self.grap_cam.close()

    def manage(self, programs_list:list, order_index=0):

        def all_task():
            time.sleep(4)
            for func in programs_list:
                func()

        def lane_test():
            #self.set_pose_offset([2,0,0])
            self.lane_dis_offset(0.35, 30)
        def lane_whole():
            self.task.arm.safe_reset()
            self.lane_dis_offset(0.3, 0.2,stop=True)
            time.sleep(0.2)
            print(self.get_odometry())
            self.set_pose_offset([0.5,0,0])
            print(self.get_odometry())
            det_side = self.lane_det_dis2pt(0.2, 0.19)
            side = self.get_card_side()
            time.sleep(0.2)
            self.set_pose_offset([-0.1,0,0], 1)
            self.set_pose_offset([0, 0, math.pi/4*side])
            self.lane_dis_offset(0.3,5,stop=False)
            self.set_pose_offset([0, 0, -math.pi/6])
            self.lane_dis_offset(0.3,3,stop=False)
            self.set_pose_offset([0.5, 0, 0], 1)
            self.lane_dis_offset(0.3,6,stop=False)
        def pose_front():
            self.set_pose_offset([2,0,0])
        programs_suffix = [all_task, lane_test, lane_whole,pose_front,self.task.arm.safe_reset, self.debug,self.reset_pose]
        programs = programs_list.copy()
        programs.extend(programs_suffix)
        # print(programs)
        # 选中的python脚本序号
        # 当前选中的序号
        win_num = 5
        win_order = 0
        # 把programs的函数名转字符串
        logger.info(order_index)
        programs_str = [str(i.__name__) for i in programs]
        logger.info(programs_str)
        dis_str = sellect_program(programs_str, order_index, win_order)
        self.display.show(dis_str)

        self.stop()
        run_flag = False
        stop_flag = False
        stop_count = 0
        while True:
            # self.button_all.event()
            btn = self.key.get_key()
            # 短按1=1,2=2,3=3,4=4
            # 长按1=5,2=6,3=7,4=8
            # logger.info(btn)
            # button_num = car.button_all.clicked()

            if btn != 0:
                # logger.info(btn)
                # 长按1按键，退出
                if btn == 5:
                    # run_flag = True
                    self._stop_flag = True
                    self._end_flag = True
                    print("已经退出")
                    break
                else:
                    if btn == 4:
                        # 序号减1
                        self.beep()
                        if order_index == 0:
                            order_index = len(programs)-1
                            win_order = win_num-1
                        else:
                            order_index -= 1
                            if win_order > 0:
                                win_order -= 1
                        # res = sllect_program(programs, num)
                        print("当前任务为{}".format(str(programs_str[order_index])))
                        dis_str = sellect_program(programs_str, order_index, win_order)
                        self.display.show(dis_str)

                    elif btn == 2:
                        self.beep()
                        # 序号加1
                        if order_index == len(programs)-1:
                            order_index = 0
                            win_order = 0
                        else:
                            order_index += 1
                            if len(programs) < win_num:
                                win_num = len(programs)
                            if win_order != win_num-1:
                                win_order += 1
                        # res = sllect_program(programs, num)
                        print("当前任务为{}".format(str(programs_str[order_index])))
                        dis_str = sellect_program(programs_str, order_index, win_order)
                        self.display.show(dis_str)

                    elif btn == 3:
                        # 确定执行
                        # 调用别的程序
                        dis_str = "\n{} running......\n".format(str(programs_str[order_index]))
                        print(dis_str)
                        self.display.show(dis_str)
                        self.beep()
                        self._stop_flag = False
                         # 🔧 使用线程执行程序并监听中断
                        program_thread = threading.Thread(target=programs[order_index])
                        program_thread.daemon = True
                        program_thread.start()
                        
                        # 🔧 主线程监听按键1中断
                        interrupted = False
                        while program_thread.is_alive():
                            btn_interrupt = self.key.get_key()
                            if btn_interrupt == 1:  # 按键1中断
                                print(f"🛑 检测到按键1，中断程序: {programs_str[order_index]}")
                                try:
                                    self.display.show("Stopping...")
                                except:
                                    pass
                                self.beep()
                                self._stop_flag = True
                                interrupted = True
                                break
                            time.sleep(0.05)
                        
                        # 等待程序线程结束
                        program_thread.join(timeout=3.0)
                        
                        if interrupted:
                            print(f"程序被中断: {programs_str[order_index]}")
                        else:
                            print(f"程序执行完成: {programs_str[order_index]}")
    
                        self._stop_flag = True
                        dis_str = sellect_program(programs_str, order_index, win_order)
                        self.stop()
                        self.beep()

                        # 自动跳转下一条
                        # if order_index == len(programs)-1:
                        #     order_index = 0
                        #     win_order = 0
                        # else:
                        #     order_index += 1
                        #     if len(programs) < win_num:
                        #         win_num = len(programs)
                        #     if win_order != win_num-1:
                        #         win_order += 1
                        # res = sllect_program(programs, num)
                        dis_str = sellect_program(programs_str, order_index, win_order)
                        self.display.show(dis_str)
                    logger.info(programs_str[order_index])
            else:
                self.delay(0.02)

            time.sleep(0.02)

        for i in range(2):
            self.beep()
            time.sleep(0.4)
        time.sleep(0.1)
        self.close()
    

if __name__ == "__main__":
    kill_other_python()
    my_car = MyCar()
    time.sleep(0.4)
    # my_car.task.get_ingredients(1, arm_set=True)
    my_car.set_pose([0.15,0,0])
    def start_det_loc():
        det1 = [15, 60, "cylinder3", 0, 0, 0, 0.47, 0.7]
        det2 = [14, 80, "cylinder2", 0, 0, 0, 0.69, 0.7]
        det3 = [13, 100, "cylinder1", 0,  0, 0, 0.77, 0.7]
        dets = [det1, det2, det3]
        my_car.lane_det_location(0.2, dets)

    def lane_det_test():
        my_car.lane_det_dis2pt(0.2, 0.16)

    def move_test():
        my_car.set_vel_time(0.3, 0, -0.6, 1)

    def ocr_test():
        print(my_car.get_ocr())

    # my_car.manage([start_det_loc, lane_det_test, move_test, ocr_test])
    # my_car.lane_time(0.3, 5)

    # my_car.lane_dis_offset(0.3, 1.2)
    # my_car.lane_sensor(0.3, 0.5)
    # my_car.debug()

    # text = "犯人没有带着眼镜，穿着短袖"
    # criminal_attr = my_car.hum_analysis.get_res_json(text)
    # print(criminal_attr)
    # my_car.task.reset()
    # pt_tar = my_car.task.punish_crimall(arm_set=True)
    # hum_attr = my_car.get_hum_attr(pt_tar)
    # print(hum_attr)
    # res_bool = my_car.compare_humattr(criminal_attr, hum_attr)
    # print(res_bool)
    # pt_tar = [0, 1, 'pedestrian',  0, 0.02, 0.4, 0.22, 0.82]
    # for i in range(4):
    #     my_car.set_pos_offset([0.07, 0, 0])
    #     my_car.lane_det_location(0.1, pt_tar, det="mot", side=-1)
    # my_car.close()
    # text = my_car.get_ocr()
    # print(text)
    # pt_tar = my_car.task.pick_up_ball(arm_set=True)
    # my_car.lane_det_location(0.1, pt_tar)

    my_car.close()
    # my_car.debug()
    # while True:
    #     text = my_car.get_ocr()
    #     print(text)

    # my_car.task.reset()
    # my_car.lane_advance(0.3, dis_offset=0.01, value_h=500, sides=-1)
    # my_car.lane_task_location(0.3, 2)
    # my_car.lane_time(0.3, 5)
    # my_car.debug()

    # my_car.debug()


    # my_car.task.pick_up_block()
    # my_car.task.put_down_self_block()
    # my_car.lane_time(0.2, 2)
    # my_car.lane_advance(0.3, dis_offset=0.01, value_h=500, sides=-1)
    # my_car.lane_task_location(0.3, 2)
    # my_car.task.pick_up_block()
    # my_car.close()
    # logger.info(time.time())
    # my_car.lane_task_location(0.3, 2)


    # my_car.debug()
    # programs = [func1, func2, func3, func4, func5, func6]
    # my_car.manage(programs)
    # import sys
    # test_ord = 0
    # if len(sys.argv) >= 2:
    #     test_ord = int(sys.argv[1])
    # logger.info("test:", test_ord)
    # car_test(test_ord)
