SCHEDULERS = {}


def register_scheduler(name):
    def _decorator(cls):
        SCHEDULERS[cls.__module__ + '.' + cls.__qualname__] = (name, cls)
        return cls

    return _decorator
