import RPi.GPIO as GPIO
import time
import os
import signal
import sys

rpm = 0
t = time.time()
t1 = 1
t2 = 0

def startGetSpeed(gpioPin):
    GPIO.add_event_detect(gpioPin, GPIO.FALLING, speedcallback)

def stopGetSpeed(gpioPin):
    GPIO.remove_event_detect(gpioPin)

def speedcallback(pin):
    global t, rpm
    PULSE = 2
    dt = time.time() - t
    if dt < 0.005: return # Reject spuriously short pulses

    freq = 1 / dt
    rpm = (freq / PULSE) * 60
    t = time.time()

def speedcallback2(pin):
    global t1, t2, rpm
    PULSE = 2
    if t2 != 0:
        t1 = time.time() - t2
        t2 = 0
    else:
        t2 = time.time()
    rpm = round(60/(t1*2))

# Get CPU's temperature
def getCpuTemperature():
    # f = open('/sys/class/thermal/thermal_zone0/temp')
    # return int(f.read())/1000.0
    res = os.popen('vcgencmd measure_temp').readline()
    temp =(res.replace("temp=","").replace("'C\n",""))
    # print("temp is {0}".format(temp)) # Uncomment for testing
    return temp

def handleFanSpeed(temp, minTemp, maxTemp, fanLow, fanHigh, fanMax):
    # temp = float(getCpuTemperature())
    # Turn off the fan if temperature is below MIN_TEMP
    if temp < minTemp:
        # print("Fan OFF")
        return 0
    # Set fan speed to MAXIMUM if the temperature is above MAX_TEMP
    elif temp > maxTemp:
        # print("Fan MAX")
        return fanMax
    # Caculate dynamic fan speed
    else:
        step = (fanHigh - fanLow)/(maxTemp - minTemp)
        temp -= minTemp
        # print(f'Calculated fan power in %d' % (fanLow + (round(temp) * step)))
        return fanLow + ( round(temp) * step )

def main():
    global t, rpm, pwm
    pwmPin = 19    # BCM pin used to drive PWM fan
    fgPin = 17     # Tachometer Pin
    pwrFreq = 250  # in Khz (was 1000 from example)
    waitTime = 1   # secconds

    minTemp = 50
    maxTemp = 100
    fanLow = 10
    fanHigh = 100
    fanMax = 100

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pwmPin, GPIO.OUT)
        GPIO.setup(fgPin, GPIO.IN)
        pwm = GPIO.PWM(pwmPin, pwrFreq)
        # start fan disabled
        pwm.start(0)
        # Start listening for thachometer data
        GPIO.add_event_detect(fgPin, GPIO.FALLING, speedcallback2)

        # counter to delay changes for fun speed
        count = 0
        while True:
            temp = float(getCpuTemperature())
            speed = handleFanSpeed(temp, minTemp, maxTemp, fanLow, fanHigh, fanMax)

            if count > 0:
                pwm.ChangeDutyCycle(speed)
                count = 0

            print(f"\rFan power: {round(speed,1)}% | Fun speed: {rpm} RPM | CPU Temp: {temp} C", end="")

            count = count+1
            rpm = 0
            time.sleep(waitTime)

    except KeyboardInterrupt as e:
        pwm.stop()
        GPIO.remove_event_detect(fgPin)
        GPIO.cleanup()
        exit()


if __name__ == "__main__":
    main()
