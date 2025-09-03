from vehicle import ArmBase, ScreenShow, Key4Btn, ServoBus, ServoPwm, MotorWrap, StepperWrap, PoutD
import cv2
import time
import numpy as np
import yaml, os, math

class Ejection():
    def __init__(self, portm=5, portd=4, port_step=1) -> None:
        self.motor = MotorWrap(portm, -1, type="motor_280", perimeter=0.06/15*8)
        self.pout = PoutD(portd)
        self.step1 = StepperWrap(port_step)
        self.step_rad_st = self.step1.get_rad()
        self.step1_rad_cnt = 0

    def reset(self, vel=0.05):
        rad_last = self.motor.get_rad()

        while True:
            self.motor.set_linear(vel)
            time.sleep(0.02)
            rad_now = self.motor.get_rad()
            if abs(rad_now - rad_last) < 0.02:
                break
            rad_last = rad_now

        self.motor.set_linear(0)

    def eject(self, x=0.1, vel=0.05):
        self.reset()
        self.pout.set(1)
        self.motor.reset()
        self.motor.set_linear(0-abs(vel))
        length = 0.11
        while True:
            self.motor.set_linear(0-abs(vel))
            if abs(self.motor.get_dis()) > length:
                break
        self.motor.set_linear(0)
        self.step1_rad_cnt += 1
        self.step1.set_rad(math.pi/5*2*self.step1_rad_cnt + self.step_rad_st)
        self.pout.set(1)
        time.sleep(0.5)
        while True:
            self.motor.set_linear(abs(vel))
            if abs(self.motor.get_dis()) < x:
                break
        self.motor.set_linear(0)
        self.pout.set(0)


