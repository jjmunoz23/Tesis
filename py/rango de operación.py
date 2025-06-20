import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle, Polygon, Circle
from matplotlib.gridspec import GridSpec

# Configuración de la figura con GridSpec para controlar tamaños
fig = plt.figure(figsize=(14, 6))
fig.patch.set_facecolor('white')

# Usar GridSpec para hacer la vista lateral más grande (60% del ancho)
gs = GridSpec(1, 2, width_ratios=[1, 1.5])  # 1:1.5 ratio entre vistas

# Vista superior (plano XY)
ax_top = fig.add_subplot(gs[0])
ax_top.set_title('Vista Superior (Plano XY)', pad=10, fontsize=12, fontweight='bold')
ax_top.set_xlabel('Distancia Este-Oeste (m)')
ax_top.set_ylabel('Distancia Norte-Sur (m)')
ax_top.set_xlim(-350, 350)
ax_top.set_ylim(-350, 350)
ax_top.set_aspect('equal')
ax_top.grid(color='gray', linestyle='--', alpha=0.3)

# Vista lateral ampliada (plano XZ)
ax_side = fig.add_subplot(gs[1])
ax_side.set_title('Vista Lateral Ampliada (Plano XZ)', pad=10, fontsize=12, fontweight='bold')
ax_side.set_xlabel('Distancia desde costa (m)', fontsize=10)
ax_side.set_ylabel('Profundidad (m)', fontsize=10)
ax_side.set_xlim(-20, 320)
ax_side.set_ylim(-12, 5)

# Ajustar aspecto para mejor visualización de profundidad
ax_side.set_aspect(15)  # Valor aumentado para exagerar escala vertical

ax_side.grid(color='gray', linestyle='--', alpha=0.3)

## Elementos comunes ##
sub_top, = ax_top.plot([0], [0], 'ko', markersize=8)
sub_side, = ax_side.plot([0], [0], 'ko', markersize=8)
trail_top, = ax_top.plot([], [], 'k-', alpha=0.5, linewidth=1)
trail_side, = ax_side.plot([], [], 'k-', alpha=0.5, linewidth=1)

## Vista Superior ##
operational_area_top = Circle((0, 0), 300, 
                            facecolor='#f0f0f0', 
                            edgecolor='black',
                            linestyle='--',
                            alpha=0.7)
ax_top.add_patch(operational_area_top)

coastline_top = Polygon([[-350, -20], [-350, 20], [0, 0], [-350, -20]], 
                       closed=True, 
                       color='#d3d3d3')
ax_top.add_patch(coastline_top)
ax_top.text(-250, 0, 'Costa', va='center')

ax_top.arrow(0, 0, 300, 0, 
            head_width=15, head_length=20, 
            fc='black', ec='black')
ax_top.text(150, 30, 'Radio: 300m', ha='center')

## Vista Lateral Ampliada ##
# Área operativa con relleno de patrones
operational_area_side = Rectangle((0, -10), 300, 10, 
                                facecolor='#f0f0f0', 
                                edgecolor='black',
                                linestyle='--',
                                alpha=0.7,
                                hatch='///')
ax_side.add_patch(operational_area_side)

# Mejorar visualización de superficie y fondo
ax_side.axhline(0, color='black', linewidth=2, linestyle='-')
ax_side.text(310, 0.2, 'Superficie (0m)', ha='right', fontsize=9)

ax_side.axhline(-10, color='black', linewidth=1.5, linestyle='--')
ax_side.text(310, -9.8, 'Límite -10m', ha='right', fontsize=9)

# Mejorar línea de costa
coastline_side = Polygon([[0, -12], [0, 3], [-15, 0], [0, -12]], 
                        closed=True, 
                        color='#a0a0a0',
                        edgecolor='black')
ax_side.add_patch(coastline_side)
ax_side.text(-12, -6, 'Costa', rotation=90, va='center', fontsize=10)

# Indicadores de profundidad mejorados
for depth in range(0, -11, -2):
    ax_side.axhline(depth, color='gray', linestyle=':', alpha=0.5)
    ax_side.text(310, depth+0.1, f'{abs(depth)}m', ha='right', va='center', fontsize=8)

# Flecha de profundidad más visible
ax_side.arrow(280, 0, 0, -10, 
             head_width=8, head_length=0.7, 
             fc='black', ec='black',
             linewidth=1.5)
ax_side.text(285, -5, 'Profundidad\noperativa\n10m', ha='left', va='center', fontsize=9,
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.5'))

# Simulación de movimiento mejorada
def update(frame):
    angle = np.radians(frame * 3)
    radius = 200 + 50 * np.sin(np.radians(frame * 4))
    
    x = radius * np.cos(angle)
    y = radius * np.sin(angle)
    z = -5 + 3 * np.sin(np.radians(frame * 6))
    
    distance_from_shore = np.sqrt(x**2 + y**2)
    
    # Actualizar posiciones
    sub_top.set_data([x], [y])
    sub_side.set_data([distance_from_shore], [z])
    
    # Actualizar trayectorias
    for trail, new_x, new_y in zip([trail_top, trail_side],
                                  [[x], [distance_from_shore]],
                                  [[y], [z]]):
        old_data = trail.get_data()
        trail.set_data(np.append(old_data[0], new_x), 
                       np.append(old_data[1], new_y))
        
        if len(old_data[0]) > 40:
            trail.set_data(old_data[0][-40:], old_data[1][-40:])
    
    # Control de límites
    out_of_bounds = distance_from_shore > 300 or z < -10
    for sub in [sub_top, sub_side]:
        sub.set_marker('x' if out_of_bounds else 'o')
        sub.set_color('red' if out_of_bounds else 'black')
        sub.set_markersize(10 if out_of_bounds else 8)
    
    return sub_top, sub_side, trail_top, trail_side

ani = animation.FuncAnimation(fig, update, frames=240, interval=50, blit=True)

# Añadir leyenda técnica
ax_top.legend([operational_area_top], ['Área operativa (300m radio)'], loc='upper right')
ax_side.legend([operational_area_side], ['Área operativa (10m profundidad)'], loc='upper right')

plt.tight_layout()
plt.show()
