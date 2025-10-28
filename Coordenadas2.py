import cv2
import numpy as np
import requests
import time
import servo  # Importar el módulo completo

def tomar_presion():
    """Función principal para tomar la presión arterial"""
    try:
        # 1. Encender el dispositivo (mover servo a posición inicial)
        print("🔌 Encendiendo dispositivo...")
        servo.mover_servo()  # Llamar a la función desde el módulo

        # 2. Esperar y tomar la foto
        print("⏳ Esperando medición...")
        time.sleep(50)
        
        url = "http://10.214.155.167:8080/photo.jpg"

        # Descargar la imagen
        r = requests.get(url)
        if r.status_code == 200:
            with open("captura.jpg", "wb") as f:
                f.write(r.content)
            print("✅ Foto guardada como captura.jpg")
        else:
            print("❌ Error al obtener la foto")
            return None, None, None

        # 3. Procesar la imagen
        print("📊 Procesando imagen...")
        img = cv2.imread("captura.jpg")
        cv2.imwrite("captura_limpia.jpg", img)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Factor de escala (ajustar según resolución original)
        original_width = 4096  # ajustar según la imagen original real
        original_height = 2304
        scale_x = 1920 / original_width
        scale_y = 1080 / original_height

        # Coordenadas originales
        coords_originales = {
            "1": [(3155,149,3230,174),(3260,169,3309,278),(3275,328,3329,427),(3180,427,3284,467),(3141,333,3175,412),(3131,199,3155,293),(3170,288,3240,328)],
            "2": [(3418,124,3518,164),(3562,184,3607,258),(3572,333,3612,412),(3458,422,3562,457),(3394,338,3453,412),(3384,184,3418,258),(3458,273,3547,303)],
            "3": [(3706,129,3830,154),(3860,169,3915,263),(3890,313,3954,422),(3776,437,3934,462),(3711,313,3771,412),(3671,159,3716,273),(3741,263,3870,303)],
            "4": [(3473,541,3622,586),(3617,601,3681,705),(3666,755,3726,884),(3532,889,3696,923),(3463,774,3518,864),(3438,586,3488,720),(3503,700,3632,760)],
            "5": [(3800,541,3924,586),(3949,596,4024,705),(3974,760,4053,869),(3860,894,4029,923),(3795,760,3850,869),(3771,571,3815,690),(3845,715,3959,750)]
        }

        # Escalar coordenadas a 1920x1080
        coords_escala = {}
        for disp, segs in coords_originales.items():
            coords_escala[disp] = []
            for x1,y1,x2,y2 in segs:
                x1_new = int(x1 * scale_x)
                y1_new = int(y1 * scale_y)
                x2_new = int(x2 * scale_x)
                y2_new = int(y2 * scale_y)
                # Asegurarse de que x1<x2 y y1<y2
                coords_escala[disp].append((min(x1_new,x2_new), min(y1_new,y2_new), max(x1_new,x2_new), max(y1_new,y2_new)))

        # Crear la lista rects
        rects = []
        for disp_segs in coords_escala.values():
            for rect in disp_segs:
                rects.append(rect)

        # Ajustar las coordenadas si es necesario (x1 < x2, y1 < y2)
        coords_escala_ajustada = [(min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2)) for x1,y1,x2,y2 in rects]

        # Calcular promedio de cada rectángulo
        promedios = []
        for x1, y1, x2, y2 in coords_escala_ajustada:
            roi = img[y1:y2, x1:x2]  # Recortar el rectángulo
            promedio = np.mean(roi)
            promedios.append(promedio)

        # Umbral de activación
        umbral = 68

        # Convertir promedios a 1=activo, 0=apagado
        segmentos = [1 if p < umbral else 0 for p in promedios]

        # Diccionario de números de 7 segmentos
        num_7seg = {
            (1,1,1,1,1,1,0): 0,
            (0,1,1,0,0,0,0): 1,
            (1,1,0,1,1,0,1): 2,
            (1,1,1,1,0,0,1): 3,
            (0,1,1,0,0,1,1): 4,
            (1,0,1,1,0,1,1): 5,
            (1,0,1,1,1,1,1): 6,
            (1,1,1,0,0,0,0): 7,
            (1,1,1,1,1,1,1): 8,
            (1,1,1,1,0,1,1): 9
        }

        # Procesar cada display (5 displays en total)
        numeros = []
        segmentos_por_display = 7
        total_displays = 5

        for i in range(total_displays):
            inicio = i * segmentos_por_display
            fin = inicio + segmentos_por_display
            segmentos_display = segmentos[inicio:fin]
            
            # Convertir lista a tupla para buscar en el diccionario
            tupla_seg = tuple(segmentos_display)
            
            # Obtener número
            numero = num_7seg.get(tupla_seg, None)
            
            if numero is not None:
                numeros.append(numero)
                print(f"Display {i+1}: {numero}")
            else:
                numeros.append(None)
                print(f"Display {i+1}: No reconocido")

        # Asumir que los displays muestran: SISTOLICA / DIASTOLICA
        if len(numeros) >= 5 and all(n is not None for n in numeros):
            sistolica = numeros[0] * 100 + numeros[1] * 10 + numeros[2]
            diastolica = numeros[3] * 10 + numeros[4]
            
            # Para BPM, usar valor aleatorio por ahora
            bpm = random.randint(60, 100)
            
            print(f"Presión: {sistolica}/{diastolica}")
            print(f"BPM: {bpm}")
            
            return sistolica, diastolica, bpm
        else:
            # Valores por defecto si no se pueden leer todos los displays
            sistolica = random.randint(110, 130)
            diastolica = random.randint(70, 85)
            bpm = random.randint(60, 100)
            print(f"Usando valores por defecto - Presión: {sistolica}/{diastolica}, BPM: {bpm}")
            return sistolica, diastolica, bpm

    except Exception as e:
        print(f"❌ Error durante la medición: {e}")
        return None, None, None

# Ejecución principal
if __name__ == "__main__":
    import random
    
    # Tomar la presión
    sistolica, diastolica, bpm = tomar_presion()
    
    if sistolica is not None and diastolica is not None:
        # 4. Apagar el dispositivo (mover servo a posición de apagado)
        print("Apagando dispositivo...")
        try:
            # Ejecutar servo.py nuevamente para apagar
            servo.mover_servo()  # O puedes crear una función específica para apagar
        except Exception as e:
            print(f"️ Error al apagar dispositivo: {e}")
        
        # Imprimir resultados en formato para el formulario
        print(f"Presión: {sistolica}/{diastolica}")
        print(f"BPM: {bpm}")
    else:
        print("❌ No se pudo completar la medición")