# adaptado de https://github.com/peterhinch/micropython-samples/tree/7379c9085a324312a617792edb46816066348c51/DS3231

import utime
import machine
DS3231_I2C_ADDR = 104py

def bcd2dec(bcd):
    return (((bcd & 0xf0) >> 4) * 10 + (bcd & 0x0f))

def dec2bcd(dec):
    tens, units = divmod(dec, 10)
    return (tens << 4) + units

def get_time(i2c, ):
    data = bytearray(7)
    i2c.readfrom_mem_into(DS3231_I2C_ADDR, 0, data)
    ss = bcd2dec(data[0])
    mm = bcd2dec(data[1])
    if data[2] & 0x40:
        hh = bcd2dec(data[2] & 0x1f)
        if data[2] & 0x20:
            hh += 12
    else:
        hh = bcd2dec(data[2])
    wday = data[3]
    DD = bcd2dec(data[4])
    MM = bcd2dec(data[5] & 0x1f)
    YY = bcd2dec(data[6]) +2000
    return YY, MM, DD, wday, hh, mm, ss, 0

def set_time( i2c, tup_time = None ):
    if tup_time == None:
        rtc = machine.RTC()
        tup_time = rtc.datetime()
    
    byte_time = bytearray(7)
    for i, t in enumerate(reversed(tup_time[:-1])):
        if i == 6:
            byte_time[i] = dec2bcd(t-2000)
        else:
            byte_time[i] = dec2bcd(t)

    i2c.writeto_mem(DS3231_I2C_ADDR, 0, byte_time)31