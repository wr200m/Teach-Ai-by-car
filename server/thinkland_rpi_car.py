import time
import RPi.GPIO as GPIO
import random

__authors__ = 'xiao long & xu lao shi'
__version__ = 'version 0.01'
__license__ = 'Copyright...'

class Car:
    """
    *类在树莓派上直接控制小车的运动，例如直行、转弯等
    *__init_level  初始化io输出类型
    *__init_pwm    初始化pwm
    *__led_light    r、g、b同时控制，内部调用
    *led_light      打开灯
    *turn_on_led    打开灯（r、g、b）一种
    *turn_off_led   关灯
    *stop_all_wheels 停止运动
    *run_forward  向前动
    *run_reverse 向后转
    *turn_left 向左转
    *turn_right 向右转
    *spin_left 向左转弯
    *spin_right 向右转弯
    *distance_from_obstacle 超声波测距
    *line_tracking_turn_type 巡线类型
    *demo_line_tracking @@例子，巡线
    *demo_cruising @@例子，漫游
    *obstacle_status_from_infrared 障碍物类型
    *turn_servo_ultrasonic 多个角度进行超声波测距
    *obstacle_status_from_ultrasound 超声波测距状态
    *check_left_obstacle_with_sensor 左侧是否有障碍物
    *check_right_obstacle_with_sensor 右侧是否有障碍物
    *servo_front_rotate 超声波测距检测
    *servo_camera_rotate 控制相机的舵机进行旋转
    *servo_camera_rise_fall 控制相机的舵机进行抬升下降
    """
    ################################################################
    #  直流电机引脚定义
    PIN_MOTOR_LEFT_FORWARD = 20
    PIN_MOTOR_LEFT_BACKWARD = 21
    PIN_MOTOR_RIGHT_FORWARD = 19
    PIN_MOTOR_RIGHT_BACKWARD = 26
    PIN_MOTOR_LEFT_SPEED = 16
    PIN_MOTOR_RIGHT_SPEED = 13

    # 超声波引脚定义
    PIN_ECHO = 0
    PIN_TRIG = 1

    # 彩色灯引脚定义
    PIN_LED_R = 22
    PIN_LED_G = 27
    PIN_LED_B = 24

    # 伺服电机引脚定义
    PIN_FRONT_SERVER = 23
    PIN_UP_DOWN_SERVER = 11
    PIN_LEFT_RIGHT_SERVER = 9

    # 避障脚定义
    PIN_AVOID_LEFT_SENSOR = 12
    PIN_AVOID_RIGHT_SENSOR = 17

    # 巡线传感器引脚定义
    PIN_TRACK_1 = 3  # counting From left, 1
    PIN_TRACK_2 = 5  # 2
    PIN_TRACK_3 = 4  # 3
    PIN_TRACK_4 = 18  # 4

    # 蜂鸣器
    PIN_BUFFER = 8
    #########################################################
    # 宏定义特殊
    HAVE_OBSTACLE = 0
    NO_OBSTACLE = 1

    SERVO_TOTAL_STEP = 18


    LED_R = 0
    LED_G = 1
    LED_B = 2

    OPEN = GPIO.HIGH
    CLOSE = GPIO.LOW

    LINE_MOVE_TYPE = 0
    LINE_BACK_FORTH_MOVE_TYPE = 1
    TURN_CORNER_MOVE_TYPE = 2
    SPRIN_MOVE_TYPE = 3
    RECT_MOVE_TYPE = 4

    SENSOR_INFRARED_TYPE = 0
    SENSOR_BLACK_WIGHT_TYPE = 1
    SENSOR_ULTRASONIC_TYPE = 2
    #变量
    Car_Init = False

    def __init__(self):
        # 类的构造函数
        # 设置GPIO口为BCM编码方式

        GPIO.setmode(GPIO.BCM)
        # 忽略警告信息
        GPIO.setwarnings(False)
        # 初始化IO
        self.__init_level()
        #初始化 pwm
        self.__init_pwm()

        Car.Car_Init = True
        #函数列表，用于存放函数的容器
        self.Function_List = {}
        #用于灯光控制标志
        self.LED_FLAG = {}
        self.LED_FLAG[Car.LED_R] = True
        self.LED_FLAG[Car.LED_G] = True
        self.LED_FLAG[Car.LED_B] = True

    def __init_level(self):#私有变量 外部不能调用
        """
        #  设置Io的输出方式：
        # 输出模式：即是具有上拉电阻
        # 输入模式：即是能获取电平的高低，在数字电路上高于二极管的导通电压为高，否则为低电平

        Parameters
        ----------
        """
        # 设置超声波电平
        GPIO.setup(Car.PIN_ECHO, GPIO.IN)
        GPIO.setup(Car.PIN_TRIG, GPIO.OUT)

        # 小车输出电平
        GPIO.setup(Car.PIN_MOTOR_LEFT_FORWARD, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(Car.PIN_MOTOR_LEFT_BACKWARD, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(Car.PIN_MOTOR_RIGHT_FORWARD, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(Car.PIN_MOTOR_RIGHT_BACKWARD, GPIO.OUT, initial=GPIO.LOW)

        # 小车速度
        GPIO.setup(Car.PIN_MOTOR_LEFT_SPEED, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(Car.PIN_MOTOR_RIGHT_SPEED, GPIO.OUT, initial=GPIO.HIGH)

        # 蜂鸣器电平
        GPIO.setup(Car.PIN_BUFFER, GPIO.OUT, initial=GPIO.HIGH)

        # 彩灯输出设置
        GPIO.setup(Car.PIN_LED_R, GPIO.OUT)
        GPIO.setup(Car.PIN_LED_G, GPIO.OUT)
        GPIO.setup(Car.PIN_LED_B, GPIO.OUT)

        # 舵机设置为输出模式
        GPIO.setup(Car.PIN_FRONT_SERVER, GPIO.OUT)
        GPIO.setup(Car.PIN_UP_DOWN_SERVER, GPIO.OUT)
        GPIO.setup(Car.PIN_LEFT_RIGHT_SERVER, GPIO.OUT)

        # 避障传感器设置为输入模式
        GPIO.setup(Car.PIN_AVOID_LEFT_SENSOR, GPIO.IN)
        GPIO.setup(Car.PIN_AVOID_RIGHT_SENSOR, GPIO.IN)

        # 设置寻线传感器电平为输入
        GPIO.setup(Car.PIN_TRACK_1, GPIO.IN)
        GPIO.setup(Car.PIN_TRACK_2, GPIO.IN)
        GPIO.setup(Car.PIN_TRACK_3, GPIO.IN)
        GPIO.setup(Car.PIN_TRACK_4, GPIO.IN)

    def __init_pwm(self):#私有变量 外部不能调用
        """
        设置PWM，是脉冲宽度调制缩写
        它是通过对一系列脉冲的宽度进行调制，等效出所需要的波形（包含形状以及幅值），对模拟信号电平进行数字编码，
        也就是说通过调节占空比的变化来调节信号、能量等的变化，占空比就是指在一个周期内，信号处于高电平的时间占据整个信号周期的百分比
        通过设置占空比来控制车速、舵机的角度、灯光的亮度
        """

        # 初始化控制小车的PWM
        self.__pwm_left_speed  = GPIO.PWM(Car.PIN_MOTOR_LEFT_SPEED, 2000)
        self.__pwm_right_speed = GPIO.PWM(Car.PIN_MOTOR_RIGHT_SPEED, 2000)

        self.__pwm_left_speed.start(0)
        self.__pwm_right_speed.start(0)

        # 设置舵机的频率和起始占空比
        self.__pwm_front_servo_pos      = GPIO.PWM(Car.PIN_FRONT_SERVER, 50)
        self.__pwm_up_down_servo_pos    =  GPIO.PWM(Car.PIN_UP_DOWN_SERVER, 50)
        self.__pwm_left_right_servo_pos = GPIO.PWM(Car.PIN_LEFT_RIGHT_SERVER, 50)

        self.__pwm_front_servo_pos.start(0)
        self.__pwm_up_down_servo_pos.start(0)
        self.__pwm_left_right_servo_pos.start(0)

        #设置灯的频率 从而控制其亮度
        # self.__pwm_led_r = GPIO.PWM(PIN_LED_R, 1000)
        # self.__pwm_led_g = GPIO.PWM(PIN_LED_G, 1000)
        # self.__pwm_led_b = GPIO.PWM(PIN_LED_B, 1000)
        #
        # self.__pwm_led_r.start(0)
        # self.__pwm_led_g.start(0)
        # self.__pwm_led_b.start(0)

    def __set_motion(self, left_forward, left_backward,
                    right_forward, right_backward,
                    speed_left, speed_right,
                    duration=0.0):
        """
        Helper function to set car wheel motions

        Parameters
        ----------
        * left_forward   : GPIO.HIGH or LOW
        * left_backward  : GPIO.HIGH or LOW
        * right_forward  : GPIO.HIGH or LOW
        * right_backward : GPIO.HIGH or LOW
        * speed_left     : int
            An integer [0,100] for left motors speed
        * speed_right    : int
            An integer [0,100] for right motors speed
        * duration       : float
            Duration of the motion.
            (default=0.0 - continue indefinitely until called again)
        Raises
        ------
        """
        GPIO.output(Car.PIN_MOTOR_LEFT_FORWARD,   left_forward)
        GPIO.output(Car.PIN_MOTOR_LEFT_BACKWARD,  left_backward)
        GPIO.output(Car.PIN_MOTOR_RIGHT_FORWARD,  right_forward)
        GPIO.output(Car.PIN_MOTOR_RIGHT_BACKWARD, right_backward)
        self.__pwm_left_speed.ChangeDutyCycle(speed_left)
        self.__pwm_right_speed.ChangeDutyCycle(speed_right)
        if duration > 0.0:
            time.sleep(duration)
            self.__pwm_left_speed.ChangeDutyCycle(0)
            self.__pwm_right_speed.ChangeDutyCycle(0)

    def __led_light(self, r, g, b):
        """
         __led_light

         Parameters
         ----------
         * r : bool
             - GPIO.HIGH  GPIO.LOW
         * g : bool
             - GPIO.HIGH  GPIO.LOW
         * b : bool
             - GPIO.HIGH  GPIO.LOW
        """
        GPIO.output(Car.PIN_LED_R, r)
        GPIO.output(Car.PIN_LED_G, g)
        GPIO.output(Car.PIN_LED_B, b)

    def led_light(self, color):
        """
        Shine LED light

        Parameters
        ----------
        * color : str
            - one of ['red', 'green', 'blue',
                      'yellow', 'cyan', 'purple'
                      'white', 'off']
        """
        if color == 'red':
            self.__led_light(GPIO.HIGH, GPIO.LOW, GPIO.LOW)
        elif color == 'green':
            self.__led_light(GPIO.LOW, GPIO.HIGH, GPIO.LOW)
        elif color == 'blue':
            self.__led_light(GPIO.LOW, GPIO.LOW, GPIO.HIGH)
        elif color == 'yellow':
            self.__led_light(GPIO.HIGH, GPIO.HIGH, GPIO.LOW)
        elif color == 'cyan':
            self.__led_light(GPIO.LOW, GPIO.HIGH, GPIO.HIGH)
        elif color == 'purple':
            self.__led_light(GPIO.HIGH, GPIO.LOW, GPIO.HIGH)
        elif color == 'white':
            self.__led_light(GPIO.HIGH, GPIO.HIGH, GPIO.HIGH)
        else:
            self.__led_light(GPIO.LOW, GPIO.LOW, GPIO.LOW)

    def turn_on_led(self, led):
        """
         open_led:
         打开灯
         ____________
         Parameters
         ----------
         * led : int
             - LED_R  LED_G  LED_B三个选一个
         """
        print('open led')
        self.LED_FLAG[led] = True
        while self.LED_FLAG[led]:
            if led == Car.LED_R:
                GPIO.output(Car.PIN_LED_R, Car.OPEN)
            elif led == Car.LED_G:
                GPIO.output(Car.PIN_LED_G, Car.OPEN)
            else:
                GPIO.output(Car.PIN_LED_B, Car.OPEN)

    def turn_off_led(self, led):
        """
         close_led:
         关闭LED灯光
         ____________
         Parameters
         ----------
         * led : int
             - LED_R  LED_G  LED_B三个选一个
         """
        self.LED_FLAG[led] = False
        if led == Car.LED_R:
            GPIO.output(Car.PIN_LED_R, Car.CLOSE)
        elif led == Car.LED_G:
            GPIO.output(Car.PIN_LED_G, Car.CLOSE)
        else:
            GPIO.output(Car.PIN_LED_B, Car.CLOSE)

    def stop_all_wheels(self ,delay = 0):
        """
        Stop wheel movement
        """
        time.sleep(delay)

        self.__set_motion(GPIO.LOW, GPIO.LOW, GPIO.LOW, GPIO.LOW, 0, 0)

    def stop_completely(self ,delay = 0):
        """
        Completely stop the Car
        """
        time.time(delay)

        self.__pwm_left_speed.stop()
        self.__pwm_right_speed.stop()
        self.__pwm_servo_ultrasonic.stop()
        GPIO.cleanup()

    def run_forward(self, speed=50, duration=0.0):
        """
         Run forward

         Parameters
         ----------
         * speed : int
             - Speed of the motors. Valid range [0, 100]
         * duration : float
             - Duration of the motion.
             (default=0.0 - continue indefinitely until other motions are set)
         """
        self.__set_motion(GPIO.HIGH, GPIO.LOW, GPIO.HIGH, GPIO.LOW,
                         speed, speed, duration)

    def run_reverse(self, speed=10, duration=0.0):
        """
        Run forward

        Parameters
        ----------
        * speed : int
            - Speed of the motors. Valid range [0, 100]
        * duration : float
            - Duration of the motion.
            (default=0.0 - continue indefinitely until other motions are set)

        Raises
        ------
        """
        self.__set_motion(GPIO.LOW, GPIO.HIGH, GPIO.LOW, GPIO.HIGH,
                         speed, speed, duration)

    def turn_left(self, speed=10, duration=0.0):
        """
        Turn left - only right-hand-side wheels run forward

        Parameters
        ----------
        * speed : int
            - Speed of the motors. Valid range [0, 100]
        * duration : float
            - Duration of the motion.
            (default=0.0 - continue indefinitely until other motions are set)

        Raises
        ------
        """
        self.__set_motion(GPIO.LOW, GPIO.LOW, GPIO.HIGH, GPIO.LOW,
                         0, speed, duration)

    def turn_right(self, speed=10, duration=0.0):
        """
        Turn right - only left-hand-side wheels run forward

        Parameters
        ----------
        * speed : int
            - Speed of the motors. Valid range [0, 100]
        * duration : float
            - Duration of the motion.
            (default=0.0 - continue indefinitely until other motions are set)

        Raises
        ------
        """
        self.__set_motion(GPIO.HIGH, GPIO.LOW, GPIO.LOW, GPIO.LOW,
                         speed, 0, duration)

    def spin_left(self, speed=10, duration=0.0):
        """
        Spin to the left in place

        Parameters
        ----------
        * speed : int
            - Speed of the motors. Valid range [0, 100]
        * duration : float
            - Duration of the motion.
            (default=0.0 - continue indefinitely until other motions are set)

        Raises
        ------
        """
        self.__set_motion(GPIO.LOW, GPIO.HIGH, GPIO.HIGH, GPIO.LOW,
                         speed, speed, duration)

    def spin_right(self, speed=10, duration=0.0):
        """
        Spin to the left in place

        Parameters
        ----------
        * speed : int
            - Speed of the motors. Valid range [0, 100]
        * duration : float
            - Duration of the motion.
            (default=0.0 - continue indefinitely until other motions are set)

        Raises
        ------
        """
        self.__set_motion(GPIO.HIGH, GPIO.LOW, GPIO.LOW, GPIO.HIGH,
                         speed, speed, duration)

    def distance_from_obstacle(self ,val = 0):
        """
        Measure the distance between ultrasonic sensor and the obstacle
        that it faces.

        The obstacle should have a relatively smooth surface for this
        to be effective. Distance to fabric or other sound-absorbing
        surfaces is difficult to measure.

        Returns
        -------
        * int
            - Measured in centimeters: valid range is 2cm to 400cm
        """
        # set HIGH at TRIG for 15us to trigger the ultrasonic ping
        print('check distance')
        #产生一个10us的脉冲
        distance = 0
        GPIO.output(Car.PIN_TRIG, GPIO.LOW)
        time.sleep(0.02)
        GPIO.output(Car.PIN_TRIG, GPIO.HIGH)
        time.sleep(0.000015)
        GPIO.output(Car.PIN_TRIG, GPIO.LOW)
        time.sleep(0.00001)

        #等待接受
        if GPIO.input(Car.PIN_ECHO):
            distance = -2
            return distance

        time1, time2 = time.time(), time.time()

        while not GPIO.input(Car.PIN_ECHO):
            time1 = time.time()
            if time1 - time2 > 0.02:
                distance = -3
                break

        if distance == -3:
            return (distance)

        t1 = time.time()
        while GPIO.input(Car.PIN_ECHO):
            time2 = time.time()
            if time2 - t1 > 0.02:
                break

        t2 = time.time()
        distance = ((t2 - t1) * 340 / 2) * 100
        print(distance)
        return str(distance)

    def line_tracking_turn_type(self ,num = 4):
        """
        Indicates the type of turn required given current sensor values
        num = 4,是为了上层调用而设定

        Returns
        -------
        * str
            - one of ['sharp_left_turn', 'sharp_right_turn',
                      'regular_left_turn', 'regular_right_turn',
                      'smooth_left', 'smooth_right',
                      'straight', 'no_line']
        """
        s1_dark = GPIO.input(Car.PIN_TRACK_1) == GPIO.LOW
        s2_dark = GPIO.input(Car.PIN_TRACK_2) == GPIO.LOW
        s3_dark = GPIO.input(Car.PIN_TRACK_3) == GPIO.LOW
        s4_dark = GPIO.input(Car.PIN_TRACK_4) == GPIO.LOW

        if s1_dark and (s3_dark and s4_dark):
            #   1    2    3    4
            # Dark XXXX Dark Dark
            # Dark XXXX Dark Lite
            # Dark XXXX Lite Dark
            # Requires a sharp left turn (line bends at right or acute angle)
            turn = 'sharp_left_turn'
        elif (s1_dark or s2_dark) and s4_dark:
            #   1    2    3    4
            # Dark Dark XXXX Dark
            # Lite Dark XXXX Dark
            # Dark Lite XXXX Dark
            # Requires a sharp right turn (line bends at right or acute angle)
            turn = 'sharp_right_turn'
        elif s1_dark:
            #   1    2    3    4
            # Dark XXXX XXXX XXXX
            # Requires a regular left turn (line bends at obtuse angle)
            turn = 'regular_left_turn'
        elif s4_dark:
            #   1    2    3    4
            # XXXX XXXX XXXX Dark
            # Requires a regular right turn (line bends at obtuse angle)
            turn = 'regular_right_turn'
        elif s2_dark and not s3_dark:
            #   1    2    3    4
            # XXXX Dark Lite XXXX
            # Requires a smooth curve to the left (car veers off to the right)
            turn = 'smooth_left'
        elif not s2_dark and s3_dark:
            #   1    2    3    4
            # XXXX Lite Dark XXXX
            # Requires a smooth curve to the right (car veers off to the left)
            turn = 'smooth_right'
        elif s2_dark and s3_dark:
            #   1    2    3    4
            # XXXX Dark Dark XXXX
            # Requires going straight
            turn = 'straight'
        else:
            #   1    2    3    4
            # Lite Lite Lite Lite
            # Requires maintaining the previous movement
            turn = 'no_line'

        print('Turn type = {}'.format(turn))
        return turn

    def obstacle_status_from_infrared(self ,num = 0):
        """
        Return obstacle status obtained by infrared sensors that
        are situated at the left front and right front of the Car.
        The infrared sensors are located on the lower deck, so they
        have a lower view than the ultrasonic sensor.

        Indicates blockage by obstacle < 20cm away.
        Depending on sensitivity of sensors, the distance of obstacles
        sometimes needs to be as short as 15cm for effective detection

        Returns
        -------
        * str
            - one of ['only_left_blocked', 'only_right_blocked',
                    'blocked', 'clear']
        """
        is_left_clear  = GPIO.input(Car.PIN_AVOID_LEFT_SENSOR)
        is_right_clear = GPIO.input(Car.PIN_AVOID_RIGHT_SENSOR)

        if is_left_clear and is_right_clear:
            status = 'clear'
        elif is_left_clear and not is_right_clear:
            status = 'only_right_blocked'
        elif not is_left_clear and is_right_clear:
            status = 'only_left_blocked'
        else:
            status = 'blocked'
        print('Infrared status = {}'.format(status))
        return status

    def turn_servo_ultrasonic(self, dir='degree', degree=90):
        """
        Turn the servo for ultrasonic sensor

        Parameters
        ----------
        * dir : str
            - one of ['left', 'center', 'right']
            - if dir == 'degree', use degree parameter
        * degree : int
            - the angle to turn, measured in degree [0, 180]
            - if dir is specified other than 'degree', this is ignored
        """
        # 0 degrees :  duty cycle =  2.5% of 20ms
        # 90 degrees:  duty cycle =  7.5% of 20ms
        # 180 degrees: duty cycle = 12.5% of 20ms
        if dir == 'center':
            degree = 90
        elif dir == 'right':
            degree = 0
        elif dir == 'left':
            degree = 180

        for i in range(10):  # do this for multiple times just to make sure
            self.__pwm_front_servo_pos.ChangeDutyCycle(2.5 + 10 * degree/180)
        self.__pwm_front_servo_pos.ChangeDutyCycle(0)
        time.sleep(0.02) # give enough time to settle

    def obstacle_status_from_ultrasound(self, dir='center'):
        """
        Return obstacle status obtained by ultrasonic sensor that is
        situated in the front of the Car. The ultrasonic sensor is
        located in the upper deck so it has a higher view than the
        infrared sensors.

        Parameters
        ----------
        * dir : str
            - set the ultrasonic sensor to face a direction,
            one of ['center', 'left', 'right']. Default is 'center'

        Returns
        -------
        * str
            - 'blocked' if distance <= 20cm
            - 'approaching_obstacle' if distance is (20, 50]
            - 'clear' if distance > 50cm
        """

        self.turn_servo_ultrasonic(dir)
        distance = self.distance_from_obstacle()
        if distance <= 20:
            status = 'blocked'
        elif distance <= 50:
            status = 'approaching_obstacle'
        else:
            status = 'clear'
        print('Ultrasound status = {}'.format(status))
        return status

    def check_left_obstacle_with_sensor(self ,delay = 0):
        """
        利用小车左侧的红外对管传感器检测物体是否存在

        Parameters
        ----------
        * delay ：int
        读取稳定时间

        Returns
        -------
        * bool
            - High : 有障碍
            -Low   : 无障碍
        """
        have_obstacle = GPIO.input(Car.PIN_AVOID_LEFT_SENSOR)
        time.sleep(delay)
        if have_obstacle :
            return str(Car.NO_OBSTACLE)
        else:
            return str(Car.HAVE_OBSTACLE)

    def check_right_obstacle_with_sensor(self ,delay = 0):
        """
        利用小车右侧的红外对管传感器检测物体是否存在

        Parameters
        ----------
        * delay ：int
        读取稳定时间
        -----------
        Returns
        -------
        * bool
            - High : 有障碍
            -Low   : 无障碍
        """
        have_obstacle = GPIO.input(Car.PIN_AVOID_RIGHT_SENSOR)
        time.sleep(delay)

        if have_obstacle:
            return str(Car.NO_OBSTACLE)
        else:
            return str(Car.HAVE_OBSTACLE)

    def servo_front_rotate(self , pos):
        """
        *function:servo_front_roate
        功能：控制超声波的舵机进行旋转
        舵机：SG90 脉冲周期为20ms,脉宽0.5ms-2.5ms对应的角度-90到+90，对应的占空比为2.5%-12.5%
        Parameters
        *pos
        舵机旋转的角度：0 到 180 度
        ----------
        * none
        Returns
        -------
        None
        """
        for i in range(Car.SERVO_TOTAL_STEP):
            self.__pwm_front_servo_pos.ChangeDutyCycle(2.5 + 10 * pos / 180)
            time.sleep(0.02)

        self.__pwm_front_servo_pos.ChangeDutyCycle(0)
        time.sleep(0.02)

    def turn_servo_camera_horizental(self , pos):
        """
        *function:servo_camera_roate
        功能：调整控制相机的舵机进行旋转
        原理：舵机：SG90 脉冲周期为20ms,脉宽0.5ms-2.5ms对应的角度-90到+90，对应的占空比为2.5%-12.5%

        Parameters
        *pos
        舵机旋转的角度：0 到 180 度
        ----------
        Returns
        -------
        * None
        """
        for i in range(Car.SERVO_TOTAL_STEP):
            self.__pwm_left_right_servo_pos.ChangeDutyCycle(2.5 + 10 * pos / 180)
            time.sleep(0.02)

        self.__pwm_left_right_servo_pos.ChangeDutyCycle(0)
        time.sleep(0.02)


    def turn_servo_camera_vertical(self , pos):
        """
        *function:servo_camera_rise_fall
        功能：舵机让相机上升和下降
        舵机：SG90 脉冲周期为20ms,脉宽0.5ms-2.5ms对应的角度-90到+90，对应的占空比为2.5%-12.5%
        Parameters
        *pos
        舵机旋转的角度：0 到 180 度
        ----------
        Returns
        -------
        * None
        """
        for i in range(Car.SERVO_TOTAL_STEP):
            self.__pwm_up_down_servo_pos.ChangeDutyCycle(2.5 + 10 * pos / 180)
            time.sleep(0.02)

        self.__pwm_up_down_servo_pos.ChangeDutyCycle(0)
        time.sleep(0.02)

    @staticmethod  #自动巡游功能
    def demo_cruising():
        """
        Demonstrates a cruising car that avoids obstacles in a room

        * Use infrared sensors and ultrasonic sensor to gauge obstacles
        * Use LED lights to indicate running/turning decisions
        """
        car = Car()
        try:
            while True:
                obstacle_status_from_infrared = car.obstacle_status_from_infrared()
                should_turn = True
                if obstacle_status_from_infrared == 'clear':
                    should_turn = False
                    obstacle_status_from_ultrasound = \
                        car.obstacle_status_from_ultrasound()
                    if obstacle_status_from_ultrasound == 'clear':
                        car.led_light('green')
                        car.run_forward(speed=10)
                    elif obstacle_status_from_ultrasound == 'approaching_obstacle':
                        car.led_light('yellow')
                        car.run_forward(speed=5)
                    else:
                        should_turn = True
                if should_turn:
                    car.run_reverse(duration=0.02)
                    if obstacle_status_from_infrared == 'only_right_blocked':
                        car.led_light('purple')
                        car.spin_left(duration=random.uniform(0.25, 1.0))
                    elif obstacle_status_from_infrared == 'only_left_blocked':
                        car.led_light('cyan')
                        car.spin_right(duration=random.uniform(0.25, 1.0))
                    else:
                        car.led_light('red')
                        car.spin_right(duration=random.uniform(0.25, 1.0))
        except KeyboardInterrupt:
            car.stop_completely()

    @staticmethod  #自动巡线功能
    def demo_line_tracking(speed=50):
        """
        Demonstrates the line tracking mode using the line tracking sensor
        """
        time.sleep(2)
        car = Car()

        try:
            while True:
                turn = car.line_tracking_turn_type()
                if turn == 'straight':
                    car.run_forward(speed=speed)
                elif turn == 'smooth_left':
                    car.turn_left(speed=speed * 0.75)
                elif turn == 'smooth_right':
                    car.turn_right(speed=speed * 0.75)
                elif turn == 'regular_left_turn':
                    car.spin_left(speed=speed * 0.75)
                elif turn == 'regular_right_turn':
                    car.spin_right(speed=speed * 0.75)
                elif turn == 'sharp_left_turn':
                    car.spin_left(speed=speed)
                elif turn == 'sharp_right_turn':
                    car.spin_right(speed=speed)
        except KeyboardInterrupt:
            car.stop_completely()

    @staticmethod  #输出电平，控制小车的灯的颜色
    def demo_led_switch():
        """
        控制灯
        - one of ['red', 'green', 'blue',
          'yellow', 'cyan', 'purple'
          'white', 'off']
        """
        car = Car()
        car.led_light('red')

    @staticmethod  #小车的直行、转动、正方形
    def demo_car_moving():
        """
        运动类型：0 ：直线运动                LINE_MOVE_TYPE = 0
                  1 ：来回运动                LINE_BACK_FORTH_MOVE_TYPE = 1
                  2 : 转弯                    TURN_CORNER_MOVE_TYPE = 2
                  3 ：拐弯                    SPRIN_MOVE_TYPE = 3
                  4 ：正方形                  RECT_MOVE_TYPE = 4
        """
        run_type = 0
        run_type = input("输入运动类型(0:直线，1：来回，2：转弯，3：拐弯，4：正方形)：")
        car = Car()
        if run_type == Car.LINE_MOVE_TYPE:
            car.run_forward(5,10) #按照5的速度，走10s
        elif run_type == Car.LINE_BACK_FORTH_MOVE_TYPE:
            car.run_forward(5,10) #按照5的速度，走10s
            car.run_reverse(5,10) #按照5的速度，原路返回走10s
        elif run_type == Car.TURN_CORNER_MOVE_TYPE:
            car.run_forward(5,10) #按照5的速度，走10s
            car.turn_left(3,4)  #转弯
            car.run_forward(5,10) #按照5的速度，走10s
        elif  run_type == Car.SPRIN_MOVE_TYPE:
            car.run_forward(5,10) #按照5的速度，走10s
            car.spin_left(3,4)    #转弯
            car.run_forward(5,10) #按照5的速度，走10s
        elif run_type == Car.RECT_MOVE_TYPE:
            car.run_forward(10,20)#需要提取保持速度不变
            car.turn_left(4,6)#时间6s，需要修改，确保转90度，每一台设备有微小的差异
            car.run_forward(10,20)
            car.turn_left(4,6)#需要修改时间，确保转90度，每一台设备有微小的差异
            car.run_forward(10,20)
            car.turn_left(4,6)#时间6s，需要修改时间，确保转90度，每一台设备有微小的差异
            car.run_forward(10,20)
            car.turn_left(4,6)#时间6s，需要修改，看转多少需要

    @staticmethod  #小车的直行、转动、正方形
    def demo_sensor():
        """
        传感器类型：0 ：红外对管传感器的使用                  SENSOR_INFRARED_TYPE = 0
                   1 ：黑白传感器的使用               SENSOR_BLACK_WIGHT_TYPE = 1
                  2 : 超声波传感器                 SENSOR_ULTRASONIC_TYPE = 2
        """
        sensor_type = int(input("测试传感器类型 0:红外；1:黑白；2:超声波:"))
        car = Car()
        if sensor_type == Car.SENSOR_INFRARED_TYPE:
            """
            #用手来回挡住传感器，观看传感器的读数变化（在使用传感器前，面向传感器，                              
            调节传感器的旋钮，让右侧的两个灯恰好亮）。当传感器被挡住的时候，左侧的传感器就会亮
            根据传感器遇到障碍物类型可以分为下面四种类型
            one of ['only_left_blocked', 'only_right_blocked','blocked', 'clear']
            """
            while True:
                status = car.obstacle_status_from_infrared()
                print(status)
        elif sensor_type == Car.SENSOR_BLACK_WIGHT_TYPE:
            """
            #黑色的电工胶布一圈                          
            使用过程：把电工胶布贴在A4纸张上或桌子上，让后把黑白传感器在黑色电工胶布上来回移动，观看传感器上灯的亮度变化或输出值的变化
            当遇到黑色就会变亮，根据它可以做一个巡线机器人。根据四个传感器亮的组合可以分为下面几种情况:
            ['sharp_left_turn', 'sharp_right_turn','regular_left_turn', 'regular_right_turn',
            'smooth_left', 'smooth_right','straight', 'no_line']
             """
            while True:
                status = car.line_tracking_turn_type()
                print(status)
        elif sensor_type == Car.SENSOR_ULTRASONIC_TYPE:
            """
            #超声波测距：用双手挡住超声波、并做靠近超声波、远离超声波，来回运动，观看超声波读取值的变化
            """
            while True:
                    dis = car.distance_from_obstacle()  #固定在一个位置查看其变化
                    print(dis)


                    # dis = car.servo_front_rotate(30) #旋转超声波，并进行测距
                    # print(dis)
                    # dis = car.servo_front_rotate(90)
                    # print(dis)
                    # dis = car.servo_front_rotate(120)
                    # print(dis)


"""
@@@@主函数：
#在里面测试本地各种功能
"""

learning_level = 0 # 学习等级 0：初级 设置电平，可以控制灯的开和关
                   # 学习等级 1：控制小车直行、运动、左转等
                   # 学习等级 2：控制小车的传感器
                   # 学习等级 3：控制小车漫游
                   # 学习等级 4：控制小车巡线


def main():
    learning_level = int(input("请输入学习等级（0：灯光、1：运动、2：传感器、3：漫游、4:巡线）："))
    print(learning_level)
    if learning_level == 0:
        Car.demo_led_switch()   #灯光操作例子
    elif learning_level == 1:
        Car.demo_car_moving() #小车运动操作例子
    elif learning_level == 2:
        Car.demo_sensor()  #传感器操作例子
    elif learning_level == 3:
        Car.demo_cruising()  # 利用红外传感器、超声波和小车运动组合做漫游服务例子
    elif learning_level == 4:
        Car.demo_line_tracking() #利用黑白传感器和小车运动做巡线服务的例子

"""
@@@@例子：
#在树莓派上运行各种例子
"""
if __name__ == "__main__":
    main()





    
    





    






      


  
  




