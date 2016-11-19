
def exposify(cls):
	# cls.__dict__ does not include inherited members, so we can't use that.
	for key in dir(cls):
		val = getattr(cls, key)
		if callable(val) and not key.startswith("_"):
			setattr(cls, "exposed_%s" % (key,), val)

	return cls

class Singleton:
	"""
	A non-thread-safe helper class to ease implementing singletons.
	This should be used as a decorator -- not a metaclass -- to the
	class that should be a singleton.

	The decorated class can define one `__init__` function that
	takes only the `self` argument. Other than that, there are
	no restrictions that apply to the decorated class.

	To get the singleton instance, use the `Instance` method. Trying
	to use `__call__` will result in a `TypeError` being raised.

	Limitations: The decorated class cannot be inherited from.

	"""

	def __init__(self, decorated):
		self._decorated = decorated

	def Instance(self):
		"""
		Returns the singleton instance. Upon its first call, it creates a
		new instance of the decorated class and calls its `__init__` method.
		On all subsequent calls, the already created instance is returned.

		"""
		try:
			print("Getting instance!", self._instance)
			return self._instance
		except AttributeError:
			self._instance = self._decorated()
			print("Creating instance: ", self._instance, self._decorated)
			return self._instance

	def __call__(self):
		raise TypeError('Singletons must be accessed through `Instance()`.')

	def __instancecheck__(self, inst):
		return isinstance(inst, self._decorated)