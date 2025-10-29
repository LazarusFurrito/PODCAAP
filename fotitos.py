import cv2
import numpy as np

# Configuración
THRESHOLD = 85

# Patrones de dígitos para 7 segmentos
DIGIT_PATTERNS = {
    (0, 0, 0, 0, 0, 0, 1): '0',
    (1, 0, 0, 1, 1, 1, 1): '1', 
    (0, 0, 1, 0, 0, 1, 0): '2',
    (0, 0, 0, 0, 1, 1, 0): '3',
    (1, 0, 0, 1, 1, 0, 0): '4',
    (0, 1, 0, 0, 1, 0, 0): '5',
    (0, 1, 0, 0, 0, 0, 0): '6',
    (0, 0, 0, 1, 1, 0, 1): '7',
    (0, 0, 0, 0, 0, 0, 0): '8',
    (0, 0, 0, 0, 1, 0, 0): '9'
}

def check_segment(image, coords, threshold=85):
    """Verifica si un segmento está encendido y retorna el valor promedio"""
    x1, y1, x2, y2 = coords
    segment_roi = image[y1:y2, x1:x2]
    
    if segment_roi.size == 0:
        return 0, 0
    
    avg_intensity = np.mean(segment_roi)
    is_on = 1 if avg_intensity > threshold else 0
    
    return is_on, avg_intensity

def recognize_digit(image, segments_coords, threshold=200):
    """Reconoce un dígito y muestra los promedios de cada segmento"""
    segment_states = []
    segment_values = []
    
    print("Segmentos (estado, valor promedio):")
    for i, coords in enumerate(segments_coords, 1):
        is_on, avg_val = check_segment(image, coords, threshold)
        segment_states.append(is_on)
        segment_values.append(avg_val)
        print(f"  Segmento {i}: {is_on} - {avg_val:.1f}")
    
    segment_tuple = tuple(segment_states)
    
    if segment_tuple in DIGIT_PATTERNS:
        digit = DIGIT_PATTERNS[segment_tuple]
    else:
        digit = '?'
    
    print(f"Dígito reconocido: {digit}")
    print("-" * 40)
    return digit

# Coordenadas organizadas por grupos
sistolica_coords = [
    [(811,98,816,137), (761,151,807,165), (692,156,736,167), (678,107,688,147), (692,87,739,97), (758,85,797,94), (743,98,751,140)],  # Dígito 1
    [(811,218,828,267), (770,278,809,290), (705,285,746,295), (680,230,695,267), (695,209,733,217), (767,208,806,216), (744,222,760,261)],  # Dígito 2
    [(816,346,831,402), (770,406,811,416), (707,409,744,419), (683,353,699,400), (704,334,741,346), (768,328,807,345), (741,357,758,394)]   # Dígito 3
]

diastolica_coords = [
    [(628,105,638,154), (595,169,626,174), (531,173,568,179), (514,116,526,161), (524,100,563,108), (592,98,624,105), (568,116,583,158)],  # Dígito 1
    [(634,234,648,272), (599,290,638,305), (532,295,571,307), (515,252,531,286), (531,221,570,236), (592,221,629,233), (573,238,587,280)],  # Dígito 2
    [(641,356,653,395), (602,414,641,426), (545,418,579,426), (524,366,536,398), (532,346,573,354), (595,348,633,351), (583,364,595,402)]   # Dígito 3
]

bpm_coords = [
    [(455,254,477,264)],  # Solo segmento g para primer dígito
    [(483,300,493,326), (458,341,487,351), (419,342,443,351), (404,307,410,332), (410,290,439,297), (461,288,478,296), (441,304,448,334)],  # Dígito 2
    [(488,388,492,415), (463,425,490,432), (421,423,446,432), (410,392,419,413), (417,384,439,386), (461,376,490,384), (446,389,453,415)]   # Dígito 3
]

# Procesar imagen
img = cv2.imread('captura_limpia_cel.jpg')
if img is None:
    print("Error: No se pudo cargar la imagen")
    exit()

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

print("=== PRESIÓN SISTÓLICA ===")
sistolica = ""
for i, digit_segments in enumerate(sistolica_coords, 1):
    print(f"\nDígito {i}:")
    digit = recognize_digit(gray, digit_segments, THRESHOLD)
    sistolica += digit

print("\n=== PRESIÓN DIASTÓLICA ===")
diastolica = ""
for i, digit_segments in enumerate(diastolica_coords, 1):
    print(f"\nDígito {i}:")
    digit = recognize_digit(gray, digit_segments, THRESHOLD)
    diastolica += digit

print("\n=== PULSACIONES (BPM) ===")
bpm = ""

# Primer dígito BPM (solo segmento g)
print("\nPrimer dígito BPM (solo segmento g):")
is_on, avg_val = check_segment(gray, bpm_coords[0][0], THRESHOLD)
print(f"Segmento g: {is_on} - {avg_val:.1f}")
bpm += '1' if is_on else '0'
print(f"Dígito reconocido: {'1' if is_on else '0'}")

# Resto de dígitos BPM
for i, digit_segments in enumerate(bpm_coords[1:], 2):
    print(f"\nDígito {i}:")
    digit = recognize_digit(gray, digit_segments, THRESHOLD)
    bpm += digit

print("\n" + "="*50)
print("RESULTADOS FINALES:")
print(f"Presión sistólica: {sistolica}")
print(f"Presión diastólica: {diastolica}") 
print(f"Pulsaciones (BPM): {bpm}")