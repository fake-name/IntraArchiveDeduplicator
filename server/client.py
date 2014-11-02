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
	print(db)
	print(db.keyToCol)
	print(db.getItems)


if __name__ == "__main__":
	go()
