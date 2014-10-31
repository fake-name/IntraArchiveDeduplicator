import rpyc
import time

def go():
	conn = rpyc.connect("localhost", 12345)
	print(dir(conn.root))

	conn.root.loadTree('/media/Storage/MP/Absolute Duo [+++]/')
	x = conn.root.ArchChecker('/media/Storage/MP/Absolute Duo [+++]/Absolute Duo - - (1) - Copy.zip')
	print("Binary Unique = ", x.isBinaryUnique())
	print("pHash  Unique = ", x.isPhashUnique())
	print(x)
	print("exiting")

	conn.root.reloadTree()
	print("Binary Unique = ", x.isBinaryUnique())
	print("pHash  Unique = ", x.isPhashUnique(searchDistance=8))
	print(x)
	print("exiting")


if __name__ == "__main__":
	go()
