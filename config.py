"""
Client / brand configuration.

Structure is built to support multiple clients and multiple brands per
client later, even though today there's only one of each.

To add a new brand for an existing client: add an entry under that
client's "brands" dict with its own collector IDs. No other code changes
needed.

To add a whole new client: add a new top-level key with its own
password env var name and its own brands.
"""

CLIENTS = {
    "texas-roadhouse": {
        "display_name": "Texas Roadhouse",
        # Name of the environment variable holding this client's login password.
        # Keeps the actual password out of source code.
        "password_env": "CLIENT_TEXAS_ROADHOUSE_PASSWORD",
        "brands": {
                "Texas Roadhouse": {
                "collector_ids": ["167930110", "176162591"],
                "survey_id": "128311344",
            },
            # Example of how a second brand would be added later:
            # "Bubba's 33": {
            #     "collector_ids": ["<collector id 1>", "<collector id 2>"],
            # },
        },
    },
}
