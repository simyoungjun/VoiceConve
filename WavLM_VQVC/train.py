from config import Arguments as args
import os

os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"   
os.environ["CUDA_VISIBLE_DEVICES"]=args.train_visible_devices

import sys, random
import numpy as np

import torch
import torch.nn as nn
from torch.optim import Adam
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

from config import Arguments as args

from model import VQVC

from evaluate import evaluate
from dataset import SpeechDataset #, collate_fn

from utils.scheduler import WarmupScheduler
from utils.checkpoint import load_checkpoint, save_checkpoint
from utils.writer import Writer
from utils.vocoder import get_vocgan

from tqdm import tqdm


def train(train_data_loader, eval_data_loader, model, reconstruction_loss, vocoder, mel_stat, optimizer, scheduler, global_step, writer=None, DEVICE=None):

	model.train()

	while global_step < args.max_training_step:

		for step, (mels, _) in tqdm(enumerate(train_data_loader), total=len(train_data_loader), unit='B', ncols=70, leave=False):
			mels = mels.float().to(DEVICE)
			optimizer.zero_grad()

			mels_hat, commitment_loss, perplexity = model(mels.detach())

			commitment_loss = args.commitment_cost * commitment_loss
			recon_loss = reconstruction_loss(mels_hat, mels) 

			loss = commitment_loss + recon_loss 
			loss.backward()

			nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip_thresh)
			optimizer.step()

			if global_step % args.save_checkpoint_step == 0:
				save_checkpoint(checkpoint_path=args.model_checkpoint_path, model=model, optimizer=optimizer, scheduler=scheduler, global_step=global_step)

			if global_step % args.eval_step == 0:
				evaluate(model=model, vocoder=vocoder, eval_data_loader=eval_data_loader, criterion=reconstruction_loss, mel_stat=mel_stat, global_step=global_step, writer=writer, DEVICE=DEVICE)
				model.train()

			if args.log_tensorboard:
				writer.add_scalars(mode="train_recon_loss", global_step=global_step, loss=recon_loss)
				writer.add_scalars(mode="train_commitment_loss", global_step=global_step, loss=commitment_loss)
				writer.add_scalars(mode="train_perplexity", global_step=global_step, loss=perplexity)
				writer.add_scalars(mode="train_total_loss", global_step=global_step, loss=loss)

			global_step += 1

		scheduler.step()

def main(DEVICE):

	# define model, optimizer, scheduler
	model = VQVC().to(DEVICE)

	recon_loss = nn.L1Loss().to(DEVICE)
	vocoder = get_vocgan(ckpt_path=args.vocoder_pretrained_model_path).to(DEVICE)

	mel_stat = torch.tensor(np.load(args.mel_stat_path)).to(DEVICE)

	optimizer = Adam(model.parameters(), lr=args.init_lr)
	scheduler = WarmupScheduler( optimizer, warmup_epochs=args.warmup_steps,
        			initial_lr=args.init_lr, max_lr=args.max_lr,
				milestones=args.milestones, gamma=args.gamma)

	global_step = load_checkpoint(checkpoint_path=args.model_checkpoint_path, model=model, optimizer=optimizer, scheduler=scheduler)

	# load dataset & dataloader
	train_dataset = SpeechDataset(mem_mode=args.mem_mode, meta_dir=args.prepro_meta_train, dataset_name = args.dataset_name, mel_stat_path=args.mel_stat_path, max_frame_length=args.max_frame_length)
	eval_dataset = SpeechDataset(mem_mode=args.mem_mode, meta_dir=args.prepro_meta_eval, dataset_name=args.dataset_name, mel_stat_path=args.mel_stat_path, max_frame_length=args.max_frame_length)

	train_data_loader = DataLoader(dataset=train_dataset, batch_size=args.train_batch_size, shuffle=True, drop_last=True, pin_memory=True, num_workers=args.n_workers)
	eval_data_loader = DataLoader(dataset=eval_dataset, batch_size=args.train_batch_size, shuffle=False, pin_memory=True, drop_last=True)

	# tensorboard
	writer = Writer(args.model_log_path) if args.log_tensorboard else None		

	# train the model!
	train(train_data_loader, eval_data_loader, model, recon_loss, vocoder, mel_stat, optimizer, scheduler, global_step, writer, DEVICE)

# 데이터셋 로딩 테스트 부분 추가
def test_dataset_loading():
    print("Testing dataset loading...")
    dataset = SpeechDataset(mem_mode=args.mem_mode, meta_dir=args.prepro_meta_train, dataset_name=args.dataset_name, mel_stat_path=args.mel_stat_path, max_frame_length=args.max_frame_length)
    print(f"Dataset size: {len(dataset)}")
    if len(dataset) > 0:
        for i in range(min(5, len(dataset))):  # 처음 5개 샘플을 로드하여 테스트
            sample, _ = dataset[i]
            print(f"Sample {i}: Shape {sample.shape}")
    else:
        print("No data found in the dataset.")

if __name__ == "__main__":

	print("[LOG] Start training...")
	DEVICE = torch.device("cuda" if (torch.cuda.is_available() and args.use_cuda) else "cpu")

	seed = args.seed

	print("[Training environment]")
	print("\t\trandom_seed: ", seed)
	print("\t\tuse_cuda: ", args.use_cuda)
	print("\t\t{} threads are used...".format(torch.get_num_threads()))
	
	random.seed(seed)
	np.random.seed(seed)
	torch.manual_seed(seed)

	test_dataset_loading()  # 데이터셋 로딩 테스트 수행
	main(DEVICE)	
