import numpy as np
import torch

from .trainer_new import Trainer


#  加入了每回合的当前训练步
class SequenceTrainer(Trainer):

    def train_step(self):
        # print(self.iter_num)

        states, actions, rewards, dones, rtg, timesteps, attention_mask = (
            self.get_batch(self.batch_size, iter_num=self.iter_num)
        )
        action_target = torch.clone(actions)

        state_preds, action_preds, reward_preds = self.model.forward(
            states,
            actions,
            rewards,
            rtg[:, :-1],
            timesteps,
            attention_mask=attention_mask,
        )

        act_dim = action_preds.shape[2]
        action_preds = action_preds.reshape(-1, act_dim)[attention_mask.reshape(-1) > 0]
        action_target = action_target.reshape(-1, act_dim)[
            attention_mask.reshape(-1) > 0
        ]

        loss = self.loss_fn(
            None,
            action_preds,
            None,
            None,
            action_target,
            None,
        )

        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 0.25)
        self.optimizer.step()

        with torch.no_grad():
            self.diagnostics["training/action_error"] = (
                torch.mean((action_preds - action_target) ** 2).detach().cpu().item()
            )

        return loss.detach().cpu().item()
