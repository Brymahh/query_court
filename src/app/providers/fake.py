"""Fake model provider for tests."""

from dataclasses import dataclass, field

from app.providers.base import ModelProviderError


@dataclass
class FakeModelProvider:
    """Return predetermined responses without making network calls."""

    responses: list[str]
    _response_index: int = field(default=0, init=False)

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Return the next configured fake response.

        Parameters
        ----------
        system_prompt:
            System instruction supplied to the fake provider.
        user_prompt:
            User prompt supplied to the fake provider.

        Returns
        -------
        str
            Next configured response.

        Raises
        ------
        ModelProviderError
            If no configured responses remain.
        """
        del system_prompt, user_prompt

        if self._response_index >= len(self.responses):
            raise ModelProviderError(
                "Fake provider has no responses remaining.",
            )

        response = self.responses[self._response_index]
        self._response_index += 1
        return response
