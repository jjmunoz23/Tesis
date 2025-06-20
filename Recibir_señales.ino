// Pines para canales
#define CH1_PIN 2    
#define CH2_PIN 3    
#define CH3_PIN 4    
#define CH4_PIN 5    
#define CH5_PIN 11   
#define CH6_PIN 6    

// Variables para el tiempo entre lecturas
unsigned long tiempoAnterior = 0;
const unsigned long intervalo = 200; // Intervalo en ms

void setup() {
  Serial.begin(115200);
  
  // Configurar pines de entrada
  pinMode(CH1_PIN, INPUT);  
  pinMode(CH2_PIN, INPUT);  
  pinMode(CH3_PIN, INPUT);  
  pinMode(CH4_PIN, INPUT);
  pinMode(CH5_PIN, INPUT);  
  pinMode(CH6_PIN, INPUT);  

  Serial.println("Iniciando lectura de canales PWM...");
  Serial.println("CH1\tCH2\tCH3\tCH4\tCH5\tCH6");
  Serial.println("----------------------------------");
}

void loop() {
  if (millis() - tiempoAnterior >= intervalo) {
    tiempoAnterior = millis();
    
    // Leer señales PWM de los canales
    int ch1 = pulseIn(CH1_PIN, HIGH, 30000);
    int ch2 = pulseIn(CH2_PIN, HIGH, 30000);
    int ch3 = pulseIn(CH3_PIN, HIGH, 30000);
    int ch4 = pulseIn(CH4_PIN, HIGH, 30000);
    int ch5 = pulseIn(CH5_PIN, HIGH, 30000);
    int ch6 = pulseIn(CH6_PIN, HIGH, 30000);

    // Mostrar valores en el monitor serial
    Serial.print(ch1); Serial.print("\t");
    Serial.print(ch2); Serial.print("\t");
    Serial.print(ch3); Serial.print("\t");
    Serial.print(ch4); Serial.print("\t");
    Serial.print(ch5); Serial.print("\t");
    Serial.println(ch6);
  }
}