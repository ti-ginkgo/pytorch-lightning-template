import os

import pandas as pd
from pytorch_lightning import LightningDataModule
from sklearn.model_selection import StratifiedKFold
from torch.utils.data import DataLoader

from ishtos_datasets import get_dataset


class MyLightningDataModule(LightningDataModule):
    def __init__(self, config, fold=0):
        super(MyLightningDataModule, self).__init__()
        self.config = config
        self.fold = fold

    def _split_train_and_valid_df(self):
        df = pd.read_csv(
            os.path.join(self.config.dataset.base_dir, self.config.dataset.train_df)
        )

        skf = StratifiedKFold(
            n_splits=self.config.train.n_splits,
            shuffle=True,
            random_state=self.config.general.seed,
        )
        for n, (_, val_index) in enumerate(
            skf.split(df, df[self.config.dataset.target].values)
        ):
            df.loc[val_index, "fold"] = int(n)

        train_df = df[df["fold"] != self.fold].reset_index(drop=True)
        valid_df = df[df["fold"] == self.fold].reset_index(drop=True)

        return train_df, valid_df

    def setup(self, stage):
        self.train_df, self.valid_df = self._split_train_and_valid_df()

    def _get_dataframe(self, phase):
        if phase == "train":
            return self.train_df
        elif phase == "valid":
            return self.valid_df
        elif phase == "test":
            test_df = pd.read_csv(
                os.path.join(self.config.dataset.base_dir, self.config.dataset.test_df)
            )
            return test_df

    def _get_dataset(self, phase):
        df = self._get_dataframe(phase)
        return get_dataset(self.config, df, phase)

    def _get_dataloader(self, phase):
        dataset = self._get_dataset(phase=phase)
        return DataLoader(
            dataset,
            batch_size=self.config.dataset.loader.batch_size,
            num_workers=self.config.dataset.loader.num_workers,
            shuffle=phase == "train",
            drop_last=phase == "train",
            pin_memory=True,
        )

    def len_dataloader(self, phase):  # TODO: refactor
        return len(self._get_dataloader(phase=phase))

    def train_dataloader(self):
        return self._get_dataloader(phase="train")

    def val_dataloader(self):
        return self._get_dataloader(phase="valid")

    def test_dataloader(self):
        return self._get_dataloader(phase="test")
