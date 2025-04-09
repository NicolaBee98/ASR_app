from utils.logging_setup import logger


class EventEmitter:
    def __init__(self):
        self.listeners = {}
        self.logger = logger

    def on(self, event_name, callback):
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)

    def emit(self, event_name, *args, **kwargs):
        avoid_list = ["update_performance_metrics"]
        if event_name not in avoid_list:
            self.logger.debug(f"Emitting event {event_name}")
        if event_name in self.listeners:
            for callback in self.listeners[event_name]:
                callback(*args, **kwargs)
