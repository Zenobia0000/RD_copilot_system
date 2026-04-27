"""harness — AI-driven agent runtime.

Builds Claude Code style agent loops on top of the Anthropic SDK. Skills are
filesystem-discovered (.claude/skills/<name>/SKILL.md), commands route to
skills (.claude/commands/<name>.md), and state lives on disk (artifacts as
truth). No fixed pipelines.
"""
