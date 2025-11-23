import os

from repair.semantic_model.image_model.encoder import image_encoder
from repair.semantic_model.image_model.model import CustomImageModel
from repair.utils.package import get_resource_path

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from io import BytesIO
from PIL import Image
from repair.semantic_model.image_model.data_loader import semantic_transforms
import torch
from cachetools import LRUCache
from sentence_transformers import SentenceTransformer

device = "cuda" if torch.cuda.is_available() else "cpu"

text_model = SentenceTransformer("shibing624/text2vec-base-chinese")
image_model = CustomImageModel(image_encoder)
image_model.load_state_dict(torch.load(get_resource_path('resources/model/image_model.pth'), map_location=torch.device(device), weights_only=False))
image_model.eval()

text_cache = LRUCache(maxsize=1000000)
image_cache = LRUCache(maxsize=10000)
image_batch_size = 128


def encode_texts(texts):
    try:
        texts = [text for text in texts if not text in text_cache]
        if len(texts) != 0:
            encodes = text_model.encode(texts, convert_to_tensor=True, device=device)
            for text, encode in zip(texts, encodes):
                text_cache[text] = encode
    except:
        pass


def encode_images(images):
    try:
        images = [image for image in images if not image in image_cache]
        images_c = [convert(image) for image in images]
        with torch.no_grad():
            for i in range((len(images) + image_batch_size - 1) // image_batch_size):
                begin = i * image_batch_size
                end = min(begin + image_batch_size, len(images))
                encodes = image_model(torch.stack([image for image in images_c[begin:end]], 0).to(device))
                for image, encode in zip(images[begin:end], encodes):
                    image_cache[image] = encode
    except:
        pass


def sim_image2image(image1, image2):
    try:
        if not image1 in image_cache:
            encode_images([image1])
        if not image2 in image_cache:
            encode_images([image2])
        return torch.cosine_similarity(image_cache[image1].unsqueeze(0), image_cache[image2].unsqueeze(0), dim=1)[0].item()
    except:
        return 0


def sim_text2image(text, image):
    try:
        if not text in text_cache:
            encode_texts([text])
        if not image in image_cache:
            encode_images([image])
        return torch.cosine_similarity(text_cache[text].unsqueeze(0), image_cache[image].unsqueeze(0), dim=1)[0].item()
    except:
        return 0


def sim_text2text(text1, text2):
    try:
        if not text1 in text_cache:
            encode_texts([text1])
        if not text2 in text_cache:
            encode_texts([text2])
        return torch.cosine_similarity(text_cache[text1].unsqueeze(0), text_cache[text2].unsqueeze(0), dim=1)[0].item()
    except:
        return 0


def convert(image):
    image = bytes(i % 256 for i in image)
    image = BytesIO(image)
    image = Image.open(image).convert("RGB")
    return semantic_transforms(image)
