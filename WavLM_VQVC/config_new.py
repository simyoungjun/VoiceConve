import torch
from utils.path import get_path

class Arguments:

	""" 
		path configurations
	"""
	config = '/home/sim/VoiceConversion/WavLM_VQVC/wavlm_vqvc.json'
	model_name = 'VQ_init_2024_cos'
	model_dir = '/shared/racoon_fast/sim/Checkpoints/logs/'+model_name
 
	root_path = '/shared/racoon_fast/sim/VCTK/preprocessed/vctk-16k'
	dataset_name = "VCTK"
	dataset_path = get_path("/home/monet/VQVC/DS_10283_3443", dataset_name)

	converted_sample_dir = "results"	
	prepro_dir = "/home/monet/VQVC/DS_10283_3443/preprocessed"
	model_log_dir = "logs"
	model_checkpoint_dir = "ckpts"
	

	# path for loading audio(wav) samples to be preprocessed
	wav_dir = get_path(dataset_path, "wav48")

	# by default, preprocessed samples and metadata are stored in "prepro_path"
	prepro_path = get_path(prepro_dir, dataset_name)
	prepro_mel_dir = get_path(prepro_path, "mels")
	prepro_meta_dir = get_path(prepro_path, "metas")
	prepro_meta_train = "/home/sim/VoiceConversion/FreeVC/filelists/train.txt"
	prepro_meta_eval = "/home/sim/VoiceConversion/FreeVC/filelists/val.txt"
	prepro_meta_unseen = "/home/sim/VoiceConversion/FreeVC/filelists/unseen.txt"

	mel_stat_path = get_path(prepro_path, "mel_stats.npy")

	model_log_path = get_path(model_log_dir, model_name)
	model_checkpoint_path = get_path(model_checkpoint_dir, model_name)


	"""
		preprocessing hyperparams
	"""
	# max_frame_length = 40		# window size of random resampling

	# sr = 22050			# 22050kHz sampling rate
	n_mels = 80
	# filter_length = 1024
	# hop_length = 256
	# win_length = 1024

	# max_wav_value = 32768.0		# for other dataset
	# mel_fmin = 0
	# mel_fmax = 8000

	# trim_silence = True
	# top_db = 15			# threshold for trimming silence

	"""
		VQVC hyperparameters
	"""

	n_embeddings = 1024		# of codes in VQ-codebook
	z_dim=1024			# bottleneck dimension

	commitment_cost = 0.01		# commitment cost

	norm_epsilon = 1e-4
	speaker_emb_reduction=1

	warmup_steps = 1000
	init_lr = 1e-3			# initial learning rate
	max_lr = 4e-2			# maximum learning rate
	gamma = 0.25
	milestones = [20000]


	"""
        	data & training setting
	"""
	grad_clip_thresh=3.0
	seed = 999
	n_workers = 10

	#scheduler setting

	use_cuda = True
	#use_cuda = False
	mem_mode = False

	data_split_ratio = [0.95, 0.05]		# [train, evaluation] in 0 ~ 1 range

	train_visible_devices = "7"
	conversion_visible_devices = "7"

	# train_batch_size = 120
	# eval_batch_size = 100 
	eval_step = 1000
	eval_path = "eval_results"
	save_checkpoint_step = 5000

	log_tensorboard = True
	max_training_step = 600000

	# vocoder setting
	vocoder = "vocgan"
	vocoder_pretrained_model_name = "vctk_pretrained_model_3180.pt"
	vocoder_pretrained_model_path = get_path("./vocoder", "{}", "pretrained_models", vocoder_pretrained_model_name).format(vocoder)

	'''
	For FreeVC
	'''