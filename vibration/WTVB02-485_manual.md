# WTVB02-485 Vibration Sensor — Communication Protocol Reference

> Source: WTVB02-485 Data Sheet & User Manual V250806, wit-motion.com  
> Protocol: **Modbus RTU** over RS-485  
> Default baud rate: **9600 bps**  
> Default Modbus address: **0x50**  
> Data format: **Hexadecimal** (not ASCII)

---

## 1. Read Register (Function Code 0x03)

### Command Frame

| Field | Description |
|-------|-------------|
| `ID` | Modbus address (default: `0x50`) |
| `0x03` | Function code (Read) |
| `ADDRH[15:8]` | Register address high byte |
| `ADDRL[7:0]` | Register address low byte |
| `LENH[3:08 PM]` | Read length high byte |
| `LENL[7:0]` | Read length low byte |
| `CRCH[15:8]` | CRC high byte |
| `CRCL[7:0]` | CRC low byte |

### Response Frame

| Field | Description |
|-------|-------------|
| `ID` | Modbus address |
| `0x03` | Function code |
| `LEN[7:0]` | Byte count |
| `DATA1H[15:8]` | First data high byte |
| `DATA1L[7:0]` | First data low byte |
| `...` | Additional data bytes |
| `DATAnH` | Last data high byte |
| `DATAnL` | Last data low byte |
| `CRCH[15:8]` | CRC high byte |
| `CRCL[7:0]` | CRC low byte |

---

## 2. Write Register (Function Code 0x06)

### Command Frame

| Field | Description |
|-------|-------------|
| `ID` | Modbus address |
| `0x06` | Function code (Write) |
| `ADDRH[15:8]` | Register address high byte |
| `ADDRL[7:0]` | Register address low byte |
| `DATAH[15:8]` | Write data high byte |
| `DATAL[7:0]` | Write data low byte |
| `CRCH[15:8]` | CRC high byte |
| `CRCL[7:0]` | CRC low byte |

### ⚠️ Write Operation: 3-Step Procedure

Write operations **must** follow this sequence:

**Step 1 — Unlock** (valid for 10 seconds):
```
Send: 50 06 00 69 B5 88 22 A1
```

**Step 2 — Send the write command** (within 10 seconds of unlock)

**Step 3 — Save**:
```
Send: 50 06 00 00 00 00 84 4B
```

---

## 3. Register Address Table

| Address | Symbol | Description |
|---------|--------|-------------|
| `0x00` | SAVE | Save / Restart / Restore to Factory |
| `0x04` | BAUD | Serial port baud rate |
| `0x1A` | IICADDR | Device address (Modbus / I2C) |
| `0x30` | YYMM | Month, Year (on-chip time) |
| `0x31` | DDHH | Day, Hour |
| `0x32` | MMSS | Minutes, Seconds |
| `0x33` | MS | Milliseconds |
| `0x34` | AX | X-axis acceleration |
| `0x35` | AY | Y-axis acceleration |
| `0x36` | AZ | Z-axis acceleration |
| `0x3A` | VX | X-axis vibration speed |
| `0x3B` | VY | Y-axis vibration speed |
| `0x3C` | VZ | Z-axis vibration speed |
| `0x40` | TEMP | Chip temperature |
| `0x41` | DX | X-axis vibration displacement |
| `0x42` | DY | Y-axis vibration displacement |
| `0x43` | DZ | Z-axis vibration displacement |
| `0x44` | HZX | X-axis vibration frequency |
| `0x45` | HZY | Y-axis vibration frequency |
| `0x46` | HZZ | Z-axis vibration frequency |

---

## 4. Register Descriptions

### 4.1 SAVE — Save / Reboot / Factory Reset
- **Address:** `0x00`
- **R/W:** R/W
- **Default:** `0x0000`

| Value | Action |
|-------|--------|
| `0x0000` | Save |
| `0x00FF` | Reboot |
| `0x0001` | Factory Reset |

**Example — Reboot:**
```
Send (unlock): 50 06 00 69 B5 88 22 A1
Return:        50 06 00 69 B5 88 22 A1
Send (reboot): 50 06 00 00 00 FF C4 0B
Return:        50 06 00 00 00 FF C4 0B
```

---

### 4.2 BAUD — Serial Port Baud Rate
- **Address:** `0x04`
- **R/W:** R/W
- **Default:** `0x0002` (9600 bps)

| Value | Baud Rate |
|-------|-----------|
| `0x01` | 4800 bps |
| `0x02` | 9600 bps |
| `0x03` | 19200 bps |
| `0x04` | 38400 bps |
| `0x05` | 57600 bps |
| `0x06` | 115200 bps |
| `0x07` | 230400 bps |

**Example — Set baud to 115200:**
```
Send (unlock): 50 06 00 69 B5 88 22 A1
Send (write):  50 06 00 04 00 06 45 88
Send (save):   50 06 00 00 00 00 84 4B
Return:        50 06 00 00 00 00 84 4B
```

