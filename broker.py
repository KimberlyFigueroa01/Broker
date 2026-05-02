import asyncio

# Nombres de los tipos de paquete MQTT para mostrar en consola
TIPOS_MQTT = {
    1:  'CONNECT',
    2:  'CONNACK',
    3:  'PUBLISH',
    8:  'SUBSCRIBE',
    9:  'SUBACK',
    12: 'PINGREQ',
    13: 'PINGRESP',
    14: 'DISCONNECT',
}

# Diccionario donde guardaremos los clientes conectados 
clientes = {}

async def leer_longitud(reader):
    longitud = 0 # inicializa la longitud del paquete
    multiplicador = 1 # inicializa el multiplicador 

    while True:
        byte = await reader.read(1) #leer un byte a la vez 
        if not byte: # si no hay byte, return None
            return None
        b = byte[0] # obtener solo el valor numerico del byte
        longitud += (b & 0x7f) * multiplicador # 0x7f es 127, y 127 es el mayor valor que se puede obtener en 7 bits 
        

        if b & 0x80 == 0: # si el bit mas significativo es 0, es el ultimo byte
            break
        multiplicador *= 128 # multiplica por 128 para obtener el valor del siguiente byte 

        print("Valor del b: ", b)

        if multiplicador > 128 * 128 * 128: # si el multiplicador es mayor a 128*128*128, es un paquete invalido
            return None

    return longitud # cuando sale del ciclo devuelve la longitud total del paquete 

async def manejar_cliente(reader, writer):
    direccion = writer.get_extra_info('peername')
    print(f"[+] Cliente conectado desde {direccion}")

    try:
        while True:
            # Paso 1: leer el primer byte (tipo y flag del paquete)
            primer_byte = await reader.read(1) #leer un byte a la vez 
            if not primer_byte: # si no hay byte, return None
                break

            # Paso 2: separar el tipo y el flag PARA OBTENER EL TIPO DE PAQUETE
            tipo = primer_byte[0] >> 4 # obtener solo el valor numerico del byte (haciendo un desplazamiento de 4 bits a la derecha)
            flags = primer_byte[0] & 0x0f # obtener solo el valor numerico del byte (los 4 bits bajos son los flags), se hace uso de 0x0f para obtener solo los 4 bits bajos
            nombre = TIPOS_MQTT.get(tipo, f'DESCONOCIDO({tipo})') # obtener el nombre del tipo de paquete
            
            #Paso 3: leer la longitud
            longitud = await leer_longitud(reader)
            if longitud is None:
                break

            #Paso 4: leer el resto del paquete
            resto = b''
            if longitud > 0:
                resto = await reader.read(longitud)

            #Se muestra en consola lo que llega del cliente
            print(f" -> Paquete: {nombre} | flags: {flags} | longitud: {longitud} bytes")
            print(f"    Bytes del resto (hex): {resto.hex()}")
    except Exception as e:
        print(f"[!] Error con cliente {direccion}: {e}")

    finally:
        print(f"[-] Cliente desconectado: {direccion}")
        writer.close()
        await writer.wait_closed()


async def main():
    servidor = await asyncio.start_server(
        manejar_cliente,  # función que se llama por cada cliente nuevo
        '0.0.0.0',        # escuchar en todas las interfaces de red
        1883              # puerto MQTT estándar
    )

    direccion = servidor.sockets[0].getsockname()
    print(f"[*] Broker iniciado en {direccion}")
    print(f"[*] Esperando conexiones...")

    async with servidor:
        await servidor.serve_forever()


asyncio.run(main())