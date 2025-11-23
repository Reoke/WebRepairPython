from torchvision import transforms

semantic_transforms = transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Resize((224, 224)),
    ]
)
