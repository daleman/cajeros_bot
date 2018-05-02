# -*- coding: utf-8 -*-

from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import psycopg2
import telegram
import json

DISTANCIA_MAX = 500
EXTRACCIONES_DIA = 1000
CANT_CAJEROS_MAX = 3


class DB(object):
    """clase DB"""

    def __init__(self):
        # Me conecto a la base de datos
        self.conn = psycopg2.connect(host="localhost",
                                     database="postgres",
                                     user="postgres",
                                     password="postgres")

    def update_row_proba(self, rid, alpha, proba):
        """Actualiza extracciones de la fila rid sumandole alpha * proba
        Se asume que cada vez que alguien usa la app, hay alpha personas que quieren ir al banco
        cerca de esa ubicacion"""
        cur = self.conn.cursor()
        cur.execute(
            """UPDATE cajeros 
            SET extracciones=extracciones + ({0} * {1}) 
            WHERE id={2}""".format(proba, alpha, rid))
        self.conn.commit()

    def select(self, **data_query_format):
        """Busca los 3 cajeros que esten mas cerca de la posicion (lat,lng) pasada por parametro
        Se fija que la cantidad de extracciones no haya superado la cantidad maxima posible por dia
         """
        cur = self.conn.cursor()
        cur.execute(
            """SELECT lat,lng,banco,dom_orig,id FROM cajeros 
                WHERE red=\'{red}\' AND 
                ST_Distance(ST_SetSRID(ST_MakePoint({lng},{lat}),4326), geom) < {dmax} 
                AND extracciones < {extracciones} 
                ORDER BY ST_Distance(ST_SetSRID(ST_MakePoint({lng},{lat}),4326), geom) 
                ASC LIMIT {cant_cajeros}""".format(**data_query_format))
        return cur.fetchall()

db = DB()

with open('secrets.json') as json_data:
    secrets_json = json.load(json_data)

google_api_key = secrets_json['google_api_key']


def start(bot, update):
    """Handler de bienvenida"""
    bot.send_message(chat_id=update.message.chat_id,
                     text="Soy el bot CajerosCerca, Hola!")


def ayuda(bot, update):
    """Handler de ayuda"""
    bot.send_message(chat_id=update.message.chat_id,
                     text="Escribiendo _link_ o _banelco_ el bot te voy a decir los cajeros más cercanos de esa red!",
                     parse_mode=telegram.ParseMode.MARKDOWN)


def cajero(bot, update, user_data):
    """Handler de banelco y link
    Arranca pidiendo la direccion"""
    user_data['red'] = update.message.text.upper()
    markup_boton_direccion = ReplyKeyboardMarkup(
        [[KeyboardButton('Mandame tu direción', request_location=True)]],
        resize_keyboard=True, one_time_keyboard=True)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text='Ingresá la dirección a partir del botón',
                    reply_markup=markup_boton_direccion)


def buscarCajeros(lat, lng, user_data):
    """Busca los cajeros en la base de datos y los devuelve"""

    print(user_data['red'])

    rows = db.select(red=user_data['red'],
                     lng=lng,
                     lat=lat,
                     dmax=DISTANCIA_MAX,
                     extracciones=EXTRACCIONES_DIA,
                     cant_cajeros= CANT_CAJEROS_MAX)
    return rows


def format_query(rows):
    """Formatea los domicilios, las coordenadas y los ids de los cajeros
    Cada row esta formado por lat,lng,banco,dom_origm,id
    """
    banco_domicilio = ""
    coords, ids = [], []
    for ans in rows:
        banco_domicilio += "{} - {}\n".format(ans[2], ans[3])
        coords.append("{},{}".format(ans[0], ans[1]))
        ids.append(ans[4])
    return banco_domicilio, coords, ids


def send_photo(bot, update, user_data):
    """Envia la foto con la posicion pasada en el mensaje y las direcciones cercanas"""
    sacar_boton = ReplyKeyboardRemove()
    bot.send_message(chat_id=update.message.chat_id,
                     text="------------",
                     reply_markup=sacar_boton)

    lat = update.message.location.latitude
    lng = update.message.location.longitude
    user_address = "{0},{1}".format(lat, lng)

    rows = buscarCajeros(float(lat), float(lng), user_data)

    banco_domicilio, coords, ids = format_query(rows)
    update_rows(ids)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Estos son los cajeros {0} más cercanos:\n{1}".format(user_data['red'].lower(), banco_domicilio))

    imagen = imagenCajeros(center=user_address, direcciones=coords)
    bot.send_photo(chat_id=update.message.chat_id, photo=imagen)


def update_rows(ids, alpha=20):
    """ modifico todos los 3 cajeros cercanos:
    al primero le saco 0,7 * alpha
    al segundo le saco 0,2 * alpha
    al tercero le saco 0,1 * alpha
    siendo alpha el factor de las personas que
    van al cajero por cada vez que una busca con el bot
    """
    proba = [0.7, 0.2, 0.1]
    print(ids)
    for i, row_id in enumerate(ids):
        db.update_row_proba(row_id, alpha, proba[i])


def imagenCajeros(center, direcciones, zoom=15, size="600x300"):
    """Crea la url de la api de google maps"""
    center_url = "center={}".format(center)
    zoom = "zoom={}".format(zoom)
    api = "https://maps.googleapis.com/maps/api/staticmap?"
    size = "size={}".format(size)
    markers = "markers=color:red%7C{}&".format(center)
    colors = ["blue", "green", "yellow"]
    for i, address in enumerate(direcciones):
        markers += "markers=color:{}%7Clabel:{}%7C{}&".format(
            colors[i], i + 1, address)
    key = "key={}".format(google_api_key)
    url = api + "&".join([center, zoom, size, markers, key])
    return url


def error(bot, update, error):
    """Log de errores causados por update"""
    logger.warning('Update "{0}" caused error "{1}"'.format(update, error))
