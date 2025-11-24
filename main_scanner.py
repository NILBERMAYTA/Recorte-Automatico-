import cv2
import serial
import time
from ultralytics import YOLO
import sys
    
# --- CONFIGURACIÓN DE USUARIO ---
COM_PORT = 'COM3'        # ¡CAMBIA ESTO! (En Windows es COMx, en Linux /dev/ttyUSBx)
BAUD_RATE = 115200       # Debe coincidir con el ESP32
MODEL_PATH = 'best.pt'   # La ruta a tu modelo entrenado
CONF_THRESHOLD = 0.4     # Confianza mínima para detectar defectos
FRAMES_SKIP = 3          # Analizar 1 de cada 3 frames (para no saturar la CPU)

# Mapa de clases (Ajusta según tu entrenamiento)
# El ID debe coincidir con lo que dice tu archivo data.yaml
CLASS_NAMES = {
    0: "Perfecta",
    1: "Abolladura Leve",
    2: "Abolladura Grave",
    3: "Oxidada",
    4: "Inutilizable"
}
# -------------------------------

# 1. INICIALIZAR CONEXIÓN SERIAL
try:
    arduino = serial.Serial(port=COM_PORT, baudrate=BAUD_RATE, timeout=0.1)
    time.sleep(2) # Esperar a que el ESP32 se reinicie al conectar
    print(f"✅ Conectado al ESP32 en {COM_PORT}")
except Exception as e:
    print(f"❌ Error conectando al ESP32: {e}")
    sys.exit()

# 2. CARGAR MODELO E INICIAR CÁMARA
print("Cargando modelo YOLO...")
model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(0) # 0 suele ser la webcam principal

# Configuración opcional de cámara para evitar Motion Blur (ajusta según tu cámara)
# cap.set(cv2.CAP_PROP_EXPOSURE, -6) # Valores negativos en Windows, o manuales

if not cap.isOpened():
    print("❌ No se detectó cámara.")
    sys.exit()

print("\n" + "="*40)
print("   SISTEMA DE INSPECCIÓN DE LATAS")
print("   Presiona [ENTER] para escanear")
print("   Presiona [q] para salir")
print("="*40 + "\n")

try:
    while True:
        user_input = input("Esperando lata... (ENTER) > ")
        if user_input.lower() == 'q':
            break

        # --- INICIO DEL ESCANEO ---
        print("🔄 Iniciando giro y escaneo...")
        
        # Limpiar buffer serial basura
        arduino.reset_input_buffer()
        # Enviar comando de arranque
        arduino.write(b'S')
        
        defectos_detectados = []
        scanning = True
        frame_counter = 0

        while scanning:
            ret, frame = cap.read()
            if not ret: break

            # 1. Verificar si el ESP32 terminó el giro
            if arduino.in_waiting > 0:
                line = arduino.readline().decode().strip()
                if line == "STOP":
                    scanning = False
                    print("🛑 Giro completado.")

            # 2. Procesamiento de IA (Solo cada N frames)
            if frame_counter % FRAMES_SKIP == 0:
                # Inferencia
                results = model(frame, verbose=False, conf=CONF_THRESHOLD)
                
                # Dibujar resultados en pantalla
                annotated_frame = results[0].plot()
                cv2.imshow("Vision Artificial - Tiempo Real", annotated_frame)
                
                # Guardar detecciones
                for r in results:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        defectos_detectados.append(cls_id)
            
            else:
                # Mostrar video fluido aunque no analice este frame
                cv2.imshow("Vision Artificial - Tiempo Real", frame)

            frame_counter += 1
            if cv2.waitKey(1) & 0xFF == ord('q'):
                scanning = False

        # --- ANÁLISIS DE RESULTADOS ---
        if len(defectos_detectados) == 0:
            # Si no vio defectos, asumimos que es la clase "Perfecta" (si la tienes definida)
            # Ojo: Esto asume que tu modelo detecta "Lata Perfecta". 
            # Si tu modelo solo detecta fallos, una lista vacía es BUENA señal.
            print("\n✅ RESULTADO: La lata parece PERFECTA (No se detectaron defectos).")
        else:
            # Lógica del PEOR CASO: Tomamos el ID más alto (asumiendo que mayor ID es peor estado)
            peor_caso = max(defectos_detectados)
            nombre_defecto = CLASS_NAMES.get(peor_caso, "Desconocido")
            
            print(f"\n⚠️ RESULTADO: Se detectaron {len(defectos_detectados)} anomalías en el giro.")
            print(f"🚨 DIAGNÓSTICO FINAL: {nombre_defecto.upper()}")

        print("-" * 40)

except KeyboardInterrupt:
    print("\nSaliendo...")

finally:
    cap.release()
    cv2.destroyAllWindows()
    arduino.close()