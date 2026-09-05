# Broker MQTT seguro

Broker MQTT educativo implementado en Python con `asyncio`. El servidor acepta conexiones MQTT sobre TLS, administra clientes conectados y permite suscripciones y publicaciones básicas entre ellos.

> Este proyecto tiene fines académicos y de experimentación. No sustituye a un broker MQTT de producción como Mosquitto, EMQX o HiveMQ.

## Características

- Servidor asíncrono basado en la biblioteca estándar `asyncio`.
- Comunicación cifrada mediante TLS en el puerto `8883`.
- Gestión de conexiones por `client_id`.
- Suscripciones a topics y reenvío de mensajes publicados.
- Soporte básico para `CONNECT`, `CONNACK`, `PUBLISH`, `SUBSCRIBE`, `SUBACK`, `PINGREQ`, `PINGRESP` y `DISCONNECT`.
- Control de `keep alive` y cierre de conexiones inactivas.
- Generación local de certificados autofirmados para desarrollo.

## Requisitos

- Python 3.9 o superior.
- `pip`.
- Un cliente MQTT, como Mosquitto, MQTT Explorer o una aplicación basada en `paho-mqtt`.

La única dependencia externa se encuentra en [`requirements.txt`](requirements.txt):

```text
cryptography==47.0.0
```

## Instalación

Desde la raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

En Linux o macOS, activa el entorno con:

```bash
source .venv/bin/activate
```

## Certificados TLS

El broker carga los archivos desde la carpeta `certs/`:

```text
certs/
├── cert.pem
└── key.pem
```

Para generarlos en Windows:

```powershell
Set-Location certs
python ..\generar_cert.py
Set-Location ..
```

Para Linux o macOS:

```bash
cd certs
python ../generar_cert.py
cd ..
```

Los archivos `.pem` son material sensible y están excluidos mediante `.gitignore`. No deben publicarse ni incorporarse al repositorio. Los certificados generados por este script son autofirmados y solo deben utilizarse en entornos de desarrollo.

## Ejecución

Con el entorno virtual activo y los certificados creados:

```powershell
python broker.py
```

El broker escuchará en todas las interfaces de red mediante TLS:

```text
[*] Broker iniciado en ('0.0.0.0', 8883)
[*] Esperando conexiones...
```

Detén el proceso con `Ctrl+C`.

## Prueba con Mosquitto

Como el certificado es autofirmado, los clientes deben indicar el certificado durante las pruebas locales.

En una terminal, inicia un suscriptor:

```powershell
mosquitto_sub -h localhost -p 8883 --cafile certs/cert.pem -t "test/topic" -d
```

En otra terminal, publica un mensaje:

```powershell
mosquitto_pub -h localhost -p 8883 --cafile certs/cert.pem -t "test/topic" -m "Hola MQTT" -d
```

El suscriptor debería recibir el mensaje publicado.

## Despliegue y Conexión Remota (ESP32 con Ngrok)

Para permitir que dispositivos externos (como microcontroladores **ESP32** en redes Wi-Fi remotas o datos móviles) se conecten al broker sin estar en la misma red local (LAN), se expone el puerto TCP seguro mediante un túnel con **Ngrok**.

### 1. Iniciar el Broker
En una terminal:
```powershell
python broker.py
```

### 2. Abrir el Túnel TCP
En una segunda terminal:
```powershell
ngrok tcp 8883
```

Ngrok asignará un endpoint público similar a:
```text
Forwarding    tcp://8.tcp.ngrok.io:25566 -> localhost:8883
```

### 3. Conectar el ESP32 (MicroPython)
En el archivo [`code_esp32.py`](code_esp32.py) se encuentra el cliente para ESP32 usando `umqtt.simple` y `ssl`:

1. Configura el servidor y puerto asignados por Ngrok:
   ```python
   MQTT_SERVER = "8.tcp.ngrok.io"  # Host público entregado por Ngrok
   MQTT_PORT   = 25566            # Puerto público asignado por Ngrok
   MQTT_TOPIC  = b"sala1/dht11"
   ```
2. La conexión se establece con cifrado TLS omitiendo la validación estricta de la CA para certificados autofirmados:
   ```python
   client = MQTTClient(
       client_id="ESP32_sub",
       server=MQTT_SERVER,
       port=MQTT_PORT,
       ssl=True,
       ssl_params={"cert_reqs": ssl.CERT_NONE}
   )
   client.set_callback(callback)
   client.connect()
   client.subscribe(MQTT_TOPIC)
   ```
3. Al ejecutar el script en el ESP32 (mediante Thonny u otra herramienta), el dispositivo se suscribirá y recibirá los mensajes publicados en el broker a través de Internet.

## Estructura del proyecto

```text
.
├── broker.py          # Servidor MQTT asíncrono sobre TLS
├── code_esp32.py      # Cliente MicroPython para ESP32
├── generar_cert.py    # Generador de certificados autofirmados
├── requirements.txt   # Dependencias externas fijadas
├── certs/             # Certificados locales, excluidos de Git
└── README.md
```

## Limitaciones conocidas

Esta es una implementación simplificada del protocolo MQTT. Actualmente no incluye:

- Autenticación de usuarios ni autorización por topic.
- Persistencia de sesiones, mensajes retenidos o almacenamiento durable.
- QoS completo, retransmisiones ni manejo de `Packet Identifier` en el reenvío.
- Soporte para topics con comodines (`+` y `#`).
- Validación exhaustiva de todos los paquetes y flags definidos por MQTT.
- Alta disponibilidad, métricas, límites de conexiones o configuración externa.

Para un entorno productivo se debe utilizar un broker MQTT especializado o ampliar esta implementación con autenticación, autorización, validación de protocolo, gestión de secretos, observabilidad y pruebas de integración.

## Seguridad del repositorio

- No confirmar archivos `.pem`, claves privadas, contraseñas ni tokens.
- Generar certificados diferentes para cada entorno.
- Considerar comprometida cualquier clave que haya sido publicada en el historial Git y reemplazarla, aunque después se haya eliminado.
- Usar certificados emitidos por una autoridad de confianza en producción.
