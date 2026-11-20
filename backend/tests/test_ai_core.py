import asyncio
import unittest

from app.ai.errors import AIError, LLMRejected, LLMUnavailable, TransportError, ToolError
from app.ai.itinerary import Stop, best_order, summarize
from app.ai.language import detect_language
from app.ai.llm import anthropic as anth
from app.ai.llm import openai_compat as oai
from app.ai.llm.base import post_with_retry
from app.ai.memory import ConversationStore
from app.ai.types import Message, ToolCall, ToolSpec
from app.ai.validation import validate_args

SCHEMA = {
    "type": "object", "required": ["q"],
    "properties": {
        "q": {"type": "string", "minLength": 1, "maxLength": 5},
        "n": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
        "x": {"type": "number", "minimum": -90, "maximum": 90},
        "mode": {"type": "string", "enum": ["car", "walking"]},
        "ids": {"type": "array", "items": {"type": "string"}, "maxItems": 2},
    },
}


def code_of(fn):
    try:
        fn()
    except ToolError as e:
        return e.code
    return None


class Validation(unittest.TestCase):
    def test_ok_and_defaults(self):
        self.assertEqual(validate_args({"q": " ab "}, SCHEMA), {"q": "ab", "n": 5})

    def test_rejections(self):
        for bad in [{}, {"q": "toolong"}, {"q": "a", "n": "3"}, {"q": "a", "n": True}, {"q": "a", "n": 2.5}, {"q": "a", "x": 91},
                    {"q": "a", "x": float("nan")}, {"q": "a", "mode": "plane"}, {"q": "a", "evil": 1}, {"q": "a", "ids": ["1", "2", "3"]},
                    {"q": "a", "ids": [1]}, {"q": 5}]:
            self.assertEqual(code_of(lambda: validate_args(bad, SCHEMA)), "invalid_arguments", bad)
        self.assertEqual(code_of(lambda: validate_args("nope", SCHEMA)), "invalid_arguments")

    def test_float_integer_accepted(self):
        self.assertEqual(validate_args({"q": "a", "n": 3.0}, SCHEMA)["n"], 3)


class Language(unittest.TestCase):
    def test_detect(self):
        self.assertEqual(detect_language("نزدیک‌ترین جای تاریخی کجاست؟"), "fa")
        self.assertEqual(detect_language("Which historical places are near me?"), "en")
        self.assertEqual(detect_language("قره‌کلیسا Qareh Kelisa چطور برم"), "fa")
        self.assertEqual(detect_language("123 ?", default="en"), "en")


class Memory(unittest.TestCase):
    def test_ttl_cap_trim_and_isolation(self):
        now = [0.0]
        st = ConversationStore(ttl_s=100, max_conversations=2, max_turns=2, clock=lambda: now[0])
        a = st.create("alice")
        self.assertIsNone(st.get(a.id, "bob"))  # someone else's conversation
        self.assertIsNone(st.get(a.id, None))  # anonymous cannot open a user's conversation
        self.assertIs(st.get(a.id, "alice"), a)
        for i in range(3):
            st.add_turn(a, [Message("user", f"u{i}"), Message("assistant", f"a{i}")])
        self.assertEqual([m.content for m in st.messages(a)], ["u1", "a1", "u2", "a2"])  # whole turns only
        now[0] = 500
        self.assertIsNone(st.get(a.id, "alice"))  # expired
        st.create(); st.create(); st.create()
        self.assertLessEqual(len(st._items), 2)
        self.assertIsNone(st.get("unknown"))


