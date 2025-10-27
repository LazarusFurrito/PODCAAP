import lgpio
import time

def leer_distancia_promedio():
    """
    Versión simple que lee 100 muestras en 10 segundos y calcula 196 - promedio
    """
    # Configuración de pines
    TRIG_PIN = 23
    ECHO_PIN = 24
    
    try:
        # Inicializar GPIO
        h = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(h, TRIG_PIN)
        lgpio.gpio_claim_input(h, ECHO_PIN)
        
        print("Realizando 100 lecturas de distancia en 10 segundos...")
        lecturas_cm = []
        inicio = time.time()
        
        for i in range(100):
            try:
                # Generar pulso de trigger
                lgpio.gpio_write(h, TRIG_PIN, 0)
                time.sleep(0.000002)  # 2μs
                lgpio.gpio_write(h, TRIG_PIN, 1)
                time.sleep(0.00001)   # 10μs
                lgpio.gpio_write(h, TRIG_PIN, 0)
                
                # Medir tiempo de eco
                timeout = time.time() + 0.1  # Timeout de 100ms
                
                # Esperar inicio del eco
                while lgpio.gpio_read(h, ECHO_PIN) == 0:
                    if time.time() > timeout:
                        raise Exception("Timeout esperando inicio de eco")
                    time.sleep(0.000001)  # 1μs
                
                inicio_eco = time.time()
                
                # Esperar fin del eco
                timeout = time.time() + 0.1  # Reset timeout
                while lgpio.gpio_read(h, ECHO_PIN) == 1:
                    if time.time() > timeout:
                        raise Exception("Timeout esperando fin de eco")
                    time.sleep(0.000001)  # 1μs
                
                fin_eco = time.time()
                
                # Calcular distancia en cm
                duracion = fin_eco - inicio_eco
                distancia_cm = (duracion * 34300) / 2  # Velocidad del sonido 34300 cm/s
                
                # Filtrar lecturas fuera de rango (2-400 cm)
                if 2 <= distancia_cm <= 400:
                    lecturas_cm.append(distancia_cm)
                else:
                    print(f"Lectura {i+1} fuera de rango: {distancia_cm:.2f} cm")
                    continue
                
                # Mostrar progreso
                if (i + 1) % 10 == 0:
                    print(f"Lectura {i+1}/100 completada - Distancia: {distancia_cm:.2f} cm")
                
                # Controlar tiempo total para completar en 10 segundos
                transcurrido = time.time() - inicio
                tiempo_restante = 10.0 - transcurrido
                if tiempo_restante > 0 and i < 99:
                    tiempo_espera = tiempo_restante / (100 - i - 1)
                    time.sleep(min(tiempo_espera, 0.08))  # Máximo 80ms de espera
                    
            except Exception as e:
                print(f"Error en lectura {i+1}: {e}")
                continue
        
        # Calcular resultado final
        if lecturas_cm:
            promedio_cm = sum(lecturas_cm) / len(lecturas_cm)
            resultado = 196 - promedio_cm
            tiempo_total = time.time() - inicio
            
            print(f"\n--- RESULTADOS ---")
            print(f"Tiempo total: {tiempo_total:.2f}s")
            print(f"Lecturas válidas: {len(lecturas_cm)}/100")
            print(f"Promedio distancia: {promedio_cm:.2f} cm")
            print(f"Cálculo: 196 - {promedio_cm:.2f} = {resultado:.2f}")
            
            return round(resultado, 2)
        else:
            print("No se obtuvieron lecturas válidas")
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
    resultado = leer_distancia_promedio()
    if resultado is not None:
        print(f"\nRESULTADO FINAL: {resultado:.2f}")
    else:
        print("Error en la medición")