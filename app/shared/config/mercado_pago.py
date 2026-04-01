import mercadopago
import os
from dotenv import load_dotenv

load_dotenv()

class MercadoPagoConfig:
    def __init__(self):
        self.public_key = os.getenv('MERCADOPAGO_PUBLIC_KEY')
        self.access_token = os.getenv('MERCADOPAGO_ACCESS_TOKEN')
        self.user_id = os.getenv('USER_ID_MERCADOPAGO')
        self.usuario = os.getenv('USUARIO_MERCADOPAGO')
        self.contrasena = os.getenv('CONTRASENA_MERCADOPAGO')
        self.codigo_verificacion = os.getenv('CODIGO_VERIFICACION_MERCADOPAGO')

    def get_client(self):
        return mercadopago.SDK(self.access_token)
    
    