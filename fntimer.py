from machine import Pin, I2C, RTC 
from time import sleep
from bme280 import BME280
from time import sleep
import max7219
from machine import Pin, SoftSPI
import network
import ntptime
import time

def config():
    i2c = I2C(0, scl=Pin(19, Pin.OPEN_DRAIN, Pin.PULL_UP),
                 sda=Pin(18, Pin.OPEN_DRAIN, Pin.PULL_UP),
                 freq=100000)
    
    print('I2C:', i2c.scan())
    bme = BME280(i2c=i2c)
    return i2c, bme

i2c, bme = config()
rtc = RTC()
ID = 'ESP32'

lim = 15
t = 3
l = 16

spi3 = SoftSPI(baudrate=10000000, polarity=1, phase=0, sck=Pin(27), mosi=Pin(12), miso=Pin(36))
spi2 = SoftSPI(baudrate=10000000, polarity=1, phase=0, sck=Pin(2), mosi=Pin(5), miso=Pin(36))
spi = SoftSPI(baudrate=10000000, polarity=1, phase=0, sck=Pin(21), mosi=Pin(23), miso=Pin(36))

ss3 = Pin(14, Pin.OUT)
ss2 = Pin(4, Pin.OUT)
ss = Pin(22, Pin.OUT)

display = max7219.Matrix8x8(spi, ss, l)
display2 = max7219.Matrix8x8(spi2, ss2, l)
display3 = max7219.Matrix8x8(spi3, ss3, l)

B1 = Pin(34, Pin.IN, Pin.PULL_UP)
B2 = Pin(35, Pin.IN, Pin.PULL_UP)
B3 = Pin(32, Pin.IN, Pin.PULL_UP)
B4 = Pin(33, Pin.IN, Pin.PULL_UP)

modo_reloj_activo = False

def reloj_callback(pin):
    global modo_reloj_activo
    modo_reloj_activo = not modo_reloj_activo
    print("Modo reloj activado" if modo_reloj_activo else "Modo reloj desactivado")

B4.irq(trigger=Pin.IRQ_FALLING, handler=reloj_callback)

def conectar():
    red = "TP-Link_0C7D"
    contraseña = "86497640"
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(red, contraseña)
    while not wlan.isconnected():
        time.sleep(1)
    print("Conexión Wi-Fi establecida")

conectar()
try:
    ntptime.settime()
    print("Hora sincronizada")
except Exception as e:
    print("Error al sincronizar la hora:", e)
# print("ciclo")
def reloj():
    utc = time.localtime()
    tm = time.localtime(time.mktime(utc) - (6 * 3600))
    hora2 = "{:02}:{:02}:{:02}".format(tm[3], tm[4], tm[5])
    display.fill(0)
    display2.fill(0)
    display3.fill(0)
    display3.large_text(hora2, 0, 1, t)
    display2.large_text(hora2, 0, -7, t)
    display.large_text(hora2, 0, -15, t)
    display.show()
    display2.show()
    display3.show()
    return hora2

def scroll(text):
    global xg
    text_width = len(text) * 8
    if xg < -text_width:
        xg = 32
    print("xg", xg)
    display.fill(0)
    display.text(text, xg, 0, 1)
    display.show()
    xg -= 30
    sleep(0.08)

def display_negativo(minutos, segundos):
    global xg
    display.fill(0)
    display2.fill(0)
    display3.fill(0)
    texto = f"-{abs(minutos):02}:{abs(segundos):02}"
    msg = "Instituto de Ciencias de la Atmosfera y Cambio Climatico, UNAM"
    display3.large_text(texto, 0, 1, 2)
    display2.large_text(texto, 0, -7, 2)
    display.large_text(texto, 0, -15, 2)
    display.show()
    display2.show()
    display3.show()
    scroll(msg)

def display_print(minutos, segundos, counter):
    if minutos < 0 or (minutos == 0 and segundos > 0 and counter < 0):
        display_negativo(minutos, segundos)
    else:
        display.fill(0)
        display2.fill(0)
        display3.fill(0)
        texto = f"{minutos:02}:{segundos:02}"
        display3.large_text(texto, 8, 1, t)
        display2.large_text(texto, 8, -7, t)
        display.large_text(texto, 8, -15, t)
        display.show()
        display2.show()
        display3.show()

def display_print_start():
    display.fill(0)
    display2.fill(0)
    display3.fill(0)
    display3.large_text("START", 0, 1, t)
    display2.large_text("START", 0, -7, t)
    display.large_text("START", 0, -15, t)
    display.show()
    display2.show()
    display3.show()

def display_print_stop():
    display.fill(0)
    display2.fill(0)
    display3.fill(0)
    display3.large_text("STOP", 0, 1, t)
    display2.large_text("STOP", 0, -7, t)
    display.large_text("STOP", 0, -15, t)
    display.show()
    display2.show()
    display3.show()

def obtener_tiempo(counter):
    if counter >= 0:
        return divmod(counter, 60)
    else:
        abs_counter = abs(counter)
        minutos = -(abs_counter // 60)
        segundos = abs_counter % 60
        if abs_counter < 60:
            minutos = 0
        return minutos, segundos

counter = lim * 60
xg = 16
hora=reloj()
sleep(5)
while True:
    print(hora)
    if modo_reloj_activo:
       hora= reloj()
    else:
        minutos, segundos = obtener_tiempo(counter)
        display_print(minutos, segundos, counter)

        if B2.value() == 0:
            lim += 1
            counter = lim * 60

        if B1.value() == 0:
            lim -= 1
            counter = lim * 60

        if B3.value() == 0:
            display_print_start()
            print("START")
            sleep(1)
            original_counter = lim * 60
            while counter >= -3600:
                start = time.ticks_ms()

                minutos, segundos = obtener_tiempo(counter)
                display_print(minutos, segundos, counter)

                counter -= 1
                delta = time.ticks_diff(time.ticks_ms(), start)
                sleep(max(0, 1.0 - delta / 1000))

                if B3.value() == 0:
                    counter = original_counter
                    break

            for _ in range(3):
                display_print_stop()
                print("STOP")
                sleep(0.5)
                display.fill(0)
                display2.fill(0)
                display3.fill(0)
                display.show()
                display2.show()
                display3.show()
                sleep(0.5)

    date = rtc.datetime()
    date_str = '{:04d}-{:02d}-{:02d}_{:02d}:{:02d}:{:02d}'.format(*date[:6])

    #temp, pres, hum = bme.read_compensated_data()
    #temp /= 100
    #pres /= 25600
    #hum /= 1024

    #data_str = '{},{:.2f},{:.2f},{:.2f},{}'.format(date_str, temp, hum, pres, ID)


    sleep(2)