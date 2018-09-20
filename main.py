from func.tg_bot import *
from func.db_mongo import *
import urllib, time
import random


def write(user):
	free = False

	if user['type']:
		station = db['stations'].find_one({'id': user['station']})

		text = 'Станция №%d (%s)\n\n' % (station['id'], station['name'])

		if station['group']:
			text += 'Текущая группа: №%d' % station['group']
		else:
			text += 'Групп нет!'

		re = [['Обновить информацию']]
		if station['group']:
			re.append(['Следующая группа'])
		keyboards = keyboard(re)
	else:
		group = db['groups'].find_one({'id': user['group']})

		group['balls1'] = sum([j[0] for j in group['balls']])
		group['balls2'] = sum([j[1] for j in group['balls']])
		group['sum'] = sum([sum(j) / 2 for j in group['balls']])
		text = 'Группа №%d\nПройденно станций: %d\n\nБаллы за прохождение: %d\nБаллы за командный дух: %d\n∑ %.1f\n\n' % (group['id'], len(group['stations']), group['balls1'], group['balls2'], group['sum'])

		if group['now']:
			station = db['stations'].find_one({'id': group['now']})
			text += 'Текущая станция: %s\n%s' % (station['name'], station['geo'])
		else:
			text += 'Текущей станции нет'
			free = True

		keyboards = keyboard([['Обновить информацию']])

	bot.send_message(user['id'], text, reply_markup=keyboards)

	if free:
		tim = db['sets'].find_one({'name': 'time'})['cont']
		if tim:
			group = db['groups'].find_one({'id': user['group']})
			next_station(group, messages=False)

def next_station(group, station=None, messages=True):
	if station:
		stations = db['stations'].find_one({'id': station})
		stations['group'] = 0
		db['stations'].save(stations)

		group['stations'].append(station)
		group['now'] = 0
		db['groups'].save(group)

		for i in db['users'].find({'station': station}):
			write(i)

	if group['now']:
		for i in db['stations'].find({'id': group['now']}):
			i['group'] = 0
			db['stations'].save(i)

	tim = db['sets'].find_one({'name': 'time'})['cont']
	if tim:
		sta = [i for i in db['stations'].find({'id': {'$nin': group['stations']}})]
		if len(sta):
			random.shuffle(sta)

			yes = True
			for i in sta:
				if not i['group']:
					i['group'] = group['id']
					db['stations'].save(i)

					group['now'] = i['id']
					db['groups'].save(group)

					for j in db['users'].find({'group': group['id']}):
						write(j)

					for j in db['users'].find({'type': 1, 'station': i['id']}):
						write(j)

					yes = False
					break

			if yes and messages:
					for i in db['users'].find({'group': group['id']}):
						bot.send_message(i['id'], 'На данный момент нет свободных станций!')
		else:
			if messages:
				for i in db['users'].find({'group': group['id']}):
					bot.send_message(i['id'], 'Вы прошли все станции!')

		if not messages:
			# Если есть команды, которым пока некуда идти
			for i in db['groups'].find({'now': 0}):
				next_station(i, messages=False)
	else:
		for j in db['users'].find({'group': group['id']}):
			bot.send_message(j['id'], 'Время вышло!')


db['sets'].remove()
db['sets'].insert_one({'name': 'lock', 'cont': False})
db['sets'].insert_one({'name': 'begin', 'cont': False})
db['sets'].insert_one({'name': 'time', 'cont': True})

for i in db['groups'].find():
	i['stations'] = []
	i['now'] = 0
	i['balls'] = []
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
	bot.send_message(message.chat.id, 'Author: Poloz Alexey\n\nTelegram: @kosyachniy\nEmail: polozhev@mail.ru')

