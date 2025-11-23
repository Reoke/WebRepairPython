import os

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import torch
from transformers import SiglipModel

# 加载完整SigLIP2模型
model = SiglipModel.from_pretrained("google/siglip2-base-patch16-224")


# 提取图像编码器部分（去除最后的分类头）
class ImageEncoder(torch.nn.Module):
    def __init__(self, vision_model):
        super().__init__()
        self.embeddings = vision_model.embeddings
        self.encoder = vision_model.encoder
        self.post_layernorm = vision_model.post_layernorm

    def forward(self, pixel_values):
        embeddings = self.embeddings(pixel_values)
        encoder_outputs = self.encoder(embeddings)
        features = self.post_layernorm(encoder_outputs.last_hidden_state[:, 0, :])  # 取CLS token
        return features


image_encoder = ImageEncoder(model.vision_model)