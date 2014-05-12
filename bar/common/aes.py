from Crypto import Random
from Crypto.Cipher import AES
from binascii import unhexlify

def aes_encrypt(skey, m):
    '''
    Encrypt given message with shared key.
    '''
    iv = '\x00' * 16
    stream = AES.new(skey, AES.MODE_CFB, iv)
    return stream.encrypt(m)

def aes_decrypt(skey, c):
    '''
    Decrypt given message with shared key.
    '''
    iv = '\x00' * 16
    stream=AES.new(skey, AES.MODE_CFB, iv)
    return stream.decrypt(c)
