from abc import ABC, abstractmethod
import numpy as np


class BaseAPI(ABC):
    @abstractmethod
    def insert_audio_chunk(self, chunk: np.ndarray):
        pass

    @abstractmethod
    def process_audio(self):
        pass
