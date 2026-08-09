import pytest

from modules.ai_assistant import AIAssistantService
from modules.shared.contracts.interfaces import AIAssistant


class _FakeGenerator:
    def __init__(self, text):
        self._text = text
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self._text


def test_implements_contract():
    service = AIAssistantService(_FakeGenerator("hi"))
    assert isinstance(service, AIAssistant)


def test_chat_returns_text():
    service = AIAssistantService(_FakeGenerator("Nifty 50 index hota hai..."))
    reply = service.chat("u1", "RSI kya hai?")
    assert reply.text.startswith("Nifty 50")
    assert reply.action_taken is None
    assert reply.needs_confirmation is False


def test_chat_prompt_knows_existing_product_features():
    generator = _FakeGenerator("Current product context received")
    AIAssistantService(generator).chat("u1", "How can I improve the platform?")
    prompt = generator.prompts[0]
    assert "No-code Strategy Builder" in prompt
    assert "Do not present an existing capability" in prompt
    assert "NIFTY 50" in prompt


def test_chat_extracts_and_validates_code():
    gen = _FakeGenerator(
        "Yahan code hai:\n```python\nsignals = (data['close'] > data['close'].rolling(5).mean()).astype(int)\n```"
    )
    service = AIAssistantService(gen)
    reply = service.chat("u1", "buy when above sma5")
    assert reply.action_taken == "strategy_code_validated"
    assert reply.needs_confirmation is True


def test_chat_rejects_invalid_code():
    gen = _FakeGenerator("```python\nx = 1\n```")
    service = AIAssistantService(gen)
    reply = service.chat("u1", "something")
    assert reply.action_taken is None
    assert reply.needs_confirmation is False


def test_confirm_action_matching():
    service = AIAssistantService(_FakeGenerator(""))
    service.propose_action("u1", "run backtest")
    assert service.confirm_action("u1", "run backtest") is True


def test_confirm_action_mismatch():
    service = AIAssistantService(_FakeGenerator(""))
    service.propose_action("u1", "run backtest")
    assert service.confirm_action("u1", "sell everything") is False
    assert service.confirm_action("u1", "run backtest") is True


def test_review_journal_empty():
    service = AIAssistantService(_FakeGenerator("irrelevant"))
    assert "journal entries" in service.review_journal("u1", []).lower()


def test_review_journal_passes_entries():
    gen = _FakeGenerator("Pattern: aap choti positions bhi jaldi close karte ho.")
    service = AIAssistantService(gen)
    entries = [
        {
            "symbol": "AAPL",
            "side": "BUY",
            "pnl": 120.0,
            "rating": 4,
            "tags": ["momentum"],
            "note": "Breakout entry, good setup",
            "lesson": "hold longer",
        },
        {
            "symbol": "TSLA",
            "side": "SELL",
            "pnl": -80.0,
            "rating": 2,
            "tags": ["revenge"],
            "note": "entered too fast after loss",
            "lesson": "no revenge trades",
        },
    ]
    text = service.review_journal("u1", entries)
    assert "Pattern" in text
    assert "AAPL" in gen.prompts[0]
    assert "revenge" in gen.prompts[0]


def test_review_journal_provider_error():
    class _Boom:
        def generate(self, prompt):
            raise RuntimeError("network down")

    service = AIAssistantService(_Boom())
    assert "unavailable" in service.review_journal("u1", [{"symbol": "X"}]).lower()
