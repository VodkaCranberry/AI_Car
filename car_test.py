
#!/usr/bin/python
# -*- coding: utf-8 -*-
from pydoc import cram
import time
import threading
import os
import platform
import signal
from camera import Camera
import numpy as np
# from vehicle import SensorAi, SerialWrap, ArmBase, ScreenShow, Key4Btn
from simple_pid import PID
import cv2
# from task_func import MyTask
from car_wrap import MyCar
import math

if __name__ == "__main__":
    # kill_other_python()
    my_car = MyCar()
    my_car.beep()
    #my_car.task.arm.safe_reset()
    # my_car.set_pose_offset([0.12,0,0])
    # my_car.lane_sensor(0.3, value_h=0.3, sides=1)    # 移动、检测侧边
    # my_car.task.arm.switch_side(1)                  # 切换到左臂
    # my_car.move_distance([0.3, 0, 0], 0.22)          # 预推进
    # tar = my_car.task.get_answer(arm_set=True)       # 粗定位题目 让手臂就位
    my_car.lane_sensor(0.3, value_h=0.2, sides=1)
        # 粗调 使得摄像头接近中心

    my_car.lane_dis_offset(0.3, 0.17)
    tar = my_car.task.get_ingredients(side=1, ocr_mode=True, arm_set=True)
    my_car.lane_det_location_food_new(speed=0.2,pts_tar=tar, side=1,time_out=5)#,crop_mid=True)

    tar = my_car.task.get_ingredients(side=-1, ocr_mode=True, arm_set=True)
    my_car.lane_det_location_food_new(speed=0.2,pts_tar=tar, side=-1,time_out=5)
    tar = my_car.task.get_ingredients(side=1, ocr_mode=True, arm_set=True)
    my_car.lane_det_location_food_new(speed=0.2,pts_tar=tar, side=1,time_out=5)#,crop_mid=True)

    my_car.task.arm.grap(0)
    # my_car.task.arm.set(0.12,0.08)
    # my_car.task.set_food(1, row=2)
    # my_car.set_pose_offset([0.045, 0, 0])
    # my_car.task.set_food(2, row=2)
    # my_car.task.arm.grap(0)
    # my_car.close()
    #my_car.lane_sensor(0.3, value_h=0.3, sides=1)    # 移动、检测侧边
    #my_car.set_pose_offset([-1, 0, 0],vel=[0.4, 0, 0])  # 调整车身位置
    #my_car.task.eject(1)
    # my_car.set_pose_offset([0.045, 0, 0])
    # my_car.set_pose_offset([0.38,0,0])
    # my_car.task.set_food(1, row=2)
    # my_car.task.arm.set(0.01,0.045)
    # my_car.lane_det_location_food(speed=0.2,label=0,pts_tar=tar,side=1)       # 精定位
    # my_car.set_pose_offset([-0.05,0,0])
    # my_car.set_pose_offset([0.07,0,0])
    # my_car.close()
    # tar = my_car.task.pick_ingredients(tar=[13,0,10,0.945,0.04567308,-0.15384615,0.24519231,0.32692308],num=1, row=1, arm_set=True)
    # # col = 1
    # #     #寻找目标
    # # y_offset = (col-2)*0.08
    # # #根据第几列调整车身位置    (这里可以选择调整手臂位置 或者 调整车身位置 最好还是调整手臂位置) 有待商榷
    # # my_car.set_pose_offset([y_offset,0,0])
    # my_car.lane_det_location_food(0.2, tar, side=1)
    #     #抓取第一个目标
    # my_car.task.pick_ingredients(tar=tar,num=1, row=2)
    #  time.sleep(0.2)
    # 巡线
    #my_car.task.pick_up_cylinder(1, True)
    # my_car.lane_dis_offset(0.3, 0.3,stop=False)
    # print(my_car.get_odometry())
    # my_car.set_pose_offset([0.3,0,0], 1)
    # print(my_car.get_odometry())
    # det_side = my_car.lane_det_dis2pt(0.2, 0.19)
    # print(det_side)
    # print("检测到")
    # side = my_car.get_card_side()
    # print(side)
    # #  调整车子朝向
    # my_car.set_pose_offset([0, 0, math.pi/4*side], 1)
    # my_car.lane_time(0.3,100,stop=False)
    # my_car.move_time([0.2,0,-0.78],0.8,stop=False)
    # my_car.lane_time(0.3,5,stop=False)
    # my_car.move_time([0.2,0,-0.78],1,stop=False)
    # my_car.lane_time(0.3,10,stop=False)
    # my_car.move_time([0.2,0,0],2.5,stop=False)
    # my_car.lane_time(0.3,30.2)
    # task1
    # flag=False
    # my_car.lane_dis_offset(0.3, 0.3,stop=flag)
    # print(my_car.get_odometry())
    # my_car.set_pose_offset([0.3,0,0], 1)
    # print(my_car.get_odometry())
    # det_side = my_car.lane_det_dis2pt(0.2, 0.19)
    # side = my_car.get_card_side()
    # print(side)
    # 调整检测方向
    # my_car.task.arm.switch_side(side*-1)

    # # 调整车子朝向
    # my_car.set_pose_offset([0, 0, math.pi/4*side], 1)

    # # 第一个要抓取的圆柱
    # cylinder_id = 1
    # # 调整抓手位置，获取要抓取的圆柱信息
    # pts = my_car.task.pick_up_cylinder(cylinder_id, True)
    # # 走一段距离
    # my_car.lane_dis_offset(0.3,0.5)

    # # 第二次感应到侧面位置
    # # my_car.lane_sensor(0.2, value_h=0.3, sides=side*-1)
    # my_car.lane_sensor(0.2, value_h=0.3, sides=side*-1, stop=True)
    # # return
    # # 记录此时的位置
    # pose_dict = {}
    # pose_last = None
    # for i in range(3):
    #     # 根据给定信息定位目标
    #     index = my_car.lane_det_location(0.2, pts, side=side*-1)
    #     my_car.beep()
    #     pose_dict[index] = my_car.get_odometry().copy()
    #     if i == 2:
    #         pose_last = my_car.get_odometry().copy()
    #     # print(index)
    #     # pose_list.append([index, my_car.get_odometry().copy()])

    #     if i < 2:
    #         my_car.set_pose_offset([0.08, 0, 0])
    #         my_car.beep()
    #         angle_det = my_car.get_odometry()[2]
    # # 计算目的地终点坐标
    # pose_end = [0, 0, angle_det]
    # pose_end[0] = pose_last[0] + 0.12*math.cos(angle_det)
    # pose_end[1] = pose_last[1] + 0.12*math.sin(angle_det)
    # # print(det)
    # # 调整到目的地
    # # my_car.set_pose(det)
    # for i in range(3):
    #     det = pose_dict[i]
    #     det[2] = angle_det
    #     my_car.set_pose(det)
    #     # my_car.lane_det_location(0.2, pts, side=side*-1)
    #     my_car.task.pick_up_cylinder(i)
    #     my_car.set_pose(pose_end)
    #     my_car.task.put_down_cylinder(i)
    #task2
    #   my_car.lane_dis_offset(0.3, 0.8)
    #   # 准备手臂位置
    #   pts = my_car.task.bmi_set(arm_set=True)
    #   # 巡航到bmi识别附件
    #   my_car.lane_sensor(0.3, value_h=0.30, sides=1,stop=True)
    #   result=True
    #   print(result)
    #   if result==True:
    #       time.sleep(0.2)
    #       # # 推开bmi识别标签
    #       my_car.set_pose_offset([0.15,0,0])
    #       my_car.set_pose_offset([0,-0.03,0])
    #       my_car.set_pose_offset([0.05,0.18,0],vel=[0.4,0.4,math.pi/3])
    #       my_car.set_pose_offset([0.02,-0.05,0])
    #       my_car.set_pose_offset([-0.1,0,0])
    #       # 调整bmi识别位置
    #       my_car.lane_det_location(0.2, pts, side=1)
    #       # 识别相关文字
    #   text = my_car.get_ocr_whole()
    #   print(text)
    #   bmi=my_car.yiyan_get_bmi(text)["bmi"]
    #   print(bmi)
    #   bmii=0
    #   if bmi<18.5:
    #       bmii=0
    #   elif bmi<=24:
    #       bmii=1
    #   elif bmi<=28:
    #       bmii=2
    #   else:
    #       bmii=3
    # my_car.task.bmi_set(3)
    #1 绿色 2 蓝色 3 橙色 4 huangse
    #     # time.sleep(0.3)
    #     out = 2
    #     my_car.task.bmi_set(out)
    #     my_car.lane_dis_offset(0.4,4.9)
    #     my_car.set_pose_offset([0.5,0,0])
    #     my_car.lane_time(0.3,20)
    # else:
    #     my_car.lane_dis_offset(0.2,0.5)
    # time.sleep(0.5)
    # 调整位置准备放置球
    # my_car.lane_dis_offset(0.21, 0.19)
    # my_car.set_pose_offset([0, 0.05, 0], 0.7)
    # my_car.task.put_down_ball()

    import math, datetime
    now_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S.%f')[2:-3]  # 当前日期格式化
    print(now_time)
    time.sleep(0.2)
    now_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S.%f')[2:-3]  # 当前日期格式化
    print(now_time)
    my_car.close()
    # from vehicle import MecanumBase
    # car = MecanumBase()
    # car.beep()
    # print(car.get_odom())
    # car.set_pos_offset([0, 0, math.pi/2], 2)
    # car.stop()
    # print(car.get_odom())
    # 前进
    # print("forward")
    # car.set_pos_offset([0.3, 0, 0])
    # # 后退
    # print("backward")
    # car.set_pos_offset([-0.3, 0, 0])
    # car.set_pos_offset([-0.3, -0.3, -2], 5)
    # while True:
    #     car.set_pos([0.3, 0.2, math.pi/2], 2)
    #     time.sleep(1)
    #     car.set_pos([0, 0, 0], 2)
    #     time.sleep(1)
    # while True:

    #     car.turn(1.5, 1.57)
    #     time.sleep(1)

    #     car.turn(1.5, -1.57)
    #     time.sleep(1)
    # car = ()
    # while True:
    #     car.move_closed([-0.15, 0.07], 1)
    #     time.sleep(2)
    #     car.move_closed([0.15, - 0.07], 1)
    #     time.sleep(2)
    # while True:
    #     if my_car.key.get_key() == 3:
    #         my_car.task.arm.switch_side(-1)
    #         my_car.task.arm.reset()
    #         my_car.task.arm.set(-0.05, 0, 1.5)
    #         # while True:

    #             # my_car.lane_forward(0.2, 0.0, 0.1)
    #         my_car.lane_time(0.2, 1)
    #         my_car.lane_advance(0.3, dis_offset=0.01, value_h=500, sides=-1)
    #         my_car.lane_task_location(0.3, 2)

    # my_car.task.pick_up_block()
    # my_car.task.put_down_self_block()
    # my_car.lane_time(0.2, 2)
    # my_car.lane_advance(0.3, dis_offset=0.01, value_h=500, sides=-1)
    # my_car.lane_task_location(0.3, 2)
    # my_car.task.pick_up_block()
    # my_car.close()
    # print(time.time())
    # my_car.lane_task_location(0.3, 2)


    # my_car.debug()
    # programs = [func1, func2, func3, func4, func5, func6]
    # my_car.manage(programs)
    # import sys
    # test_ord = 0
    # if len(sys.argv) >= 2:
    #     test_ord = int(sys.argv[1])
    # print("test:", test_ord)
    # car_test(test_ord)
