"""Temporary conversation memory (in process, with expiry). Fine for one server process on a laptop or a
single small VM; with several processes move it to Redis/DB (same interface).

* Conversation ids are unguessable random tokens. `owner` is None for anonymous users; once accounts
  exist, pass the user id and a conversation can only be opened by its owner.
* Whole TURNS are stored/trimmed, so a tool call is never separated from its tool result.
* Nothing is written to disk. Memory dies with the process or after the TTL."""
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from .types import Message


@dataclass
class Conversation:
    id: str
    owner: Optional[str]
    turns: list[list[Message]] = field(default_factory=list)
    state: dict = field(default_factory=dict)
    touched: float = 0.0


class ConversationStore:
    def __init__(self, ttl_s: int = 1800, max_conversations: int = 2000, max_turns: int = 8, clock: Callable[[], float] = time.monotonic):
        self._ttl, self._max, self._max_turns, self._clock = ttl_s, max_conversations, max_turns, clock
        self._items: dict[str, Conversation] = {}
        self._lock = threading.Lock()

    def _expire(self) -> None:
        now = self._clock()
        for cid in [c for c, v in self._items.items() if now - v.touched > self._ttl]:
            del self._items[cid]

    def create(self, owner: Optional[str] = None) -> Conversation:
        with self._lock:
            self._expire()
            while len(self._items) >= self._max:  # drop the least recently used
                oldest = min(self._items.values(), key=lambda c: c.touched)
                del self._items[oldest.id]
            conv = Conversation(secrets.token_urlsafe(16), owner, touched=self._clock())
            self._items[conv.id] = conv
            return conv

    def get(self, conversation_id: Optional[str], owner: Optional[str] = None) -> Optional[Conversation]:
        """None for unknown, expired, or someone else's conversation (the three are indistinguishable)."""
        if not conversation_id:
            return None
        with self._lock:
            self._expire()
            conv = self._items.get(conversation_id)
            if conv is None or conv.owner != owner:
                return None
            conv.touched = self._clock()
            return conv

    def messages(self, conv: Conversation) -> list[Message]:
        with self._lock:
            return [m for turn in conv.turns[-self._max_turns :] for m in turn]

    def add_turn(self, conv: Conversation, turn: list[Message]) -> None:
        with self._lock:
            conv.turns.append(turn)
            del conv.turns[: -self._max_turns]
            conv.touched = self._clock()

    def delete(self, conversation_id: str, owner: Optional[str] = None) -> bool:
        with self._lock:
            conv = self._items.get(conversation_id)
            if conv is None or conv.owner != owner:
                return False
            del self._items[conversation_id]
            return True
