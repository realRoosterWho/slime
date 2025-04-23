import time
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

print("准备初始化 OLED...")
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)
print("初始化完成，开始发送数据...")

for i in range(100):
    device.clear()
    device.show()
    time.sleep(1)

print("完成")
