
def exposify(cls):
	# cls.__dict__ does not include inherited members, so we can't use that.
	for key in dir(cls):
		val = getattr(cls, key)
		if callable(val) and not key.startswith("_"):
			setattr(cls, "exposed_%s" % (key,), val)

	return cls

