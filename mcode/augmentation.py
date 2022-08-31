import numpy as np
import cv2
import torch
import torch.nn.functional as F
from PIL import Image, ImageOps, ImageFilter, ImageEnhance


class Resize:
    def __init__(self, size):
        self.size = size

    def __call__(self, sample):
        if 'image' in sample.keys():
            sample['image'] = sample['image'].resize(self.size, Image.BILINEAR)
        if 'mask' in sample.keys():
            sample['mask'] = sample['mask'].resize(self.size, Image.BILINEAR)
        if 'mask' in sample.keys():
            sample['mask'] = sample['mask'].resize(self.size, Image.BILINEAR)

        return sample


class RandomScaleCrop:
    def __init__(self, range=[0.75, 1.25]):
        self.range = range

    def __call__(self, sample):
        scale = np.random.random() * (self.range[1] - self.range[0]) + self.range[0]
        if np.random.random() < 0.5:
            for key in sample.keys():
                if key in ['image', 'mask', 'contour']:
                    base_size = sample[key].size

                    scale_size = tuple((np.array(base_size) * scale).round().astype(int))
                    sample[key] = sample[key].resize(scale_size)

                    sample[key] = sample[key].crop(((sample[key].size[0] - base_size[0]) // 2,
                                                    (sample[key].size[1] - base_size[1]) // 2,
                                                    (sample[key].size[0] + base_size[0]) // 2,
                                                    (sample[key].size[1] + base_size[1]) // 2))

        return sample


class RandomFlip:
    def __init__(self, lr=True, ud=True):
        self.lr = lr
        self.ud = ud

    def __call__(self, sample):
        lr = np.random.random() < 0.5 and self.lr is True
        ud = np.random.random() < 0.5 and self.ud is True

        for key in sample.keys():
            if key in ['image', 'mask', 'contour']:
                sample[key] = np.array(sample[key])
                if lr:
                    sample[key] = np.fliplr(sample[key])
                if ud:
                    sample[key] = np.flipud(sample[key])
                sample[key] = Image.fromarray(sample[key])

        return sample


class RandomRotate:
    def __init__(self, range=[0, 360], interval=1):
        self.range = range
        self.interval = interval

    def __call__(self, sample):
        rot = (np.random.randint(*self.range) // self.interval) * self.interval
        rot = rot + 360 if rot < 0 else rot

        if np.random.random() < 0.5:
            for key in sample.keys():
                if key in ['image', 'mask', 'contour']:
                    base_size = sample[key].size

                    sample[key] = sample[key].rotate(rot, expand=True)

                    sample[key] = sample[key].crop(((sample[key].size[0] - base_size[0]) // 2,
                                                    (sample[key].size[1] - base_size[1]) // 2,
                                                    (sample[key].size[0] + base_size[0]) // 2,
                                                    (sample[key].size[1] + base_size[1]) // 2))

        return sample


class RandomImageEnhance:
    def __init__(self, methods=['contrast', 'brightness', 'sharpness']):
        self.enhance_method = []
        if 'contrast' in methods:
            self.enhance_method.append(ImageEnhance.Contrast)
        if 'brightness' in methods:
            self.enhance_method.append(ImageEnhance.Brightness)
        if 'sharpness' in methods:
            self.enhance_method.append(ImageEnhance.Sharpness)

    def __call__(self, sample):
        image = sample['image']
        np.random.shuffle(self.enhance_method)

        for method in self.enhance_method:
            if np.random.random() > 0.5:
                enhancer = method(image)
                factor = float(1 + np.random.random() / 10)
                image = enhancer.enhance(factor)
        sample['image'] = image

        return sample


class RandomDilationErosion:
    def __init__(self, kernel_range):
        self.kernel_range = kernel_range

    def __call__(self, sample):
        mask = sample['mask']
        mask = np.array(mask)
        key = np.random.random()
        # kernel = np.ones(tuple([np.random.randint(*self.kernel_range)]) * 2, dtype=np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (np.random.randint(*self.kernel_range),) * 2)
        if key < 1 / 3:
            mask = cv2.dilate(mask, kernel)
        elif 1 / 3 <= key < 2 / 3:
            mask = cv2.erode(mask, kernel)

        sample['mask'] = Image.fromarray(mask)

        return sample


class RandomGaussionBlur:
    def __init__(self):
        pass

    def __call__(self, sample):
        image = sample['image']
        if np.random.random() < 0.5:
            image = image.filter(ImageFilter.GaussianBlur(radius=np.random.random()))
        sample['image'] = image

        return sample


class ToNumpy:
    def __init__(self):
        pass

    def __call__(self, sample):
        image, mask = sample['image'], sample['mask']

        sample['image'] = np.array(image, dtype=np.float32)
        sample['mask'] = np.array(mask, dtype=np.float32)

        return sample


class Normalize:
    def __init__(self, mean, std):
        self.mean = mean
        self.std = std

    def __call__(self, sample):
        image, mask = sample['image'], sample['mask']
        image /= 255
        image -= self.mean
        image /= self.std

        mask /= 255
        sample['image'] = image
        sample['mask'] = mask

        return sample


class ToTensor:
    def __init__(self):
        pass

    def __call__(self, sample):
        image, mask = sample['image'], sample['mask']
        image = image.transpose((2, 0, 1))
        image = torch.from_numpy(image).float()
        mask = torch.from_numpy(mask)
        mask = mask.unsqueeze(dim=0)
        sample['image'] = image
        sample['mask'] = mask

        return sample