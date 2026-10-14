# TPO - Programación III - Juan Cruz Rocca 
import json
import math
import os
import sys

# Variables de interés
LIBRE = 0
OBSTACULO = 1
PROHIBIDA = 2

ORIENTACIONES = ["NORTE", "ESTE", "SUR", "OESTE"]

# El orden es el de desempate
MOVIMIENTOS = [
    ("ARRIBA", -1, 0),
    ("DERECHA", 0, 1),
    ("ABAJO", 1, 0),
    ("IZQUIERDA", 0, -1),
]

# Estados posibles
DESTINO_ALCANZADO = "DESTINO_ALCANZADO"
BLOQUEADO = "BLOQUEADO"
LIMITE_DE_PASOS = "LIMITE_DE_PASOS"

DESCRIPCION_CAUSA = {
    DESTINO_ALCANZADO: "El robot llego a la celda destino.",
    BLOQUEADO: "No existen candidatos validos para continuar.",
    LIMITE_DE_PASOS: "Se alcanzo el maximo de pasos permitido.",
}

# Flecha que se dibuja segun hacia donde se mueve el robot desde esa celda
FLECHAS = {"NORTE": "^", "ESTE": ">", "SUR": "v", "OESTE": "<"}

# Carpeta donde esta este archivo (asi funciona sin importar desde donde se ejecute)
CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))


# Validación y carga del mapa

def dentro_de_grilla(grilla, fila, columna):
    return 0 <= fila < len(grilla) and 0 <= columna < len(grilla[0]) # Como son cuadradas funciona con cualquier [x]


def validar_mapa(mapa):
    campos = ["nombre", "grilla", "inicio", "destino",
              "tamano_celda_metros", "orientacion_inicial", "maximo_pasos"]
    for campo in campos:
        if campo not in mapa:
            raise ValueError("Falta el campo '" + campo + "' en el mapa")

    grilla = mapa["grilla"]
    if len(grilla) == 0:
        raise ValueError("La grilla esta vacia")

    cantidad_columnas = len(grilla[0])
    for fila in grilla:
        if len(fila) != cantidad_columnas:
            raise ValueError("Todas las filas de la grilla deben tener el mismo largo")
        for celda in fila:
            if celda not in [LIBRE, OBSTACULO, PROHIBIDA]:
                raise ValueError("La grilla solo puede tener valores 0, 1 o 2")

    # El inicio y el destino tienen que estar dentro de los valores posibles según el mapa
    for x in ["inicio", "destino"]:
        if len(mapa[x]) != 2:
            raise ValueError("'" + x + "' debe tener fila y columna")
        fila = mapa[x][0]
        columna = mapa[x][1]
        if not dentro_de_grilla(grilla, fila, columna):
            raise ValueError("'" + x + "' esta fuera de la grilla")
        if grilla[fila][columna] != LIBRE:
            raise ValueError("'" + x + "' no esta sobre una celda libre")

    if mapa["tamano_celda_metros"] <= 0: 
        raise ValueError("El tamano de celda debe ser mayor que 0")

    if mapa["orientacion_inicial"] not in ORIENTACIONES:
        raise ValueError("Orientacion inicial invalida: " + str(mapa["orientacion_inicial"]))

    if mapa["maximo_pasos"] <= 0:
        raise ValueError("El maximo de pasos debe ser mayor que 0")


def cargar_mapa(ruta_archivo): # Lee el archivo JSON, valida y devuelve como diccionario
    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        mapa = json.load(archivo)

    validar_mapa(mapa)

    ''' 
    PARA ACORDARME: 
    El JSON trae las posiciones como listas [fila, columna].
    Por eso las paso a tuplas porque despues las comparo con las
    posiciones de la ruta, y una lista != tupla SIEMPRE'''


    mapa["inicio"] = tuple(mapa["inicio"])
    mapa["destino"] = tuple(mapa["destino"])
    return mapa


# Greedy y Cirterio Greedy

def distancia_manhattan(posicion, destino):
    return abs(posicion[0] - destino[0]) + abs(posicion[1] - destino[1])


