"""
Factory to instantiate the appropriate Twitter client v2 based on TWITTER_MODE.
Uses Bearer for reads and OAuth1a for writes in live mode.
"""
from src.config import Config
from src.twitter_client_v2_new import TwitterClientV2New
from src.twitter_client_dryrun_v2 import TwitterClientDryRunV2
from src.twitter_client_mock_v2 import TwitterClientMockV2


def make_twitter_client():
    """
    Create appropriate Twitter client v2 based on mode.
    
    Modes:
    - live: Uses TwitterClientV2New (Bearer reads, OAuth1a writes)
    - dryrun: Uses TwitterClientDryRunV2 that writes to outbox
    - mock: Uses TwitterClientMockV2 for testing with mock data
    """
    mode = (Config.TWITTER_MODE or "live").lower()
    if mode == "mock":
        return TwitterClientMockV2()
    if mode == "dryrun":
        return TwitterClientDryRunV2()
    return TwitterClientV2New()



