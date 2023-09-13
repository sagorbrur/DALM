from typing import Union

import torch
from transformers import AutoModel, AutoTokenizer


class AutoModelForSentenceEmbedding(torch.nn.Module):
    def __init__(self, model_name: str, tokenizer: AutoTokenizer, normalize: bool = True) -> None:
        super(AutoModelForSentenceEmbedding, self).__init__()

        self.model = AutoModel.from_pretrained(model_name, load_in_8bit=True, device_map={"": 0})
        self.normalize = normalize
        self.tokenizer = tokenizer

    def forward(self, **kwargs: torch.Tensor) -> torch.Tensor:
        model_output = self.model(**kwargs)
        embeddings = self.mean_pooling(model_output, kwargs["attention_mask"])
        if self.normalize:
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

        return embeddings

    def mean_pooling(self, model_output: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def __getattr__(self, name: str) -> Union[torch.Tensor, torch.nn.modules.module.Module]:
        """Forward missing attributes to the wrapped module."""
        try:
            return super().__getattr__(name)  # defer to nn.Module's logic
        except AttributeError:
            return getattr(self.model, name)
