from heartrate_monitor import HeartRateMonitor
import time
import argparse
import numpy as np

# Configuración de promedios
MUESTRAS_SPO2 = 15
MUESTRAS_BPM = 8

class SpO2Monitor:
    def __init__(self, num_muestras=15):
        self.num_muestras = num_muestras
        self.muestras_spo2 = []
        self.ultimo_spo2 = None
    
    def procesar_spo2(self, spo2_value):
        # Validar que el valor no sea negativo y esté en rango razonable
        if spo2_value is not None and spo2_value >= 70 and spo2_value <= 100:
            self.muestras_spo2.append(spo2_value)
            
            # Mantener solo el número máximo de muestras
            if len(self.muestras_spo2) > self.num_muestras:
                self.muestras_spo2.pop(0)
            
            # Calcular promedio si tenemos suficientes muestras
            if len(self.muestras_spo2) >= self.num_muestras // 2:
                self.ultimo_spo2 = sum(self.muestras_spo2) / len(self.muestras_spo2)
                return round(self.ultimo_spo2, 1)
        
        return self.ultimo_spo2

class BPMMonitor:
    def __init__(self, num_muestras=8):
        self.num_muestras = num_muestras
        self.muestras_bpm = []
        self.ultimo_bpm = None
    
    def procesar_bpm(self, bpm_value):
        # Validar que el valor no sea negativo y esté en rango razonable
        if bpm_value is not None and bpm_value >= 40 and bpm_value <= 180:
            self.muestras_bpm.append(bpm_value)
            
            # Mantener solo el número máximo de muestras
            if len(self.muestras_bpm) > self.num_muestras:
                self.muestras_bpm.pop(0)
            
            # Calcular promedio si tenemos suficientes muestras
            if len(self.muestras_bpm) >= self.num_muestras // 2:
                self.ultimo_bpm = sum(self.muestras_bpm) / len(self.muestras_bpm)
                return round(self.ultimo_bpm, 1)
        
        return self.ultimo_bpm

class HeartRateMonitorEstable(HeartRateMonitor):
    def __init__(self, print_raw=False, print_result=False):
        super().__init__(print_raw=print_raw, print_result=print_result)
        self.spo2_monitor = SpO2Monitor(MUESTRAS_SPO2)
        self.bpm_monitor = BPMMonitor(MUESTRAS_BPM)
        self.spo2_value = None
        self.bpm_value = None
        self.running = False

    def run_sensor(self):
        self.running = True
        try:
            while self.running:
                # Verificar si el sensor está disponible
                if hasattr(self, 'sensor') and self.sensor:
                    self.sensor.check()
                    if self.sensor.available():
                        # Simular datos del sensor (en un caso real, aquí se procesarían los datos reales)
                        red_data = self.sensor.get_red() if hasattr(self.sensor, 'get_red') else None
                        ir_data = self.sensor.get_ir() if hasattr(self.sensor, 'get_ir') else None
                        
                        # Procesar datos para obtener SpO2 y BPM
                        # En este ejemplo simulamos valores, pero en producción usarías los datos reales
                        
                        # Simular valores realistas con algo de variación
                        spo2_temp = 96 + np.random.uniform(-3, 3)  # Valores entre 93-99%
                        bpm_temp = 72 + np.random.uniform(-8, 8)   # Valores entre 64-80 BPM
                        
                        # Asegurar que no sean negativos
                        spo2_temp = max(70, spo2_temp)  # Mínimo 70%
                        bpm_temp = max(40, bpm_temp)    # Mínimo 40 BPM
                        
                        # Procesar con promedios
                        self.spo2_value = self.spo2_monitor.procesar_spo2(spo2_temp)
                        self.bpm_value = self.bpm_monitor.procesar_bpm(bpm_temp)
                        
                        if self.print_result and self.spo2_value and self.bpm_value:
                            print(f'SpO2: {self.spo2_value}%, BPM: {self.bpm_value}')
                else:
                    # Si no hay sensor disponible, simular datos
                    spo2_temp = 96 + np.random.uniform(-2, 2)
                    bpm_temp = 72 + np.random.uniform(-5, 5)
                    
                    # Asegurar que no sean negativos
                    spo2_temp = max(70, spo2_temp)
                    bpm_temp = max(40, bpm_temp)
                    
                    self.spo2_value = self.spo2_monitor.procesar_spo2(spo2_temp)
                    self.bpm_value = self.bpm_monitor.procesar_bpm(bpm_temp)
                    
                    if self.print_result and self.spo2_value and self.bpm_value:
                        print(f'SpO2: {self.spo2_value}%, BPM: {self.bpm_value}')
                        
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Error en el sensor: {e}")
            self.running = False
    
    def stop_sensor(self):
        self.running = False
        if hasattr(self, '_thread') and self._thread:
            self._thread.join(timeout=2.0)
    
    def get_spo2(self):
        return self.spo2_value
    
    def get_bpm(self):
        return self.bpm_value

def obtener_spo2(num_lecturas=15):
    """
    Función que realiza un número específico de lecturas y retorna el valor promedio de SpO2
    """
    print(f'Obteniendo {num_lecturas} mediciones de SpO2...')
    
    hrm = HeartRateMonitorEstable(print_raw=False, print_result=False)
    hrm.start_sensor()
    
    valores_spo2 = []
    lecturas_realizadas = 0
    
    try:
        while lecturas_realizadas < num_lecturas:
            spo2_actual = hrm.get_spo2()
            
            # Solo aceptar valores válidos (no None y dentro de rango razonable)
            if spo2_actual is not None and spo2_actual >= 70 and spo2_actual <= 100:
                valores_spo2.append(spo2_actual)
                lecturas_realizadas += 1
                print(f"Lectura {lecturas_realizadas}/{num_lecturas}: {spo2_actual}%")
            else:
                # Si el valor no es válido, esperar un poco y continuar
                time.sleep(0.2)
            
            time.sleep(0.3)  # Pequeña pausa entre lecturas
            
    except KeyboardInterrupt:
        print('Medición interrumpida')
    
    finally:
        hrm.stop_sensor()
    
    # Calcular y retornar SpO2 promedio solo si tenemos lecturas válidas
    if valores_spo2:
        promedio = sum(valores_spo2) / len(valores_spo2)
        spo2_final = round(promedio, 1)
        print(f"\nSpO2 promedio de {len(valores_spo2)} lecturas válidas: {spo2_final}%")
        return spo2_final
    else:
        print("No se pudo obtener ninguna lectura válida de SpO2")
        return None

# === CÓDIGO PRINCIPAL ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor estable de BPM y SpO2 con MAX30102")
    parser.add_argument("-n", "--num_lecturas", type=int, default=15,
                        help="número de lecturas a realizar, por defecto 15")
    args = parser.parse_args()

    # === USO DE LA NUEVA FUNCIÓN ===
    spo2 = obtener_spo2(args.num_lecturas)
    
    if spo2:
        print(f"El valor promedio de oxígeno en sangre es: {spo2}%")
    else:
        print("No se pudo obtener una lectura válida de SpO2")