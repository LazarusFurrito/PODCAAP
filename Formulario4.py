import sys
import random
import string
import subprocess
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QMessageBox, QGridLayout, QDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class WorkerThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    status = pyqtSignal(str)

    def run(self):
        try:
            self.status.emit("Activando servo...")
            subprocess.run(['python', 'servo.py'], check=True)
            
            self.status.emit("Realizando medición...")
            self.msleep(3000)  # Esperar 3 segundos
            
            # Generar presión simulada
            sistolica = random.randint(110, 130)
            diastolica = random.randint(70, 85)
            presion = f"{sistolica}/{diastolica}"
            
            self.finished.emit(presion)
            
        except subprocess.CalledProcessError as e:
            self.error.emit(f"Error al activar el dispositivo: {e}")
        except FileNotFoundError:
            self.error.emit("No se encontró el archivo servo.py")
        except Exception as e:
            self.error.emit(f"Error inesperado: {e}")


# 🔹 NUEVO THREAD PARA LLAMAR A rotador2.py 🔹
class RotadorThread(QThread):
    finished = pyqtSignal(float)
    error = pyqtSignal(str)

    def run(self):
        try:
            result = subprocess.run(
                ['python3', 'leer_valor.py'], capture_output=True, text=True, check=True
            )
            # Extraer el valor final de la salida
            for line in result.stdout.splitlines():
                if "Valor final leído" in line:
                    valor = float(line.split(":")[-1].strip())
                    self.finished.emit(valor)
                    return
            raise ValueError("No se encontró el valor en la salida.")
        except Exception as e:
            self.error.emit(str(e))


