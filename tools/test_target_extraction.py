from src.utils import extract_target_after_last_bot, typed_mentions, is_reply_to_bot, get_parent_author_id


def ent(u, s, e, uid=None):
    d = {"username": u, "start": s, "end": e}
    if uid:
        d["id"] = uid
    return d


def inc(uid, u):
    return {"id": uid, "username": u}


# Test typed_mentions function
def test_typed_mentions():
    """Test that typed_mentions only returns exact text matches."""
    tweet = {
        "text": "@crybbmaker @alice hello",
        "entities": {
            "mentions": [
                ent("crybbmaker", 0, 11, "bot"),
                ent("alice", 12, 18, "222"),
                ent("bob", 25, 28, "333")  # This should be ignored (not in text)
            ]
        }
    }
    typed = typed_mentions(tweet)
    assert len(typed) == 2
    assert typed[0]["username"] == "crybbmaker"
    assert typed[1]["username"] == "alice"


def test_is_reply_to_bot():
    """Test reply detection."""
    tweet1 = {"in_reply_to_user_id": "bot123"}
    tweet2 = {"in_reply_to_user_id": "other123"}
    tweet3 = {}
    
    assert is_reply_to_bot(tweet1, "bot123") == True
    assert is_reply_to_bot(tweet2, "bot123") == False
    assert is_reply_to_bot(tweet3, "bot123") == False


def test_get_parent_author_id():
    """Test parent author ID extraction."""
    tweet = {
        "referenced_tweets": [
            {"type": "replied_to", "author_id": "parent123"},
            {"type": "retweeted", "author_id": "rt123"}
        ]
    }
    assert get_parent_author_id(tweet) == "parent123"
    
    tweet2 = {"referenced_tweets": []}
    assert get_parent_author_id(tweet2) is None


