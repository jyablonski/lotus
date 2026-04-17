from dagster import ConfigurableResource, EnvVar
from openai import OpenAI


class OpenAIResource(ConfigurableResource):
    """Resource wrapping the OpenAI chat completions API for reuse across assets."""

    api_key: str
    default_model: str = "gpt-5.4-nano-2026-03-17"

    def get_client(self) -> OpenAI:
        return OpenAI(api_key=self.api_key)

    def complete(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
    ) -> str:
        """Send a single-turn chat completion and return the assistant's text.

        `model` overrides `default_model`. `system` adds an optional system message.
        """
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = self.get_client().chat.completions.create(
            model=model or self.default_model,
            messages=messages,
        )
        return resp.choices[0].message.content or ""


openai_client = OpenAIResource(api_key=EnvVar("OPENAI_API_KEY"))
