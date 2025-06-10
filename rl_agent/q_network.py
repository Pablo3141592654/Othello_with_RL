import torch
import torch.nn as nn

class QNetwork(nn.Module):
    def __init__(self, board_size=8):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(2, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
        )
        self.fc = nn.Sequential(
            nn.Linear(128 * board_size * board_size, 512),
            nn.ReLU(),
            nn.Linear(512, board_size * board_size)
        )

    def forward(self, x):
        x = self.conv(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x  # shape: [batch, board_size*board_size]