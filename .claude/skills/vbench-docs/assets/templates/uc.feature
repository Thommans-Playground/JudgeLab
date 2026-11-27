# Acceptance criteria for {{ID}}. One Scenario per criterion, tagged with its ID.
#
# Rules:
# - Every Scenario carries exactly one @AC-{{NUM}}-NN tag (next ID: docids.py next AC --usecase {{ID}}).
# - Write observable outcomes (Then) in the user's language, not implementation steps.
# - Clarifying the wording is fine. Changing the meaning is a new criterion: add a new Scenario,
#   tag the old one @retired, and comment "# Superseded by AC-{{NUM}}-NN: <reason>" above it.
# - Never reuse or renumber an ID.

Feature: {{ID}} {{TITLE}}
  As a <actor>
  I want <goal>
  So that <benefit>

  Requirements: REQ-###

  @AC-{{NUM}}-01
  Scenario: <one observable behaviour>
    Given <context>
    When <event>
    Then <observable outcome>
