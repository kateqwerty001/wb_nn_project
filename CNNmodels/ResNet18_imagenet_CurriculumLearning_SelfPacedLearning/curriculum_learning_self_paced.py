from RSSCN7_dataLoader import RSSCN7_DataLoader
from torchvision.models import resnet18
import torch.nn as nn
import torch.optim as optim
import time

time0 = time.time()

data_dir = '/Users/katebokhan/Desktop/wb_nn_project/data/RSSCN7'
batch_size = 32
learning_rate = 0.001
num_epochs = 250
lambda_beginning = 0.1
lambda_end = 1

rsscn7_data_loader = RSSCN7_DataLoader(data_dir, batch_size=batch_size)
train_loader = rsscn7_data_loader.get_train_dataloader()
test_loader = rsscn7_data_loader.get_test_dataloader()

model = resnet18(weights='ResNet18_Weights.DEFAULT')
num_filters = model.fc.in_features
model.fc = nn.Linear(num_filters, 7)

criterion = nn.CrossEntropyLoss()
opitmizer = optim.Adam(model.parameters(), lr=learning_rate)

step = 0.03

import torch
from torch.utils.data import DataLoader, TensorDataset


def train_model_self_paced(model, train_loader, test_loader, criterion, optimizer, num_epochs):
    device = torch.device('mps')
    model.to(device)
    counter = 0

    lambda_current = lambda_beginning

    for epoch in range(num_epochs):
        start_time = time.time()

        model.train()
        total_loss = 0.0
        correct = 0
        total = 0
        train_samples = []

        if lambda_current < 1:
            with torch.no_grad():
                for inputs, labels in train_loader:
                    inputs, labels = inputs.to(device), labels.to(device)
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                    train_samples.append((inputs, labels, loss.item()))

            train_samples.sort(key=lambda x: x[2])  # sort by loss (the first are the easiest)

            num_samples_current = int(lambda_current * len(train_samples))

            easy_enough_samples = train_samples[:num_samples_current]
            easy_enough_inputs = torch.cat([x[0] for x in easy_enough_samples])
            easy_enough_labels = torch.cat([x[1] for x in easy_enough_samples])
            easy_enough_dataset = TensorDataset(easy_enough_inputs, easy_enough_labels)
            easy_enough_loader = DataLoader(easy_enough_dataset, batch_size=batch_size, shuffle=True)
        else:
            easy_enough_loader = train_loader

        for inputs, labels in easy_enough_loader:
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * inputs.size(0)

            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        train_loss = total_loss / len(easy_enough_loader.dataset)
        train_accuracy = correct / total
        num_images = len(easy_enough_loader.dataset)

        print(
            f'Epoch [{epoch + 1}/{num_epochs}], Loss: {train_loss:.4f}, Accuracy: {train_accuracy:.4f}, Images: {num_images}, Lambda: {lambda_current:.2f}, Time: {time.time() - time0:.2f} seconds')

        if train_accuracy > 0.8:
            if lambda_current < 0.8:
                lambda_current += step
            else:
                counter = counter + 1
                if counter % 3 == 0:
                    lambda_current += step
                    counter = 0

        evaluate_model(model, test_loader, criterion)

    print('Finished Training Successfully')


def evaluate_model(model, test_loader, criterion):
    model.eval()
    device = next(model.parameters()).device
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            total_loss += loss.item() * inputs.size(0)

            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    test_loss = total_loss / len(test_loader.dataset)
    test_accuracy = correct / total

    print(f'Test Loss: {test_loss:.4f}, Test Accuracy: {test_accuracy:.4f}')


train_model_self_paced(model, train_loader, test_loader, criterion, opitmizer, num_epochs)







