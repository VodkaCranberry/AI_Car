#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import threading
import os
import numpy as np
from task_func import MyTask
from log_info import logger
from car_wrap import MyCar
from tools import CountRecord
import math
import sys, os
# 添加上本文件对应目录
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    # kill_other_python()
    my_car = MyCar()
    my_car.beep()
    my_car.task.arm.safe_reset()
    my_car.beep()
    my_car.STOP_PARAM = False
    # my_car.task.reset()


    def hanoi_tower_func():
        my_car.task.arm.safe_reset()
        my_car.set_pose_offset([0.9,0,0])
        print(my_car.get_odometry())
        det_side = my_car.lane_det_dis2pt(0.2, 0.19)
        side = my_car.get_card_side()
        print(side)
        # # 调整检测方向
        #
        #
        # # 调整车子朝向
        my_car.set_pose_offset([-0.15,0, 0])
        my_car.set_pose_offset([0, 0, math.pi/4*side], 1)
        my_car.set_pose_offset([0.10,0, 0])
        # # 第一个要抓取的圆柱
        cylinder_id = 1
        # # 调整抓手位置，获取要抓取的圆柱信息
        my_car.task.arm.switch_side(side*-1)
        my_car.task.arm.set_offset(0.04*side,0)
        pts = my_car.task.pick_up_cylinder(cylinder_id, True)
        # # 走一段距离
        my_car.lane_time(0.3,1.8)

        # 第二次感应到侧面位置
        my_car.lane_sensor(0.2, value_h=0.3, sides=side*-1)
        my_car.lane_sensor(0.2, value_h=0.3, sides=side*-1, stop=True)
        #my_car.lane_time(0,1)
        #
        # 记录此时的位置
        pose_dict = {}
        pose_last = None
        for i in range(3):
            # 根据给定信息定位目标
            index = my_car.lane_det_location(0.5, pts, side=side*-1,crop_mid=False,time_out=5,threshold=0.02)
            my_car.beep()
            pose_dict[index] = my_car.get_odometry().copy()
            if i == 2:
                pose_last = my_car.get_odometry().copy()
            print("shibiedao")
            print(index)
            # pose_list.append([index, my_car.get_odometry().copy()])

            if i < 2:
                my_car.set_pose_offset([0.1, 0, 0])
                my_car.beep()
        if len(pose_dict) < 3:
            logger.error("识别圆柱失败，无法完成任务")
            return
        print(pose_dict)

        # 根据识别到的位置调整方向位置
        # angle = math.atan((pose_dict[2][1] - pose_dict[0][1]) / (pose_dict[2][0] - pose_dict[0][0]))
        # print(angle)
        # my_car.set_pose_offset([0, 0, -angle])
        # 重新定位最后一个圆柱
        # my_car.lane_det_location(0.2, pts, side=side*-1)
        angle_det = my_car.get_odometry()[2]
        # 计算目的地终点坐标
        pose_end = [0, 0, angle_det]
        pose_end[0] = pose_last[0] + 0.15*math.cos(angle_det)
        pose_end[1] = pose_last[1] + 0.15*math.sin(angle_det)
        # print(det)
        # 调整到目的地
        # my_car.set_pose(det)
        for i in range(3):
            det = pose_dict[i]
            det[2] = angle_det
            my_car.set_pose(det)
            # my_car.lane_det_location(0.2, pts, side=side*-1)
            my_car.task.pick_up_cylinder(i)
            my_car.set_pose(pose_end)
            my_car.task.put_down_cylinder(i)
        # return

        #去年的版本
        # my_car.set_pose_offset([0.85,0,0],during=2.5,threshold=[0.01,0.01,0.2])
        # #print(my_car.get_odometry())
        # det_side = my_car.lane_det_dis2pt(0.2, 0.19)
        # side = my_car.get_card_side()
        # print(side)
        # my_car.task.arm.switch_side(side*-1)
        # # 第一个要抓取的圆柱
        # cylinder_id = 0
        # # 调整抓手位置，获取要抓取的圆柱信息
        # pt = my_car.task.pick_up_cylinder(cylinder_id, True)
        # my_car.set_pose_offset([-0.17,0, 0],threshold=[0.01,0.01,0.2])
        # my_car.set_pose_offset([0, 0, 1*math.pi/ 6 * 1.5 * side],threshold=[0.01,0.01,0.2])
        # my_car.set_pose_offset([0.10,0, 0],threshold=[0.01,0.01,0.2])
        # print(my_car.get_odometry())
        # # det_side = my_car.lane_det_dis2pt(0.2, 0.19)
        # # side = my_car.get_card_side()
        # # print(side)
        # # my_car.set_pose_offset([-0.1,0, 0])
        # # # 调整检测方向
        # # my_car.task.arm.switch_side(side * -1)
        # # # 调整车子朝向
        # # my_car.set_pose_offset([0, 0, math.pi / 6 * 1.5 * side], 1)

        # # 走一段距离
        # my_car.lane_dis_offset(0.3, 0.7)
        # # 第二次感应到侧面位置
        # #my_car.lane_sensor(0.2, value_h=0.3, sides=side * -1)
        # my_car.lane_sensor(0.2, value_l=0.3, sides=side * -1, stop=True)
        # # 记录此时的位置
        # pos_start = np.array(my_car.get_odometry())
        # logger.info("start pos:{}".format(pos_start))
        # return
        # my_car.lane_dis(0.2, 0.1)
        # return
        # # 根据给定信息定位目标
        # my_car.lane_det_location(0.2, pt, side=side * -1)
        # # 抓取圆柱
        # my_car.task.pick_up_cylinder(cylinder_id)
        # # 计算走到记录位置的距离
        # run_dis = my_car.calculation_dis(pos_start, np.array(my_car.get_odometry()))
        # # print("run_dis:{}".format(run_dis))
        # # 后移刚才计算的距离，稍微多走一点儿
        # my_car.set_pose_offset([(run_dis + 0.065), 0, 0])

        # # # # print("stop pos:{}".format(my_car.get_odom()))
        # # tar_pos = my_car.get_odometry()
        # # # 记录位置
        # # logger.info("tar_pos:{}".format(tar_pos))
        # # my_car.task.put_down_cylinder(cylinder_id)

        # # 抓取2号圆柱
        # cylinder_id = 1
        # pt = my_car.task.pick_up_cylinder(cylinder_id, True)
        # my_car.lane_det_location(0.2, pt, dis_out=0.5, side=-1 * side)
        # my_car.task.pick_up_cylinder(cylinder_id)
        # my_car.set_pose(tar_pos)
        # # print(my_car.get_odom())
        # my_car.task.put_down_cylinder(cylinder_id)

        # # 抓取3号圆柱
        # cylinder_id = 2
        # pt = my_car.task.pick_up_cylinder(cylinder_id, True)
        # my_car.lane_dis_offset(0.2, 0.1)
        # my_car.lane_det_location(0.2, pt, dis_out=0.5, side=-1 * side)
        # my_car.task.pick_up_cylinder(cylinder_id)
        # my_car.set_pose(tar_pos)
        # # print(my_car.get_odom())
        # my_car.task.put_down_cylinder(cylinder_id)

        # # 调整位置
        # # my_car.task.pick_up_cylinder(cylinder_id, True)
        '''
        '''

    def bmi_cal():
        """
        获取车辆 OCR 文本，解析 BMI 并根据结果设置任务等级。
        BMI 对应关系:
            <18.5 → 2（偏瘦）
            18.5–24 → 1（正常）
            24–28 → 4（超重）
            >=28 → 3（肥胖）
        无有效文本或解析失败则直接返回。
        """
        # 1. 准备阶段
        my_car.task.bmi_set(3)                      # 默认姿态
        pts = my_car.task.bmi_set(arm_set=True)     # 机械臂到预设位
        state=my_car.lane_sensor_time(0.3, value_h=0.3,litime=10, sides=1, stop=True)
        print(state)
        time.sleep(0.2)
        if state==False:
            # 2. 按序执行位姿调整
            pose_sequence = [
                ([0.15,  0.00,  0.0],None),            # 推开标签
                ([0.00, -0.03,  0.0],None),
                ([0.20,  0.25,  0.0], [0.6, 0.6, 0]),   # 向前+侧移，加速度自定义
                ([-0.03, -0.07, 0],None),
                ([0.10, 0.00,  0.0],None)
            ]
            for offset, vel in pose_sequence:
                if vel is None:
                    my_car.set_pose_offset(offset)
                else:
                    my_car.set_pose_offset(offset, vel=vel)

            # 3. 获取 OCR 文本并解析 BMI
            text = my_car.get_ocr_whole()
            print(text)
            if not text:       # 同时判断 None / 空字符串
                return
            res = my_car.yiyan_get_bmi(text)
            print(res)
            if not res or "bmi" not in res:
                return
            bmi = res["bmi"]
            print(bmi)
            # 4. 映射 BMI → 等级
            from bisect import bisect
            bmi_thresholds  = [18.5, 24, 28, float("inf")]
            bmi_categories  = [2, 1, 4, 3]              # 对应阈值区间输出
            bmii = bmi_categories[bisect(bmi_thresholds, bmi)]

            # 5. 写回任务系统
            my_car.task.bmi_set(bmii)
            #1 绿色 2 蓝色 3 橙色 4 huangse
            time.sleep(1)
            my_car.lane_time(0.3, 5)
            my_car.set_pose_offset([0,0,-math.pi/6])
            my_car.lane_time(0.3, 9.5)
            my_car.set_pose_offset([0.3,0,0])
            my_car.lane_time(0.3, 2)
        else:
            my_car.set_pose_offset([0,0,-math.pi/6])
            my_car.lane_time(0.3, 9.5)
            my_car.set_pose_offset([0.32,0,0])
            state=my_car.lane_sensor_time(0.3, value_h=0.3,litime=2, sides=1, stop=True)
            pose_sequence = [
                ([0.05,  0.00,  0.0],None),            # 推开标签
                ([0.00, -0.03,  0.0],None),
                ([0.0,  0.4,  0.0], [0.6, 0.6, 0]),   # 向前+侧移，加速度自定义
                ([0.00, -0.07, 0],None),
                ([0.10, 0, 0],None),
                ([0.10, 0.00,  0.0],None)
            ]
            for offset, vel in pose_sequence:
                if vel is None:
                    my_car.set_pose_offset(offset)
                else:
                    my_car.set_pose_offset(offset, vel=vel)

            # 3. 获取 OCR 文本并解析 BMI
            text = my_car.get_ocr_whole()
            print(text)
            if not text:       # 同时判断 None / 空字符串
                return
            res = my_car.yiyan_get_bmi(text)
            print(res)
            if not res or "bmi" not in res:
                return
            bmi = res["bmi"]
            if bmi is None:
                return
            print(bmi)
            # 4. 映射 BMI → 等级
            from bisect import bisect
            bmi_thresholds  = [18.5, 24, 28, float("inf")]
            bmi_categories  = [2, 1, 4, 3]              # 对应阈值区间输出
            bmii = bmi_categories[bisect(bmi_thresholds, bmi)]

            # 5. 写回任务系统
            my_car.task.bmi_set(bmii)
            #1 绿色 2 蓝色 3 橙色 4 huangse
            return


    def camp_fun():
        angle_offset = -math.pi/2*0.82
        # dis_angle = -math.pi/2*0.3
        # dis = 1.
        dis_x = 1.36
        dis_y = -0.87
        # print(dis_x, dis_y)
        angle_now = my_car.get_odometry()[2]
        x_offset = dis_x*math.cos(angle_now) - dis_y*math.sin(angle_now)
        y_offset = dis_y*math.cos(angle_now) + dis_x*math.sin(angle_now)
        angle_tar = angle_now - math.pi*2 + angle_offset
        pose = my_car.get_odometry().copy()
        pose[0] = pose[0] + x_offset
        pose[1] = pose[1] + y_offset
        pose[2] = angle_tar
        # print(pose)
        # return

        my_car.lane_sensor(0.3, value_h=1, sides=-1)
        # time.sleep(25)
        # my_car.lane_sensor()
        my_car.lane_dis_offset(0.3, 0.5)
        my_car.set_vel_time(0.3, 0, -0.5, 1.8)
        my_car.lane_dis_offset(0.3, 2.95)

        my_car.set_pose(pose, vel=[0.2, 0.2, math.pi/3])

        # my_car.
        # my_car.set_vel_time(0.3, 0, -0.1, 1)
        # my_car.move_advance([0.3, 0, 0], value_l=1, sides=-1)
        # my_car.lane_time(0, 1)
        # my_car.move_advance([0.3, 0, -0.2], value_l=1, sides=-1)
        # my_car.move_distance([0.3, 0, 0], 0.25)
        # my_car.move_advance([0.3, 0, 0], value_l=1, sides=-1)
        # my_car.move_advance([0.3, 0, 0], value_l=0.5, sides=-1)


    def send_fun():
        # my_car.move_advance([0.3, 0, 0], value_l=1, sides=-1)
        # my_car.move_distance([0.3, 0, -0.1], 0.25)
        my_car.lane_dis_offset(0.3,1)
        my_car.lane_sensor(0.2, value_l=0.5, sides=-1)
        #my_car.lane_sensor(0.2, value_l=0.5, sides=-1)
        my_car.lane_dis_offset(0.3, 0.17)
        my_car.lane_time(0, 1.5)
        my_car.reset_pose()
        my_car.set_pose_offset([-1.3,0,0])
        #my_car.lane_dis_offset(0.3, 1.54)
        my_car.task.eject(1)


    # 获取食材
    def task_ingredients():
        tar = my_car.task.get_ingredients(side=1,ocr_mode=True, arm_set=True)
        my_car.lane_sensor(0.3, value_h=0.2, sides=1)
        my_car.lane_dis_offset(0.3, 0.17)
        my_car.lane_det_location(0.2, tar, side=1)


        my_car.set_pose_offset([-0.12, 0, 0])
        tar = my_car.task.pick_ingredients(1, 1, arm_set=True)
        my_car.lane_det_location(0.2, tar, side=1)
        my_car.task.pick_ingredients(1, 1)

        my_car.set_pose_offset([0.115, 0, 0])
        my_car.task.arm.switch_side(-1)
        tar = my_car.task.pick_ingredients(2, 2, arm_set=True)
        my_car.lane_det_location(0.2, tar, side=-1)
        my_car.task.pick_ingredients(2, 2)


    def task_ingredients_1():
        def get_food_position(infer_result, target_label):
            """
            内部函数：根据目标 label，在 infer_result 中找到对应食材的二维排布位置
            返回值：row（第几行 1/2），col（该行第几个 1~3）
            """
            # 筛除文本框（box[2] == '0'）
            food_boxes = []
            index_map = {}  # 映射 food_idx → infer_result 原始索引
            for i, box in enumerate(infer_result):
                if box[2] != '0':
                    index_map[len(food_boxes)] = i
                    food_boxes.append(box)

            if len(food_boxes) < 6:
                print(f"期望检测到6个食材框，实际为 {len(food_boxes)}")
                return None, None

            # 找目标框在原始 infer_result 中的索引
            target_index = None
            for i, box in enumerate(infer_result):
                if box[2] != '0' and box[2] == str(target_label):
                    target_index = i
                    break

            if target_index is None:
                print(f"未找到 label = {target_label} 的目标框")
                return None, None

            # 排序框：先按 c_y 分行，再按 c_x 排序
            food_boxes_with_idx = list(enumerate(food_boxes))
            food_sorted_by_y = sorted(food_boxes_with_idx, key=lambda x: x[1][5])  # c_y

            row1 = sorted(food_sorted_by_y[:3], key=lambda x: x[1][4])  # c_x
            row2 = sorted(food_sorted_by_y[3:], key=lambda x: x[1][4])
            sorted_all = row1 + row2

            # 查找目标在排序后的位置
            for idx, (food_idx, box) in enumerate(sorted_all):
                infer_idx = index_map[food_idx]
                if infer_idx == target_index:
                    row = 1 if idx < 3 else 2
                    col = idx % 3 + 1
                    return row, col

            print("未在排序结果中找到目标位置")
            return None, None

        #主函数逻辑
        my_car.task.arm.safe_reset()
        my_car.task.arm.set_hand_angle(80)
        #左侧部分

        # 红外检测边缘
        my_car.lane_sensor(0.2, value_h=0.5, sides=-1)
        #my_car.lane_sensor(0.2, value_h=0.5, sides=-1)
        # 粗调 使得摄像头接近中心

        my_car.lane_dis_offset(0.3, 0.17)
        # my_car.set_pose_offset([0.17,0,0],vel=[0.3, 0,0],threshold=[0.01,0.01,0.2])  # 调整到合适位置

        # 细调 找文本框
        #my_car.task.arm.set(0.09,0)
        #tar = my_car.task.get_ingredients(side=1, ocr_mode=True, arm_set=True)
        #my_car.lane_det_location(0.2, tar, side=1)  # 定位目标
        #my_car.lane_det_location_food_new(speed=0.2,pts_tar=tar, side=1)
        #my_car.lane_det_location_food_new(speed=0.2,pts_tar=tar, side=1,time_out=10)#,crop_mid=True)
        tar = my_car.task.get_ingredients(side=1, ocr_mode=True, arm_set=True)
        my_car.lane_det_location_food_new(speed=0.2,pts_tar=tar, side=1,time_out=5,threshold=0.02)#,crop_mid=True)
        zoods=my_car.get_odometry().copy()
        tar = my_car.task.get_ingredients(side=-1, ocr_mode=True, arm_set=True)
        index=my_car.lane_det_location_food_new(speed=0.2,pts_tar=tar, side=-1,time_out=5,threshold=0.02)
        if index is False:
            my_car.set_pose(zoods)
            #此处如果没有识别到食材文本框,返回原位置
        text = my_car.get_ocr_food_text()
        print("text:",text)
        label = None  # 先初始化，避免后续未定义
        if text is not None:
            print("右侧文本识别内容为：",text)
            yiyan_res = my_car.yiyan_get_food(text)
            # 调试信息
            if yiyan_res is not None:
                label = yiyan_res["label"]
                print("识别成功!", "右侧食材名称为", yiyan_res["name"], "食材label为", label, "理由为", yiyan_res["analysis"])
                my_car.food_names.append(yiyan_res["name"])  # ✅ 保存右侧食材名称
        my_car.task.arm.set(0.13, 0.05)
        img = my_car.cap_side.read()
        infer_result = my_car.task_det(img)  # 检测框信息 定位目标的参数 [label_id, obj_id, label, prob, c_x, c_y, width, height]
        print("infer_result:", infer_result)
        #获得左侧的目标食物的位置信息
        tar_box = None
        for box in infer_result:
            if box[2] != '0' and box[2] == str(label):
                tar_box = box
                break
        if tar_box is None:
            print(f"未找到 label = {label} 的目标框")
        else:
            print(f"找到目标框:", tar_box,yiyan_res["name"])
        #此时手臂水平方向处于中心位置
        row,col = get_food_position(infer_result=infer_result,target_label=label)
        if row is None and col is None:
            row = 1
            col = 2
        print("row",row,"col",col,"label",label)

        #设置手臂位置  具体参数还需要微调
        tar = my_car.task.pick_ingredients(tar=tar_box,num=1, row=row, arm_set=True)

        #寻找目标
        y_offset = 0#(col-2)*0.13
        if col == 3:
            y_offset = -0.10
        elif col == 1:
            y_offset = 0.12
        else:
            y_offset = 0.03

        #根据第几列调整车身位置    (这里可以选择调整手臂位置 或者 调整车身位置 最好还是调整手臂位置) 有待商榷
        my_car.set_pose_offset([y_offset,0,0])
        my_car.set_pose_offset([0,-0.06,0])
        print("--------这里----------传给pts_tar的为",tar,"类型为",type(tar))
        # #抓取第一个目标
        my_car.task.pick_ingredients(tar=tar,num=1, row=row,grap=True)
        my_car.task.arm.switch_side(0)  # 切换到右侧手臂
        my_car.task.arm.set_offset(-0.06,0)
        my_car.task.arm.set_offset(0,-0.05)
        my_car.task.arm.grap(0)
        my_car.set_pose_offset([0,0.065,0])
        my_car.set_pose_offset([-y_offset,0,0])
        my_car.set_pose_offset([-0.05,0,0])

        tar = my_car.task.get_ingredients(side=1, ocr_mode=True, arm_set=True)
        my_car.lane_det_location_food_new(speed=0.2,pts_tar=tar, side=1,time_out=5,threshold=0.02)#,crop_mid=True)
        text = my_car.get_ocr_food_text()
        print("左侧文本识别内容为：",text)
        if text is None or text == "":
            print("未识别到左侧食材文本")
            return
        # 大模型识别食物,获得文字描述的食物对应的label {label: food: analysis:}
        
        # 调试信息
        label = None  # 先初始化，避免后续未定义\
        yiyan_res = my_car.yiyan_get_food(text)
        if yiyan_res is not None:
            label = yiyan_res["label"]
            print("识别成功!", "左侧食材名称为", yiyan_res["name"], "食材label为", label, "理由为", yiyan_res["analysis"])
            my_car.food_names.append(yiyan_res["name"])  # ✅ 保存左侧食材名称
        else:
            return
        # 读取图像，获取所有的框信息
        # 调整摄像头位置 更好地识别
        my_car.task.arm.set(0.04, 0.05)
        img = my_car.cap_side.read()
        infer_result = my_car.task_det(img)  # 检测框信息 定位目标的参数 [label_id, obj_id, label, prob, c_x, c_y, width, height]
        print("infer_result:", infer_result)
        #获得左侧的目标食物的位置信息
        tar_box = None
        for box in infer_result:
            if box[2] != '0' and box[2] == str(label):
                tar_box = box
                break
        if tar_box is None:
            print(f"未找到 label = {label} 的目标框")
        else:
            print(f"找到目标框:", tar_box,yiyan_res["name"])
        #此时手臂水平方向处于中心位置
        row,col = get_food_position(infer_result=infer_result,target_label=label)
        if row is None and col is None:
            row = 1
            col = 2
        print("row",row,"col",col,"label",label)

        #设置手臂位置  具体参数还需要微调
        tar = my_car.task.pick_ingredients(tar=tar_box,num=1, row=row, arm_set=True)

        #寻找目标
        y_offset = 0#(col-2)*0.13
        if col == 1:
            y_offset = -0.10
        elif col == 3:
            y_offset = 0.14
        else:
            y_offset = 0

        #根据第几列调整车身位置    (这里可以选择调整手臂位置 或者 调整车身位置 最好还是调整手臂位置) 有待商榷
        my_car.set_pose_offset([y_offset,0,0])
        my_car.set_pose_offset([0,0.03,0])
        print("--------这里----------传给pts_tar的为",tar,"类型为",type(tar))
        # #抓取第一个目标
        my_car.task.pick_ingredients(tar=tar,num=1, row=row,grap=True)


        # #第二个目标逻辑 这里只读取
        # my_car.set_pose_offset([-y_offset,0,0])
        # #切换到右侧
        # tar = my_car.task.get_ingredients(side=-1,ocr_mode=True,arm_set=True)
        # my_car.lane_det_location(speed=0.2, pts_tar = tar, side=-1)
        # text = my_car.get_ocr_food_text()
        # print("左侧文本识别内容为：",text)
        # if text is None or text == "":
        #     print("未识别到左侧食材文本")
        #     return
        # # 大模型识别食物,获得文字描述的食物对应的label {label: food: analysis:}
        # yiyan_res = my_car.yiyan_get_food(text)
        # # 调试信息
        # right_name = None  # 先初始化，避免后续未定义
        # right_name = yiyan_res["name"]
        # my_car.food_names.append(right_name)

        return

        '''
        #原来的答题任务
        def task_answer():
            my_car.lane_sensor(0.3, value_h=0.3, sides=1)
            my_car.task.arm.switch_side(1)
            my_car.move_distance([0.3, 0, 0], 0.22)
            tar = my_car.task.get_answer(arm_set=True)
            my_car.lane_det_location(0.2, tar, side=1)
            text = my_car.get_ocr()
            # print(text)
            out = 0
            pose_tar_offset = [0.08*out-0.12, 0, 0]
            my_car.set_pose_offset(pose_tar_offset)
            my_car.task.get_answer()
        # my_car.move_distance([0.3, 0, 0], 0.24)
        '''

    #修改后的答题任务
    def task_answer():
        my_car.lane_sensor(0.43, value_h=0.3, sides=1)    # 移动、检测侧边
        my_car.task.arm.switch_side(1)                  # 切换到左臂
        my_car.move_distance([0.3, 0, 0], 0.22)          # 预推进
        tar = my_car.task.get_answer(arm_set=True)       # 粗定位题目 让手臂就位
        #my_car.task.arm.set(0.01,0.045)

        my_car.lane_det_location_food(speed=0.2,label=0,pts_tar=tar,side=1,time_out=5)       # 精定位
        # my_car.lane_det_location(speed=0.2,pts_tar=tar,side=1)

        # my_car.set_pose_offset([0.03,0,0])
        #调整到适应高度识别整个文字
        #my_car.task.arm.set(0.01,0.045)
        my_car.task.arm.set(0.04,0.043)
        #识别得到ocr结果 包含题目和答案
        text = my_car.get_ocr_questions()                          # OCR 识别文字题目
        #打印ocr信息
        print("ocr的识别结果为",text)
        #将手臂调整到适应高度 准备击打
        my_car.task.arm.set(0.12,0.10)
        conbined = ""
        if text:
            question = text[0]
            options = text[1:]
            conbined = question + " " + " ".join([f"{i}: {opt}" for i, opt in enumerate(options)])
            print("组合后的结果为:", conbined)
        answer = my_car.yiyan_get_answer(conbined)             # 大模型判断答案
        if answer is None:
            print("未能识别到答案，请检查 OCR 结果或大模型响应")
            #return
            out = 0
        else:
            out = 0
            out = answer["answer"]
        print(answer)
        print("out为",out,"理由为",answer["analysis"])
        print(out)
        # pose_tar_offset = [0.08 * out - 0.12, 0, 0]
        pose_tar_offset = [0.08 * out - 0.12, 0, 0]
        my_car.set_pose_offset(pose_tar_offset)
        my_car.task.get_answer()  # 执行击打任务

    def task_fun2():
        # 巡航到投掷任务点2
        my_car.lane_sensor(0.4, value_h=0.5, sides=-1)
        # 调整方向
        my_car.lane_time(0, 1)
        my_car.set_pose_offset([-0.03, 0, 0])
        my_car.task.eject(2)
        my_car.set_pose_offset([0.03, 0, 0])
        # my_car.task.arm.switch_side(-1)
        # my_car.move_distance([0.3, 0, 0], 0.24)
        # tar = my_car.task.get_answer(arm_set=True)

    def task_food():
        # my_car.lane_sensor(0.3, value_h=0.5, sides=-1)

        tar = my_car.task.set_food(arm_set=True)
        my_car.task.arm.switch_side(-1)
        my_car.set_pose_offset([0.18, 0, 0])
        my_car.lane_time(0, 1)
        my_car.lane_det_location(0.2, tar, side=-1)
        my_car.set_pose_offset([0.075, 0, 0])
        my_car.task.set_food(1, row=2)
        my_car.set_pose_offset([0.045, 0, 0])
        my_car.task.set_food(2, row=2)
        # my_car.lane_dis_offset(0.3, 0.17)
        # my_car.lane_det_location(0.2, tar, side=1)
        # my_car.task.pick_ingredients(1, 1)
    def task_food_1():
        # my_car.lane_sensor(0.3, value_h=0.5, sides=-1)
        #手臂设置呈右边 准备放
        tar = my_car.task.set_food(arm_set=True)
        my_car.task.arm.switch_side(-1)
        #向前移动一段距离
        my_car.set_pose_offset([0.1, 0, 0])
        my_car.task.arm.set_hand_angle(0)
        my_car.task.arm.set(0.12,0.02)
        # 定位文字前面的两行
        my_car.lane_det_location(0.2, tar, side=-1)
        # my_car.set_pose_offset([0.075, 0, 0])

        #检测前面两个的描述

        texts = my_car.get_two_ocr_texts()
        all_text = "两个描述为" + " ".join(texts) + "以获取的食材为：" + "、".join(my_car.food_names)
        output = my_car.yiyan_get_ingredients_answer(all_text)
        row = -1
        if output is None:
            print("未能识别到食材，请检查 OCR 结果或大模型响应")
            return
        else:
            print("analysis:", output["analysis"],"row:", output["row"])
        row = output["row"]
        if row != -1: #如果前面两个文本框里的描述中的一个可以很好的匹配食材，那么开始放置
            print("执行的是row!=-1的程序")
            my_car.set_pose_offset([0.08,0,0])
            my_car.task.set_food(1, row=2-row)
            return
            # 抓取第二个逻辑 已验证正确
            # my_car.set_pose_offset([0.045, 0, 0])
            # my_car.task.set_food(2, row=2-row)
        else: #否则 前进到后面的两个文本框，继续读取
            print("执行的是row==-1的程序")
            my_car.set_pose_offset([0.38,0,0])
            # my_car.lane_time(0, 1)
            # 定位文字前面的两行
            my_car.lane_det_location(0.2, tar, side=-1)
            texts = my_car.get_two_ocr_texts()
            all_text = "两个描述为" + " ".join(texts) + "以获取的食材为：" + "、".join(my_car.food_names)
            output = my_car.yiyan_get_ingredients_answer(all_text)
            row = output["row"]
            #放置第一个食材
            my_car.task.set_food(1, row=2-row)
            return
            #放置第二个食材的逻辑
            my_car.set_pose_offset([-0.045, 0, 0])
            my_car.task.set_food(2, row=2-row)
        # my_car.lane_dis_offset(0.3, 0.17)
        # my_car.lane_det_location(0.2, tar, side=1)
        # my_car.task.pick_ingredients(1, 1)
    def task_food_2():
        #my_car.lane_sensor(0.3, value_h=0.5, sides=-1)
        #手臂设置呈右边 准备放
        tar = my_car.task.set_food(arm_set=True)
        my_car.task.arm.switch_side(-1)
        #向前移动一段距离
        my_car.set_pose_offset([0.1, 0, 0])
        my_car.task.arm.set_hand_angle(0)
        my_car.task.arm.set(0.12,0.02)
        # 定位文字前面的两行
        my_car.lane_det_location(0.2, tar, side=-1)
        # my_car.set_pose_offset([0.075, 0, 0])

        #检测右边的两个的描述
        texts_right = my_car.get_two_ocr_texts()
        #移动到左边的大致识别两个文本的位置
        my_car.set_pose_offset([0.38,0,0])
        #定位左边的文字
        my_car.lane_det_location(0.2, tar, side=-1)
        #获得左边的两个描述
        texts_left = my_car.get_two_ocr_texts()

        #得到所有的题目的字符串
        texts_all = texts_right + texts_left
        # 加编号并格式化成字符串
        numbered_texts = [f"{i}:{text}" for i, text in enumerate(texts_all)]
        final_text = "、".join(numbered_texts)
        print(final_text)
        final_text = "描述为：\n" + "\n".join(numbered_texts) + "\n已经获取的食材为: " + " ".join(my_car.food_names)

        output = my_car.yiyan_get_ingredients_answer(final_text)
        print("row",output["row"],"analysis",output["analysis"])
        #获取对应的编号
        idx = output["row"]
        print("idx=",idx)
        # print("食材种类为",my_car.food_names)
        #idx==0 和idx==1 表明是前面检测的两个文本，说明在右边，还要回去
        if idx == 0 or idx == 1:
            #计算行数
            row = 0
            row = idx % 2
            #回到摄像头对准文本的位置
            my_car.set_pose_offset([-0.38,0,0])
            #精定位文字,这里精确对准文字后，再偏移就可以找到放置的位置
            my_car.lane_det_location(0.2, tar, side=-1)
            #定位后向前移动一段距离 开始
            my_car.set_pose_offset([0.08,0,0])
            #放置第一个物品
            my_car.task.set_food(1, row=2-row)
            # #移动一段距离
            # my_car.task.set_pose_offset([0.045,0,0])
            # #放置第二个物品
            # my_car.task.set_food(2, row=2-row)
        else: #否则的话 idx就是2或者3
            row = idx % 2
            #向后移动一段距离 开始放置物品
            my_car.set_pose_offset([-0.08,0,0])
            #放置第一个物品
            my_car.task.set_food(1, row=2-row)
            # #移动一段距离
            # my_car.task.set_pose_offset([-0.045,0,0])
            # #放置第二个物品
            # my_car.task.set_food(2, row=2-row)

        # if output is None:
        #     print("未能识别到食材，请检查 OCR 结果或大模型响应")
        #     return
        # else:
        #     print("analysis:", output["analysis"],"row:", output["row"])
        # row = output["row"]
        # if row != -1: #如果前面两个文本框里的描述中的一个可以很好的匹配食材，那么开始放置
        #     print("执行的是row!=-1的程序")
        #     my_car.set_pose_offset([0.08,0,0])
        #     my_car.task.set_food(1, row=2-row)
        #     return
        #     # 抓取第二个逻辑 已验证正确
        #     # my_car.set_pose_offset([0.045, 0, 0])
        #     # my_car.task.set_food(2, row=2-row)
        # else: #否则 前进到后面的两个文本框，继续读取
        #     print("执行的是row==-1的程序")
        #     my_car.set_pose_offset([0.38,0,0])
        #     # my_car.lane_time(0, 1)
        #     # 定位文字前面的两行
        #     my_car.lane_det_location(0.2, tar, side=-1)
        #     texts = my_car.get_two_ocr_texts()
        #     all_text = "两个描述为" + " ".join(texts) + "以获取的食材为：" + "、".join(my_car.food_names)
        #     output = my_car.yiyan_get_ingredients_answer(all_text)
        #     row = output["row"]
        #     #放置第一个食材
        #     my_car.task.set_food(1, row=2-row)
        #     return
        #     #放置第二个食材的逻辑
        #     my_car.set_pose_offset([-0.045, 0, 0])
        #     my_car.task.set_food(2, row=2-row)
        # my_car.lane_dis_offset(0.3, 0.17)
        # my_car.lane_det_location(0.2, tar, side=1)
        # my_car.task.pick_ingredients(1, 1)
    def task_help():
        my_car.lane_sensor(0.3, value_h=0.3, sides=1)
        my_car.task.help_peo(arm_set=True)
        my_car.set_pose_offset([0.08, 0.15, 0])
        my_car.set_pose_offset([-0.1, 0.18, 0],vel=[0.4, 0.4, 0])
        my_car.set_pose_offset([0, -0.26, 0])
        my_car.set_pose_offset([0.5, 0, 0], vel=[0.3, 0.3, 0])
        # my_car.set_pose_offset([0.1, -0.1, 0])

        # my_car.move_advance([0.2, 0, 0], value_h=0.5, sides=1, dis_out=0.05)
        # my_car.task.help_peo()

    def go_start():
        my_car.lane_sensor(0.3, value_l=0.4, sides=-1)
        my_car.set_pose_offset([0.85, 0, 0], 2.8)
        my_car.set_pose_offset([0.45, -0.09, -0.6], 2.5)
        # 前移
        # my_car.set_pose_offset([0.3, 0, 0], 2.5)
        # my_car.set_pose_offset([0.45, -0.09, -0.6], 2.5)
        # 离开道路到修整营地
        # my_car.set_pose_offset([0.15, -0.4, 0], 2)
        # 做任务
        # my_car.do_action_list(actions_map)
    def car_move():
        my_car.set_pose([0.20, 0,0], 1)
    def final_task():
        #my_car.lane_dis_offset(0.3, 0.3,stop=False)
        #print(my_car.get_odometry())
        my_car.reset_pose()
        my_car.set_pose_offset([0.85,0,0],during=2.5,threshold=[0.01,0.01,0.2])
        #print(my_car.get_odometry())
        #det_side = my_car.lane_det_dis2pt(0.1, 0.19)
        side = -1#my_car.get_card_side()
        time.sleep(0.5)
        print(side)
        my_car.reset_pose()
        my_car.set_pose_offset([-0.10,0, 0],threshold=[0.01,0.01,0.2])
        my_car.set_pose_offset([0, 0, 1*math.pi/4*side],threshold=[0.01,0.01,0.2])
        my_car.reset_pose()
        my_car.set_pose_offset([0.15,0, 0],threshold=[0.01,0.01,0.2])
        my_car.set_pose_offset([0,0.05*side, 0],threshold=[0.01,0.01,0.2])
        my_car.lane_dis_offset(0.5,1.8)
        # if side==1:
        #     my_car.set_pose_offset([0, 0, 1*math.pi/6*side],threshold=[0.01,0.01,0.2])
        my_car.lane_dis_offset(0.5,1.25)
        my_car.reset_pose()
        my_car.set_pose_offset([0.55,0,0],threshold=[0.01,0.01,0.2])
        my_car.lane_dis_offset(0.4,1.3)
        my_car.reset_pose()
        my_car.set_pose_offset([0.2,0,0],threshold=[0.01,0.01,0.2])
        my_car.set_pose_offset([0,0,-math.pi/4],threshold=[0.01,0.01,0.4])
        my_car.set_pose_offset([0.1,0,0],threshold=[0.01,0.01,0.2])
        my_car.lane_dis_offset(0.4, 2.9)
        my_car.reset_pose()
        my_car.set_pose_offset([0.4,0,0],threshold=[0.01,0.01,0.2])
        # for _ in range(5):
        #     my_car.set_pose_offset([0.10,0,-math.pi/60],threshold=[0.01,0.01,0.2])
        send_fun()
        my_car.lane_dis_offset(0.3,0.3)
        task_ingredients_1()
        my_car.lane_dis_offset(0.3,0.5)
        task_answer()
        task_fun2()
        task_food_2()
        #my_car.lane_dis_offset(0.3,2.5)
        task_help()

    my_car.beep()
    time.sleep(0.2)
    functions = [hanoi_tower_func, bmi_cal, camp_fun, send_fun, task_ingredients, task_answer, task_fun2, task_food, task_help,task_ingredients_1,final_task,task_food_1,task_food_2]
    my_car.manage(functions,10)

