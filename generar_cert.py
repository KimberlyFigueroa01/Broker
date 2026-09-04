import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography import x509
from cryptography.x509.oid import NameOID

def generar_certificados():
    print("Generando llave privada...")
    # Generar llave privada (Private Key)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    print("Configurando certificado...")
    # Configurar detalles del certificado
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"CO"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Bogota"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Bogota"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Semillero Broker"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])

    # Generar certificado autofirmado (Self-Signed Certificate)
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # Válido por 1 año
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(private_key, hashes.SHA256())

    print("Guardando key.pem...")
    # Escribir la llave privada en key.pem
    with open("key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    print("Guardando cert.pem...")
    # Escribir el certificado en cert.pem
    with open("cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print("¡Archivos cert.pem y key.pem generados exitosamente!")

if __name__ == "__main__":
    generar_certificados()
