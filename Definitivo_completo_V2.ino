#include <Servo.h>
#include <Q2HX711.h>  // Librería para el sensor de presión
#include <Wire.h>
#include <MPU6050.h>

// Pines para canales PWM
#define CH1_PIN 2    
#define CH2_PIN 3    
#define CH3_PIN 4    
#define CH4_PIN 5   
#define CH5_PIN 11 
#define CH6_PIN 6    
#define RELE_PIN 7   // Pin para el relé/luces

// Pines para sensores
#define TRIG_PIN 8   // Ultrasónico
#define ECHO_PIN 9
const byte PIN_DATOS_HX711 = A2;  // Sensor de presión
const byte PIN_RELOJ_HX711 = A3;
#define PIN_VOLT_A0 A0  // Entrada de voltaje

// Objetos de los componentes
Servo motor1, motor2, motor3, motor4;
Q2HX711 sensorPresion(PIN_DATOS_HX711, PIN_RELOJ_HX711);
MPU6050 imu;

// Variables de control
int velocidadMotores = 1000;
int distanciaMinima = 20;
bool lucesEncendidas = false;
bool estadoAnteriorCH6 = false;

// Variables de sensores
float profundidad = 0;      // en cm
int distanciaActual = 0;    // en cm
float pitch = 0, roll = 0;  // Ángulos de inclinación
float voltajeBateria = 0;   // Voltaje leído
bool alertaBateria = false; // Estado de alerta
float voltajeReal = 0;

// Constantes para cálculo de profundidad
const float FACTOR_CALIBRACION = 0.00001945;
const float OFFSET_CALIBRACION = -172.67;

// Tiempos
unsigned long tiempoAnterior = 0;
const unsigned long INTERVALO_LECTURA = 200;  // ms

// --- MODIFICACIONES PARA CONTROL HÍBRIDO ---
// Constantes para motores bidireccionales
const int NEUTRAL = 1480;       // Punto neutral (ajustable entre 1450-1500)
const int DEADZONE = 20;        // Zona muerta para evitar vibraciones
const int MIN_PULSO = 1000;
const int MAX_PULSO = 2000;

void setup() {
  Serial.begin(9600);

  while(!Serial){
    ;
  }
  Wire.begin();
  
  // Inicializar MPU6050
  imu.initialize();
  if (!imu.testConnection()) {
    //Serial.println("Error: No se detecta el MPU6050");
    while (1);
  }
  
  // Configurar pines
  configurarPines();
  
  // Inicializar ESCs
  inicializarMotores();
  
  //Serial.println("Sistema ROV iniciado");
}

void loop() {
  if (millis() - tiempoAnterior >= INTERVALO_LECTURA) {
    tiempoAnterior = millis();
    
    // 1. Leer todos los canales PWM
    int ch1 = pulseIn(CH1_PIN, HIGH, 30000);
    int ch2 = pulseIn(CH2_PIN, HIGH, 30000);
    int ch3 = pulseIn(CH3_PIN, HIGH, 30000);
    int ch4 = pulseIn(CH4_PIN, HIGH, 30000);
    int ch5 = pulseIn(CH5_PIN, HIGH, 30000);
    int ch6 = pulseIn(CH6_PIN, HIGH, 30000);

    // 2. Leer sensores
    leerSensores();
    leerIMU();
    leerVoltaje();

    // 3. Verificar batería baja (umbral de 10.5V)
    if (voltajeBateria < 10.5 && !alertaBateria) {
      //Serial.println("¡ALERTA! Voltaje bajo: " + String(voltajeBateria, 1) + "V");
      alertaBateria = true;
    } else if (voltajeBateria >= 10.5) {
      alertaBateria = false;
    }

    // 4. Control de motores principales (REEMPLAZADO POR CONTROL HÍBRIDO)
    controlMotoresBidireccionales(ch1, ch2);

    // 5. Control de velocidad motores 3-4 con seguridad por distancia
    controlarMotoresSecundarios(ch3, ch4, ch5);

    // 6. Control de luces con toggle por CH6
    controlarLuces(ch6);

    // 7. Mostrar datos
    mostrarDatos(ch1, ch2, ch3, ch4, ch5, ch6);
  }
}

