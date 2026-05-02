# Broker

Se realiza un broker propio para un sistema MQTT

## Explicación del Código

El código implementa un broker MQTT básico utilizando la biblioteca `asyncio` de Python. Este broker no es una implementación completa del protocolo MQTT, sino una versión simplificada que permite conectar clientes y leer paquetes MQTT para fines de demostración y aprendizaje.

### Componentes Principales:

1. **Diccionario de Tipos MQTT (`TIPOS_MQTT`)**:
   - Contiene los códigos numéricos de los tipos de paquetes MQTT estándar (CONNECT, PUBLISH, SUBSCRIBE, etc.) y sus nombres correspondientes para mostrar en consola.

2. **Diccionario de Clientes (`clientes`)**:
   - Un diccionario vacío inicialmente destinado a almacenar información sobre los clientes conectados. En esta implementación básica, no se utiliza para gestionar suscripciones o publicaciones.

3. **Función `leer_longitud(reader)`**:
   - Lee la longitud variable del paquete MQTT según el protocolo. El protocolo MQTT utiliza una codificación variable donde cada byte tiene 7 bits de datos y 1 bit de continuación.
   - Calcula la longitud total del paquete leyendo bytes hasta que el bit de continuación sea 0.
   - Retorna `None` si hay un error o si el paquete es inválido.

4. **Función `manejar_cliente(reader, writer)`**:
   - Maneja cada conexión de cliente de forma asíncrona.
   - Lee el primer byte del paquete para determinar el tipo de paquete y los flags.
   - Lee la longitud del paquete usando `leer_longitud`.
   - Lee el resto del paquete.
   - Imprime información sobre el paquete recibido (tipo, flags, longitud y bytes en hexadecimal).
   - Cierra la conexión cuando el cliente se desconecta o hay un error.

5. **Función `main()`**:
   - Inicia un servidor asíncrono que escucha en todas las interfaces de red (`0.0.0.0`) en el puerto estándar de MQTT (1883).
   - Llama a `manejar_cliente` para cada nueva conexión.
   - Mantiene el servidor corriendo indefinidamente.

### Limitaciones:
- No implementa la lógica completa de MQTT (no maneja suscripciones, publicaciones, QoS, etc.).
- Solo lee y registra paquetes; no responde a los clientes.
- No gestiona el estado de las conexiones ni las sesiones.
- Es útil para inspeccionar tráfico MQTT o como base para una implementación más completa.

## Cómo Ejecutar el Código

### Requisitos Previos:
- Python 3.7 o superior instalado en el sistema.
- No se requieren bibliotecas externas adicionales, ya que utiliza solo `asyncio` que viene incluido con Python.

### Pasos para Ejecutar:

1. **Navegar al Directorio del Proyecto**:
   - Abre una terminal o línea de comandos.
   - Navega al directorio donde se encuentra el archivo `broker.py`:
     ```
     cd c:\Users\Kimberly Figueroa\Documents\SEMILLERO\Broker\Broker
     ```

2. **Ejecutar el Broker**:
   - Ejecuta el script con Python:
     ```
     python broker.py
     ```
   - O si tienes Python 3 específicamente:
     ```
     python3 broker.py
     ```

3. **Verificar que el Broker Está Ejecutándose**:
   - Deberías ver un mensaje en la consola indicando que el broker se inició:
     ```
     [*] Broker iniciado en ('0.0.0.0', 1883)
     [*] Esperando conexiones...
     ```

4. **Conectar un Cliente MQTT**:
   - Usa un cliente MQTT como `mosquitto_pub` o `mosquitto_sub` (de Mosquitto), o cualquier biblioteca MQTT en Python (como `paho-mqtt`).
   - Ejemplo con `mosquitto_pub` para publicar un mensaje:
     ```
     mosquitto_pub -h localhost -t "test/topic" -m "Hola Mundo"
     ```
   - El broker debería mostrar información sobre los paquetes recibidos en la consola.

5. **Detener el Broker**:
   - Presiona `Ctrl + C` en la terminal para detener el servidor.

### Notas:
- Asegúrate de que el puerto 1883 no esté siendo usado por otro servicio (como un broker MQTT real).
- Este broker es para fines educativos; para producción, usa un broker MQTT completo como Mosquitto o HiveMQ.
