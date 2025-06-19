import cv2
import serial
import time
import threading
from datetime import datetime, timedelta
import numpy as np

class BluetoothCameraOverlay:
    def __init__(self, puerto="COM24", baudrate=9600):
        """Inicializa la cámara y la conexión Bluetooth."""
        self.puerto = puerto
        self.baudrate = baudrate
        self.bt = None
        self.start_time = datetime.now()
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        self.modo_prueba_bateria = False

        # Valores por defecto
        self.valores_actuales = {
            "Profundidad": "Sin Conexion",
            "Distancia": "Sin Conexion",
            "Pitch": "Sin Conexion",
            "Roll": "Sin Conexion",
            "Bateria": "Sin Conexion",
            "Luces": "Off",
            "Velocidad": "Sin Conexion",
            "Seguridad": "Sin Conexion"
        }

        # Variables para alertas
        self.alerta_bateria = False
        self.ultimo_parpadeo = datetime.now()
        self.mostrar_alerta = True
        self.estado_conexion = "Desconectado"

        # Configuración de cámara
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        
        if not self.cap.isOpened():
            print("Error: No se pudo abrir la cámara")
            exit()

        # Hilo Bluetooth
        self.conectando_bt = True
        self.hilo_bt = threading.Thread(target=self.gestionar_bluetooth, daemon=True)
        self.hilo_bt.start()

    def gestionar_bluetooth(self):
        """Hilo para gestión de Bluetooth."""
        while self.conectando_bt:
            try:
                if not self.bt or not self.bt.is_open:
                    self.estado_conexion = "Conectando..."
                    self.bt = serial.Serial(self.puerto, self.baudrate, timeout=0.1)
                    self.estado_conexion = "Conectado"
                    print(f"Conectado a {self.puerto}")
                time.sleep(1)
            except Exception as e:
                self.estado_conexion = f"Error: {str(e)}"
                time.sleep(2)

    def calcular_fps(self):
        """Calcula los FPS del video."""
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_fps_time
        
        if elapsed >= 1.0:  # Actualizar cada segundo
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = current_time

    def leer_bluetooth(self):
        """Lee datos del Bluetooth."""
        if self.modo_prueba_bateria:
            # Forzar valores de prueba
            self.valores_actuales.update({
                "Profundidad": "150 cm",
                "Distancia": "50 cm",
                "Pitch": "0.0",
                "Roll": "0.0",
                "Bateria": "9.8V",  # Valor bajo para activar alerta
                "Luces": "Off",
                "Velocidad": "50%",
                "Seguridad": "Off"
            })
            self.alerta_bateria = True
            return
            
        if self.bt and self.bt.is_open:
            try:
                if self.bt.in_waiting:
                    datos = self.bt.readline().decode('utf-8').strip()
                    valores = datos.split(",")

                    if len(valores) == 8:
                        self.valores_actuales.update({
                            "Profundidad": f"{valores[0]} cm",
                            "Distancia": f"{valores[1]} cm",
                            "Pitch": f"{valores[2]}",
                            "Roll": f"{valores[3]}",
                            "Bateria": f"{valores[4]}V",
                            "Luces": "On" if valores[5] == "1" else "Off",
                            "Velocidad": f"{valores[6]}%",
                            "Seguridad": "On" if valores[7] == "1" else "Off"
                        })

                        # Control de batería
                        try:
                            voltaje = float(valores[4])
                            self.alerta_bateria = voltaje < 9
                        except:
                            self.alerta_bateria = False
            except Exception as e:
                print(f"Error lectura BT: {e}")
        else:
            for key in self.valores_actuales:
                self.valores_actuales[key] = "Sin Conexion"

    def dibujar_interfaz(self, frame):
        """Dibuja la interfaz en el frame."""
        height, width = frame.shape[:2]
        
        # Panel inferior
        panel_inferior = np.zeros((150, width, 3), dtype=np.uint8)
        cv2.rectangle(panel_inferior, (0, 0), (width, 150), (0, 0, 0), -1)
        frame[height-150:height, 0:width] = cv2.addWeighted(
            frame[height-150:height, 0:width], 0.3, panel_inferior, 0.7, 0)

        # Título
        cv2.putText(frame, "NEPTUNE", (width//2 - 150, 50), 
                   cv2.FONT_HERSHEY_COMPLEX, 1.5, (255, 255, 0), 3)

        # Estado conexión
        color_conexion = (0, 255, 0) if "Conectado" in self.estado_conexion else (0, 0, 255)
        cv2.putText(frame, f"BT: {self.estado_conexion}", (width - 300, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_conexion, 1)

        # Temporizador
        tiempo_transcurrido = str(datetime.now() - self.start_time).split('.')[0]
        cv2.putText(frame, f"Tiempo: {tiempo_transcurrido}", (20, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        
        # Hora actual
        hora_actual = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, hora_actual, (width - 120, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        # Datos
        datos_posiciones = [
            ("Profundidad", (30, height-120)),
            ("Distancia", (30, height-95)),
            ("Pitch", (30, height-70)),
            ("Roll", (30, height-45)),
            ("Seguridad", (width//2 + 30, height-120)),
            ("Velocidad", (width//2 + 30, height-95)),
            ("Luces", (width//2 + 30, height-70)),
            ("Bateria", (width//2 + 30, height-45))
        ]

        for key, pos in datos_posiciones:
            color = (255, 255, 255)
            if key == "Luces" and self.valores_actuales[key] == "On":
                color = (0, 255, 0)
            elif key == "Seguridad" and self.valores_actuales[key] == "On":
                color = (0, 255, 255)
            elif key == "Bateria" and self.alerta_bateria:
                color = (0, 0, 255)
                
            cv2.putText(frame, f"{key}: {self.valores_actuales[key]}",
                       pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)

        # Alerta batería
        if self.alerta_bateria:
            if (datetime.now() - self.ultimo_parpadeo).total_seconds() >= 0.5:
                self.mostrar_alerta = not self.mostrar_alerta
                self.ultimo_parpadeo = datetime.now()
            
            if self.mostrar_alerta:
                self.dibujar_alerta_bateria(frame, width, height)

        # FPS
        cv2.putText(frame, f"FPS: {int(self.fps)}", (width - 100, height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    def dibujar_alerta_bateria(self, frame, width, height):
        """Dibuja alerta de batería baja."""
        texto = "!ALERTA! BATERIA BAJA"
        tamaño = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
        
        # Fondo
        overlay = frame.copy()
        cv2.rectangle(overlay, 
                     (width//2 - tamaño[0]//2 - 10, height//2 - tamaño[1]//2 - 10),
                     (width//2 + tamaño[0]//2 + 10, height//2 + tamaño[1]//2 + 10),
                     (0, 0, 100), -1)
        frame = cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        
        # Texto
        cv2.putText(frame, texto,
                   (width//2 - tamaño[0]//2, height//2 + tamaño[1]//2),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    def iniciar(self):
        """Bucle principal."""
        cv2.namedWindow("NEPTUNE - Control", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("NEPTUNE - Control", 1280, 720)
        
        try:
            while True:
                start_time = time.time()
                
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Fallo en cámara")
                    break

                self.leer_bluetooth()
                self.calcular_fps()  # Ahora este método existe
                self.dibujar_interfaz(frame)

                cv2.imshow("NEPTUNE - Control", frame)
                
                # Control
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('f'):
                    print(f"FPS: {int(self.fps)}")
                elif key == ord('t'):  # Tecla 't' para activar modo prueba
                    self.modo_prueba_bateria = not self.modo_prueba_bateria
                    estado = "ACTIVADO" if self.modo_prueba_bateria else "DESACTIVADO"
                    print(f"Modo prueba batería {estado}")
                    if self.modo_prueba_bateria:
                        self.alerta_bateria = True
                    else:
                        self.alerta_bateria = False
                
                # Limitar FPS
                elapsed = time.time() - start_time
                if elapsed < 0.033:
                    time.sleep(0.033 - elapsed)
                    
        finally:
            self.conectando_bt = False
            self.cap.release()
            if self.bt and self.bt.is_open:
                self.bt.close()
            cv2.destroyAllWindows()
            print("Sistema cerrado")

if __name__ == "__main__":
    sistema = BluetoothCameraOverlay(puerto="COM24")
    sistema.iniciar()