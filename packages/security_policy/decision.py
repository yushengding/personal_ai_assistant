from packages.agent_runtime.models import ImportanceLevel


def should_pause_for_decision(ticket_level: ImportanceLevel, core_pause_level: ImportanceLevel) -> bool:
    return int(ticket_level) <= int(core_pause_level)

