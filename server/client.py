import rpyc
import time

def go():
	conn = rpyc.connect("localhost", 12345)
	print(dir(conn.root))
	x = conn.root.isBinaryUnique()
	print("exiting")
if __name__ == "__main__":
	go()
