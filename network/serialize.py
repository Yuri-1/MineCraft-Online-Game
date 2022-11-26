from .event import *
import pickle

def serialize_event(event: Event) -> bytes:
    return pickle.dumps(event)

def deserialize_event(data: bytes) -> Event:
    return pickle.loads(data)