class MyTask:
    def __init__(self):
        # 旋转舵机
        self.servo_bmi = ServoBus(2)
        # self.servo_rotate.set_angle(90, 0)

        # 发射装置
        self.ejection = Ejection()
        time.sleep(0.3)

        # 机械臂
        self.arm = ArmBase()

    def reset(self):
        self.arm.reset()

    # 抓圆柱，选则大小
    def pick_up_cylinder(self, radius, arm_set=False):
        # 定位目标的参数 label_id, obj_width, label, prob, err_x, err_y, width, height
        tar_list =  [[10, 100, "13", 0,  0.18, 0.68, 0.86, 0.62], [9, 80, "14", 0, 0.07, 0.689, 0.6538, 0.620],
                      [8, 60, "15", 0, 0.18, 0.72, 0.56, 0.53]]
        # tar_list =  [[10, 100, "13", 0,  0, 0,0,0], [9, 80, "14", 0, 0, 0, 0, 0],
        #               [8, 60, "15", 0, 0, 0, 0, 0]]
        # pt_tar = tar_list[radius-1]
        height_list = [0.08, 0.08, 0.15]
        tar_height = height_list[0]
        tar_horiz = self.arm.horiz_mid
        # 手臂方向向下
        self.arm.set_hand_angle(80)
        if arm_set:
            tar_height = 0.03
            # 到达目标位置
            self.arm.set(tar_horiz, tar_height)
            return tar_list
        # 抓取圆柱

        # 到圆柱的位置
        horiz_offset = 0.14 * self.arm.side
        if radius == 0:
            # self.arm.set(tar_horiz, tar_height+0.04)
            self.arm.set_offset(0, 0.04)
        tar_horiz = self.arm.horiz_mid-0.02 + horiz_offset
        self.arm.set(tar_horiz, tar_height)
        # 往下放,抓住
        self.arm.set_offset(0, -0.05)
        self.arm.grap(1)
        time.sleep(1)
        # 抬起一定高度
        # height_offset = 0.07
        height_offset = 0.12
        if radius == 2:
            height_offset += 0.06
        self.arm.set_offset(0, height_offset)
        # self.arm.set_offset(0, 0.08, 1.3)

    def put_down_cylinder(self, radius):
        # tar_height = 0.02
        height_offset = 0.02
        if radius==0:
            height_offset = 0.12
        # 下放放开物块
        self.arm.set_offset(0, 0-height_offset)
        # time.sleep(0.2)
        self.arm.grap(0)
        time.sleep(0.5)
        # 抬起
        self.arm.set_offset(0, 0.04)
        # horiz_offset = 0.1 * self.arm.side * -1
        # self.arm.set_offset(horiz_offset, 0)

    def bmi_set(self, num=0, arm_set=False):
        tar = [[0, 70, 'text_det', 0, 0, -0.31, 0.85, 1.0]]
        bmi = {0:0, 1:-45, 2: -135, 3:45, 4:135}
        tar_height = 0.02
        tar_horiz = 0.14
        if arm_set:
            self.arm.set_hand_angle(48)
            self.arm.set(tar_horiz, tar_height)
            return tar
        self.servo_bmi.set_angle(bmi[num])
        # self.servo_bmi.set_angle(0)

    def get_ingredients(self, side=1, ocr_mode=False, arm_set=False):
        #原代码

        tar =[[15,50,"0",0.0,0.05048077,0.78365385,0.39903846,0.42307692]] if side==1 else [[15,50,"0",0,0,0.85,0.42,0.30]]# [[15,0,0,0.607,-0.02884615,0.84375,0.46153846,0.3125]]
        if ocr_mode:
            tar_height = 0.0
        else:
            tar_height = 0.07

        tar_horiz = 0.02 if side==1 else 0.20 #self.arm.horiz_mid
        self.arm.set_hand_angle(48)
        self.arm.switch_side(side)
        self.arm.set(tar_horiz, tar_height)

        if arm_set:
            return tar
        # self.arm.switch_side(side)
        # self.arm.set_offset(0.1, 0)


    def pick_ingredients(self, tar,num=1, row=1, arm_set=False,grap=False):
        # 计算高度，手臂根据高度设置位置
        if row==1:
            tar_height = 0.085
        else:
            tar_height = 0
        horiz_offset = 0 * self.arm.side
        tar_horiz = self.arm.horiz_mid + horiz_offset

        self.arm.set(tar_horiz, tar_height)
        # 准备抓取
        self.arm.grap(1)
        # 如果是进行识别，这里手向下
        if arm_set:
            self.arm.set_hand_angle(80)
            return [tar]
        # 手水平
        self.arm.set_hand_angle(-60)
        time.sleep(0.5)
        # 手臂向外伸，去抓取物块
        horiz_offset = 0.115*self.arm.side
        self.arm.set_offset(horiz_offset, 0)

        # self.arm.set(0.26, 0.10)
        if num > 1:
            # 第二块保持住不动
            self.arm.set_offset(-0.18*self.arm.side, 0.02, speed=[0.12, 0.04])
            return tar
        # 收回手臂
        # self.arm.set_offset(-0.14*self.arm.side, 0.03, speed=[0.12, 0.04])
        self.arm.set(tar_horiz, tar_height)
        if row==2:
            self.arm.set(tar_horiz, 0.085)
        # 手向下
        self.arm.set_offset(0,0.02)  #7_22 22:37新加入的逻辑 为了应对拿取物块之后 可能先转会导致挡到掉食物
        self.arm.set_hand_angle(80)
        time.sleep(0.3)             #7_22
        self.arm.set_offset(0,0.02)  #7_22
        # 放下物块
        self.arm.set_offset(-0.13*self.arm.side, 0, speed=[0.12, 0.04])
        # self.arm.set(0.14-self.arm.side*0.14, 0.04, speed=[0.08, 0.04])

        self.arm.set_offset(0, -0.050, speed=[0.12, 0.04])
        # time.sleep(0.5)
        if grap==False:
            self.arm.grap(0)
        time.sleep(0.5)
        self.arm.set_offset(0, 0.045, speed=[0.12, 0.04])


    def get_answer(self, arm_set=False):
        # tar = [[0, 70, 0, 0, 0, -0.5, 0.44, 0.6]]
        tar = [[0, 70, "0", 0, 0, -0.5, 0.44, 0.6]]
        # tar = [[0,70,0,0,0.11298077,-0.34855769,0.47596154,0.58173077]]
        # tar = [[0,70,0,0,0.05769231,-0.36298077,0.5,0.64903846]]
        #self.arm.grap(1)
        self.arm.switch_side(1)
        self.arm.set_hand_angle(80)
        tar_height = 0.045
        tar_horiz = self.arm.horiz_mid

        self.arm.set(tar_horiz, tar_height)
        if arm_set:
            return tar
        # 竖着向下为-45
        self.arm.set_hand_angle(-55)
        self.arm.set(0.12,0.07)
        self.arm.set_offset(0.11, 0)
        self.arm.set_offset(-0.11, 0)


    def set_food(self, num=1, row=1, arm_set=False):
        # 定位目标的参数 label_id, obj_id, label, prob, err_x, err_y, width, height
        tar = [[15, 70, 0 , 0, 0.09615385,-0.15865385,0.44230769,0.57692308]]
        # 气泵吸气并关闭阀门，调整手臂方向向右

        self.arm.grap(1)
        self.arm.switch_side(-1)

        if arm_set:
            # 准备识别的位置，手朝向下
            self.arm.set_hand_angle(80)
            tar_height = 0.12
            tar_horiz = self.arm.horiz_mid
            # 到达准备位置
            self.arm.set(tar_horiz, tar_height)
            return tar


        if num > 1:
            # 如果放的不是第一个，需要先抓取，手朝向下
            self.arm.set_hand_angle(80)
            # 到达抓取位置，准备抓取
            self.arm.set(self.arm.horiz_mid+0.14, 0.04, speed=[0.12, 0.04])
            # 向下移动抓取
            self.arm.grap(1)
            self.arm.set_offset(0, -0.04, speed=[0.12, 0.04])
            time.sleep(0.5)
            # 向上移动
            self.arm.set_offset(0, 0.05, speed=[0.12, 0.04])
            # 手臂指向方向调整水平
            self.arm.set_hand_angle(-60)
        self.arm.set_hand_angle(-60)
        # 根据目标位置调整手臂位置
        tar_height = 0.005+(row-1)*0.1
        horiz_offset = 0 * self.arm.side
        #  准备放食材到指定位置
        tar_horiz = self.arm.horiz_mid + horiz_offset
        self.arm.set(tar_horiz, tar_height)
        # 手臂向前伸运动0.14m
        self.arm.set_offset(0.11*self.arm.side, 0, speed=[0.12, 0.04])
        # self.arm.set()
        # self.arm.set_hand_angle(-45)
        # self.arm.set_offset(-0.09, 0)
        time.sleep(0.5)
        self.arm.grap(0)
        time.sleep(0.5)
        self.arm.set_offset(-0.1*self.arm.side, 0, speed=[0.12, 0.04])
    def eject(self, area=1):
        dis_list = {1:0.0845, 2:0.063}
        self.ejection.eject(dis_list[area])

    def help_peo(self, arm_set=False):
        # 调整方向向左
        self.arm.switch_side(1)
        # 调整手水平
        self.arm.set_hand_angle(-45)
        tar_height = 0.08
        tar_horiz = self.arm.horiz_mid
        self.arm.set(tar_horiz, tar_height)
        if arm_set:
            return
        # 伸长手臂
        self.arm.set_offset(0.1, 0)
        self.arm.set_offset(-0.1, 0)



