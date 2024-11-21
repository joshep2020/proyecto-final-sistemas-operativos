import mmap
from collections import deque

# === Clases para Planificación de Procesos ===

class Process:
    def __init__(self, id, time_llegada, time_ejecucion):
        self.id = id
        self.time_llegada = time_llegada
        self.time_ejecucion = time_ejecucion
        self.time_finalizacion = 0
        self.time_retorno = 0
        self.time_espera = 0
        self.remaining_time = time_ejecucion  # Usado para Round Robin

def planificacion_procesos():
    # Solicitar el número de procesos al usuario
    no_procesos = int(input("¿Cuántos procesos desea crear?: "))
    procesos = []

    # Solicitar los tiempos de ejecución y llegada para cada proceso
    for i in range(no_procesos):
        time_ejecucion = int(input(f"Ingrese el tiempo de ejecución del proceso P{i+1}: "))
        time_llegada = int(input(f"Ingrese el tiempo de llegada del proceso P{i+1}: "))
        proceso = Process(id=f'P{i+1}', time_llegada=time_llegada, time_ejecucion=time_ejecucion)
        procesos.append(proceso)

    # Solicitar el algoritmo a usar
    print("\nSeleccione el algoritmo de planificación:")
    print("1. FIFO (First In, First Out)")
    print("2. SJF (Shortest Job First)")
    print("3. Round Robin (RR)")
    opcion = int(input("Ingrese el número del algoritmo (1/2/3): "))

    if opcion == 3:
        quantum = int(input("Ingrese el valor del quantum para Round Robin: "))

    # FIFO
    if opcion == 1:
        procesos.sort(key=lambda p: p.time_llegada)
        time_actual = 0
        for proceso in procesos:
            time_actual = max(time_actual, proceso.time_llegada) + proceso.time_ejecucion
            proceso.time_finalizacion = time_actual
            proceso.time_retorno = proceso.time_finalizacion - proceso.time_llegada
            proceso.time_espera = proceso.time_retorno - proceso.time_ejecucion

    # SJF
    elif opcion == 2:
        procesos.sort(key=lambda p: (p.time_llegada, p.time_ejecucion))
        time_actual = 0
        completados = 0
        while completados < no_procesos:
            procesos_disponibles = [p for p in procesos if p.time_llegada <= time_actual and p.time_finalizacion == 0]
            if procesos_disponibles:
                procesos_disponibles.sort(key=lambda p: p.time_ejecucion)
                proceso_actual = procesos_disponibles[0]
                time_actual += proceso_actual.time_ejecucion
                proceso_actual.time_finalizacion = time_actual
                proceso_actual.time_retorno = proceso_actual.time_finalizacion - proceso_actual.time_llegada
                proceso_actual.time_espera = proceso_actual.time_retorno - proceso_actual.time_ejecucion
                completados += 1
            else:
                time_actual += 1

    # Round Robin
    elif opcion == 3:
        time_actual = 0
        cola = [p for p in procesos if p.time_llegada <= time_actual]
        index = 0

        while cola or any(p.remaining_time > 0 for p in procesos):
            if cola:
                proceso_actual = cola.pop(0)
                if proceso_actual.remaining_time > quantum:
                    time_actual += quantum
                    proceso_actual.remaining_time -= quantum
                    # Agregar procesos que llegaron durante la ejecución
                    cola += [p for p in procesos if p.time_llegada <= time_actual and p.remaining_time > 0 and p not in cola]
                    cola.append(proceso_actual)
                else:
                    time_actual += proceso_actual.remaining_time
                    proceso_actual.remaining_time = 0
                    proceso_actual.time_finalizacion = time_actual
                    proceso_actual.time_retorno = proceso_actual.time_finalizacion - proceso_actual.time_llegada
                    proceso_actual.time_espera = proceso_actual.time_retorno - proceso_actual.time_ejecucion
            else:
                time_actual += 1
                cola += [p for p in procesos if p.time_llegada <= time_actual and p.remaining_time > 0]

    # Mostrar resultados
    print("\nResultado de los procesos:")
    print(f"{'#Proceso':<10}{'Llegada':<10}{'Ejecución':<12}{'Finalización':<15}{'Retorno':<10}{'Espera':<10}")
    total_retorno = 0
    total_espera = 0

    for proceso in procesos:
        print(f"{proceso.id:<10}{proceso.time_llegada:<10}{proceso.time_ejecucion:<12}{proceso.time_finalizacion:<15}{proceso.time_retorno:<10}{proceso.time_espera:<10}")
        total_retorno += proceso.time_retorno
        total_espera += proceso.time_espera

    print("\nEstadísticas:")
    print(f"Tiempo promedio de retorno: {total_retorno / no_procesos:.2f}")
    print(f"Tiempo promedio de espera: {total_espera / no_procesos:.2f}")


# === Clases para Distribución de Memoria ===

class Segmento:
    def __init__(self, nombre, tamano, offset):
        self.nombre = nombre
        self.tamano = tamano
        self.offset = offset

class ProcesoMemoria:
    def __init__(self, id_proceso):
        self.id_proceso = id_proceso
        self.segmentos = []

    def agregar_segmento(self, nombre, tamano):
        offset = sum([s.tamano for s in self.segmentos])
        self.segmentos.append(Segmento(nombre, tamano, offset))

