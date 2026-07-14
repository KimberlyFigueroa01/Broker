from asyncio import constants
import asyncio
import ssl


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

# clave: client_id
# valor: { 'writer': writer, 'topics': [lista de topics] }
clientes = {}

contexto_ssl = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
contexto_ssl.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
# ─────────────────────────────────────────────
async def leer_longitud(reader):
    longitud = 0
    multiplicador = 1
    while True:
        byte = await reader.read(1)
        if not byte:
            return None
        b = byte[0]
        longitud += (b & 0x7F) * multiplicador
        if b & 0x80 == 0:
            break
        multiplicador *= 128
        if multiplicador > 128 * 128 * 128:
            return None
    return longitud

# ─────────────────────────────────────────────
async def procesar_connect(resto, writer):
   

    keep_alive = (resto[8] << 8) | resto[9]
    print(f"    Keep Alive: {keep_alive} segundos")

    pos = 10  # salta los 10 bytes fijos del Variable Header
    
    # leer longitud del Client ID (2 bytes)
    largo_id = (resto[pos] << 8) | resto[pos + 1]
    pos += 2

    # leer el Client ID
    client_id = resto[pos: pos + largo_id].decode('utf-8')

    print(f"    Client ID: {client_id}")

    # si ya existía ese client_id, cerrar la conexión anterior
    if client_id in clientes:
        print(f"    ⚠️  '{client_id}' ya conectado — cerrando sesión anterior")
        try:
            clientes[client_id]['writer'].close()
        except:
            pass

    # guardar nuevo cliente
    clientes[client_id] = {'writer': writer, 'topics': [], 'keep_alive': keep_alive}
    print(f"    Clientes conectados: {list(clientes.keys())}")

    # enviar CONNACK
    connack = bytes([0x20, 0x02, 0x00, 0x00])
    writer.write(connack)
    await writer.drain()
    print(f"CONNACK enviado a '{client_id}'")

    return client_id, keep_alive

# ─────────────────────────────────────────────
async def procesar_subscribe(resto, writer, client_id):
    packet_id_msb = resto[0]
    packet_id_lsb = resto[1]
    pos = 2

    topics_suscritos = []

    while pos < len(resto):
        largo_topic = (resto[pos] << 8) | resto[pos + 1]
        pos += 2
        topic = resto[pos: pos + largo_topic].decode('utf-8')
        pos += largo_topic
        qos = resto[pos]
        pos += 1

        topics_suscritos.append(topic)
        print(f"    Suscripción: '{topic}' QoS {qos}")

        if client_id and client_id in clientes:
            if topic not in clientes[client_id]['topics']:
                clientes[client_id]['topics'].append(topic)

    print(f"    Topics de '{client_id}': {clientes.get(client_id, {}).get('topics', [])}")

    # enviar SUBACK
    long_suback = 2 + len(topics_suscritos)
    suback = bytes([0x90, long_suback, packet_id_msb, packet_id_lsb])
    suback += bytes([0x00] * len(topics_suscritos))
    writer.write(suback)
    await writer.drain()
    print(f"     SUBACK enviado a '{client_id}'")

# ─────────────────────────────────────────────
async def procesar_publish(resto, flags):
    # extraer el topic
    largo_topic = (resto[0] << 8) | resto[1]
    topic = resto[2: 2 + largo_topic].decode('utf-8')

    # el payload empieza después del topic
    # QoS 0 no tiene Packet ID, así que el payload viene directo
    qos = (flags >> 1) & 0x03
    inicio_payload = 2 + largo_topic
    if qos > 0:
        inicio_payload += 2  # saltar los 2 bytes del Packet ID

    payload = resto[inicio_payload:]

    print(f"    Topic:   '{topic}'")
    print(f"    Payload: '{payload.decode('utf-8', errors='replace')}'")
    print(f"    Clientes activos: {list(clientes.keys())}")

    # buscar suscriptores y reenviar
    enviado_a = []
    for cid, datos in list(clientes.items()):
        if topic in datos['topics']:
            try:
                # reconstruir el paquete PUBLISH para reenviar
                topic_bytes   = topic.encode('utf-8')
                largo_topic_b = len(topic_bytes)

                # Variable Header: longitud topic (2 bytes) + topic
                var_header = bytes([largo_topic_b >> 8, largo_topic_b & 0xFF]) + topic_bytes

                # Fixed Header
                remaining = len(var_header) + len(payload)
                publish_packet = bytes([0x30, remaining]) + var_header + payload

                datos['writer'].write(publish_packet)
                await datos['writer'].drain()
                enviado_a.append(cid)
            except Exception as e:
                print(f"    ⚠️  Error reenviando a '{cid}': {e}")

    if enviado_a:
        print(f"     Reenviado a: {enviado_a}")
    else:
        print(f"      Nadie suscrito a '{topic}'")

