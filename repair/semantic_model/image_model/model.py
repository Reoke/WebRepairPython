import torch


class CustomImageModel(torch.nn.Module):
    def __init__(self, image_encoder, proj_dim=768):
        super().__init__()
        self.image_encoder = image_encoder  # 冻结的预训练编码器
        # 使用多层非线性投影
        self.projector = torch.nn.Sequential(
            torch.nn.Linear(768, 1024),
            torch.nn.GELU(),
            torch.nn.LayerNorm(1024),
            torch.nn.Linear(1024, proj_dim)
        )

    def forward(self, images):
        features = self.image_encoder(images)
        return self.projector(features)  # 对齐文本向量空间
