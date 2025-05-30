import torch
from torch import nn, Tensor
import torch.nn.functional as F


def initialize_weights(model):
    if type(model) in [nn.Linear]:
        nn.init.xavier_uniform_(model.weight)
        nn.init.zeros_(model.bias)
    elif type(model) in [nn.LSTM, nn.RNN, nn.GRU]:
        nn.init.orthogonal_(model.weight_hh_l0)
        nn.init.xavier_uniform_(model.weight_ih_l0)
        nn.init.zeros_(model.bias_hh_l0)
        nn.init.zeros_(model.bias_ih_l0)


class MANN(nn.Module):
    def __init__(self, num_classes, samples_per_class, hidden_dim):
        super(MANN, self).__init__()
        self.num_classes = num_classes
        self.samples_per_class = samples_per_class

        self.layer1 = torch.nn.LSTM(num_classes + 784, hidden_dim, batch_first=True)
        self.layer2 = torch.nn.LSTM(hidden_dim, num_classes, batch_first=True)
        initialize_weights(self.layer1)
        initialize_weights(self.layer2)

    def forward(self, input_images, input_labels):
        """
        MANN
        Args:
            input_images: [B, K+1, N, 784] flattened images
            labels: [B, K+1, N, N] ground truth labels
        Returns:
            [B, K+1, N, N] predictions
        """
        #############################
        ### START CODE HERE ###

        # Step 1: Concatenate the full (support & query) set of labels and images

        input = torch.cat([input_images, input_labels], dim=-1)

        # print(input.shape)

        # Step 2: Zero out the labels from the concatenated corresponding to the query set
        input[:, -1, :, 784:] = torch.zeros_like(input_labels)[:, -1]

        # Step 3: Pass the concatenated set sequentially to the memory-augmented network
        support = input.reshape(input.shape[0], input.shape[1] * input.shape[2], input.shape[-1]).float()
        
        # output of LSTM : output, (h_n, c_n)
        pred, _ = self.layer1(support)
        pred, _ = self.layer2(pred)

        # Step 3: Return the predictions with [B, K+1, N, N] shape

        # print(pred.shape)
        return pred.reshape(input_labels.shape)
        ### END CODE HERE ###

    def loss_function(self, preds, labels):
        """
        Computes MANN loss
        Args:
            preds: [B, K+1, N, N] network output
            labels: [B, K+1, N, N] labels
        Returns:
            scalar loss
        Note:
            Loss should only be calculated on the N test images
            Loss should be a scalar since mean reduction is used for cross entropy loss
            You would want to use F.cross_entropy here, specifically:
            with predicted unnormalized logits as input and ground truth class indices as target.
            Your logits would be of shape [B*N, N], and label indices would be of shape [B*N].
        """
        #############################

        loss = None

        ### START CODE HERE ###

        # Step 1: extract the predictions for the query set
        predictions = preds[:, -1].reshape(-1, self.num_classes)
        # print(predictions.shape)

        # Step 2: extract the true labels for the query set and reverse the one hot-encoding  
        label = torch.argmax(labels[:, -1], dim=-1).reshape(-1)
        # print(label.shape)

        # Step 3: compute the Cross Entropy Loss for the query set only!
        loss = F.cross_entropy(predictions, label)

        ### END CODE HERE ###
        return loss