def obtener_candidatos(mapa, posicion, visitadas): # Devuelve la lista de movimientos válidos desde 'posicion' | Cada candidato es una tupla: (nombre_movimiento, fila, columna, distancia)
    grilla = mapa["grilla"]
    candidatos = []

    for nombre, cambio_fila, cambio_columna in MOVIMIENTOS:
        nueva_fila = posicion[0] + cambio_fila
        nueva_columna = posicion[1] + cambio_columna

        # VALIDACIONES
        if not dentro_de_grilla(grilla, nueva_fila, nueva_columna):
            continue

        if grilla[nueva_fila][nueva_columna] != LIBRE:
            continue

        if (nueva_fila, nueva_columna) in visitadas:
            continue
        # Añado a candidatos
        distancia = distancia_manhattan((nueva_fila, nueva_columna), mapa["destino"])
        candidatos.append((nombre, nueva_fila, nueva_columna, distancia))

    return candidatos


def elegir_candidato(candidatos):
   
    if len(candidatos) == 0:
        return None

    mejor = candidatos[0]
    for candidato in candidatos:
        if candidato[3] < mejor[3]:
            mejor = candidato
    return mejor



def describir_candidatos(candidatos): # Solo para debbug/pantalla
    textos = []
    for nombre, fila, columna, distancia in candidatos:
        textos.append(nombre + " (" + str(fila) + "," + str(columna) + ") d=" + str(distancia))
    return ", ".join(textos)

# Algoritmo principal Greedy !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def ejecutar_greedy(mapa, registro=None): # Si se pasa una lista en registro va agregando ahi lo que decide en cada paso.
    posicion = mapa["inicio"]
    ruta = [posicion]

    while True:
        if posicion == mapa["destino"]:
            return ruta, DESTINO_ALCANZADO

        cantidad_movimientos = len(ruta) - 1
        if cantidad_movimientos >= mapa["maximo_pasos"]:
            return ruta, LIMITE_DE_PASOS

        candidatos = obtener_candidatos(mapa, posicion, ruta)
        elegido = elegir_candidato(candidatos)

        if registro is not None:
            texto_paso = "Paso " + str(cantidad_movimientos + 1) + " desde " + str(posicion) + ": "
            if elegido is None:
                registro.append(texto_paso + "sin candidatos validos")
            else:
                registro.append(texto_paso + describir_candidatos(candidatos) + " -> elige " + elegido[0])

        if elegido is None:
            return ruta, BLOQUEADO

        posicion = (elegido[1], elegido[2])
        ruta.append(posicion)


def armar_texto_del_resultado(mapa, ruta, causa): # Pantalla/log que pide la consigna
    textos_ruta = []
    for posicion in ruta:
        textos_ruta.append(str(posicion))

    lineas = []
    lineas.append("Resultado: " + causa)
    lineas.append("Causa: " + DESCRIPCION_CAUSA[causa])
    lineas.append("Movimientos realizados: " + str(len(ruta) - 1))
    lineas.append("Posicion final: " + str(ruta[-1]) + " - Destino: " + str(mapa["destino"]))
    lineas.append("Ruta: " + " -> ".join(textos_ruta))
    return lineas


# ------------------------------- Instrucciones para el robot -----------------------------------------

def hacia_donde_mirar(origen, destino): # Hacia donde tiene que mirar el robot para ir de una celda a la otra
    cambio_fila = destino[0] - origen[0]
    cambio_columna = destino[1] - origen[1]

    if cambio_fila == -1:
        return "NORTE"
    if cambio_fila == 1:
        return "SUR"
    if cambio_columna == 1:
        return "ESTE"
    return "OESTE"


def giro_necesario(orientacion_actual, orientacion_nueva): # Hacia donde debe girar (puede ser None si no necesita hacerlo)
    # Cada giro es una tupla: (nombre_del_giro, grados)
    posicion_actual = ORIENTACIONES.index(orientacion_actual)
    posicion_nueva = ORIENTACIONES.index(orientacion_nueva)

    cuartos_a_la_derecha = (posicion_nueva - posicion_actual) % 4

    if cuartos_a_la_derecha == 0:
        return None
    if cuartos_a_la_derecha == 1:
        return ("GIRAR_DERECHA", 90)
    if cuartos_a_la_derecha == 2:
        return ("GIRAR_DERECHA", 180)
    return ("GIRAR_IZQUIERDA", 90)


def generar_instrucciones(ruta, tamano_celda, orientacion_inicial): # Convierte la ruta (lista de celdas) en una lista de instrucciones que entiende el robot
    # Cada instruccion es una tupla: (accion, valor)
    #   ("AVANZAR", metros)
    #   ("GIRAR_DERECHA", grados) o ("GIRAR_IZQUIERDA", grados)
    instrucciones = []
    orientacion = orientacion_inicial

    for i in range(len(ruta) - 1):
        orientacion_necesaria = hacia_donde_mirar(ruta[i], ruta[i + 1])

        giro = giro_necesario(orientacion, orientacion_necesaria)
        if giro is not None:
            instrucciones.append(giro)

        instrucciones.append(("AVANZAR", tamano_celda))
        orientacion = orientacion_necesaria

    return instrucciones


