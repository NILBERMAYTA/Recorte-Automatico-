import cv2
import os
import shutil
from ultralytics import YOLO

# --- CONFIGURACIÓN ---
input_dir = './mis_latas_raw'
output_base = './dataset_latas_autolabeled'
search_classes = ["soda can", "aluminum can", "beer can"] 
conf_threshold = 0.25
my_custom_class_id = 0
# ---------------------

img_dest = os.path.join(output_base, 'images')
lbl_dest = os.path.join(output_base, 'labels')
os.makedirs(img_dest, exist_ok=True)
os.makedirs(lbl_dest, exist_ok=True)

print("Cargando modelo YOLO-World...")
model = YOLO('yolov8s-world.pt') 
model.set_classes(search_classes)

print(f"Auto-etiquetando buscando: {search_classes}...")

count = 0
errors = 0

for filename in os.listdir(input_dir):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        filepath = os.path.join(input_dir, filename)
        
        try:
            # 1. VALIDACIÓN PREVIA: Intentamos leer con OpenCV primero
            img_check = cv2.imread(filepath)
            
            if img_check is None:
                print(f"⚠️ ALERTA: La imagen {filename} está corrupta o no se puede leer. SALTANDO.")
                errors += 1
                continue # Salta a la siguiente imagen del bucle

            # 2. PREDICCIÓN: Le pasamos la imagen ya cargada (img_check) en vez de la ruta
            # Esto evita que YOLO intente leerla de nuevo y falle
            results = model.predict(img_check, conf=conf_threshold, verbose=False)
            
            labels_content = []
            detection_found = False
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x, y, w, h = map(float, box.xywhn[0])
                    labels_content.append(f"{my_custom_class_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
                    detection_found = True

            if detection_found:
                # Copiamos el archivo original
                shutil.copy(filepath, os.path.join(img_dest, filename))
                
                txt_filename = os.path.splitext(filename)[0] + ".txt"
                with open(os.path.join(lbl_dest, txt_filename), "w") as f:
                    f.write("\n".join(labels_content))
                
                count += 1
                print(f"✅ Lata detectada en: {filename}")

        except Exception as e:
            print(f"❌ Error inesperado procesando {filename}: {e}")
            errors += 1
            continue

print(f"\n--- RESUMEN ---")
print(f"Procesadas correctamente: {count}")
print(f"Archivos con error (saltados): {errors}")
print(f"Revisa la carpeta '{output_base}' y súbela a Roboflow.")