class FormularioMedico(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Formulario médico")
        self.setFixedSize(500, 500)
        
        layout = QGridLayout()
        layout.setSpacing(10)
        
        self.campos = {}
        campos_config = [
            ("Nombre:", "name"),
            ("Segundo nombre:", "name2"), 
            ("Apellidos:", "lastname"),
            ("Altura (cm):", "height"),
            ("Peso (kg):", "weight"),
            ("Temperatura (C°):", "temperature"),
            ("Cintura (cm):", "waist"),
            ("Cadera (cm):", "hip")
        ]
        
        # Crear entradas básicas
        for i, (label_text, key) in enumerate(campos_config):
            label = QLabel(label_text)
            entry = QLineEdit()
            layout.addWidget(label, i, 0)
            
            # --- Agregar botón en Cintura y Cadera ---
            if key in ["waist", "hip"]:
                boton = QPushButton("Medir")
                boton.setStyleSheet("background-color: #2e86de; color: white; font-weight: bold;")
                boton.clicked.connect(lambda _, campo=entry: self.obtener_medida_rotador(campo))
                
                hbox = QHBoxLayout()
                hbox.addWidget(entry)
                hbox.addWidget(boton)
                layout.addLayout(hbox, i, 1)
            else:
                layout.addWidget(entry, i, 1)
            
            self.campos[key] = entry
        
        # --- Campo de presión arterial con botón ---
        pressure_label = QLabel("Presión arterial (mm/Hg):")
        self.pressure_entry = QLineEdit()
        self.pressure_btn = QPushButton("Medir Presión")
        self.pressure_btn.clicked.connect(self.obtener_presion)
        
        pressure_layout = QHBoxLayout()
        pressure_layout.addWidget(self.pressure_entry)
        pressure_layout.addWidget(self.pressure_btn)
        
        layout.addWidget(pressure_label, len(campos_config), 0)
        layout.addLayout(pressure_layout, len(campos_config), 1)
        
        # ID de registro
        id_label = QLabel("ID de Registro:")
        self.id_entry = QLineEdit()
        self.id_entry.setReadOnly(True)
        id_registro = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        self.id_entry.setText(id_registro)
        
        layout.addWidget(id_label, len(campos_config) + 1, 0)
        layout.addWidget(self.id_entry, len(campos_config) + 1, 1)
        
        # Botón enviar
        submit_btn = QPushButton("Enviar Formulario")
        submit_btn.clicked.connect(self.submit_form)
        submit_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        
        layout.addWidget(submit_btn, len(campos_config) + 2, 0, 1, 2)
        self.setLayout(layout)
        self.campos["name"].setFocus()

    # --- Nueva función para medir con rotador2.py ---
    def obtener_medida_rotador(self, campo):
        campo.setText("Midiendo...")
        self.rotador_thread = RotadorThread()
        self.rotador_thread.finished.connect(lambda valor: self.mostrar_valor_rotador(campo, valor))
        self.rotador_thread.error.connect(self.error_rotador)
        self.rotador_thread.start()

    def mostrar_valor_rotador(self, campo, valor):
        campo.setText(f"{valor:.2f}")
        QMessageBox.information(self, "Medición completa", f"Medida registrada: {valor:.2f} cm")

    def error_rotador(self, mensaje):
        QMessageBox.critical(self, "Error", f"No se pudo leer el valor del rotador:\n{mensaje}")

    # --- Presión (sin cambios) ---
    def obtener_presion(self):
        self.pressure_btn.setEnabled(False)
        self.pressure_btn.setText("Midiendo...")
        self.pressure_entry.setText("Coloque el brazalete...")
        
        self.worker = WorkerThread()
        self.worker.finished.connect(self.medicion_completada)
        self.worker.error.connect(self.medicion_error)
        self.worker.status.connect(self.actualizar_estado)
        self.worker.start()
        
    def actualizar_estado(self, mensaje):
        self.pressure_entry.setText(mensaje)
        
    def medicion_completada(self, presion):
        self.pressure_entry.setText(presion)
        self.pressure_btn.setEnabled(True)
        self.pressure_btn.setText("Medir Presión")
        QMessageBox.information(self, "Medición Completa", f"Presión medida: {presion} mm/Hg")
        
    def medicion_error(self, mensaje_error):
        self.pressure_btn.setEnabled(True)
        self.pressure_btn.setText("Medir Presión")
        self.pressure_entry.clear()
        QMessageBox.critical(self, "Error", mensaje_error)
        
    def submit_form(self):
        for key, campo in self.campos.items():
            print(f"{key}: {campo.text()}")
        print(f"Pressure: {self.pressure_entry.text()}")
        print(f"ID: {self.id_entry.text()}")
        QMessageBox.information(self, "Éxito", "Registro médico creado correctamente")
        self.accept()



class MenuRegistros(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Sistema de Registros Médicos")
        self.setFixedSize(400, 400)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # Título
        titulo = QLabel("Menú Principal")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(titulo)
        
        # Botones del menú
        botones = [
            ("1. Crear Registro", self.crear_registro),
            ("2. Modificar Registro", self.modificar_registro),
            ("3. Eliminar Registro", self.eliminar_registro),
            ("4. Buscar Registro", self.buscar_registro),
            ("5. Salir", self.salir)
        ]
        
        for texto, funcion in botones:
            boton = QPushButton(texto)
            boton.setFixedSize(200, 50)
            if texto == "5. Salir":
                boton.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; font-weight: bold; }")
            else:
                boton.setStyleSheet("QPushButton { background-color: #4e73df; color: white; font-weight: bold; }")
            boton.clicked.connect(funcion)
            layout.addWidget(boton, alignment=Qt.AlignCenter)
        
        central_widget.setLayout(layout)
        
    def crear_registro(self):
        formulario = FormularioMedico(self)
        formulario.exec_()  # Esto hace que sea modal
        
    def modificar_registro(self):
        QMessageBox.information(self, "Información", "Función 'Modificar Registro' no implementada aún")
        
    def eliminar_registro(self):
        QMessageBox.information(self, "Información", "Función 'Eliminar Registro' no implementada aún")
        
    def buscar_registro(self):
        QMessageBox.information(self, "Información", "Función 'Buscar Registro' no implementada aún")
        
    def salir(self):
        respuesta = QMessageBox.question(self, "Salir", "¿Está seguro que desea salir?")
        if respuesta == QMessageBox.Yes:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Estilo moderno
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f8f9fc;
        }
        QPushButton {
            border: none;
            border-radius: 5px;
            padding: 10px;
            font-size: 14px;
        }
        QPushButton:hover {
            opacity: 0.9;
        }
        QLineEdit {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        QLabel {
            font-size: 14px;
            font-weight: bold;
        }
    """)
    
    ventana = MenuRegistros()
    ventana.show()
    sys.exit(app.exec_())