def formatear_metros(metros): # Solo para debbug/pantalla
    # 0.5 -> "0,50" (dos decimales y coma, como en la consigna)
    return ("%.2f" % metros).replace(".", ",")


def instruccion_a_texto(instruccion): # Pantalla/log que pide la consigna
    # Pasa una instruccion a texto legible, por ejemplo "AVANZAR 0,50 m"
    accion = instruccion[0]
    valor = instruccion[1]

    if accion == "AVANZAR":
        return "AVANZAR " + formatear_metros(valor) + " m"
    if accion == "GIRAR_DERECHA":
        return "GIRAR DERECHA " + str(valor) + " grados"
    return "GIRAR IZQUIERDA " + str(valor) + " grados"


def armar_texto_de_instrucciones(instrucciones): # Pantalla/log que pide la consigna
    lineas = ["Instrucciones para el robot (" + str(len(instrucciones)) + "):"]
    for i in range(len(instrucciones)):
        lineas.append("  " + str(i + 1) + ". " + instruccion_a_texto(instrucciones[i]))
    return lineas



def dibujar_ruta(mapa, ruta): # Pantalla/log que pide la consigna
    # Dibuja la grilla en texto con la ruta recorrida
    grilla = mapa["grilla"]

    # Pasa la grilla a simbolos
    simbolos = []
    for fila in grilla:
        simbolos_fila = []
        for celda in fila:
            if celda == OBSTACULO:
                simbolos_fila.append("#")
            elif celda == PROHIBIDA:
                simbolos_fila.append("X")
            else:
                simbolos_fila.append(".")
        simbolos.append(simbolos_fila)

    # En cada celda de la ruta dibujo una flecha hacia donde se mueve despues
    for i in range(len(ruta) - 1):
        fila = ruta[i][0]
        columna = ruta[i][1]
        simbolos[fila][columna] = FLECHAS[hacia_donde_mirar(ruta[i], ruta[i + 1])]

    # Marco el inicio, la posicion final (si no llego) y el destino
    simbolos[ruta[0][0]][ruta[0][1]] = "I"
    if ruta[-1] != mapa["destino"]:
        simbolos[ruta[-1][0]][ruta[-1][1]] = "F"
    simbolos[mapa["destino"][0]][mapa["destino"][1]] = "D"

    lineas = []
    encabezado = "    "
    for columna in range(len(grilla[0])):
        encabezado = encabezado + str(columna) + " "
    lineas.append(encabezado)
    for fila in range(len(grilla)):
        lineas.append(str(fila) + "   " + " ".join(simbolos[fila]))
    lineas.append("")
    lineas.append("I = inicio | D = destino | F = posicion final (si no llego al destino)")
    lineas.append("^ > v < = hacia donde se mueve desde esa celda | # = obstaculo | X = zona prohibida | . = libre")
    return lineas


def correr_mapa(numero): # Pantalla/log que pide la consigna
    # Corre el planificador sobre un mapa, lo muestra en pantalla y lo guarda en un log
    archivo_mapa = os.path.join(CARPETA_PROYECTO, "mapas", "mapa" + str(numero) + ".json")
    archivo_log = os.path.join(CARPETA_PROYECTO, "salidas", "mapa" + str(numero) + "_log.txt")

    mapa = cargar_mapa(archivo_mapa)
    registro = []
    ruta, causa = ejecutar_greedy(mapa, registro)
    instrucciones = generar_instrucciones(ruta, mapa["tamano_celda_metros"],
                                          mapa["orientacion_inicial"])

    lineas = []
    lineas.append("=" * 60)
    lineas.append(mapa["nombre"])
    lineas.append("=" * 60)
    lineas.append("Inicio: " + str(mapa["inicio"]) + " | Destino: " + str(mapa["destino"])
                  + " | Celda: " + formatear_metros(mapa["tamano_celda_metros"]) + " m"
                  + " | Orientacion inicial: " + mapa["orientacion_inicial"]
                  + " | Maximo de pasos: " + str(mapa["maximo_pasos"]))
    lineas.append("Desempate: ARRIBA -> DERECHA -> ABAJO -> IZQUIERDA")
    lineas.append("")
    lineas.append("Decisiones paso a paso:")
    lineas = lineas + registro
    lineas.append("")
    lineas = lineas + armar_texto_del_resultado(mapa, ruta, causa)
    lineas.append("")
    lineas.append("Representacion de la ruta:")
    lineas = lineas + dibujar_ruta(mapa, ruta)
    lineas.append("")
    lineas = lineas + armar_texto_de_instrucciones(instrucciones)

    for linea in lineas:
        print(linea)

    with open(archivo_log, "w", encoding="utf-8") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    return mapa, ruta, causa, instrucciones