class Memoria:
    def __init__(self, tamano):
        self.tamano = tamano
        self.memoria = mmap.mmap(-1, tamano)
        self.segmentos_memoria = []
        self.historial_acceso = deque()
        self.segmentos_en_memoria = {}

    def agregar_proceso(self, proceso):
        for segmento in proceso.segmentos:
            if self.memoria.tell() + segmento.tamano > self.tamano:
                self.reemplazar_segmento_lru()
            if self.memoria.tell() + segmento.tamano <= self.tamano:
                self.segmentos_memoria.append((proceso.id_proceso, segmento.nombre, segmento.tamano, segmento.offset))
                self.memoria[segmento.offset:segmento.offset + segmento.tamano] = bytearray(segmento.tamano)
                self.historial_acceso.append(segmento.nombre)
                self.segmentos_en_memoria[segmento.nombre] = segmento
            else:
                print(f"Error: No hay suficiente espacio para el segmento {segmento.nombre} del Proceso {proceso.id_proceso}.")
                return False
        return True

    def reemplazar_segmento_lru(self):
        if len(self.historial_acceso) == 0:
            return
        segmento_lru = self.historial_acceso.popleft()
        print(f"Reemplazando el segmento menos recientemente utilizado: {segmento_lru}")
        if segmento_lru in self.segmentos_en_memoria:
            segmento = self.segmentos_en_memoria.pop(segmento_lru)
            self.memoria[segmento.offset:segmento.offset + segmento.tamano] = bytearray(segmento.tamano)

    def mostrar_memoria(self):
        print("Distribución de Memoria:")
        print("=" * 50)
        print(f"{'Proceso':<10} {'Segmento':<15} {'Tamaño (KB)':<15} {'Offset (KB)'}")
        print("-" * 50)
        for proceso_id, segmento_nombre, segmento_tamano, segmento_offset in self.segmentos_memoria:
            print(f"{proceso_id:<10} {segmento_nombre:<15} {segmento_tamano / 1024:<15.2f} {segmento_offset / 1024:<.2f}")
        print("=" * 50)


# === Clases para el Sistema de Archivos ===

class Archivos:
    def __init__(self):
        self.fs = {"": {}}

    def mkdir(self, path):
        dirs = path.split("/")
        current = self.fs[""]
        for d in dirs:
            if d not in current:
                current[d] = {}
            elif not isinstance(current[d], dict):
                print(f"Error: '{d}' ya es un archivo.")
                return
            current = current[d]
        print(f"Directorio '{path}' creado.")

    def touch(self, path):
        *dirs, archivo_nombre = path.split("/")
        current = self.fs[""]
        for d in dirs:
            if d not in current:
                print(f"Error: El directorio '{'/'.join(dirs)}' no existe.")
                return
            current = current[d]

        if archivo_nombre in current:
            print(f"Error: El archivo '{archivo_nombre}' ya existe.")
        else:
            current[archivo_nombre] = ""
            print(f"Archivo '{path}' creado.")

    def rm(self, path):
        *dirs, archivo_nombre = path.split("/")
        current = self.fs[""]
        for d in dirs:
            if d not in current:
                print(f"Error: El directorio '{'/'.join(dirs)}' no existe.")
                return
            current = current[d]
        if archivo_nombre in current:
            del current[archivo_nombre]
            print(f"Archivo '{archivo_nombre}' eliminado.")
        else:
            print(f"Error: El archivo '{archivo_nombre}' no existe.")

    def mostrar(self):
        def mostrar_directorio(directorio, indent=0):
            for key, value in directorio.items():
                print(" " * indent + key)
                if isinstance(value, dict):
                    mostrar_directorio(value, indent + 2)

        mostrar_directorio(self.fs[""])

def sistema_archivos():
    sistema = Archivos()
    while True:
        print("\n1. Crear directorio")
        print("2. Crear archivo")
        print("3. Eliminar archivo")
        print("4. Mostrar estructura de directorios")
        print("5. Salir")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            path = input("Ingrese el path del directorio a crear: ")
            sistema.mkdir(path)
        elif opcion == "2":
            path = input("Ingrese el path del archivo a crear: ")
            sistema.touch(path)
        elif opcion == "3":
            path = input("Ingrese el path del archivo a eliminar: ")
            sistema.rm(path)
        elif opcion == "4":
            sistema.mostrar()
        elif opcion == "5":
            break
        else:
            print("Opción no válida.")

def main():
    print("Bienvenido al sistema operativo simulado")
    while True:
        print("\nSeleccione una opción:")
        print("1. Planificación de procesos")
        print("2. Gestión de memoria")
        print("3. Sistema de archivos")
        print("4. Salir")
        opcion = input("Ingrese su elección: ")

        if opcion == "1":
            planificacion_procesos()
        elif opcion == "2":
            memoria = Memoria(tamano=1024 * 10)  # Ejemplo con 10 KB de memoria
            procesos_memoria = [ProcesoMemoria(id_proceso=f"P{i+1}") for i in range(3)]

            # Agregar segmentos a los procesos
            procesos_memoria[0].agregar_segmento("segmento1", 512)
            procesos_memoria[1].agregar_segmento("segmento2", 256)
            procesos_memoria[2].agregar_segmento("segmento3", 128)

            for proceso in procesos_memoria:
                memoria.agregar_proceso(proceso)

            memoria.mostrar_memoria()
        elif opcion == "3":
            sistema_archivos()
        elif opcion == "4":
            break
        else:
            print("Opción no válida.")

# Ejecutar el programa principal
if __name__ == "__main__":
    main()
