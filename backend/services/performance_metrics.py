import time

class PerformanceTimer:
    def __init__(self):
        self.metrics = {}

    def start(self, name):
        self.metrics[name] = time.perf_counter()

    def stop(self, name):
        self.metrics[name] = round(
            (time.perf_counter() - self.metrics[name]) * 1000,
            2
        )

    def get_metrics(self):
        return self.metrics