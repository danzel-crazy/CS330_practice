import numpy as np
import os
import random
import torch
from torch.utils.data import IterableDataset
import time
import imageio


def get_images(paths, labels, num_samples=None):
    """
    Takes a set of character folders and labels and returns paths to image files
    paired with labels.
    Args:
        paths: A list of character folders
        labels: List or numpy array of same length as paths
        num_samples: Number of images to retrieve per character
    Returns:
        List of (label, image_path) tuples
    """
    if num_samples is not None:
        sampler = lambda x: random.sample(x, num_samples)
    else:
        sampler = lambda x: x
    labels_and_images = [
        (i, os.path.join(path, image))
        for i, path in zip(labels, paths)
        for image in sampler(os.listdir(path))
    ]

    return labels_and_images


class DataGenerator(IterableDataset):
    """
    Data Generator capable of generating batches of Omniglot data.
    A "class" is considered a class of omniglot digits.
    """

    def __init__(
        self,
        num_classes,
        num_samples_per_class,
        batch_type,
        config={},
        cache=True,
    ):
        """
        Args:
            num_classes: Number of classes for classification (N-way)
            num_samples_per_class: num samples to generate per class in one batch (K+1)
            batch_type: train/val/test
            config: data_folder - folder where the data is located
                    img_size - size of the input images
            cache: whether to cache the images loaded
        """
        self.num_samples_per_class = num_samples_per_class-1
        self.num_classes = num_classes

        data_folder = config.get("data_folder", "./omniglot_resized")
        self.img_size = config.get("img_size", (28, 28))

        self.dim_input = np.prod(self.img_size)
        self.dim_output = self.num_classes

        character_folders = [
            os.path.join(data_folder, family, character)
            for family in os.listdir(data_folder)
            if os.path.isdir(os.path.join(data_folder, family))
            for character in os.listdir(os.path.join(data_folder, family))
            if os.path.isdir(os.path.join(data_folder, family, character))
        ]

        random.seed(1)
        random.shuffle(character_folders)
        num_val = 100
        num_train = 1100
        self.metatrain_character_folders = character_folders[:num_train]
        self.metaval_character_folders = character_folders[num_train : num_train + num_val]
        self.metatest_character_folders = character_folders[num_train + num_val :]
        self.image_caching = cache
        self.stored_images = {}

        if batch_type == "train":
            self.folders = self.metatrain_character_folders
        elif batch_type == "val":
            self.folders = self.metaval_character_folders
        else:
            self.folders = self.metatest_character_folders


    def image_file_to_array(self, filename, dim_input):
        """
        Takes an image path and returns numpy array
        Args:
            filename: Image filename
            dim_input: Flattened shape of image
        Returns:
            1 channel image
        """
        if self.image_caching and (filename in self.stored_images):
            return self.stored_images[filename]
        image = imageio.imread(filename)  # misc.imread(filename)
        image = image.reshape([dim_input])
        image = image.astype(np.float32) / image.max()
        image = 1.0 - image
        if self.image_caching:
            self.stored_images[filename] = image
        return image

    def _sample(self):
        """
        Samples a batch for training, validation, or testing
        Returns:
            A tuple of (1) Image batch and (2) Label batch:
                1. image batch has shape [K+1, N, 784] and is a numpy array
                2. label batch has shape [K+1, N, N] and is a numpy array
            where K is the number of "shots", N is number of classes
        Note:
            1. The numpy functions np.random.shuffle and np.eye (for creating)
            one-hot vectors would be useful.

            2. For shuffling, remember to make sure images and labels are shuffled
            in the same order, otherwise the one-to-one mapping between images
            and labels may get messed up. Hint: we encourage you to use
            np.random.shuffle here.
            
            3. The value for `self.num_samples_per_class` will be set to K+1 
            since for K-shot classification you need to sample K supports and 
            1 query.

            4. PyTorch uses float32 as default for representing model parameters. 
            You would need to return numpy arrays with the same datatype
        """

        #############################
        ### START CODE HERE ###

        # Step 1: Sample N (self.num_classes in our case) different characters folders 
        Samples = random.sample(self.folders, self.num_classes)
        lables_id = np.eye(self.num_classes, dtype=int)

        # Step 2: Sample and load K + 1 (self.self.num_samples_per_class in our case) images per character together with their labels preserving the order!
        # Use our 3 function defined above.
        # You should be able to complete this with only one call of get_images(...)!
        # Please closely check the input arguments of get_images to understand how it works.
        
        #get labels and images pair
        batch = get_images(Samples, lables_id, self.num_samples_per_class)
        

        # Step 3: Iterate over the sampled files and create the image and label batches
        
        images_batch = np.vstack([self.image_file_to_array(images, dim_input=self.dim_input) for (_, images) in batch]) # N * k+1 
        labels_batch = np.vstack([label for (label, _) in batch])

        images_batch = torch.from_numpy(images_batch).view(self.num_classes,self.num_samples_per_class,self.dim_input).permute(1, 0, 2)
        labels_batch = torch.from_numpy(labels_batch).view(self.num_classes,self.num_samples_per_class,self.num_classes).permute(1, 0, 2)

        #check shape    
        # print(images_batch.shape)
        # print(labels_batch.shape)

        # Make sure that we have a fixed order as pictured in the assignment writeup
        # Use our image_file_to_array function defined above.
        
        # Step 4: Shuffle the order of examples from the query set

        #Sample Query images and labels
        query_batch = get_images(Samples, lables_id, num_samples=1)
        random.shuffle(query_batch)
        # print(query_batch)

        query_images_batch = np.vstack([self.image_file_to_array(images, dim_input=self.dim_input) for (_, images) in query_batch])
        query_labels_batch = np.vstack([label for (label, _) in query_batch])
        query_images_batch = torch.from_numpy(query_images_batch).view(self.num_classes,1,784).permute(1, 0, 2)
        query_labels_batch = torch.from_numpy(query_labels_batch).view(self.num_classes,1,self.num_classes).permute(1, 0, 2)

        #check shape 
        # print(query_images_batch.shape)
        # print(query_labels_batch.shape)
        # print(f'hi')

        # Step 5: return tuple of image batch with shape [K+1, N, 784] and
        #         label batch with shape [K+1, N, N]

        #test1_0 K+1: 2, N = 2
        # images = np.concatenate()

        # images = torch.from_numpy()
        images = torch.cat((images_batch, query_images_batch), dim=0)
        labels = torch.cat((labels_batch, query_labels_batch), dim=0)

        # print(images.shape)

        return images, labels
        ### END CODE HERE ###

    def __iter__(self):
        while True:
            yield self._sample()
