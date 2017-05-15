#include <Wire.h>

#define X 0
#define Y 1
#define Z 2

#define SERIAL_BAUD_RATE 115200

/* acc data */

boolean acc_read_first = false;
boolean acc_read = false;
long last_acc_time = 0;
volatile int acc[2]; // updated on falling edge from accel

/* volatile vars used for interrupt */

volatile int rising_0_time, rising_1_time;

/* gyro constants */

#define GYRO_BOOT_TIME 10 // ms
#define GYRO_TO_NORMAL_MODE_TIME 250 // ms

#define I2C_ADDR 0x69

// addresses for registers
// see application note p.6 for details
#define CTRL_REG1  0x20
#define CTRL_REG2  0x21
#define CTRL_REG3  0x22
#define CTRL_REG4  0x23
#define CTRL_REG5  0x24
#define STATUS_REG 0x27
#define OUT_X_L    0x28
#define OUT_X_H    0x29
#define OUT_Y_L    0x2A
#define OUT_Y_H    0x2B
#define OUT_Z_L    0x2C
#define OUT_Z_H    0x2D

/* gyro data */

long last_gyro_time;

int16_t gyro[3];
uint8_t* gyro_bytes;

/* pins */

const int pin_led = 13;

/* vars */

byte b, i;

void setup(){
    /* setup and reset led pin */

    pinMode(pin_led, OUTPUT);
    digitalWrite(pin_led, LOW);

    /* interrupts */

    // on interrupt 0 (pin 2), trigger rising_0 on RISING edge
    attachInterrupt(0, rising_0, RISING);

    // on interrupt 1 (pin 3), trigger rising_0 on RISING edge
    attachInterrupt(1, rising_1, RISING);

    /* serial */

    Serial.begin(SERIAL_BAUD_RATE); // init serial over usb

    /* i2c */

    Wire.begin(); // init arduino i2c
    delay(GYRO_BOOT_TIME); // wait for gyro to start

    /*
        note:
        b = (b & ~x) | y;
        changes the bits set to 1 in x to corresponding bit in y
    */

    // enable low pass filter
    // application note 4.1 p.13
    b = i2c_get(CTRL_REG5);
    b = (b & ~0b00010010) | 0b00000010; // - - - HPen - - OutSel1 -
    i2c_set(CTRL_REG5, b);

    // config low pass filter and output data rate (ODR)
    // application note 4.2 p.14
    // ODR: 100 Hz
    // LPF1: 32 Hz
    // LPF2: 25 Hz
    b = i2c_get(CTRL_REG1);
    b = (b & ~0b11110000) | 0b00110000; // DR1 DR0 BW1 BW0 - - - -
    i2c_set(CTRL_REG1, b);

    // config full scale to 2000dps
    b = i2c_get(CTRL_REG4);
    b = (b & ~0b00110000) | 0b00110000; // - - FS1 FS0 - - - -
    i2c_set(CTRL_REG4, b);

    // go from sleeping mode to normal mode
    b = i2c_get(CTRL_REG1);
    b |= 0b00001111; // set to 1: PD, Zen, Yen, Xen
    i2c_set(CTRL_REG1, b);

    // wait for the gyro to switch to normal mode
    delay(GYRO_TO_NORMAL_MODE_TIME);

    /*
       Small trick for not having to convert the incoming bytes manually to
       ints. The gyro array holds the 3 (x, y, z) integer (2 byte signed)
       values, a total of 6 bytes. The gyro sends each of the ints one after
       another split up into bytes. They are sent as little endian (LSB first),
       matching the Arduino CPU which is also little endian. Now, by simply
       seeing the gyro array as a byte array, we can feed the data straight into
       the gyro array and get it right.
    */

    gyro_bytes = (byte*)gyro;

    /* turn on led, indicating that we are now looping */

    digitalWrite(pin_led, HIGH);
}

void loop(){
    // see application note 3.1.1 p.10 for details about reading STATUS_REG
    b = i2c_get(STATUS_REG);
    if(b & 1<<3){ // if gyro data is ready
        long now = micros();
        long dt = now - last_gyro_time;
        last_gyro_time = now;

        if(b & 1<<7){ // if skipped a gyro reading
            // send warning: w skipped gyro read
            Serial.println("w\tskipped gyro read");
        }

        // fetch the gyro data
        // see application note 3.1.1 p.10 for details
        for(i=0; i<6; i++){
            gyro_bytes[i] = i2c_get(OUT_X_L+i);
        }

        // send gyro data to serial
        // output example: gtxyz 10023 -500 674 23
        Serial.print("gtxyz\t");
        Serial.print(dt); // microseconds, should be around 10000us <=> 100Hz
        Serial.print("\t");
        Serial.print(gyro[X]);
        Serial.print("\t");
        Serial.print(gyro[Y]);
        Serial.print("\t");
        Serial.println(gyro[Z]);
    }

    if(acc_read){ // acc_read is set by the interrupt functions
        acc_read = false;

        long now = micros();
        long dt = now - last_acc_time;
        last_acc_time = now;

        // send acc data to serial
        // output example: atxy 9983 4678 5121
        Serial.print("atxy\t");
        Serial.print(dt); // microseconds, should be around 10000us <=> 100Hz
        Serial.print("\t");
        Serial.print(acc[X]);
        Serial.print("\t");
        Serial.println(acc[Y]);
    }
}

/* i2c helper functions */

byte i2c_get(byte reg){
    Wire.beginTransmission(I2C_ADDR);
    Wire.write(reg);
    Wire.endTransmission();
    Wire.requestFrom(I2C_ADDR, 1);
    return Wire.read();
}

void i2c_set(byte reg, byte b){
    Wire.beginTransmission(I2C_ADDR);
    Wire.write(reg);
    Wire.write(b);
    Wire.endTransmission();
}

/* interrupt functions */

// interrupt 0 on pin 2 (y accel)
void rising_0(){
    attachInterrupt(0, falling_0, FALLING);
    rising_0_time = micros();
}

// interrupt 1 on pin 3 (x accel)
void rising_1(){
    attachInterrupt(1, falling_1, FALLING);
    rising_1_time = micros();
}

// interrupt 0 on pin 2 (y accel)
void falling_0(){
    attachInterrupt(0, rising_0, RISING);
    acc[Y] = micros() - rising_0_time;

    if(acc_read_first){
        acc_read_first = false;
        acc_read = true;
    }else{
        acc_read_first = true;
    }
}

// interrupt 1 on pin 3 (x accel)
void falling_1(){
    attachInterrupt(1, rising_1, RISING);
    acc[X] = micros() - rising_1_time;

    if(acc_read_first){
        acc_read_first = false;
        acc_read = true;
    }else{
        acc_read_first = true;
    }
}
