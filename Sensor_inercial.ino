#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

void setup() {
  Serial.begin(115200);
  Wire.begin();

  // Iniciar el MPU6050
  mpu.initialize();
  
  if (mpu.testConnection()) {
    Serial.println("Conexión exitosa con el MPU6050.");
  } else {
    Serial.println("Fallo en la conexión con el MPU6050.");
    while (1); // Detener el programa si el sensor no está conectado
  }
}

void loop() {
  // Leer los valores del acelerómetro y giroscopio
  int16_t ax, ay, az;
  int16_t gx, gy, gz;
  
  mpu.getAcceleration(&ax, &ay, &az);
  mpu.getRotation(&gx, &gy, &gz);
  
  // Convertir los valores del acelerómetro a valores de ángulo
  float ax_f = (float)ax;
  float ay_f = (float)ay;
  float az_f = (float)az;
  
  // Calcular el pitch (ángulo de inclinación)
  float pitch = atan2(ay_f, sqrt(ax_f * ax_f + az_f * az_f)) * 180.0 / PI;
  
  // Calcular el roll (ángulo de balanceo)
  float roll = atan2(-ax_f, sqrt(ay_f * ay_f + az_f * az_f)) * 180.0 / PI;
  
  // Mostrar los resultados
  Serial.print("Pitch: ");
  Serial.print(pitch);
  Serial.print("°  Roll: ");
  Serial.print(roll);
  Serial.println("°");
  
  delay(500); // Actualizar cada 500 ms
}
