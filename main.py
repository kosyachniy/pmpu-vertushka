from func.tg_bot import *
from func.mongodb import *
import urllib, time

@bot.message_handler(commands=['start', 'help', 'info'])
def handle_start(message):
	bot.send_message(message.chat.id, 'Приветики!')

@bot.message_handler(commands=['about', 'author'])
def about(message):
	bot.send_message(message.chat.id, 'Author: Poloz Alexey\npolozhev@mail.ru')

@bot.message_handler(commands=['regorg'])
def handler_org(message):
	try:
		id = db['stations'].find().sort('id', -1)[0]['id'] + 1
	except:
		id = 1

	station = {
		'id': id,
		'name': name, #
		'geo': geo, #
		'free': True,
	}
	db['stations'].insert_one(station)

	user = db['users'].find_one({'id': message.chat.id})	
	if not user:
		user = {
			'id': message.chat.id,
		}
	user['type'] = 1
	db['users'].save(user)

	bot.send_message(message.chat.id, 'Организатор зарегистрирован!')

@bot.message_handler(commands=['reguser'])
def handler_user(message):
	user = db['users'].find_one({'id': message.chat.id})
	if not user:
		user = {
			'id': message.chat.id,
		}
	user['type'] = 0
	user['group'] = group #
	db['users'].save(user)

	bot.send_message(message.chat.id, 'Пользователь зарегистрирован!')

@bot.message_handler(content_types=["text"])
def handle_message(message):
	user = db['users'].find_one({'id': message.chat.id})
	if not user:
		bot.send_message(message.chat.id, 'Вы не зарегистрировались!\nВведите команду "\\reguser N", где N - номер вашей группы.')
	else:
		if user['type']:
			text = ''
			keyboards = keyboard([['']])
		else:
			text = 'Группа №%d\n\nПройденно станций: %d\nБаллов: %d\n\nТекущая станция: %s' % (group, count, balls, name) #
			keyboards = keyboard([['Обновить информацию']])
		bot.send_message(message.chat.id, text, reply_markup=keyboards)

if __name__ == '__main__':
	bot.polling(none_stop=True)