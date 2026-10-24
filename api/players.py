"""Profile and career statistics endpoints, requested only on user action."""

from api.client import identifier


def profile(client, player_id):
    return client.get(f"/stats/v1/player/{identifier(player_id)}")


def batting(client, player_id):
    return client.get(f"/stats/v1/player/{identifier(player_id)}/batting")


def bowling(client, player_id):
    return client.get(f"/stats/v1/player/{identifier(player_id)}/bowling")
