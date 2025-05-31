#include <SPI.h>
#include "Adafruit_GFX.h"
#include "Adafruit_HX8357.h"    //TFT Screen
#include <HCSR04.h>             //Dist Sensor
#include "Adafruit_STMPE610.h"  //Touch IC

static const unsigned char PROGMEM image_download_bits[] = {0x01,0xf0,0x00,0x07,0xfc,0x00,0x1e,0x0f,0x00,0x39,0xf3,0x80,0x77,0xfd,0xc0,0xef,0x1e,0xe0,0x5c,0xe7,0x40,0x3b,0xfb,0x80,0x17,0x1d,0x00,0x0e,0xee,0x00,0x05,0xf4,0x00,0x03,0xb8,0x00,0x01,0x50,0x00,0x00,0xe0,0x00,0x00,0x40,0x00,0x00,0x00,0x00};

static const unsigned char PROGMEM image_download_1_bits[] = {0x21,0xf0,0x00,0x16,0x0c,0x00,0x08,0x03,0x00,0x25,0xf0,0x80,0x42,0x0c,0x40,0x89,0x02,0x20,0x10,0xa1,0x00,0x23,0x58,0x80,0x04,0x24,0x00,0x08,0x52,0x00,0x01,0xa8,0x00,0x02,0x04,0x00,0x00,0x42,0x00,0x00,0xa1,0x00,0x00,0x40,0x80,0x00,0x00,0x00};


// TFT
#define TFT_CS 9
#define TFT_DC 12
#define TFT_RST -1 // RST can be set to -1 if you tie it to Arduino's reset

// Touch Sensor
#define STMPE_CS 5

// My Defines and Variables
#define UFI 6
#define ABI 10

// Dist Sensor
byte triggerPin = 3;
byte echoPin = 4;

Adafruit_HX8357 tft = Adafruit_HX8357(TFT_CS, TFT_DC, TFT_RST);
Adafruit_STMPE610 touch = Adafruit_STMPE610(STMPE_CS);

void setup() {
  delay(2000);
  Serial.begin(9600);
  pinMode(UFI, OUTPUT);
  pinMode(ABI, OUTPUT);
  pinMode(STMPE_CS, OUTPUT);
  HCSR04.begin(triggerPin, echoPin);
  
  tft.begin();
  tft.setRotation(1);
  tft.fillScreen(HX8357_RED);
  tft.fillScreen(HX8357_GREEN);
  tft.fillScreen(HX8357_BLUE);
  tft.fillScreen(HX8357_WHITE);
  tft.fillScreen(HX8357_BLACK);
  tft.setCursor(0, 0);
  tft.setTextColor(HX8357_WHITE);  tft.setTextSize(1);
  tft.println("Hello World!");
  draw();

  if (! touch.begin()) {
    Serial.println("STMPE not found!");
    while(1);
  }
  Serial.println("Waiting for touch sense");
  
}

void loop() {
  uint16_t x, y;
  uint8_t z;
  double* distances = HCSR04.measureDistanceCm();
  while (touch.touched()) {
    // read x & y & z;
    while (! touch.bufferEmpty()) {
      Serial.print(touch.bufferSize());
      touch.readData(&x, &y, &z);
      Serial.print("->("); 
      Serial.print(x); Serial.print(", "); 
      Serial.print(y); Serial.print(", "); 
      Serial.print(z);
      Serial.println(")");

      if(y > 2200 && y < 3800){
        digitalWrite(UFI, LOW);
      }
      else{
        digitalWrite(UFI, HIGH);
      }
      
      if(y > 100 && y < 1900){
        digitalWrite(ABI, LOW);
      }
      else{
        digitalWrite(ABI, HIGH);
      }
    }
    touch.writeRegister8(STMPE_INT_STA, 0xFF); // reset all ints, in this example unneeded depending in use
  }
  
  tft.setCursor(0, 0);
  tft.setTextColor(HX8357_WHITE, HX8357_BLACK);
  tft.print("                   ");
  tft.setTextColor(HX8357_WHITE);
  tft.setCursor(0, 0);
  tft.print((distances[0]));
  tft.print(" cm");
  
  Serial.print("1: ");
  Serial.print(distances[0]);
  Serial.println(" cm");
  delay(50);
  digitalWrite(UFI, HIGH);
  digitalWrite(ABI, HIGH);

}

void draw(void) {

    tft.fillRect(312, 119, 111, 61, 0x554A);

    tft.fillRect(50, 120, 111, 61, 0x554A);

    tft.setTextColor(0xFFFF);
    tft.setTextSize(2);
    tft.setTextWrap(false);
    tft.setCursor(67, 162);
    tft.print("ABI");

    tft.setCursor(327, 159);
    tft.print("UFI");

    tft.drawLine(240, 0, 240, 320, 0xFFFF);

    tft.drawBitmap(424.5, 22, image_download_bits, 19, 16, 0xFFFF);

    tft.drawBitmap(358.5, 21, image_download_1_bits, 19, 16, 0xFFFF);
}
