import queue
from multiprocessing.managers import BaseManager


_finish_queue         = queue.Queue()
_transition_queue     = queue.Queue()
_policy_dict          = {}


class TrainingManager(BaseManager):
    pass

TrainingManager.register('get_finish_queue',         callable=lambda: _finish_queue)
TrainingManager.register('get_transition_queue',     callable=lambda: _transition_queue)
TrainingManager.register('get_policy_dict',          callable=lambda: _policy_dict)
