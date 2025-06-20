import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import Slider, Button
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d

class ROUVDynamicControlSimulator:
    def __init__(self):
        # Parámetros físicos
        self.m = 10.0  # masa (kg)
        self.Iy = 2.0  # inercia pitch (kg·m²)
        self.Iz = 1.5  # inercia yaw (kg·m²)
        self.g = 9.81
        self.b_neutral = self.m * self.g
        self.Dx, self.Dz = 1.0, 1.2
        
        # Geometría
        self.d = 0.5  # distancia del centro de masa a propulsores verticales
        self.l = 0.3  # distancia del centro de masa a propulsores horizontales (F1, F2)
        self.phi = np.deg2rad(39.4)
        
        # Coeficientes de amortiguamiento angular (reducidos para respuesta más rápida)
        self.D_theta = 0.3  # amortiguamiento pitch
        self.D_beta = 0.3   # amortiguamiento yaw
        
        # Estado inicial
        self.reset_state()
        
        # Configuración gráfica
        self.fig = plt.figure(figsize=(12, 9))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self._setup_environment()
        self._create_sliders()
        
        self.history = []
        self.max_history = 300
        self.reference_vectors = np.eye(3)
        self.orientation_history = []
        self.dt = 0.03  # paso de tiempo reducido para respuesta más rápida
        
        # Control tipo dron con nuevas teclas
        self.drone_control = {
            'forward': False,    # W
            'backward': False,   # S
            'left': False,       # A
            'right': False,      # D
            'up': False,         # R
            'down': False        # F
        }
        self.max_thrust = 15.0  # Empuje máximo para control tipo dron

    def reset_state(self):
        self.x, self.y, self.z = 0.0, 0.0, -2.0
        self.vx, self.vy, self.vz = 0.0, 0.0, 0.0  # Velocidades en sistema local
        self.theta, self.beta = 0.0, 0.0  # Pitch y Yaw
        self.omega_theta, self.omega_beta = 0.0, 0.0  # Velocidades angulares
        self.t = 0.0
        self.b = self.b_neutral
        self.F1 = self.F2 = self.F3 = self.F4 = 0.0
        self.reference_vectors = np.eye(3)
        self.orientation_history = []

    def _setup_environment(self):
        self.ax.set_xlim(-5, 5)
        self.ax.set_ylim(-5, 5)
        self.ax.set_zlim(-5, 1)
        self.ax.set_title('')
        self.ax.set_xlabel('X Global')
        self.ax.set_ylabel('Y Global')
        self.ax.set_zlabel('Z Global')
        
        # Mantener la navegación 3D con mouse habilitada

    def _create_sliders(self):
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.35)
        
        # Sliders para fuerzas manuales
        ax_F1 = plt.axes([0.1, 0.30, 0.35, 0.025])
        ax_F2 = plt.axes([0.1, 0.27, 0.35, 0.025])
        ax_F34 = plt.axes([0.1, 0.24, 0.35, 0.025])
        ax_b = plt.axes([0.1, 0.21, 0.35, 0.025])
        
        self.slider_F1 = Slider(ax_F1, 'F1 (Manual)', -20, 20, valinit=0)
        self.slider_F2 = Slider(ax_F2, 'F2 (Manual)', -20, 20, valinit=0)
        self.slider_F34 = Slider(ax_F34, 'F3+F4 (Manual)', -20, 20, valinit=0)
        self.slider_b = Slider(ax_b, 'Flotabilidad', -10, 10, valinit=0)
        
        # Slider solo para pitch
        ax_pitch = plt.axes([0.6, 0.27, 0.25, 0.025])
        self.slider_pitch = Slider(ax_pitch, 'Pitch (grados)', -45, 45, valinit=0)
        
        # Botones de control tipo dron
        button_size = 0.06
        button_height = 0.04
        
        # Botones de movimiento con nuevas etiquetas
        ax_forward = plt.axes([0.55, 0.18, button_size, button_height])
        ax_backward = plt.axes([0.55, 0.10, button_size, button_height])
        ax_left = plt.axes([0.48, 0.14, button_size, button_height])  
        ax_right = plt.axes([0.62, 0.14, button_size, button_height])
        ax_up = plt.axes([0.72, 0.18, button_size, button_height])
        ax_down = plt.axes([0.72, 0.10, button_size, button_height])
        
        self.btn_forward = Button(ax_forward, 'W\nAdelante', color='lightgreen')
        self.btn_backward = Button(ax_backward, 'X\nAtrás', color='lightcoral') 
        self.btn_left = Button(ax_left, 'A\nIzq', color='lightblue')
        self.btn_right = Button(ax_right, 'D\nDer', color='lightblue')
        self.btn_up = Button(ax_up, 'R\nSubir', color='lightyellow')
        self.btn_down = Button(ax_down, 'T\nBajar', color='lightyellow')
        
        # Conectar eventos de botones
        self.btn_forward.on_clicked(lambda x: self._toggle_control('forward'))
        self.btn_backward.on_clicked(lambda x: self._toggle_control('backward'))
        self.btn_left.on_clicked(lambda x: self._toggle_control('left'))
        self.btn_right.on_clicked(lambda x: self._toggle_control('right'))
        self.btn_up.on_clicked(lambda x: self._toggle_control('up'))
        self.btn_down.on_clicked(lambda x: self._toggle_control('down'))
        
        # Botón de reset
        resetax = plt.axes([0.8, 0.15, 0.08, 0.04])
        self.reset_button = Button(resetax, 'Reset', color='lightgoldenrodyellow')
        self.reset_button.on_clicked(self._reset_simulation)
        
        # Conectar eventos de teclado
        self.fig.canvas.mpl_connect('key_press_event', self._on_key_press)
        self.fig.canvas.mpl_connect('key_release_event', self._on_key_release)
        
        # Información sobre controles actualizada
        control_info = ("CONTROLES TIPO DRON:\n"
                       "Teclas WAXD + R/T o botones\n"
                       "W/X: Adelante/Atrás\n"
                       "A/D: Girar Izq/Der\n"
                       "R/T: Subir/Bajar\n"
                       "Yaw dinámico: ΔF = l*(F1-F2)/2")
        plt.figtext(0.75, 0.5, control_info, fontsize=9,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcyan", alpha=0.8))

    def _toggle_control(self, direction):
        """Alterna el estado de control de un movimiento"""
        self.drone_control[direction] = not self.drone_control[direction]
        
    def _on_key_press(self, event):
        """Maneja eventos de teclas presionadas - WASD + R/F"""
        key = event.key.lower() if event.key else ''
        
        if key == 'w':
            self.drone_control['forward'] = True
        elif key == 'x':
            self.drone_control['backward'] = True
        elif key == 'a':
            self.drone_control['left'] = True
        elif key == 'd':
            self.drone_control['right'] = True
        elif key == 'r':
            self.drone_control['up'] = True
        elif key == 't':
            self.drone_control['down'] = True
            
    def _on_key_release(self, event):
        """Maneja eventos de teclas liberadas - WASD + R/F"""
        key = event.key.lower() if event.key else ''
        
        if key == 'w':
            self.drone_control['forward'] = False
        elif key == 'x':
            self.drone_control['backward'] = False
        elif key == 'a':
            self.drone_control['left'] = False
        elif key == 'd':
            self.drone_control['right'] = False
        elif key == 'r':
            self.drone_control['up'] = False
        elif key == 't':
            self.drone_control['down'] = False

    def _calculate_drone_forces(self):
        """Calcula las fuerzas basadas en el control tipo dron"""
        F1_drone = F2_drone = F34_drone = 0.0
        
        # Movimiento adelante/atrás (W/S)
        if self.drone_control['forward']:
            F1_drone += self.max_thrust
            F2_drone += self.max_thrust
        if self.drone_control['backward']:
            F1_drone -= self.max_thrust
            F2_drone -= self.max_thrust
            
        # Giro izquierda/derecha (A/D) - diferencial en F1, F2
        if self.drone_control['left']:
            F1_drone -= self.max_thrust * 0.7  # Menos empuje en izquierda
            F2_drone += self.max_thrust * 0.7  # Más empuje en derecha
        if self.drone_control['right']:
            F1_drone += self.max_thrust * 0.7  # Más empuje en izquierda
            F2_drone -= self.max_thrust * 0.7  # Menos empuje en derecha
            
        # Movimiento vertical (R/F)
        if self.drone_control['up']:
            F34_drone += self.max_thrust
        if self.drone_control['down']:
            F34_drone -= self.max_thrust
            
        return F1_drone, F2_drone, F34_drone

    def update(self, frame):
        # Obtener fuerzas del control tipo dron
        F1_drone, F2_drone, F34_drone = self._calculate_drone_forces()
        
        # Combinar fuerzas del control dron con sliders manuales
        self.F1 = self.slider_F1.val + F1_drone
        self.F2 = self.slider_F2.val + F2_drone
        total_vertical = self.slider_F34.val + F34_drone
        self.F3 = self.F4 = total_vertical / 2
        self.b = self.b_neutral + self.slider_b.val
        
        # Pitch se puede controlar directamente (o también podrías hacerlo dinámico)
        self.theta = np.deg2rad(self.slider_pitch.val)
        
        # Actualizar tiempo
        self.t += self.dt
        
        # 1. CALCULAR MOMENTOS
        # Momento de yaw generado por diferencia de fuerzas F1-F2
        M_yaw = self.l * (self.F1 - self.F2) / 2
        
        # Momento de pitch generado por propulsores verticales (si están descentrados)
        # Para simplificar, asumimos que F3 y F4 están en el centro, por lo que no generan momento de pitch
        # Pero el empuje horizontal sí puede generar momento de pitch
        M_pitch_from_horizontal = 0  # Lo dejamos en 0 por ahora
        
        # 2. CALCULAR ACELERACIONES ANGULARES
        # Aceleración angular de yaw
        alpha_beta = (M_yaw - self.D_beta * self.omega_beta) / self.Iz
        
        # Para pitch, si quieres que también sea dinámico, descomenta la siguiente línea:
        # alpha_theta = (M_pitch_from_horizontal - self.D_theta * self.omega_theta) / self.Iy
        
        # 3. INTEGRAR VELOCIDADES ANGULARES
        self.omega_beta += alpha_beta * self.dt
        # self.omega_theta += alpha_theta * self.dt  # Si quieres pitch dinámico
        
        # 4. INTEGRAR ÁNGULOS
        self.beta += self.omega_beta * self.dt
        # self.theta += self.omega_theta * self.dt  # Si quieres pitch dinámico
        
        # 5. CALCULAR FUERZAS Y ACELERACIONES LINEALES
        # Fuerzas en sistema local
        F_forward_local = (self.F1 + self.F2) * np.cos(self.theta)
        F_vertical_local = ((self.F3 + self.F4) + (self.F1 + self.F2) * np.sin(self.theta) 
                          + (self.b - self.b_neutral))
        
        # Aceleraciones lineales en sistema local
        ax_local = (F_forward_local - self.Dx * np.abs(self.vx) * self.vx) / self.m
        ay_local = (-self.Dx * np.abs(self.vy) * self.vy) / self.m
        az_local = (F_vertical_local - self.Dz * np.abs(self.vz) * self.vz) / self.m
        
        # 6. ACTUALIZAR VELOCIDADES LINEALES (en sistema local)
        self.vx += ax_local * self.dt
        self.vy += ay_local * self.dt
        self.vz += az_local * self.dt
        
        # 7. ACTUALIZAR VECTORES DE REFERENCIA (orientación)
        self.update_reference_vectors()
        
        # 8. CONVERTIR VELOCIDAD LOCAL A GLOBAL PARA ACTUALIZAR POSICIÓN
        v_global = self.local_to_global(np.array([self.vx, self.vy, self.vz]))
        self.x += v_global[0] * self.dt
        self.y += v_global[1] * self.dt
        self.z += v_global[2] * self.dt
        
        # Guardar estado para visualización
        self.history.append((self.x, self.y, self.z))
        if len(self.history) > self.max_history:
            self.history.pop(0)
            
        self.orientation_history.append((self.beta, self.theta))
        if len(self.orientation_history) > self.max_history:
            self.orientation_history.pop(0)
        
        # Actualización gráfica
        self.ax.clear()
        self._setup_environment()
        
        # Dibujar trayectoria en 3D
        if len(self.history) > 1:
            hist = np.array(self.history)
            self.ax.plot(hist[:,0], hist[:,1], hist[:,2], 'g-', alpha=0.5, label='Trayectoria')
            
        # Dibujar ROUV y sistema de referencia
        self._draw_relative_system()
        
        # Info del estado
        active_controls = [k for k, v in self.drone_control.items() if v]
        controls_text = f"Controles activos: {', '.join(active_controls) if active_controls else 'Ninguno'}"
        
        info_text = (f"Tiempo: {self.t:.1f}s\n"
                    f"Posición Global: ({self.x:.2f}, {self.y:.2f}, {self.z:.2f})\n"
                    f"Velocidad Local: ({self.vx:.2f}, {self.vy:.2f}, {self.vz:.2f}) m/s\n"
                    f"Orientación: Pitch={np.rad2deg(self.theta):.1f}°, Yaw={np.rad2deg(self.beta):.1f}°\n"
                    f"Velocidad Angular Yaw: {np.rad2deg(self.omega_beta):.1f}°/s\n"
                    f"Momento Yaw: {M_yaw:.2f} N·m\n"
                    f"Fuerzas Totales: F1={self.F1:.1f}N, F2={self.F2:.1f}N, ΔF={self.F1-self.F2:.1f}N\n"
                    f"{controls_text}")
        self.ax.text2D(0.02, 0.95, info_text, transform=self.ax.transAxes, 
                      bbox=dict(facecolor='white', alpha=0.85), fontsize=8)
        self.ax.legend()

    def update_reference_vectors(self):
        """Actualiza los vectores de referencia del sistema local"""
        # Matriz de rotación para yaw (eje Z)
        R_yaw = np.array([
            [np.cos(self.beta), -np.sin(self.beta), 0],
            [np.sin(self.beta), np.cos(self.beta), 0],
            [0, 0, 1]
        ])
        
        # Matriz de rotación para pitch (eje Y)
        R_pitch = np.array([
            [np.cos(self.theta), 0, np.sin(self.theta)],
            [0, 1, 0],
            [-np.sin(self.theta), 0, np.cos(self.theta)]
        ])
        
        # Rotación combinada (primero yaw, luego pitch)
        R_combined = np.dot(R_pitch, R_yaw)
        self.reference_vectors = R_combined.T

    def local_to_global(self, local_vector):
        """Convierte un vector del sistema local al global"""
        return np.dot(self.reference_vectors, local_vector)
    
    def global_to_local(self, global_vector):
        """Convierte un vector del sistema global al local"""
        return np.dot(self.reference_vectors.T, global_vector)

    def _draw_relative_system(self):
        """Dibuja el ROV y su sistema de referencia local"""
        # Dibujar el ROV
        self.ax.scatter(self.x, self.y, self.z, color='red', s=100, label='ROUV')
        
        # Longitud de los ejes de referencia
        axis_length = 1.0
        
        # Dibujar ejes del sistema local
        x_axis = self.local_to_global(np.array([axis_length, 0, 0]))
        y_axis = self.local_to_global(np.array([0, axis_length, 0]))
        z_axis = self.local_to_global(np.array([0, 0, axis_length]))
        
        # Flechas para los ejes locales
        class Arrow3D(FancyArrowPatch):
            def __init__(self, xs, ys, zs, *args, **kwargs):
                super().__init__((0,0), (0,0), *args, **kwargs)
                self._verts3d = xs, ys, zs

            def do_3d_projection(self, renderer=None):
                xs3d, ys3d, zs3d = self._verts3d
                xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, self.axes.M)
                self.set_positions((xs[0],ys[0]),(xs[1],ys[1]))
                return min(zs)
        
        # Eje X (Forward - Rojo)
        arrow_x = Arrow3D(
            [self.x, self.x + x_axis[0]],
            [self.y, self.y + x_axis[1]],
            [self.z, self.z + x_axis[2]],
            mutation_scale=15, lw=2, arrowstyle="-|>", color="r", label='Frente'
        )
        self.ax.add_artist(arrow_x)
        
        # Eje Y (Starboard - Verde)
        arrow_y = Arrow3D(
            [self.x, self.x + y_axis[0]],
            [self.y, self.y + y_axis[1]],
            [self.z, self.z + z_axis[2]],
            mutation_scale=15, lw=2, arrowstyle="-|>", color="g", label='Lateral'
        )
        self.ax.add_artist(arrow_y)
        
        # Eje Z (Down - Azul)
        arrow_z = Arrow3D(
            [self.x, self.x + z_axis[0]],
            [self.y, self.y + z_axis[1]],
            [self.z, self.z + z_axis[2]],
            mutation_scale=15, lw=2, arrowstyle="-|>", color="b", label='Eje Z'
        )
        self.ax.add_artist(arrow_z)

    def _reset_simulation(self, event):
        self.reset_state()
        self.slider_F1.reset()
        self.slider_F2.reset()
        self.slider_F34.reset()
        self.slider_b.reset()
        self.slider_pitch.reset()
        self.history = []
        self.orientation_history = []
        # Resetear también los controles del dron
        for key in self.drone_control:
            self.drone_control[key] = False

    def run(self):
        self.ani = FuncAnimation(self.fig, self.update, frames=200,
                               interval=100, blit=False)
        plt.show()

# Ejecutar simulación
if __name__ == "__main__":
    sim_dynamic = ROUVDynamicControlSimulator()
    sim_dynamic.run()
