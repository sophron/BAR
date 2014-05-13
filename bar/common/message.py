import bar.common.aes as aes

class Message:

    def __init__(self, message):
        self.message = message
        self.label, self.encrypted_payload = message.split("|||") 

    def decrypt(self, sharedkey):
        self.cleartext_payload = aes.aes_decrypt(sharedkey, self.encrypted_payload) 
        self.new_label, self.cleartext_msg = self.cleartext_payload.split("|||")
