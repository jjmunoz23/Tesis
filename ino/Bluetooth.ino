
void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  // set the data rate for the SoftwareSerial port
  mySerial.begin(9600);
}

void loop() {
  int profundidad = random(50, 201);  // cm entre 50 y 200
  int distancia = random(10, 101);    // cm entre 10 y 100
  int pitch = random(-30, 31);        // grados entre -30 y 30
  int roll = random(-15, 16);         // grados entre -15 y 15
  int bateria = random(0, 101);       // % entre 0 y 100

  // Enviar datos como una línea separada por comas
  mySerial.print(profundidad); mySerial.print(",");
  mySerial.print(distancia); mySerial.print(",");
  mySerial.print(pitch); mySerial.print(",");
  mySerial.print(roll); mySerial.print(",");
  mySerial.println(bateria); // 'println' agrega salto de línea (\r\n)

  delay(500);  // 1 segundo entre envíos
}