# Variables del Robot o para su uso

# Velocidades con las que se mueve el robot 
VELOCIDAD_AVANCE = 0.25  # metros/segundo
VELOCIDAD_GIRO = 0.5     # radianes/segundo

# El simulador acepta como maximo 10 segundos 
TIEMPO_MAXIMO_ORDEN = 10.0

# Al terminar la ruta (llegue al destino, quede bloqueado o llegue al limite de pasos) el robot gira sobre si mismo esta cantidad de vueltas completas a modo de aviso
VUELTAS_DE_AVISO = 3

# Si es True, ademas de la celda del laberinto se muestra la posicion (x, y) y el angulo que informa el robot despues de cada instruccion
MOSTRAR_ESTADO_ROBOT = False

# Cuanto cambian fila y columna al avanzar una celda mirando hacia cada orientacion
AVANCE_POR_ORIENTACION = {"NORTE": (-1, 0), "ESTE": (0, 1), "SUR": (1, 0), "OESTE": (0, -1)}

# Carpeta del laboratorio donde esta g1_student_api.py (la API del robot)
CARPETA_API_ROBOT = os.path.join(CARPETA_PROYECTO, "UadeRobotLab", "04Simuladores",
                                 "UnitreeMujocoOficial")


def convertir_a_movimiento(instruccion):
    ''' Pasa una instruccion a los datos que necesita robot.movimiento(...).
    Devuelve (adelante, giro, tiempo):
      -adelante: velocidad hacia adelante, en metros por segundo
      -giro: velocidad de giro en radianes por segundo (positivo = izquierda, negativo = derecha)
      -tiempo: cuantos segundos dura el movimiento'''
    accion = instruccion[0]
    valor = instruccion[1]

    if accion == "AVANZAR":
        return (VELOCIDAD_AVANCE, 0.0, valor / VELOCIDAD_AVANCE)

    # Para girar: angulo en radianes = velocidad de giro * tiempo
    radianes = math.radians(valor)
    tiempo = radianes / VELOCIDAD_GIRO
    if accion == "GIRAR_DERECHA":
        return (0.0, -VELOCIDAD_GIRO, tiempo)
    return (0.0, VELOCIDAD_GIRO, tiempo)


def enviar_movimiento(robot, adelante, giro, tiempo):
    # Manda un movimiento al robot. Si dura mas del maximo permitido por orden,lo parte en varias ordenes seguidas
    estado = None
    while tiempo > 0:
        parte = min(tiempo, TIEMPO_MAXIMO_ORDEN)
        estado = robot.movimiento(adelante=adelante, costado=0.0, giro=giro, tiempo=parte)
        tiempo = tiempo - parte
    return estado


def texto_estado(estado): # Solo para debbug/pantalla
    # Posicion x e y en metros y angulo del robot, para mostrar en pantalla
    return ("robot en x = %.2f m, y = %.2f m, angulo = %.0f grados"
            % (estado.x, estado.y, math.degrees(estado.yaw)))


