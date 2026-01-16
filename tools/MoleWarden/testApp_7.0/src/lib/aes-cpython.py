import binascii
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def decrypt_aes_cbc(key, iv, encrypted_message):
    # Create an AES cipher object with the key and IV
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    
    # Decrypt the encrypted message
    decrypted_message = decryptor.update(encrypted_message) + decryptor.finalize()
    return decrypted_message

# Get user input for key, IV, and encrypted message in hex
key_hex = input("Enter the key in hex format: ")
iv_hex = input("Enter the IV in hex format: ")
encrypted_message_hex = input("Enter the encrypted message in hex format: ")
expected_decrypted_hex = input("Enter the decrypted message in hex format (leave empty to compute): ")

# Convert hex to bytes
key = binascii.unhexlify(key_hex)
iv = binascii.unhexlify(iv_hex)
encrypted_message = binascii.unhexlify(encrypted_message_hex)
expected_decrypted_message = binascii.unhexlify(expected_decrypted_hex)

# Decrypt the message
decrypted_message = decrypt_aes_cbc(key, iv, encrypted_message)

# Check if the decryption is successful
if expected_decrypted_message:
  is_valid = decrypted_message == expected_decrypted_message
  print("Decryption successful:", is_valid)
else:
  print("Decrypted message:", decrypted_message.hex())