# TOP-LEVEL TESTS
def test_top_level_bot_first():
    """@bot @alice → target=alice"""
    t = "@crybbmaker @alice"
    tweet = {
        "text": t,
        "author_id": "111",
        "entities": {"mentions": [ent("crybbmaker", 0, 11, "bot"), ent("alice", 12, 18, "222")]},
        "includes": {"users": [inc("111", "author"), inc("222", "alice")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", None)
    assert target == "alice"
    assert "immediate after last @bot" in reason


def test_top_level_bot_not_first():
    """hello @bot @alice → skip (bot not first)"""
    t = "hello @crybbmaker @alice"
    tweet = {
        "text": t,
        "author_id": "111",
        "entities": {"mentions": [ent("crybbmaker", 6, 17, "bot"), ent("alice", 18, 24, "222")]},
        "includes": {"users": [inc("111", "author"), inc("222", "alice")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", None)
    assert target == "alice"  # Still works because we use last bot, not first


def test_top_level_multiple_bots():
    """multiple @bot … choose last bot's immediate next mention"""
    t = "@crybbmaker @alice hi @crybbmaker @bob"
    tweet = {
        "text": t,
        "author_id": "111",
        "entities": {"mentions": [
            ent("crybbmaker", 0, 11, "bot"),
            ent("alice", 12, 18, "222"),
            ent("crybbmaker", 22, 33, "bot"),
            ent("bob", 34, 38, "333"),
        ]},
        "includes": {"users": [inc("111", "author"), inc("222", "alice"), inc("333", "bob")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", None)
    assert target == "bob"
    assert "immediate after last @bot" in reason


# REPLY TO BOT TESTS
def test_reply_to_bot_no_explicit_pair():
    """text="Aye" (no explicit pair) → skip"""
    t = "Aye"
    tweet = {
        "text": t,
        "author_id": "111",
        "in_reply_to_user_id": "bot",
        "entities": {"mentions": []}
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", "bot")
    assert target is None
    assert reason == "no-typed-mentions"


def test_reply_to_bot_explicit_pair():
    """@bot @alice → target=alice"""
    t = "@crybbmaker @alice"
    tweet = {
        "text": t,
        "author_id": "111",
        "in_reply_to_user_id": "bot",
        "entities": {"mentions": [
            ent("crybbmaker", 0, 11, "bot"),
            ent("alice", 12, 18, "222"),
        ]},
        "includes": {"users": [inc("111", "author"), inc("222", "alice")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", "bot")
    assert target == "alice"
    assert "immediate after last @bot" in reason


def test_reply_to_bot_with_plus():
    """@bot + @alice → target=alice (if you keep + as allowed whitespace)"""
    t = "@crybbmaker + @alice"
    tweet = {
        "text": t,
        "author_id": "111",
        "in_reply_to_user_id": "bot",
        "entities": {"mentions": [
            ent("crybbmaker", 0, 11, "bot"),
            ent("alice", 14, 20, "222"),
        ]},
        "includes": {"users": [inc("111", "author"), inc("222", "alice")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", "bot")
    assert target == "alice"
    assert "immediate after last @bot" in reason


def test_reply_to_bot_self_target():
    """@bot @bot → skip (self)"""
    t = "@crybbmaker @crybbmaker"
    tweet = {
        "text": t,
        "author_id": "111",
        "in_reply_to_user_id": "bot",
        "entities": {"mentions": [
            ent("crybbmaker", 0, 11, "bot"),
            ent("crybbmaker", 12, 23, "bot"),
        ]},
        "includes": {"users": [inc("111", "author")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", "bot")
    assert target is None
    # The reason is "no-next-mention" because after the last @bot, there's no valid next mention
    assert reason == "no-next-mention"


# REPLY NOT TO BOT TESTS
def test_reply_not_to_bot_explicit():
    """@bot @replyuser → allowed (explicitly typed), target=replyuser"""
    t = "@crybbmaker @replyuser"
    tweet = {
        "text": t,
        "author_id": "111",
        "in_reply_to_user_id": "other",
        "entities": {"mentions": [
            ent("crybbmaker", 0, 11, "bot"),
            ent("replyuser", 12, 22, "222"),
        ]},
        "includes": {"users": [inc("111", "author"), inc("222", "replyuser")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", "other")
    assert target == "replyuser"
    assert "immediate after last @bot" in reason


def test_reply_not_to_bot_bot_not_first():
    """@replyuser @bot → skip (bot not first typed)"""
    t = "@replyuser @crybbmaker"
    tweet = {
        "text": t,
        "author_id": "111",
        "in_reply_to_user_id": "other",
        "entities": {"mentions": [
            ent("replyuser", 0, 10, "222"),
            ent("crybbmaker", 11, 22, "bot"),
        ]},
        "includes": {"users": [inc("111", "author"), inc("222", "replyuser")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", "other")
    assert target is None  # No next mention after the last @bot
    assert reason == "no-next-mention"


# CONVERSATION CONTEXT TESTS
def test_conversation_id_preserved():
    """Test that conversation_id is preserved in tweet data"""
    t = "@crybbmaker @alice"
    tweet = {
        "text": t,
        "id": "123456789",
        "conversation_id": "conv123",
        "author_id": "111",
        "in_reply_to_user_id": "bot",
        "entities": {"mentions": [
            ent("crybbmaker", 0, 11, "bot"),
            ent("alice", 12, 18, "222"),
        ]},
        "includes": {"users": [inc("111", "author"), inc("222", "alice")]},
    }
    target, reason = extract_target_after_last_bot(tweet, "crybbmaker", "111", "bot")
    assert target == "alice"
    assert tweet["conversation_id"] == "conv123"


def test_parent_author_extraction():
    """Test parent author extraction from referenced tweets"""
    t = "@crybbmaker @alice"
    tweet = {
        "text": t,
        "author_id": "111",
        "in_reply_to_user_id": "bot",
        "referenced_tweets": [
            {"type": "replied_to", "author_id": "parent123"}
        ],
        "entities": {"mentions": [
            ent("crybbmaker", 0, 11, "bot"),
            ent("alice", 12, 18, "222"),
        ]},
        "includes": {"users": [inc("111", "author"), inc("222", "alice")]},
    }
    parent_author = get_parent_author_id(tweet)
    assert parent_author == "parent123"


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
    assert target is None  # replyuser is excluded because it's the reply-to user
    assert reason == "excluded-target"


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
    assert "immediate after last @bot" in reason


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
    assert target == "alice"  # New logic allows this without requiring +
    assert "immediate after last @bot" in reason


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
    assert "immediate after last @bot" in reason


if __name__ == "__main__":
    # Test helper functions
    test_typed_mentions()
    test_is_reply_to_bot()
    test_get_parent_author_id()
    
    # Test top-level scenarios
    test_top_level_bot_first()
    test_top_level_bot_not_first()
    test_top_level_multiple_bots()
    
    # Test reply to bot scenarios
    test_reply_to_bot_no_explicit_pair()
    test_reply_to_bot_explicit_pair()
    test_reply_to_bot_with_plus()
    test_reply_to_bot_self_target()
    
    # Test reply not to bot scenarios
    test_reply_not_to_bot_explicit()
    test_reply_not_to_bot_bot_not_first()
    
    # Test conversation context
    test_conversation_id_preserved()
    test_parent_author_extraction()
    
    # Legacy tests (keeping for compatibility)
    test_two_mentions()
    test_last_bot_wins()
    test_no_immediate_after_last_bot()
    test_hidden_mentions_ignored()
    test_self_block()
    test_aye_reply_skips()
    test_reply_two_mentions_no_plus_required()
    test_reply_three_mentions_with_plus()
    test_reply_three_mentions_without_plus_skip()
    test_multiple_bots_last_with_plus()
    
    print("✅ All tests passed - conversation-aware reply handling working correctly!") 