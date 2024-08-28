import base64
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

KDF_ALGORITHM = hashes.SHA256()
KDF_LENGTH = 32
KDF_ITERATIONS = 120000

def encrypt(plaintext: str, password: str):
    # Derive a symmetric key using the passsword and a fresh random salt.
    salt = secrets.token_bytes(128)
    kdf = PBKDF2HMAC(
        algorithm=KDF_ALGORITHM, length=KDF_LENGTH, salt=salt,
        iterations=KDF_ITERATIONS)
    key = kdf.derive(password.encode("utf-8"))

    # Encrypt the message.
    f = Fernet(base64.urlsafe_b64encode(key))
    ciphertext = f.encrypt(plaintext.encode("utf-8"))

    return ciphertext, salt

def decrypt(ciphertext: bytes, password: str, salt: bytes) -> str:
    # Derive the symmetric key using the password and provided salt.
    kdf = PBKDF2HMAC(
        algorithm=KDF_ALGORITHM, length=KDF_LENGTH, salt=salt,
        iterations=KDF_ITERATIONS)
    key = kdf.derive(password.encode("utf-8"))

    # Decrypt the message
    f = Fernet(base64.urlsafe_b64encode(key))
    plaintext = f.decrypt(ciphertext)

    return plaintext.decode("utf-8")

def main():
    password = "C3gzSBf8DwsXyw0n9NQFP_ZWKXioXctfMIKr1UWqUhNkc7KEoBCoGq3iPffQ6xLINs9EYs0hIl_bVmw_HEpQ8SVhF8MMAHc20Z-0EVSoCI2oL00gRo3jkyY_3lB-CcGKy-WJXHhED3wyFklYI2ZnwzqQzpOnDUQwTs12S6cZ-nU"
    message = "AStrongAndS3cur3SecretP4ssword++==12"

    encrypted, salt = encrypt(message, password)
    decrypted = decrypt(encrypted, password, salt)

    print(f"message: {message}")
    print(f"encrypted: {encrypted}")
    print(f"decrypted: {decrypted}")

main()