---

### 4.3 IICADDR — Device Address
- **Address:** `0x1A`
- **R/W:** R/W
- **Default:** `0x0050`
- **Range:** `0x01` ~ `0x7F`

**Example — Set address to 0x02:**
```
Send (unlock):  50 06 00 69 B5 88 22 A1
Send (write):   50 06 00 1A 00 02 24 4D
Send to new ID: 02 06 00 69 B5 88 2F 13
Send (save):    02 06 00 00 00 00 89 F9
```

---

### 4.4 AX ~ AZ — Acceleration (Read Only)
- **Address:** `0x34` ~ `0x36`
- **R/W:** R (read only)

**Conversion formula:**
```
Acceleration (m/s²) = raw_value / 32768 * 16 * 9.8
```

**Raw value assembly:**
```c
AX[15:0] = ((short)AXH << 8) | AXL;
AY[15:0] = ((short)AYH << 8) | AYL;
AZ[15:0] = ((short)AZH << 8) | AZL;
```

**Example — Read 3-axis acceleration:**
```
Send:   50 03 00 34 00 03 49 84
Return: 50 03 06 AXH AXL AYH AYL AZH AZL CRCH CRCL
```

---

### 4.5 VX ~ VZ — Vibration Speed (Read Only)
- **Address:** `0x3A` ~ `0x3C`
- **R/W:** R (read only)
- **Unit:** mm/s

**Raw value assembly:**
```c
VX[15:0] = (((short)VXH << 8) | VXL);
VY[15:0] = (((short)VYH << 8) | VYL);
VZ[15:0] = (((short)VZH << 8) | VZL);
```

**Example — Read 3-axis vibration speed:**
```
Send:   50 03 00 3A 00 03 28 47
Return: 50 03 06 VXH VXL VYH VYL VZH VZL CRCH CRCL
```

---

### 4.6 TEMP — Chip Temperature (Read Only)
- **Address:** `0x40`
- **R/W:** R (read only)

**Conversion formula:**
```
Temperature (°C) = raw_value / 100
```

**Raw value assembly:**
```c
TEMP[15:0] = (((short)TEMPH << 8) | TEMPL);
```

**Example:**
```
Send:   50 03 00 40 00 01 88 5F
Return: 50 03 02 TEMPH TEMPL CRCH CRCL
```

---

### 4.7 DX ~ DZ — Vibration Displacement (Read Only)
- **Address:** `0x41` ~ `0x43`
- **R/W:** R (read only)
- **Unit:** μm

**Raw value assembly:**
```c
DX[15:0] = (((short)DXH << 8) | DXL);
DY[15:0] = (((short)DYH << 8) | DYL);
DZ[15:0] = (((short)DZH << 8) | DZL);
```

**Example — Read triaxial displacement:**
```
Send:   50 03 00 41 00 03 58 5E
Return: 50 03 06 DXH DXL DYH DYL DZH DZL CRCH CRCL
```

---

### 4.8 HZX ~ HZZ — Vibration Frequency (Read Only)
- **Address:** `0x44` ~ `0x46`
- **R/W:** R (read only)
- **Unit:** Hz

**Conversion formula:**
```
Frequency (Hz) = raw_value / 10
```

**Raw value assembly:**
```c
HZX[15:0] = (((short)HZXH << 8) | HZXL) / 10;
HZY[15:0] = (((short)HZYH << 8) | HZYL) / 10;
HZZ[15:0] = (((short)HZZH << 8) | HZZL) / 10;
```

**Example — Read 3-axis vibration frequency:**
```
Send:   50 03 00 44 00 03 48 5F
Return: 50 03 06 HZXH HZXL HZYH HZYL HZZH HZZL CRCH CRCL
```

---

## 5. Typical Read Patterns

### Read All Sensor Data in One Request

You can read multiple consecutive registers in a single Modbus request.

| Data Group | Start Addr | Count | Covers |
|-----------|-----------|-------|--------|
| Acceleration only | `0x34` | 3 | AX, AY, AZ |
| Vibration speed only | `0x3A` | 3 | VX, VY, VZ |
| Displacement only | `0x41` | 3 | DX, DY, DZ |
| Frequency only | `0x44` | 3 | HZX, HZY, HZZ |
| Accel + Speed (gap at 0x37~0x39) | — | — | Read separately |
| Temp + Displacement + Frequency | `0x40` | 7 | TEMP, DX~DZ, HZX~HZZ |

> **Note:** Registers `0x37~0x39` and `0x3D~0x3F` are reserved. When reading across gaps, split into separate requests.

---

## 6. CRC Calculation

Uses standard **Modbus CRC-16** (polynomial `0x8005`, initial value `0xFFFF`).

```python
def modbus_crc(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return bytes([crc & 0xFF, (crc >> 8) & 0xFF])  # Little-endian (LSB first)
```

> CRC is appended **LSB first** (low byte, then high byte) in Modbus RTU.
