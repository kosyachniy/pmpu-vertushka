from func.tg_bot import *
from func.db_mongo import *
import urllib, time


def write(user):
	if user['type']:
		station = db['stations'].find_one({'id': user['station']})

		text = 'Станция №%d (%s)\n\n' % (station['id'], station['name'])

		if station['group']:
			text += 'Текущая группа: №%d' % station['group']
		else:
			text += 'Групп нет!'

		keyboards = keyboard([['Обновить информацию'], ['Следующая группа']])
	else:
		group = db['groups'].find_one({'id': user['group']})

		text = 'Группа №%d\n\nПройденно станций: %d\nБаллов: %d\n\n' % (group['id'], len(group['stations']), group['balls'])

		if group['now']:
			station = db['stations'].find_one({'id': group['now']})
			text += 'Текущая станция: %s' % station
		else:
			text += 'Текущей станции нет'

		keyboards = keyboard([['Обновить информацию']])

	bot.send_message(user['id'], text, reply_markup=keyboards)

def next_station(group, station=None):
	if station:
		stations = db['stations'].find_one({'id': station})
		stations['group'] = 0
		db['stations'].save(stations)

		group['stations'].append(station)
		group['now'] = 0
		db['groups'].save(group)

		for i in db['users'].find({'station': station}):
			message(i)

	all = True
	yes = True
	for i in db['stations'].find():
		if i['id'] not in group['stations']:
			all = False
			if not i['group']:
				i['group'] = group['id']
				db['stations'].save(i)

				group['now'] = i['id']
				db['groups'].save(i)

				for i in db['users'].find({'group': group['id']}):
					write(i)

				yes = False
				break

	if all:
		for i in db['users'].find({'group': group['id']}):
			bot.send_message(i['id'], 'Вы прошли все станции!')

	elif yes:
		for i in db['users'].find({'group': group['id']}):
			bot.send_message(i['id'], 'На данный момент нет свободных станций!')


db['sets'].remove()
db['sets'].insert_one({'name': 'lock', 'cont': False})

for i in db['groups'].find():
	i['stations'] = []
	i['now'] = 0
	db['groups'].save(i)

for i in db['stations'].find():
	i['group'] = 0
	db['stations'].save(i)


# Приветствие
@bot.message_handler(commands=['start', 'help', 'info'])
def handle_start(message):
	bot.send_message(message.chat.id, 'Приветики!')

	lock = db['sets'].find_one({'name': 'lock'})['cont']
	if lock:
		bot.send_message(message.chat.id, 'Введите команду "/reguser N", где N - номер вашей группы\n\nНапример: /reguser 106')
	else:
		bot.send_message(message.chat.id, 'Введите команду "/regorg N", где N - номер квеста по документу: https://docs.google.com/document/d/1ttuSOii4huDjALe4rvZSTSrDiRwkbSkDwRkIjApA6nk/edit\n\nНапример: /regorg 7')

# Автор
@bot.message_handler(commands=['about', 'author'])
def about(message):
	bot.send_message(message.chat.id, 'Author: Poloz Alexey\npolozhev@mail.ru')

# Добавление организатора
@bot.message_handler(commands=['regorg'])
def handler_org(message):
	lock = db['sets'].find_one({'name': 'lock'})['cont']
	if lock:
		bot.send_message(message.chat.id, 'Регистрация закрыта!')
	else:
		params = message.text.split()

		user = db['users'].find_one({'id': message.chat.id})	
		if not user:
			user = {
				'id': message.chat.id,
			}
		user['type'] = 1
		user['station'] = params[1]
		db['users'].save(user)

		bot.send_message(message.chat.id, 'Организатор зарегистрирован!')

# Добавление участника
@bot.message_handler(commands=['reguser'])
def handler_user(message):
	group = int(message.text.split()[1])

	x = db['groups'].find_one({'id': group})
	if not x:
		bot.send_message(message.chat.id, 'Неправильный номер группы!')
	else:
		user = db['users'].find_one({'id': message.chat.id})
		if not user:
			user = {
				'id': message.chat.id,
			}
		user['type'] = 0
		user['group'] = group
		db['users'].save(user)

		write(user)

# Остановка регистрации организаторов
@bot.message_handler(commands=['stop'])
def handler_stop(message):
	x = db['sets'].find_one({'name': 'lock'})
	x['cont'] = True
	db['sets'].save(x)

# Начало квеста
@bot.message_handler(commands=['begin'])
def handler_begin(message):
	for i in db['groups'].find():
		next_station(i)

# Вышло время
@bot.message_handler(commands=['time'])
def handler_time(message):
	for i in db['users'].find():
		bot.send_message(message.chat.id, 'Время вышло, поздравляем, квест окончен! Иди подкрепись и приходи на гала концерт в НИИ!')

# Левое сообщение
@bot.message_handler(content_types=["text"])
def handle_message(message):
	user = db['users'].find_one({'id': message.chat.id})

	if not user:
		bot.send_message(message.chat.id, 'Вы не зарегистрировались!\nВведите команду "/reguser N", где N - номер вашей группы.')
	else:
		mes = message.text.strip()
		if user['type']:
			# Организатор закончил квест
			if mes == 'Следующая группа':
				station = db['stations'].find_one({'id': user['station']})
				group = db['groups'].find_one({'id': station['group']})
				next_station(group, station['id'])

			# Организатор начислил / списал баллы
			elif mes.isdigit():
				station = db['stations'].find_one({'id': user['station']})
				group = db['groups'].find_one({'id': station['group']})
				group['balls'] += int(mes)
				db['groups'].save(group)

			else:
				write(user)
		else:
			write(user)
		

if __name__ == '__main__':
	bot.polling(none_stop=True)