// Configurar pines
void configurarPines() {
  pinMode(CH1_PIN, INPUT);  
  pinMode(CH2_PIN, INPUT);  
  pinMode(CH3_PIN, INPUT);  
  pinMode(CH4_PIN, INPUT);  
  pinMode(CH5_PIN, INPUT);
  pinMode(CH6_PIN, INPUT);  
  pinMode(RELE_PIN, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(PIN_VOLT_A0, INPUT);  // Configurar A0 como entrada
  
  motor1.attach(10);       // Motor 1 en pin 10
  motor2.attach(A1);       // Motor 2 en pin A1 (descomentar esta línea)
  motor3.attach(12);       // Motor 3 en pin 12
  motor4.attach(13);       // Motor 4 en pin 13
}

// Inicializar ESCs
void inicializarMotores() {
  motor1.writeMicroseconds(NEUTRAL);  // Valor neutral para motores bidireccionales
  motor2.writeMicroseconds(NEUTRAL);  // Valor neutral para motores bidireccionales
  motor3.writeMicroseconds(1000);     // Valor mínimo para motores estándar
  motor4.writeMicroseconds(1000);
  delay(5000); // Tiempo para inicialización de ESCs
}

// Función para mapeo preciso con deadzone
int mapearMotor(int valorPWM) {
  if (abs(valorPWM - NEUTRAL) < DEADZONE) return NEUTRAL;
  return constrain(valorPWM, MIN_PULSO, MAX_PULSO);
}

// Control híbrido (tank-style)
void controlMotoresBidireccionales(int ch1, int ch2) {
  // Verificar si hay señal válida
  if (ch1 == 0 || ch2 == 0) {
    motor1.writeMicroseconds(NEUTRAL);
    motor2.writeMicroseconds(NEUTRAL);
    return; // Salir de la función inmediatamente
  }
  
  // Mapear CH1 (Avance/Retroceso) y CH2 (Giro)
  int avance = map(ch1, 1000, 2000, -500, 500); // Rango simétrico
  int giro = map(ch2, 1000, 2000, -500, 500);
  
  // Calcular velocidades para cada motor
  int m1 = NEUTRAL + avance + giro;
  int m2 = NEUTRAL + avance - giro;
  
  // Aplicar valores con seguridad
  motor1.writeMicroseconds(mapearMotor(m1));
  motor2.writeMicroseconds(mapearMotor(m2));
}

// Leer sensores
void leerSensores() {
  // Sensor ultrasónico
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duracion = pulseIn(ECHO_PIN, HIGH);
  distanciaActual = duracion * 0.034 / 2;

  // Sensor de presión
  uint32_t lectura = sensorPresion.read();
  profundidad = (FACTOR_CALIBRACION * lectura) + OFFSET_CALIBRACION;
}

// Leer datos del IMU
void leerIMU() {
  int16_t ax, ay, az;
  imu.getAcceleration(&ax, &ay, &az);
  
  // Convertir a valores en g (1g = 16384 para escala ±2g)
  float ax_g = ax / 16384.0;
  float ay_g = ay / 16384.0;
  
  // Calcular pitch y roll (en grados)
  pitch = atan2(ax_g, sqrt(ay_g * ay_g + 1)) * 180.0 / PI;
  roll = atan2(ay_g, sqrt(ax_g * ax_g + 1)) * 180.0 / PI;
}

// Leer voltaje de batería
void leerVoltaje() {
  // Leer valor analógico y convertir a voltaje (0-5V)
  voltajeBateria = (analogRead(PIN_VOLT_A0) * 5.0 / 1023.0);
  voltajeReal = voltajeBateria *= 3.16;
  // Si usas un divisor de voltaje, multiplica por el factor de división
  // Ejemplo para divisor 3:1: voltajeBateria *= 3.0;
}

// Control motores secundarios (3 y 4)
void controlarMotoresSecundarios(int ch3, int ch4, int ch5) {
  //Funcion de perdida de señal 
  if (ch3 == 0 || ch4 == 0) {
    motor3.writeMicroseconds(1000);
    motor4.writeMicroseconds(1000);
    return; // Salir de la función inmediatamente
  }

  // Verificar si CH5 está en alto Y distancia < 20cm
  bool seguridadActivada = (ch5 > 1500) && (distanciaActual < 20);
  
  if (!seguridadActivada) { 
    // Operación normal (si CH5 está bajo O distancia >= 20cm)
    if (ch3 > 1500) velocidadMotores = constrain(velocidadMotores - 10, 1000, 2000);
    if (ch4 > 1500) velocidadMotores = constrain(velocidadMotores + 10, 1000, 2000);
    
    motor3.writeMicroseconds(velocidadMotores + 30);
    motor4.writeMicroseconds(velocidadMotores + 60);
  } else { 
    // Detener motores solo si CH5 está alto Y distancia < 20cm
    motor3.writeMicroseconds(1000);
    motor4.writeMicroseconds(1000);
  }
}

// Toggle luces
void controlarLuces(int ch6) {
  bool estadoActualCH6 = (ch6 > 1600);
  if(estadoActualCH6 && !estadoAnteriorCH6) {
    lucesEncendidas = !lucesEncendidas;
    digitalWrite(RELE_PIN, lucesEncendidas ? HIGH : LOW);
  }
  estadoAnteriorCH6 = estadoActualCH6;
}

// Mostrar datos
void mostrarDatos(int ch1, int ch2, int ch3, int ch4, int ch5, int ch6) {
  int prof_int = (int)round(profundidad);
  int pitch_int = (int)round(pitch);
  int roll_int = (int)round(roll);
  int volt_int = (int)round(voltajeBateria);

  // Envía solo los valores separados por comas
  Serial.print(prof_int); Serial.print(",");
  Serial.print(distanciaActual); Serial.print(",");
  Serial.print(pitch_int); Serial.print(",");
  Serial.print(roll_int); Serial.print(",");
  Serial.print(volt_int); Serial.print(",");
  Serial.print(lucesEncendidas ? "0" : "1"); Serial.print(",");
  Serial.print(velocidadMotores); Serial.print(",");
  Serial.println(ch5 > 1500 ? "1" : "0");
}