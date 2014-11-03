import rpyc
import time

def go():
	conn = rpyc.connect("localhost", 12345)
	print(dir(conn.root))

	# conn.root.loadTree('/media/Storage/MP/Absolute Duo [+++]/')
	# x = conn.root.ArchChecker('/media/Storage/MP/Absolute Duo [+++]/Absolute Duo - - (1).zip')
	# print("Binary Unique = ", x.isBinaryUnique())
	# print("pHash  Unique = ", x.isPhashUnique())
	# print(x)
	# print("exiting")

	# conn.root.reloadTree()
	# print("Binary Unique = ", x.isBinaryUnique())
	# print("pHash  Unique = ", x.isPhashUnique())
	# print(x)
	# print("exiting")

	db = conn.root.DbApi()
	print(db.doLoad())
	print(db)
	print(db.keyToCol)
	print(db.getItems)
	matches = db.getWithinDistance(0)
	print(len(matches))
	matches = db.getWithinDistance(55)
	print(len(matches))
	matches = db.getWithinDistance(1111155)
	print(len(matches))
	matches = db.getWithinDistance(11111550000)
	print(len(matches))
	matches = db.getWithinDistance(111115500000)
	print(len(matches))
	matches = db.getWithinDistance(1111155000000)
	print(len(matches))


if __name__ == "__main__":
	go()
