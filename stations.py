from func.db_mongo import *

while True:
	try:
		id = db['stations'].find().sort('id', -1)[0]['id'] + 1
	except:
		id = 1

	station = {
		'id': id,
		'name': input('Название: '),
		'geo': input('Расположение: '),
		'group': 0,
	}
	db['stations'].insert_one(station)