def task_reset():
    task = MyTask()
    task.reset()
    time.sleep(0.1)

def bmi_test():
    task = MyTask()
    task.bmi_set(0)

def cylinder_test():
    task = MyTask()
    key = Key4Btn(1)
    # task.arm.reset()
    i = 0
    tar = task.pick_up_cylinder(i, arm_set=True)
    while True:
        if key.get_key()!=0:

            time.sleep(1)
            task.pick_up_cylinder(i)
            time.sleep(1)
            task.put_down_cylinder(i)
            time.sleep(1)
            i = i+1
    # for i in range(3):
    #     tar = task.pick_up_cylinder(i+1, arm_set=True)
    #     time.sleep(0.8)
    #     task.pick_up_cylinder(i+1)
    #     time.sleep(0.5)
    #     task.put_down_cylinder(i+1)
    #     time.sleep(0.5)

# 定义一个函数highball_test
def ingredients_test():
    task = MyTask()
    task.get_ingredients(1, arm_set=True)

def pick_ingredients_test():
    task = MyTask()
    tar = task.get_ingredients(1, ocr_mode=True, arm_set=True)
    print(tar)
    # task.arm.switch_side(1)
    # task.pick_ingredients(1)
    # task.arm.switch_side(-1)
    # task.pick_ingredients(2, 2)

