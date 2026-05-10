"""Make AI Server Actions respect the user's preferred LLM provider.

Native Odoo 19 hardcodes ``AI_PROVIDER = "openai"`` and
``AI_MODEL = "gpt-4.1"`` on ``ir.actions.server``.  This means every
AI-powered automation (document sort, auto-actions, etc.) always calls
OpenAI regardless of the model selected on the AI Agent.

This override reads a configurable model from system parameters
(``suite_ai_provider_pool.server_action_model``) and derives the
provider automatically.  When no preference is saved, it falls back to
the native default (``gpt-4.1`` on OpenAI).

Administrators can set the preferred model in Settings > AI.
"""

from odoo import models
from odoo.addons.ai.utils.llm_providers import get_provider


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    _SUITE_DEFAULT_MODEL = "gpt-4.1"
    _SUITE_PARAM_KEY = "suite_ai_provider_pool.server_action_model"

    @property
    def AI_MODEL(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(self._SUITE_PARAM_KEY, self._SUITE_DEFAULT_MODEL)
        )

    @property
    def AI_PROVIDER(self):
        return get_provider(self.env, self.AI_MODEL)
