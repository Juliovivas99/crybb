from src.utils import extract_target_after_last_bot


def ent(u, s, e, uid=None):
    d = {"username": u, "start": s, "end": e}
    if uid:
        d["id"] = uid
    return d


def inc(uid, u):
    return {"id": uid, "username": u}


# 1) Two mentions: @bot @alice -> alice

def test_two_mentions():
    t = "@crybbmaker @alice"
    tweet = {
        "text": t,
        "author_id": "111",
        "entities": {"mentions": [ent("crybbmaker", 0, 11, "bot"), ent("alice", 12, 18, "222")]},
        "includes": {"users": [inc("111", "author"), inc("222", "alice")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", None)
    assert target == "alice"
    assert isinstance(reason, str) and len(reason) > 0


# 2) Multi: pick immediate after LAST @bot

def test_last_bot_wins():
    t = "@crybbmaker @alice hi @crybbmaker + @bob"
    tweet = {
        "text": t,
        "author_id": "111",
        "entities": {"mentions": [
            ent("crybbmaker", 0, 11, "bot"),
            ent("alice", 12, 18, "222"),
            ent("crybbmaker", 22, 33, "bot"),
            ent("bob", 36, 40, "333"),
        ]},
        "includes": {"users": [inc("111", "author"), inc("222", "alice"), inc("333", "bob")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", None)
    assert target == "bob"
    assert isinstance(reason, str) and len(reason) > 0


# 3) Missing immediate target after last bot -> None

def test_no_immediate_after_last_bot():
    t = "@crybbmaker hello world"
    tweet = {"text": t, "author_id": "111", "entities": {"mentions": [ent("crybbmaker", 0, 11, "bot")]}}
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", None)
    assert target is None
    assert isinstance(reason, str) and len(reason) > 0


# 4) Hidden/ghost mentions ignored (offsets must match @text)

def test_hidden_mentions_ignored():
    t = "LFG"
    tweet = {"text": t, "author_id": "111", "entities": {"mentions": [ent("crybbmaker", 0, 11, "bot")]}}
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", None)
    assert target is None
    assert isinstance(reason, str) and len(reason) > 0


# 5) Self-PFP blocked (author)

def test_self_block():
    t = "@crybbmaker @author"
    tweet = {
        "text": t,
        "author_id": "111",
        "entities": {"mentions": [ent("crybbmaker", 0, 11, "bot"), ent("author", 12, 19, "111")]},
        "includes": {"users": [inc("111", "author")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", None)
    assert target is None
    assert isinstance(reason, str) and len(reason) > 0


# 6) Reply “Aye” to bot with no explicit pair -> None

def test_aye_reply_skips():
    t = "Aye"
    tweet = {"text": t, "author_id": "111", "in_reply_to_user_id": "bot", "entities": {"mentions": []}}
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", "bot")
    assert target is None
    assert isinstance(reason, str) and len(reason) > 0


# 7) Duplicate typed mention immediately after target: dedupe but same target

def test_duplicate_typed_mention_after_target():
    t = "@crybbmaker @alice @alice"
    tweet = {
        "text": t,
        "author_id": "111",
        "entities": {"mentions": [
            ent("crybbmaker", 0, 11, "bot"),
            ent("alice", 12, 18, "222"),
            ent("alice", 19, 25, "222"),
        ]},
        "includes": {"users": [inc("111", "author"), inc("222", "alice")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", None)
    assert target == "alice"
    assert "immediate after last @bot" in reason


# 8) Reply, exactly 2 mentions: @bot @replyuser -> replyuser (no plus required)

def test_reply_two_mentions_no_plus_required():
    t = "@crybbmaker @replyuser"
    tweet = {
        "text": t,
        "author_id": "111",
        "in_reply_to_user_id": "222",
        "entities": {"mentions": [
            ent("crybbmaker", 0, 11, "bot"),
            ent("replyuser", 12, 22, "222"),
        ]},
        "includes": {"users": [inc("111", "author"), inc("222", "replyuser")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", "222")
    assert target == "replyuser"
    assert "immediate after last @bot" in reason


# 9) Reply, 3 mentions with plus: require plus

def test_reply_three_mentions_with_plus():
    t = "@crybbmaker + @alice @extra"
    tweet = {
        "text": t,
        "author_id": "111",
        "in_reply_to_user_id": "999",
        "entities": {"mentions": [
            ent("crybbmaker", 0, 11, "bot"),
            ent("alice", 14, 20, "222"),
            ent("extra", 21, 27, "333"),
        ]},
        "includes": {"users": [inc("111", "author"), inc("222", "alice"), inc("333", "extra")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", "999")
    assert target == "alice"
    assert "require-plus" in reason


# 10) Reply, 3 mentions without plus: skip

def test_reply_three_mentions_without_plus_skip():
    t = "@crybbmaker @alice @extra"
    tweet = {
        "text": t,
        "author_id": "111",
        "in_reply_to_user_id": "999",
        "entities": {"mentions": [
            ent("crybbmaker", 0, 11, "bot"),
            ent("alice", 12, 18, "222"),
            ent("extra", 19, 25, "333"),
        ]},
        "includes": {"users": [inc("111", "author"), inc("222", "alice"), inc("333", "extra")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", "999")
    assert target is None
    assert reason == "require-plus-gap-missing"


# 11) Multiple bots, pick last bot immediate next with plus

def test_multiple_bots_last_with_plus():
    t = "@x @crybbmaker @a hi @crybbmaker + @b @c"
    tweet = {
        "text": t,
        "author_id": "111",
        "in_reply_to_user_id": "999",
        "entities": {"mentions": [
            ent("x", 0, 2, "x"),
            ent("crybbmaker", 3, 14, "bot"),
            ent("a", 15, 17, "a"),
            ent("crybbmaker", 21, 32, "bot"),
            ent("b", 35, 37, "b"),
            ent("c", 38, 40, "c"),
        ]},
        "includes": {"users": [inc("111", "author"), inc("b", "b"), inc("c", "c"), inc("a", "a")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", "999")
    assert target == "b"
    assert "require-plus" in reason


if __name__ == "__main__":
    test_two_mentions()
    test_last_bot_wins()
    test_no_immediate_after_last_bot()
    test_hidden_mentions_ignored()
    test_self_block()
    test_aye_reply_skips()
    print("✅ Extraction OK") 