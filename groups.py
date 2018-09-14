from func.db_mongo import *

while True:
	group = {
		'id': int(input('Номер: ')),
		'stations': [],
		'now': 0,
		'balls': 0,
	}
	db['groups'].insert_one(group)