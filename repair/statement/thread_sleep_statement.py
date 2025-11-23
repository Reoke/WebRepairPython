import time

from repair.statement.statement import Statement


class ThreadSleepStatement(Statement):

    def __init__(self, sleep_time):
        self.sleep_time = sleep_time

    def act(self):
        time.sleep(self.sleep_time)

    def __repr__(self):
        return 'time.sleep(' + repr(self.sleep_time) + ')'