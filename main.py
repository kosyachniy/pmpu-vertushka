from func.tg_bot import *
from func.db_mongo import *
import urllib, time


def write(user):
	if user['type']:
		station = db['stations'].find_one({'id': user['station']})

		text = 'Станция №%d (%s)\n\nТекущая группа: №%d' % (station['id'], station['name'], station['group'])
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


db['sets'].insert_one({'name': 'lock', 'cont': False})


# Приветствие
@bot.message_handler(commands=['start', 'help', 'info'])
def handle_start(message):
	bot.send_message(message.chat.id, 'Приветики!')

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
	group = message.text.split()[1]

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
@bot.message_handler(commands=['start'])
def handler_start(message):
	for i in db['groups'].find():
		free = db['stations'].find_one({'group': 0})
		if free:
			free['group'] = i['id']
			db['stations'].save(free)

			i['now'] = free['id']
			db['groups'].save(i)
		else:
			bot.send_message(message.chat.id, 'На данный момент нет свободных пунктов!')

	for i in db['users'].find():
		write(i)

# Левое сообщение
@bot.message_handler(content_types=["text"])
def handle_message(message):
	user = db['users'].find_one({'id': id})

	if not user:
		bot.send_message(message.chat.id, 'Вы не зарегистрировались!\nВведите команду "\\reguser N", где N - номер вашей группы.')
	else:
		mes = message.text.strip()
		if user['type']:
			# Организатор закончил квест
			if mes == 'Следующая группа':
				pass

			# Организатор начислил / списал баллы
			elif mes.isdigit():
				pass

			else:
				write(user)
		else:
			write(user)
		

if __name__ == '__main__':
	bot.polling(none_stop=True)