def answer_test():
    task = MyTask()
    task.get_answer(arm_set=True)
    # time.sleep(1)
    # task.get_answer()

def food_test():
    task = MyTask()
    task.set_food(arm_set=True)
    time.sleep(1)
    task.set_food()
    task.set_food(2)

def eject_test():
    task = MyTask()
    task.eject(2)

if __name__ == "__main__":

    # import argparse
    # args = argparse.ArgumentParser()
    # args.add_argument('--op', type=str, default="none")
    # args = args.parse_args()
    # print(args)
    # if args.op == "reset":
    #     task_reset()
    task=MyTask()
    # task.arm.set(0.135,0)
    # pick_ingredients_test()
    # task.servo_bmi.set_angle(-90)
    # eject_test()
    #task.arm.set(0.10,0.045)
    #task.arm.set(0.02,0.045)
    # task.arm.set_hand_angle(80)
    # task.arm.set(0.12,0.05)
    # task.arm.set_offset(0.125, 0)
    # task.arm.set_offset(-0.125, 0)
    #
    # task.arm.grap(1)
    # task.arm.safe_reset()
    # task.arm.set(0,0)
    # task.set_food(1, row=1)
    # task.set_food(2, row=1)

    # task.arm.grap(1)
    # time.sleep(1)
    # task.arm.set_offset(-0.11,0)

    # task.arm.grap(1)
    # task.arm.safe_reset()
    #task.arm.grap(1)

    # time.sleep(2)
    # task.arm.set_offset(0.11,0)
    #task.arm.set_hand_angle(80)
    #task.arm.safe_reset()
    # task.arm.set_hand_angle(-60)
    task.arm.grap(0)
    # task.arm.set_hand_angle(0)
    # task.arm.set(0.12,0.02)
    # task.arm.set(0.11, 0.09)

    # task.arm.set_offset(0.115,0)


    #物块抓取调试
    # # task.arm.set(0.23,0.18)
    # task.arm.safe_reset()
    # task.arm.set(0.12, 0)
    # task.arm.grap(1)
    # task.arm.set_hand_angle(-80)
    # time.sleep(0.2)
    # task.arm.set_offset(0.115, 0)
    # time.sleep(0.5)

    # # task.arm.set_offset(-0.23, 0.06)
    # task.arm.set_arm_angle(85)
    # task.arm.set_offset(-0.24, 0.06)
    # task.arm.set_hand_angle(80)
    # task.arm.set_offset(0, -0.06)
    # time.sleep(5)
    # task.arm.grap(0)
    # task.arm.set_offset(0.06,0.06)


    # task.arm.safe_reset()
    # # task.arm.set_hand_angle(-55)
    # # task.arm.grap(1)
    # task.arm.grap(1)
    # task.arm.set_hand_angle(-79)
    # task.arm.set_offset(-0.115, 0)
    # task.arm.set_offset(0.235,0)
    # task.arm.set_offset(-0.235,0)
    # task.arm.set_hand_angle(80)
    # task.arm.grap(0)
    # row = 2
    # if row==1:
    #     task.arm.set(0.12, 0.07)
    # else:
    #     task.arm.set(0.12, 0)
    #     task.arm.set_offset(0,-0.1)
    # task.arm.set_offset(0.115,0)
    # task.arm.set_offset(-0.115,0)
    # task.arm.set_offset(0,0.1)
    # task.arm.grap(0)
    # task.arm.set_hand_angle(80)
    # task.get_answer()
    # task.arm.safe_reset()
    # task.arm.safe_reset()
    # task.arm.set(0.12, 0.11)
    # task.arm.set(0.12,0.08)
    # task.arm.grap(0)
    # task.arm.switch_side(1)

    # task.arm.set_hand_angle(-43)
    # cylinder_test()
    # bmi_test()
    # task.bmi_set(4)
    # # ingredients_test()
    # # pick_ingredients_test()
    # answer_test()
    # food_test()
