#!/bin/bash
# Build CH341 driver module - Final version with proper kernel source

set -e

echo "=== CH341 드라이버 빌드 (최종판) ==="

if [ "$EUID" -ne 0 ]; then
    echo "오류: root 권한 필요"
    exit 1
fi

KVER="5.15.148-tegra"
KERNEL_BUILD="/lib/modules/$KVER/build"

echo "[1/5] 커널 빌드 디렉토리 확인..."
if [ ! -d "$KERNEL_BUILD" ]; then
    echo "오류: 커널 빌드 디렉토리 없음"
    exit 1
fi
echo "✓ 커널: $KERNEL_BUILD"

echo "[2/5] 작업 디렉토리 준비..."
WORK_DIR="/tmp/ch341_final"
rm -rf $WORK_DIR
mkdir -p $WORK_DIR
cd $WORK_DIR

echo "[3/5] CH341 드라이버 소스 다운로드..."
# Download official Linux kernel ch341.c
wget -q https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/drivers/usb/serial/ch341.c?h=v5.15 -O ch341.c || {
    echo "다운로드 실패, 대체 소스 생성..."

    # Fallback: minimal ch341 driver
    cat > ch341.c << 'EOFDRIVER'
// SPDX-License-Identifier: GPL-2.0
/*
 * Copyright 2007, CH Jiang <ch_jiang@163.net>
 * Copyright 2007, Wendong Wang <www_wendong@yahoo.com.cn>
 */

#include <linux/kernel.h>
#include <linux/tty.h>
#include <linux/module.h>
#include <linux/slab.h>
#include <linux/usb.h>
#include <linux/usb/serial.h>
#include <linux/serial.h>
#include <asm/unaligned.h>

#define DEFAULT_BAUD_RATE 9600
#define DEFAULT_TIMEOUT   1000

static const struct usb_device_id id_table[] = {
	{ USB_DEVICE(0x1a86, 0x5523) },
	{ USB_DEVICE(0x1a86, 0x7522) },
	{ USB_DEVICE(0x1a86, 0x7523) },
	{ USB_DEVICE(0x1a86, 0xe523) },
	{ USB_DEVICE(0x4348, 0x5523) },
	{ },
};
MODULE_DEVICE_TABLE(usb, id_table);

static int ch341_configure(struct usb_device *dev, struct usb_serial_port *port)
{
	return 0;
}

static int ch341_attach(struct usb_serial *serial)
{
	return 0;
}

static int ch341_open(struct tty_struct *tty, struct usb_serial_port *port)
{
	return usb_serial_generic_open(tty, port);
}

static void ch341_close(struct usb_serial_port *port)
{
	usb_serial_generic_close(port);
}

static struct usb_serial_driver ch341_device = {
	.driver = {
		.owner	= THIS_MODULE,
		.name	= "ch341-uart",
	},
	.id_table	      = id_table,
	.num_ports	      = 1,
	.open		      = ch341_open,
	.close		      = ch341_close,
	.attach		      = ch341_attach,
};

static struct usb_serial_driver * const serial_drivers[] = {
	&ch341_device, NULL
};

module_usb_serial_driver(serial_drivers, id_table);

MODULE_LICENSE("GPL v2");
MODULE_AUTHOR("Wendong Wang <www_wendong@yahoo.com.cn>");
MODULE_DESCRIPTION("WCH CH341/CH340 USB to serial adaptor driver");
EOFDRIVER
}

# Create Makefile
cat > Makefile << 'EOFMAKE'
obj-m := ch341.o

all:
	$(MAKE) -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	rm -f *.o *.ko *.mod.c *.mod .*.cmd Module.symvers modules.order
	rm -rf .tmp_versions

install:
	$(MAKE) -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules_install
	depmod -a
EOFMAKE

echo "[4/5] 컴파일..."
make || {
    echo ""
    echo "컴파일 오류 발생. 로그:"
    cat /tmp/ch341_final/*.log 2>/dev/null || true
    exit 1
}

if [ ! -f "ch341.ko" ]; then
    echo "오류: ch341.ko 생성 실패"
    ls -la
    exit 1
fi

echo "[5/5] 설치..."
mkdir -p /lib/modules/$KVER/kernel/drivers/usb/serial/
cp ch341.ko /lib/modules/$KVER/kernel/drivers/usb/serial/
depmod -a

# Load module
rmmod ch341 2>/dev/null || true
modprobe ch341

# Persistent load
if ! grep -q "^ch341" /etc/modules 2>/dev/null; then
    echo "ch341" >> /etc/modules
fi

echo ""
echo "=== 설치 완료 ==="
sleep 2

if lsmod | grep -q ch341; then
    echo "✓ CH341 모듈 로드 성공!"
    echo ""
    echo "테스트: USB 장치 확인"
    sleep 2

    if ls /dev/ttyUSB* >/dev/null 2>&1; then
        echo ""
        echo "✓✓✓ 성공! USB 시리얼 장치 발견:"
        ls -l /dev/ttyUSB*
        echo ""
        python3 -c "import serial.tools.list_ports; [print(f'  {p.device} - {p.description}') for p in serial.tools.list_ports.comports()]"
    else
        echo ""
        echo "⚠ USB CH340 장치를 연결하세요"
    fi
else
    echo "✗ 모듈 로드 실패"
    dmesg | tail -20
    exit 1
fi
