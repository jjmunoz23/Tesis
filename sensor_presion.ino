#include <Q2HX711.h>

// Pines para el sensor de presión
const byte pin_Datos = A2; // OUT del módulo HX711
const byte pin_Reloj = A3; // SCK del módulo HX711
Q2HX711 hx711(pin_Datos, pin_Reloj);

// Valores crudos de referencia para la calibración
const uint32_t valor_0cm = 8398375;
const uint32_t valor_8cm = 9289384;

void setup() {
  Serial.begin(115200);
  Serial.println("Iniciando lectura y calibración del sensor HX711...");
}

void loop() {
  // Leer el valor crudo del sensor
  uint32_t valorSensor = hx711.read();

  // Calcular la distancia en cm mediante interpolación lineal
  float distancia = calcularDistancia(valorSensor);

  // Mostrar el valor crudo y la distancia calibrada
  Serial.print("Valor crudo del sensor: ");
  Serial.println(valorSensor);
  Serial.print("Distancia (cm): ");
  Serial.println(distancia, 2); // Mostrar con dos decimales

  delay(500); // Esperar 500 ms antes de la siguiente lectura
}

float calcularDistancia(uint32_t valorSensor) {
  // Interpolación lineal entre los valores de referencia
  float pendiente = (8.0 - 0.0) / (float)(valor_8cm - valor_0cm);
  float intercepto = 0.0 - pendiente * valor_0cm;

  // Aplicar la fórmula para obtener la distancia
  return pendiente * valorSensor + intercepto;
}
