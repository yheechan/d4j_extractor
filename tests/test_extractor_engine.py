from lib.extractor_engine import ExtractorEngine

def test_extractor_engine_initialization():
    engine = ExtractorEngine()
    assert engine is not None, "ExtractorEngine should be initialized."

    assert engine.slack is not None, "ExtractorEngine should initialize Slack client."
    assert engine.slack.channel_name is not None, "Slack channel name should be set."
    assert engine.slack.bot_name == "Extractor Engine", "Bot name should be 'Extractor Engine'."
    assert engine.slack.deactivated is False, "Slack client should not be deactivated."
    
    assert engine.db is not None, "ExtractorEngine should initialize Database client."
    assert engine.db.host is not None, "Database host should be set."
    assert engine.db.port is not None, "Database port should be set."
    assert engine.db.user is not None, "Database user should be set."
    assert engine.db.password is not None, "Database password should be set."
    assert engine.db.database is not None, "Database name should be set."
    
    # Check if the environment variables are loaded correctly
    print("SLACK_CHANNEL:", engine.os_copy.get("SLACK_CHANNEL"))
    print("SLACK_TOKEN:", engine.os_copy.get("SLACK_TOKEN"))

