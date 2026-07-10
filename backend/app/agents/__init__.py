"""Agent registry."""
from app.agents.research import ResearchAgent
from app.agents.script import ScriptAgent
from app.agents.voiceover import VoiceoverAgent
from app.agents.visuals import VisualsAgent
from app.agents.captions import CaptionsAgent
from app.agents.render import RenderAgent
from app.agents.seo import SeoAgent
from app.agents.thumbnail import ThumbnailAgent
from app.agents.monetize import MonetizeAgent
from app.agents.qa import QAAgent
from app.agents.publish import PublishAgent
from app.agents.analytics import AnalyticsAgent
from app.agents.strategy import StrategyAgent

# Ordered content-production pipeline (up to the approval gate + publish).
PRODUCTION_PIPELINE = [
    ResearchAgent(),
    ScriptAgent(),
    VoiceoverAgent(),
    VisualsAgent(),
    CaptionsAgent(),
    RenderAgent(),
    SeoAgent(),
    ThumbnailAgent(),
    MonetizeAgent(),
    QAAgent(),
]

PUBLISH_AGENT = PublishAgent()
ANALYTICS_AGENT = AnalyticsAgent()
STRATEGY_AGENT = StrategyAgent()

__all__ = [
    "PRODUCTION_PIPELINE",
    "PUBLISH_AGENT",
    "ANALYTICS_AGENT",
    "STRATEGY_AGENT",
]
