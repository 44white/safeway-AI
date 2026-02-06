#include <Wire.h>
#include "DRV2605.h"

DRV2605 drv;

void setup() {
  Serial.begin(9600);
  Serial.println("DRV test");
  drv.begin();

  drv.setMode(DRV2605_MODE_INTTRIG); 
  drv.selectLibrary(1);
  drv.setWaveform(0, 84);  
  drv.setWaveform(1, 1);  
  drv.setWaveform(2, 0);  
}

void loop() {
    drv.go();
    delay(1000);
}