# ─────────────────────────────────────────────
async def manejar_cliente(reader, writer):
    direccion = writer.get_extra_info('peername')
    print(f"\n[+] Cliente conectado desde {direccion}")

    client_id = None
    timeout_actual = 30 #tiempo de gracia antes de que llegue el primer CONNECT
    motivo_desconexion = "desconocido"

    try:
        while True:
            try:
                primer_byte = await asyncio.wait_for(reader.read(1), timeout=timeout_actual)
            except asyncio.TimeoutError:
                motivo_desconexion = "timeout"
                break

            if not primer_byte:
                motivo_desconexion = "cierre_tcp"
                break

            tipo  = primer_byte[0] >> 4
            flags = primer_byte[0] & 0x0F
            nombre = TIPOS_MQTT.get(tipo, f'DESCONOCIDO({tipo})')

            longitud = await leer_longitud(reader)
            if longitud is None:
                break

            resto = b''
            if longitud > 0:
                resto = await reader.readexactly(longitud)

            print(f" -> Paquete: {nombre} | flags: {flags} | longitud: {longitud} bytes")

            if tipo == 1:    # CONNECT
                client_id, keep_alive = await procesar_connect(resto, writer)
                timeout_actual = keep_alive * 1.5 if keep_alive > 0 else None

            elif tipo == 8:  # SUBSCRIBE
                await procesar_subscribe(resto, writer, client_id)

            elif tipo == 3:  # PUBLISH
                await procesar_publish(resto, flags)

            elif tipo == 12: # PINGREQ
                # responder PINGRESP para mantener la conexión viva
                writer.write(bytes([0xD0, 0x00]))
                await writer.drain()
                print(f"     PINGRESP enviado a '{client_id}'")

            elif tipo == 14: # DISCONNECT
                motivo_desconexion = "desconexión_limpia"
                print(f"    Cliente '{client_id}' se desconectó limpiamente")
                break

            else:
                print(f"    Bytes (hex): {resto.hex()}")

    except Exception as e:
        motivo_desconexion = "error"
        print(f"[!] Error con '{client_id}' {direccion}: {e}")

    finally:
        mensajes = {
            "desconexión_limpia": f"'{client_id}' se desconectó limpiamente (DISCONNECT)",
            "desconocido":  f" '{client_id}' cerró el socket sin avisar (cierre TCP)",
            "timeout": f"  '{client_id}' no respondió a tiempo — timeout de keep_alive ({timeout_actual}s)",
            "cierre_tcp": f" '{client_id}' se desconectó por un error",
            "error": f" '{client_id}' se desconectó por una razón no identificada"
        }

        print(f"[-] Desconectado: {direccion} | Motivo: {mensajes.get(motivo_desconexion, 'desconocido')}")
        if client_id and client_id in clientes:
            del clientes[client_id]
            print(f"    '{client_id}' eliminado del diccionario")
        print(f"[-] Desconectado: {direccion} | Clientes activos: {list(clientes.keys())}")
        writer.close()
        await writer.wait_closed()

# ─────────────────────────────────────────────
async def main():
    servidor = await asyncio.start_server(
        manejar_cliente,
        '192.168.18.9',
        8883,
        ssl=contexto_ssl
    )
    direccion = servidor.sockets[0].getsockname()
    print(f"[*] Broker iniciado en {direccion}")
    print(f"[*] Esperando conexiones...")
    async with servidor:
        await servidor.serve_forever()

asyncio.run(main())