import torch
import torch.nn as nn

class LSTMPolicy(nn.Module):
    def __init__(self, input_size, hidden_size, action_size):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.policy_head = nn.Linear(hidden_size, action_size)

    def forward(self, x, hidden=None):
        out, hidden = self.lstm(x, hidden)
        logits = self.policy_head(out[:, -1, :])  # use last time step
        return logits, hidden
