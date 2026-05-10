"""Embedding fallback for providers without an embedding model.

Anthropic, DeepSeek, and Self-Hosted providers registered by this
module do not ship an embedding model (they are chat-only).  The
native ``_get_embedding_model()`` looks up the agent's own provider
and raises ``UserError`` when no embedding model is found there.

This override implements a transparent fallback: when the agent's
provider has no embedding model, the method returns the first
available embedding model from any configured provider (typically
OpenAI or Google).  The user only needs *one* embedding-capable API
key alongside their chosen chat key.

If *no* embedding provider has a key configured, the method raises a
clear ``UserError`` directing the user to Settings > AI.
"""

from odoo import _, models
from odoo.exceptions import UserError
from odoo.addons.ai.utils.llm_api_service import LLMApiService
from odoo.addons.ai.utils.llm_providers import PROVIDERS


class AiAgent(models.Model):
    _inherit = "ai.agent"

    def _get_embedding_model(self):
        """Return the embedding model for this agent's provider, falling
        back to any provider that has both an embedding model and a
        configured API key."""
        self.ensure_one()
        provider = self._get_provider()

        # 1. Agent's own provider has an embedding model — use it
        for p in PROVIDERS:
            if p.name == provider and p.embedding_model:
                return p.embedding_model

        # 2. Fallback: first provider with an embedding model + valid key
        for p in PROVIDERS:
            if not p.embedding_model:
                continue
            try:
                LLMApiService(self.env, p.name)._get_api_token()
                return p.embedding_model
            except UserError:
                continue

        # 3. Nothing available — clear error message
        raise UserError(_(
            "Knowledge Sources require an OpenAI or Google API key for "
            "text embedding. Your current chat model does not include an "
            "embedding service. Please configure an OpenAI or Google key "
            "in Settings > AI."
        ))
