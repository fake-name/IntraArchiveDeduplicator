



def binStrToInt(inStr):
	if len(inStr) != 64:
		raise ValueError("Input strings must be 64 chars long!")
	ret = 0
	mask = 1 << len(inStr) - 1
	for char in inStr:  # Specify memory order, so we're (theoretically) platform agnostic
		if char == '1':
			ret |= mask
		mask >>= 1

	# Convert to signed representation
	VALSIZE = 64
	if ret >= 2**(VALSIZE-1):
		ret = ret - 2**VALSIZE
	return ret


def binary_array_to_int(arr):
	ret = 0
	arr = arr.flatten()
	arr = arr[::-1]
	for i,v in enumerate(arr):
		if v:
			ret += 1 << i

	VALSIZE = 64
	if ret >= 2**(VALSIZE-1):
		ret = ret - 2**VALSIZE

	return ret