def seguir_posicion_en_laberinto(mapa, instrucciones): # Solo para debbug/pantalla
    fila = mapa["inicio"][0]
    columna = mapa["inicio"][1]
    orientacion = mapa["orientacion_inicial"]

    posiciones = []
    for accion, valor in instrucciones:
        if accion == "AVANZAR":
            celdas = int(round(valor / mapa["tamano_celda_metros"]))
            cambio_fila, cambio_columna = AVANCE_POR_ORIENTACION[orientacion]
            fila = fila + cambio_fila * celdas
            columna = columna + cambio_columna * celdas
        else:
            cuartos = int(valor // 90)
            if accion == "GIRAR_IZQUIERDA":
                cuartos = -cuartos
            orientacion = ORIENTACIONES[(ORIENTACIONES.index(orientacion) + cuartos) % 4]
        posiciones.append((fila, columna, orientacion))
    return posiciones


def avisar_fin_de_ruta(robot):
    # Aviso de que la ruta termino: el robot gira hacia la izquierda VUELTAS_DE_AVISO vueltas completas (360 grados cada una).
    # Como son vueltas enteras queda mirando hacia donde miraba, asi que no cambia su orientacion en el laberinto.
    print("Fin de la ruta: el robot gira " + str(VUELTAS_DE_AVISO) + " veces sobre si mismo como aviso.")
    tiempo = VUELTAS_DE_AVISO * 2 * math.pi / VELOCIDAD_GIRO
    return enviar_movimiento(robot, 0.0, VELOCIDAD_GIRO, tiempo)


def ejecutar_en_robot(instrucciones, host="127.0.0.1", puerto=8765, posiciones=None):
    # Manda las instrucciones, una por una, al simulador o al robot real.
    # Usa la API del laboratorio (g1_student_api.py), que es la misma en los dos.
    # El import se hace aca adentro para que el resto del programa funcione aunque el simulador no este instalado.
    sys.path.insert(0, CARPETA_API_ROBOT)
    try:
        from g1_student_api import RobotG1
    except ImportError:
        raise RuntimeError("No se encontro g1_student_api.py en " + CARPETA_API_ROBOT)

    robot = RobotG1(host, puerto)
    estado = robot.conectar()
    if MOSTRAR_ESTADO_ROBOT:
        print("Estado inicial: " + texto_estado(estado))
    try:
        for i in range(len(instrucciones)):
            print("Enviando " + str(i + 1) + "/" + str(len(instrucciones)) + ": "
                  + instruccion_a_texto(instrucciones[i]))
            adelante, giro, tiempo = convertir_a_movimiento(instrucciones[i])
            estado = enviar_movimiento(robot, adelante, giro, tiempo)
            if posiciones is not None:
                fila, columna, orientacion = posiciones[i]
                print("    -> en el laberinto: celda (" + str(fila) + ", " + str(columna)
                      + "), mirando al " + orientacion)
            if MOSTRAR_ESTADO_ROBOT:
                print("    -> " + texto_estado(estado))
        estado = avisar_fin_de_ruta(robot)
        if MOSTRAR_ESTADO_ROBOT:
            print("    -> " + texto_estado(estado))
    finally:
        robot.detenerse()
        robot.desconectar()


#----------------------------------------------------------------------------------------------------------------------------------------------
# Main
#   python tp_greedy_rocca.py            -> corre los 3 mapas y guarda los logs
#   python tp_greedy_rocca.py robot 2    -> corre el mapa 2 y manda sus instrucciones al robot


if __name__ == "__main__":
    os.makedirs(os.path.join(CARPETA_PROYECTO, "salidas"), exist_ok=True)

    if len(sys.argv) >= 2 and sys.argv[1] == "robot":
        if len(sys.argv) != 3 or sys.argv[2] not in ["1", "2", "3"]:
            print("Uso: python tp_greedy_rocca.py robot <numero de mapa: 1, 2 o 3>")
        else:
            mapa, ruta, causa, instrucciones = correr_mapa(int(sys.argv[2]))
            print()
            posiciones = seguir_posicion_en_laberinto(mapa, instrucciones)
            print("Se van a enviar " + str(len(instrucciones)) + " instrucciones al robot.")
            print("Posicion inicial en el laberinto: celda " + str(mapa["inicio"])
                  + ", mirando al " + mapa["orientacion_inicial"])
            print("Verifique que el area este despejada y que el simulador o robot este listo.")
            input("Presione ENTER para comenzar (Ctrl+C para cancelar)... ")
            try:
                ejecutar_en_robot(instrucciones, posiciones=posiciones)
                print("Listo: se enviaron todas las instrucciones.")
                print("El robot termino en la celda " + str((posiciones[-1][0], posiciones[-1][1]))
                      + " del laberinto (destino: " + str(mapa["destino"]) + "). Resultado: " + causa)
            except RuntimeError as error:
                print("No se pudo ejecutar en el robot:", error)
    else:
        resumen = []
        for numero in [1, 2, 3]:
            mapa, ruta, causa, instrucciones = correr_mapa(numero)
            resumen.append(mapa["nombre"] + " -> " + causa + " (" + str(len(ruta) - 1) + " movimientos)")
            print()

        print("=" * 60)
        print("RESUMEN")
        print("=" * 60)
        for linea in resumen:
            print(linea)
        print("Los logs quedaron guardados en la carpeta 'salidas'.")
