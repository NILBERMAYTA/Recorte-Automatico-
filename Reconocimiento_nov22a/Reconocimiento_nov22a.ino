#include <AccelStepper.h>

// --- CONFIGURACIÓN DE PINES (ESP32) ---
// Asegúrate que estos pines coincidan con tu cableado real
#define STEP_PIN 14  // Al pin STEP del driver
#define DIR_PIN  12  // Al pin DIR del driver
#define ENABLE_PIN 13 // Al pin EN del driver (opcional)

const long PASOS_POR_VUELTA = 200; 

// Velocidad y Aceleración
const float VELOCIDAD = 200.0; 
const float ACELERACION = 100.0;

// Definir motor (1 significa driver con pines Step y Dir)
AccelStepper stepper(1, STEP_PIN, DIR_PIN);

void setup() {
  // ESTO SE EJECUTA UNA VEZ AL INICIO
  Serial.begin(115200); // Iniciar comunicación con Python
  
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, HIGH); // Desactivar motor al inicio (HIGH suele ser OFF en drivers A4988)

  stepper.setMaxSpeed(1000);
  stepper.setAcceleration(ACELERACION);
  stepper.setSpeed(VELOCIDAD);
}

void loop() {
  // ESTO SE EJECUTA TODO EL TIEMPO
  // El ESP32 está escuchando si llega una orden por el cable USB
  if (Serial.available() > 0) {
    char comando = Serial.read();
    
    if (comando == 'S') { // Si Python manda una 'S' (Start)
      realizarGiroCompleto();
    }
  }
}

void realizarGiroCompleto() {
  digitalWrite(ENABLE_PIN, LOW); // Activar motor (LOW suele ser ON)
  
  // Prepara el movimiento
  stepper.move(PASOS_POR_VUELTA);
  
  // Bucle bloqueante: No hace nada más hasta terminar de girar
  while (stepper.distanceToGo() != 0) {
    stepper.setSpeed(VELOCIDAD); 
    stepper.runSpeedToPosition();
  }
  
  digitalWrite(ENABLE_PIN, HIGH); // Apagar motor (para que no caliente)
  Serial.println("STOP"); // Le grita a Python: "¡YA TERMINÉ!"
}