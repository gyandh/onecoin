import json, ecdsa, os, struct
from ecdsa import SigningKey, VerifyingKey
from binascii import hexlify, unhexlify

# The Transaction class handles all the transactions that we use in the blockchain
class Transaction:

    # Signs the transaction with it's attributes and the keypair from the miner
    @staticmethod
    def sign(data, keypair):
        jsondata = json.dumps(data, sort_keys=True)
        return keypair.sign(str.encode(jsondata))

    # Validates the transaction using the signature generated from the sign() function
    @staticmethod
    def validate(transaction):
        try:
            signature = transaction['signature']
            sender = transaction['sender']
            del transaction['signature']
        except KeyError:
            raise KeyError("No signature/sender provided")
        try:
            pubkey = VerifyingKey.from_string(unhexlify(sender))
        except Exception as e:
            print(e)
        try:
            data = json.dumps(transaction, sort_keys=True)
            pubkey.verify(unhexlify(signature), str.encode(data))
        except ecdsa.BadSignatureError as e:
            print(e)
            return False
        return True
    
    def __init__(self, sender, receiver, amount, comment, signature, nonce):
        self.sender = sender
        self.receiver = receiver
        if amount > 0:
            self.amount = amount
        else:
            raise ValueError('Transaction amount must be > 0')
        self.comment = comment
        self.signature = signature
        self.nonce = nonce


    @classmethod
    def new(cls, sender, receiver, amount, comment, keypair):
        nonce = int.from_bytes(os.urandom(4), byteorder='big')
        d = {
            'sender': sender,
            'receiver': receiver,
            'amount': amount,
            'comment': comment,
            'nonce': nonce
        }
        signature = cls.sign(d, keypair)
        return cls(sender, receiver, amount, comment, signature, nonce)

    # Decodes the JSON object to a transaction object
    @classmethod
    def from_json(cls, jsonData):
        try:
            decoded = json.loads(jsonData)
        except Exception as e:
            print(e)
        try:
            if cls.validate(json.loads(jsonData)):
                return cls(decoded['sender'], decoded['receiver'],
                           decoded['amount'], decoded['comment'],
                           unhexlify(decoded['signature']), decoded['nonce'])
            else:
                raise ecdsa.BadSignatureError("Invalid transaction signature")
        except KeyError as e:
            print(e)

    # Ecodes the transaction object into a JSON object
    def to_json(self):
        return json.dumps({'sender': self.sender,
                           'receiver': self.receiver,
                           'amount': self.amount,
                           'comment': self.comment,
                           'signature': hexlify(self.signature).decode("utf-8"),
                           'nonce': self.nonce}, sort_keys=True)

    # Checks that the transaction sent by the sender is actually the transaction recieved
    def __eq__(self, other):
        s = self.sender == other.sender
        r = self.receiver == other.receiver
        a = self.amount == other.amount
        c = self.comment == other.comment
        n = self.nonce == other.nonce
        sig = self.signature == other.signature
        return s and r and a and c and n and sig