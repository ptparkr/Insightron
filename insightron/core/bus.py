from dataclasses import dataclass, field
from typing import Callable, Any, Optional
from enum import Enum, auto
from datetime import datetime
import threading
import weakref


class EventType(Enum):
    """Core event types for the message bus."""

    TRANSCRIPTION_STARTED = auto()
    TRANSCRIPTION_PROGRESS = auto()
    TRANSCRIPTION_COMPLETED = auto()
    TRANSCRIPTION_FAILED = auto()
    BATCH_STARTED = auto()
    BATCH_PROGRESS = auto()
    BATCH_COMPLETED = auto()
    MODEL_LOADED = auto()
    MODEL_UNLOADED = auto()
    CONFIG_RELOADED = auto()
    ERROR = auto()


@dataclass
class Event:
    """Lightweight event container."""

    type: EventType
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None


class MessageBus:
    """
    O(1) publish/subscribe message bus for inter-component communication.
    Thread-safe event dispatch with weak references to prevent leaks.
    """

    _instance: Optional["MessageBus"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = object.__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._subscribers: dict[EventType, list[weakref.ref[Callable]]] = {}
        self._global_subscribers: list[weakref.ref[Callable]] = []
        self._sub_lock = threading.Lock()

    def subscribe(
        self, handler: Callable[[Event], None], event_type: Optional[EventType] = None
    ) -> Callable[[], None]:
        """
        Subscribe to events. O(1) registration.
        Returns unsubscribe function.
        """
        ref = weakref.ref(handler)

        with self._sub_lock:
            if event_type is None:
                self._global_subscribers.append(ref)
            else:
                if event_type not in self._subscribers:
                    self._subscribers[event_type] = []
                self._subscribers[event_type].append(ref)

        def unsubscribe():
            with self._sub_lock:
                if event_type is None:
                    self._global_subscribers = [
                        r for r in self._global_subscribers if r is not ref and r() is not None
                    ]
                else:
                    self._subscribers[event_type] = [
                        r
                        for r in self._subscribers.get(event_type, [])
                        if r is not ref and r() is not None
                    ]

        return unsubscribe

    def publish(self, event: Event) -> None:
        """
        Fire-and-forget event dispatch. O(n) where n = subscribers.
        """
        handlers = []

        with self._sub_lock:
            # Get global handlers
            for ref in self._global_subscribers:
                handler = ref()
                if handler is not None:
                    handlers.append(handler)

            # Get specific handlers
            for ref in self._subscribers.get(event.type, []):
                handler = ref()
                if handler is not None:
                    handlers.append(handler)

        # Dispatch outside lock
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass  # Swallow handler errors

    def clear(self) -> None:
        """Clear all subscriptions."""
        with self._sub_lock:
            self._subscribers.clear()
            self._global_subscribers.clear()


# Convenience functions
_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """Get global message bus instance."""
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus


def emit(event_type: EventType, data: dict = None, source: str = None) -> None:
    """Emit an event."""
    bus = get_message_bus()
    bus.publish(Event(type=event_type, data=data or {}, source=source))


def on(event_type: EventType, handler: Callable[[Event], None]) -> Callable[[], None]:
    """Subscribe to an event type."""
    bus = get_message_bus()
    return bus.subscribe(handler, event_type)