# Добавление организатора
@bot.message_handler(commands=['regorg'])
def handler_org(message):
	lock = db['sets'].find_one({'name': 'lock'})['cont']
	if lock:
		bot.send_message(message.chat.id, 'Регистрация закрыта!')
	else:
		try:
			station = int(message.text.split()[1])
		except:
			bot.send_message(message.chat.id, 'Неправильный формат!')
		else:
			stations = db['stations'].find_one({'id': station})
			if not stations:
				bot.send_message(message.chat.id, 'Нет такой станции!')
			else:
				user = db['users'].find_one({'id': message.chat.id})	
				if not user:
					user = {
						'id': message.chat.id,
					}
				user['type'] = 1
				user['station'] = station
				db['users'].save(user)

				bot.send_message(message.chat.id, 'Организатор зарегистрирован!')

# Добавление участника
@bot.message_handler(commands=['reguser'])
def handler_user(message):
	try:
		group = int(message.text.split()[1])
	except:
		bot.send_message(message.chat.id, 'Неправильный формат!')
	else:
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
	x = db['sets'].find_one({'name': 'begin'})
	if x['cont']:
		bot.send_message(message.chat.id, 'Уже был старт!')
	else:
		for i in db['groups'].find():
			next_station(i)
		for j in db['users'].find():
			if j['type']:
				write(j)

		x['cont'] = True
		db['sets'].save(x)

# Вышло время
@bot.message_handler(commands=['time'])
def handler_time(message):
	x = db['sets'].find_one({'name': 'time'})
	x['cont'] = False
	db['sets'].save(x)

	for i in db['users'].find():
		bot.send_message(i['id'], 'Время вышло, поздравляем, квест окончен! Иди подкрепись и приходи на гала концерт в НИИ!')

# Статистика
@bot.message_handler(commands=['stats'])
def handler_stats(message):
	groups = [i for i in db['groups'].find({}, {'_id': False})]
	for i in range(len(groups)):
		groups[i]['balls1'] = sum([j[0] for j in groups[i]['balls']])
		groups[i]['balls2'] = sum([j[1] for j in groups[i]['balls']])
		groups[i]['sum'] = sum([sum(j) / 2 for j in groups[i]['balls']])

	stats = sorted(groups, key=lambda i: i['sum'])
	text = 'Статистика\n\n'
	j = 0
	past = 0
	for i in stats:
		if past != i['sum']:
			past = i['sum']
			j += 1

		if j:
			text += '🏆%d     №%d     (∑%.1f)\n' % (j, i['id'], i['sum'])
	bot.send_message(message.chat.id, text)

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

				if station['group']:
					group = db['groups'].find_one({'id': station['group']})
					if len(group['stations']) < len(group['balls']):
						next_station(group, station['id'])
					else:
						bot.send_message(message.chat.id, 'Вы забыли начислить баллы!')
				else:
					bot.send_message(message.chat.id, 'У Вас сейчас нет группы!')

			# Организатор начислил / списал баллы
			else:
				balls = mes.split()
				if len(balls) == 2 and all([i.isdigit() for i in balls]):
					station = db['stations'].find_one({'id': user['station']})

					if station['group']:
						group = db['groups'].find_one({'id': station['group']})
						
						balls = [int(i) for i in balls]
						if any([i < 0 or i > 10 for i in balls]):
							bot.send_message(message.chat.id, 'Неправильный формат! Оценка может быть от 0 до 10 включительно.')
						else:
							if len(group['balls']) > len(group['stations']):
								group['balls'][-1] = balls
							else:
								group['balls'].append(balls)
								
							db['groups'].save(group)

							bot.send_message(message.chat.id, 'Баллы за прохождение: %d\nБаллы за командный дух: %d\n∑ %.1f' % (balls[0], balls[1], (balls[0] + balls[1]) / 2), reply_markup=keyboard([['Обновить информацию'], ['Следующая группа']]))
					else:
						bot.send_message(message.chat.id, 'У вас сейчас нет групп!')

				else:
					write(user)
		else:
			write(user)
		

if __name__ == '__main__':
	while True:
		try:
			bot.polling(none_stop=True)
		except Exception as e:
			print(e)
			time.sleep(5)