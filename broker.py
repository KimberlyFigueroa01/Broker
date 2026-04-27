import asyncio

# Diccionario donde guardaremos los clientes conectados 
clientes = {}

async def manejar_cliente(reader, writer):
    direccion = writer.get_extra_info('peername')
    print(f"[+] Cliente conectado desde {direccion}")

    try:
        while True:
            # Leer hasta 1024 bytes crudos
            datos = await reader.read(1024)

            if not datos:
                # El cliente cerró la conexión
                break

            print(f"[bytes recibidos] {datos.hex()}")

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