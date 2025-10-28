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

        # Mapeo de coordenadas actualizado (ya en 1920x1080)
        coordenadas_digitos = {
            # SISTÓLICA (abc) - COORDENADAS ACTUALIZADAS
            "a": [
                (808,611,824,680),  # a1
                (749,676,815,695),  # a2 (corregido)
                (678,677,742,695),  # a3 (corregido)
                (664,611,683,675),  # a4 (corregido)
                (673,589,740,611),  # a5
                (752,592,812,609),  # a6
                (736,612,751,666)   # a7
            ],
            "b": [
                (808,743,823,810),  # b1 (corregido)
                (754,809,812,826),  # b2 (corregido)
                (679,806,745,824),  # b3 (corregido)
                (673,744,689,806),  # b4
                (681,724,742,741),  # b5
                (757,726,813,743),  # b6
                (739,748,757,797)   # b7
            ],
            "c": [
                (808,877,825,950),  # c1 (corregido)
                (744,935,805,952),  # c2 (corregido)
                (678,932,740,951),  # c3 (corregido)
                (667,866,683,927),  # c4
                (674,853,744,870),  # c5
                (749,850,820,869),  # c6
                (737,878,756,929)   # c7
            ],
            # DIASTÓLICA (def) - COORDENADAS ACTUALIZADAS
            "d": [
                (625,604,642,670),  # d1 (corregido)
                (564,658,628,677),  # d2 (corregido)
                (498,657,562,674),  # d3 (corregido)
                (493,596,510,653),  # d4
                (508,585,567,604),  # d5
                (574,587,637,602),  # d6
                (555,609,574,654)   # d7
            ],
            "e": [
                (628,729,645,795),  # e1 (corregido)
                (564,786,627,803),  # e2 (corregido)
                (503,781,558,798),  # e3 (corregido)
                (503,721,519,778),  # e4
                (511,703,572,722),  # e5
                (582,705,640,724),  # e6
                (564,729,578,773)   # e7
            ],
            "f": [
                (632,855,650,917),  # f1 (corregido)
                (578,908,632,927),  # f2 (corregido)
                (518,906,571,925),  # f3 (corregido)
                (505,840,523,905),  # f4
                (515,826,571,841),  # f5
                (586,829,639,844),  # f6
                (569,850,583,901)   # f7
            ],
            # BPM (ghi) - COORDENADAS ACTUALIZADAS
            "g": [
                (440,720,481,737),  # g1 (corregido)
                (392,719,430,738)   # g2 (corregido)
            ],
            "h": [
                (469,765,483,821),  # h1
                (427,808,474,821),  # h2
                (384,806,424,822),  # h3
                (384,758,399,799),  # h4
                (394,744,433,760),  # h5
                (442,749,483,761),  # h6
                (428,763,440,800)   # h7
            ],
            "i": [
                (471,846,483,902),  # i1
                (432,892,479,906),  # i2
                (384,888,427,903),  # i3
                (377,843,389,885),  # i4
                (391,836,432,848),  # i5
                (437,836,481,846),  # i6
                (427,855,438,887)   # i7
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

        # Diccionario de números de 7 segmentos (con patrones alternativos para 1)
        num_7seg = {
            (1,1,1,1,1,1,0): 0,
            (0,1,1,0,0,0,0): 1,        # Patrón tradicional del 1
            (0,1,1,1,1,0,0): 1,        # Patrón alternativo 1
            (0,1,1,1,1,0,1): 1,        # Patrón alternativo 2
            (1,1,0,1,1,0,1): 2,
            (1,1,1,1,0,0,1): 3,
            (0,1,1,0,0,1,1): 4,
            (1,0,1,1,0,1,1): 5,
            (1,0,1,1,1,1,1): 6,
            (1,1,1,0,0,0,0): 7,
            (1,1,1,1,1,1,1): 8,
            (1,1,1,1,0,1,1): 9
        }

        # Umbral de activación ajustado
        umbral = 71

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
            
            # Para dígito g (solo 2 segmentos) - manejo especial
            if digito == "g":
                # Para el dígito g que tiene solo 2 segmentos
                # Si ambos segmentos están apagados = 0, patrones específicos
                if segmentos_activos == [0, 0]:
                    resultados[digito] = 0
                elif segmentos_activos == [1, 0]:
                    resultados[digito] = 1
                elif segmentos_activos == [0, 1]:
                    resultados[digito] = 1  # También podría ser 1
                elif segmentos_activos == [1, 1]:
                    resultados[digito] = 1  # Ambos encendidos = 1
                else:
                    resultados[digito] = 0
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
            (resultados["g"] if resultados["g"] is not None else 0) * 100 +
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