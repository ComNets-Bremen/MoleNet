import binascii
from cryptography.hazmat.primitives import cmac
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.backends import default_backend

def compute_cmac(key, message):
    # Create a CMAC object using AES
    c = cmac.CMAC(algorithms.AES(key), backend=default_backend())
    c.update(message)
    return c.finalize()

def verify_cmac(key, message, expected_cmac):
    # Create a CMAC object using AES
    c = cmac.CMAC(algorithms.AES(key), backend=default_backend())
    c.update(message)
    
    # Attempt to verify the CMAC
    try:
        c.verify(expected_cmac)
        return True
    except Exception:
        return False

# Get user input for key and message in hex
key_hex = input("Enter the key in hex format: ")
message_hex = input("Enter the message in hex format: ")
cmac_hex = input("Enter the CMAC in hex format (leave empty to compute): ")

# Convert hex to bytes
key = binascii.unhexlify(key_hex)
message = binascii.unhexlify(message_hex)
expected_cmac = binascii.unhexlify(cmac_hex) if cmac_hex else None

# Compute CMAC if not provided
if not expected_cmac:
    cmac_result = compute_cmac(key, message)
    print("Computed CMAC:", cmac_result.hex())
else:
    # Check CMAC
    is_valid = verify_cmac(key, message, expected_cmac)
    print("CMAC valid:", is_valid)

