import numpy as np
import torch

from .trainer import Trainer

# loss加入了rewards
class SequenceTrainer(Trainer):

    def train_step(self):
        states, actions, rewards, dones, rtg, timesteps, attention_mask = self.get_batch(self.batch_size)
        action_target = torch.clone(actions)
        rewards_target = torch.clone(rewards)
        state_preds, action_preds, rtg_preds, reward_preds = self.model.forward(
            states, actions, rewards, rtg[:,:-1], timesteps, attention_mask=attention_mask,
        )

        act_dim = action_preds.shape[2]
        action_preds = action_preds.reshape(-1, act_dim)[attention_mask.reshape(-1) > 0]
        action_target = action_target.reshape(-1, act_dim)[attention_mask.reshape(-1) > 0]

        r_dim = reward_preds.shape[2]
        reward_preds = reward_preds.reshape(-1, r_dim)[attention_mask.reshape(-1) > 0]
        r_target = rewards_target.reshape(-1, r_dim)[attention_mask.reshape(-1) > 0]


        loss = self.loss_fn(
            None, action_preds, reward_preds,
            None, action_target, r_target,
        )

        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), .25)
        self.optimizer.step()

        with torch.no_grad():
            self.diagnostics['training/action_error'] = torch.mean((action_preds-action_target)**2).detach().cpu().item()

        return loss.detach().cpu().item()