class Itinerary(unittest.TestCase):
    def test_order_is_shortest_path(self):
        a, b, c = Stop("a", "A", 39.0, 44.0), Stop("b", "B", 39.0, 44.5), Stop("c", "C", 39.0, 44.1)
        self.assertEqual([s.id for s in best_order((39.0, 44.0), [b, c, a])], ["a", "c", "b"])
        self.assertEqual([s.id for s in best_order(None, [b, a, c])], ["a", "c", "b"])
        self.assertEqual(best_order(None, []), [])

    def test_summary_never_claims_without_routed_legs(self):
        routed = {"source": "routing", "duration_min": 30, "distance_km": 20}
        est = {"source": "straight_line_estimate_only", "duration_min": None, "distance_km": 9}
        s = summarize([routed, est], 2)
        self.assertIsNone(s["total_travel_min"]); self.assertIsNone(s["travel_time_fits_available_time"])
        s = summarize([routed, routed], 2)
        self.assertEqual((s["total_travel_min"], s["travel_time_fits_available_time"]), (60, True))
        self.assertFalse(summarize([routed, routed], 0.5)["travel_time_fits_available_time"])
        self.assertFalse(s["visit_durations_known"])


class Providers(unittest.IsolatedAsyncioTestCase):
    def test_anthropic_build_groups_tool_results(self):
        msgs = [Message("user", "hi"), Message("assistant", "", [ToolCall("1", "a", {"x": 1}), ToolCall("2", "b", {})]),
                Message("tool", "r1", tool_call_id="1"), Message("tool", "r2", tool_call_id="2"), Message("assistant", "done")]
        out = anth.build_messages(msgs)
        self.assertEqual([m["role"] for m in out], ["user", "assistant", "user", "assistant"])
        self.assertEqual([b["tool_use_id"] for b in out[2]["content"]], ["1", "2"])
        self.assertEqual(out[1]["content"][0]["type"], "tool_use")

    def test_anthropic_parse(self):
        r = anth.parse_response({"content": [{"type": "text", "text": "hello "}, {"type": "tool_use", "id": "t", "name": "n", "input": {"a": 1}}],
                                 "usage": {"input_tokens": 7, "output_tokens": 3}}, "m")
        self.assertEqual((r.text, r.tool_calls[0].arguments, r.usage.input_tokens), ("hello ", {"a": 1}, 7))
        with self.assertRaises(AIError):
            anth.parse_response({"nope": 1}, "m")

    def test_openai_build_and_parse(self):
        out = oai.build_messages("SYS", [Message("user", "u"), Message("assistant", "", [ToolCall("1", "n", {"a": "قره"})]), Message("tool", "r", tool_call_id="1")])
        self.assertEqual([m["role"] for m in out], ["system", "user", "assistant", "tool"])
        self.assertIn("قره", out[2]["tool_calls"][0]["function"]["arguments"])
        r = oai.parse_response({"choices": [{"message": {"content": None, "tool_calls": [
            {"id": "1", "function": {"name": "n", "arguments": "{bad json"}}]}}], "usage": {"prompt_tokens": 4, "completion_tokens": 2}}, "m")
        self.assertIn("__invalid_json__", r.tool_calls[0].arguments)  # will be rejected by validation
        self.assertEqual(r.usage.output_tokens, 2)

    async def test_retry_policy(self):
        sleeps = []

        async def sleep(s): sleeps.append(s)

        def poster(seq):
            items = list(seq)

            async def post(*a):
                it = items.pop(0)
                if isinstance(it, Exception):
                    raise it
                return it
            return post

        run = lambda seq, retries=2: post_with_retry(poster(seq), "u", {}, {}, provider="p", timeout_s=1, retries=retries, sleep=sleep)  # noqa: E731
        self.assertEqual(await run([(503, {}), TransportError("t"), (200, {"ok": 1})]), {"ok": 1})
        self.assertEqual(sleeps, [0.5, 1.0])
        with self.assertRaises(LLMUnavailable):
            await run([(503, {})] * 3)
        with self.assertRaises(LLMRejected) as cm:
            await run([(401, {"error": "secret-bearing text"})])
        self.assertNotIn("secret", str(cm.exception))
        with self.assertRaises(LLMRejected):
            await run([(400, {})])  # not retried


if __name__ == "__main__":
    unittest.main()
