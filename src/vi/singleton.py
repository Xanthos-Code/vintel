# Thread safe Singelton

import threading


class Singleton(type):
    """ A singleton metaclass. """

    def __init__(cls, name, bases, dictionary):
        super(Singleton, cls).__init__(name, bases, dictionary)
        cls._instance = None
        cls._rlock = threading.RLock()

    def __call__(cls, *args, **kws):
        with cls._rlock:
            if cls._instance is None:
                cls._instance = super(Singleton, cls).__call__(*args, **kws)
        return cls._instance


'''
	Example usage - its that simple!

	class Sound():
		__metaclass__ = Singleton
'''
