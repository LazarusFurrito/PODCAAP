import cv2
import numpy as np
import requests
import time
import servo  # Importar el módulo completo
import random

def tomar_presion():
    """Función principal para tomar la presión arterial"""
    try:
        # 1. Encender el dispositivo (mover servo a posición inicial)
        print("Encendiendo dispositivo...")
        servo.mover_servo()  # Llamar a la función desde el módulo

        # 2. Esperar y tomar la foto
        print("Esperando medición...")
        time.sleep(50)
        
        url = "http://10.214.155.167:8080/photo.jpg"

        # Descargar la imagen
        r = requests.get(url)
        if r.status_code == 200:
            with open("captura.jpg", "wb") as f:
                f.write(r.content)
            print("Foto guardada como captura.jpg")
        else:
            print("Error al obtener la foto")
            return None, None, None

        # 3. Procesar la imagen
        print("Procesando imagen...")
        img = cv2.imread("captura.jpg")
        cv2.imwrite("captura_limpia.jpg", img)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Mapeo de coordenadas según el nuevo mapa (ya en 1920x1080)
        # Cada dígito tiene 7 segmentos (excepto g que tiene 1)
        coordenadas_digitos = {
            # SISTÓLICA (abc)
            "a": [
                (795,463,815,505),  # a1
                (761,514,800,529),  # a2
                (689,515,732,529),  # a3
                (671,470,683,507),  # a4
                (686,446,720,459),  # a5
                (756,446,798,454),  # a6
                (728,471,751,504)   # a7
            ],
            "b": [
                (808,600,822,641),  # b1
                (761,646,808,658),  # b2
                (701,644,737,661),  # b3
                (674,592,695,631),  # b4
                (691,570,740,587),  # b5
                (752,568,798,582),  # b6
                (740,595,757,637)   # b7
            ],
            "c": [
                (820,722,832,773),  # c1
                (771,766,813,783),  # c2
                (705,771,749,785),  # c3
                (684,721,696,763),  # c4
                (703,700,747,710),  # c5
                (762,700,820,715),  # c6
                (751,726,764,763)   # c7
            ],
            # DIASTÓLICA (def)
            "d": [
                (620,459,639,509),  # d1
                (583,519,628,539),  # d2
                (527,526,557,536),  # d3
                (501,475,520,514),  # d4
                (522,453,564,465),  # d5
                (581,451,613,463),  # d6
                (562,471,578,512)   # d7
            ],
            "e": [
                (630,583,645,636),  # e1
                (591,646,630,660),  # e2
                (533,641,566,658),  # e3
                (506,597,523,632),  # e4
                (516,575,564,588),  # e5
                (593,570,625,582),  # e6
                (572,593,584,643)   # e7
            ],
            "f": [
                (635,715,654,761),  # f1
                (596,766,627,785),  # f2
                (537,768,576,778),  # f3
                (522,717,537,753),  # f4
                (532,697,572,709),  # f5
                (591,700,632,710),  # f6
                (581,712,593,758)   # f7
            ],
            # BPM (ghi) - g tiene solo 1 segmento
            "g": [
                (396,595,471,607)   # g (solo 1 segmento)
            ],
            "h": [
                (472,644,489,676),  # h1
                (450,680,474,692),  # h2
                (421,683,442,690),  # h3
                (393,644,408,678),  # h4
                (410,627,435,637),  # h5
                (449,629,474,639),  # h6
                (435,644,447,675)   # h7
            ],
            "i": [
                (483,729,494,761),  # i1
                (460,768,494,777),  # i2
                (416,761,445,775),  # i3
                (405,722,418,749),  # i4
                (420,712,444,722),  # i5
                (455,712,481,724),  # i6
                (444,727,459,760)   # i7
            ]
        }

        # Asegurar que las coordenadas estén en el orden correcto (x1 < x2, y1 < y2)
        coords_ajustadas = {}
        for digito, segmentos in coordenadas_digitos.items():
            coords_ajustadas[digito] = []
            for x1, y1, x2, y2 in segmentos:
                coords_ajustadas[digito].append((
                    min(x1, x2), 
                    min(y1, y2), 
                    max(x1, x2), 
                    max(y1, y2)
                ))

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

        # Umbral de activación
        umbral = 68

        # Procesar cada dígito
        resultados = {}
        
        for digito, segmentos_coords in coords_ajustadas.items():
            segmentos_activos = []
            valores_promedio = []
            
            for x1, y1, x2, y2 in segmentos_coords:
                roi = img[y1:y2, x1:x2]
                promedio = np.mean(roi)
                valores_promedio.append(promedio)
                # 1 = activo (oscuro), 0 = apagado (claro)
                segmentos_activos.append(1 if promedio < umbral else 0)
            
            # Mostrar valores previos al umbral
            print(f"Digito {digito}:")
            print(f"  Promedios: {[f'{v:.1f}' for v in valores_promedio]}")
            print(f"  Estados: {segmentos_activos}")
            
            # Para dígito g (solo 1 segmento)
            if digito == "g":
                # Si el segmento está activo, es 1; si no, es 0
                resultados[digito] = 1 if segmentos_activos[0] == 1 else 0
                print(f"  Resultado: {resultados[digito]}")
            else:
                # Para dígitos de 7 segmentos
                tupla_seg = tuple(segmentos_activos)
                numero = num_7seg.get(tupla_seg, None)
                resultados[digito] = numero
                print(f"  Resultado: {resultados[digito]}")
            
            print()  # Línea en blanco para separar

        # Construir los valores finales
        # SISTÓLICA: abc (3 dígitos)
        sistolica = (
            (resultados["a"] if resultados["a"] is not None else 0) * 100 +
            (resultados["b"] if resultados["b"] is not None else 0) * 10 +
            (resultados["c"] if resultados["c"] is not None else 0)
        )
        
        # DIASTÓLICA: def (3 dígitos)
        diastolica = (
            (resultados["d"] if resultados["d"] is not None else 0) * 100 +
            (resultados["e"] if resultados["e"] is not None else 0) * 10 +
            (resultados["f"] if resultados["f"] is not None else 0)
        )
        
        # BPM: ghi (3 dígitos)
        bpm = (
            resultados["g"] * 100 +  # g siempre es 0 o 1
            (resultados["h"] if resultados["h"] is not None else 0) * 10 +
            (resultados["i"] if resultados["i"] is not None else 0)
        )

        print("RESULTADOS FINALES:")
        print(f"   Sistolica: {sistolica}")
        print(f"   Diastolica: {diastolica}")
        print(f"   BPM: {bpm}")
        
        return sistolica, diastolica, bpm

    except Exception as e:
        print(f"Error durante la medicion: {e}")
        return None, None, None

# Ejecución principal
if __name__ == "__main__":
    # Tomar la presión
    sistolica, diastolica, bpm = tomar_presion()
    
    if sistolica is not None and diastolica is not None:
        # 4. Apagar el dispositivo (mover servo a posición de apagado)
        print("Apagando dispositivo...")
        try:
            servo.mover_servo()  # O puedes crear una función específica para apagar
        except Exception as e:
            print(f"Error al apagar dispositivo: {e}")
        
        # Imprimir resultados finales
        print("MEDICION COMPLETADA:")
        print(f"   Presion: {sistolica}/{diastolica}")
        print(f"   BPM: {bpm}")
    else:
        print("No se pudo completar la medicion")