#include <Servo.h>

Servo esc;  
const int escPin = 9;  // Pin donde está conectado el ESC

const int minThrottle = 1000;  // Señal mínima en microsegundos
const int maxThrottle = 2000;  // Señal máxima en microsegundos
const int slowSpeed = 1200;  // Ajustar si es necesario

void setup() {
  Serial.begin(115200);
  esc.attach(escPin);
  
  Serial.println("Calibrando ESC...");
  
  // Proceso de calibración (Enviar máxima señal y luego mínima)
  esc.writeMicroseconds(minThrottle);
  delay(3000);
  esc.writeMicroseconds(minThrottle);
  delay(3000);
  
  Serial.println("ESC calibrado. Iniciando motor lentamente...");
}

void loop() {
  esc.writeMicroseconds(slowSpeed);  // Mantener el motor girando lentamente
  delay(100);
}
