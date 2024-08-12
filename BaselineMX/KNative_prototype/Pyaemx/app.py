import pyaes

import time

def lambda_handler():
    input_file = './generated_strings_500.txt'
    with open(input_file, 'r') as f:
        data = f.read().splitlines()

    # 128-bit key (16 bytes)
    KEY = b'\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,'

    generation_count = 100

    start = time.time()
    for j in range(generation_count):
        message = data[j % len(data)]
        aes = pyaes.AESModeOfOperationCTR(KEY)
        ciphertext = aes.encrypt(message)
        aes = pyaes.AESModeOfOperationCTR(KEY)
        plaintext = aes.decrypt(ciphertext)
    end = time.time()

    average_time = (end - start) / generation_count
    return {"average_execution_time": average_time}