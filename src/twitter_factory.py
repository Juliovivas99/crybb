"""
Factory to instantiate the appropriate Twitter client based on TWITTER_MODE.
"""
from .config import Config
from .twitter_client_live import TwitterClientLive
from .twitter_client_dryrun import TwitterClientDryRun
from .twitter_client_mock import TwitterClientMock


def make_twitter_client():
    mode = (Config.TWITTER_MODE or "live").lower()
    if mode == "mock":
        return TwitterClientMock()
    if mode == "dryrun":
        return TwitterClientDryRun()
    return TwitterClientLive()



