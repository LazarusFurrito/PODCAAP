import lgpio
import time

def leer_peso_kg_simple():
    """
    Versión simple que solo lee el peso en KG con 100 muestras
    """
    # Configuración de pines
    DOUT_PIN = 5
    PD_SCK_PIN = 6
    
    # Factor de corrección basado en tus datos
    # 97kg real = 2318.39g leído → factor = 2318.39 / 97 = 23.89
    FACTOR_CORRECCION = 23.89
    
    try:
        # Inicializar HX711
        h = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_input(h, DOUT_PIN)
        lgpio.gpio_claim_output(h, PD_SCK_PIN)
        
        print("Realizando 100 lecturas en 10 segundos...")
        lecturas_kg = []
        inicio = time.time()
        
        for i in range(100):
            try:
                # Esperar hasta que el sensor esté listo
                timeout = time.time() + 0.5
                while lgpio.gpio_read(h, DOUT_PIN) != 0:
                    if time.time() > timeout:
                        raise Exception("Timeout")
                    time.sleep(0.001)
                
                # Leer los 24 bits de datos
                data = 0
                for j in range(24):
                    lgpio.gpio_write(h, PD_SCK_PIN, 1)
                    lgpio.gpio_write(h, PD_SCK_PIN, 0)
                    bit = lgpio.gpio_read(h, DOUT_PIN)
                    data = (data << 1) | bit
                
                # Configurar ganancia
                for j in range(128):
                    lgpio.gpio_write(h, PD_SCK_PIN, 1)
                    lgpio.gpio_write(h, PD_SCK_PIN, 0)
                
                # Convertir a signed integer
                if data & 0x800000:
                    data = data - 0x1000000
                
                # Aplicar corrección directa a KG
                peso_kg = (data / FACTOR_CORRECCION) / 1000.0
                peso_kg = max(0, peso_kg)  # Evitar negativos
                
                lecturas_kg.append(peso_kg)
                
                # Mostrar progreso
                if (i + 1) % 10 == 0:
                    print(f"Lectura {i+1}/100 completada")
                
                # Controlar tiempo total
                transcurrido = time.time() - inicio
                tiempo_restante = 10.0 - transcurrido
                if tiempo_restante > 0 and i < 99:
                    tiempo_espera = tiempo_restante / (100 - i - 1)
                    time.sleep(min(tiempo_espera, 0.1))
                    
            except Exception as e:
                print(f"Error en lectura {i+1}: {e}")
                continue
        
        # Calcular resultado
        if lecturas_kg:
            promedio_kg = sum(lecturas_kg) / len(lecturas_kg)
            tiempo_total = time.time() - inicio
            print(f"Tiempo total: {tiempo_total:.2f}s")
            print(f"Lecturas válidas: {len(lecturas_kg)}/100")
            return round(promedio_kg, 2)
        else:
            return None
            
    except Exception as e:
        print(f"Error general: {e}")
        return None
    finally:
        try:
            lgpio.gpiochip_close(h)
        except:
            pass

# Uso directo
if __name__ == "__main__":
    peso = leer_peso_kg_simple()
    if peso is not None:
        print(f"\nRESULTADO: {peso:.2f} kg")
    else:
        print("Error en la medición")