import os
import argparse
import torch
import librosa
import time
from scipy.io.wavfile import write
from tqdm import tqdm

import utils
from models import SynthesizerTrn
from mel_processing import mel_spectrogram_torch
from wavlm import WavLM, WavLMConfig
from speaker_encoder.voice_encoder import SpeakerEncoder
import logging
import shutil
logging.getLogger('numba').setLevel(logging.WARNING)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hpfile", type=str, default="/home/sim/VoiceConversion/FreeVC/logs/freevc-s/config.json", help="path to json config file")
    parser.add_argument("--ptfile", type=str, default="/home/sim/VoiceConversion/FreeVC/logs/freevc-s/G_0.pth", help="path to pth file")
    parser.add_argument("--txtpath", type=str, default="/home/sim/VoiceConversion/conversion_metas/VCTK_seen_pairs.txt", help="path to txt file")
    parser.add_argument("--outdir", type=str, default="/home/sim/VoiceConversion/FreeVC/output/VCTK_seen-0", help="path to output dir")
    parser.add_argument("--use_timestamp", default=False, action="store_true")
    args = parser.parse_args()
    
    os.makedirs(args.outdir, exist_ok=True)
    hps = utils.get_hparams_from_file(args.hpfile)

    print("Loading model...")
    net_g = SynthesizerTrn(
        hps.data.filter_length // 2 + 1,
        hps.train.segment_size // hps.data.hop_length,
        **hps.model).cuda()
    _ = net_g.eval()
    print("Loading checkpoint...")
    _ = utils.load_checkpoint(args.ptfile, net_g, None, True)

    print("Loading WavLM for content...")
    cmodel = utils.get_cmodel(0)
    
    if hps.model.use_spk:
        print("Loading speaker encoder...")
        smodel = SpeakerEncoder('speaker_encoder/ckpt/pretrained_bak_5805000.pt')

    print("Processing text...")
    titles, srcs, tgts = [], [], []
    with open(args.txtpath, "r") as file:
        for rawline in file.readlines()[:]:
            title, tgt, src = rawline.strip().split("|")

            titles.append('src;'+src.split('/')[-1][:-4]+'&tgt;'+tgt.split('/')[-1][:-4])
            
            srcs.append(src)
            tgts.append(tgt)

    print("Synthesizing...")
    with torch.no_grad():
        for line in tqdm(zip(titles, srcs, tgts)):
            title, src, tgt = line
            # tgt
            wav_tgt, _ = librosa.load(tgt, sr=hps.data.sampling_rate)
            wav_tgt, _ = librosa.effects.trim(wav_tgt, top_db=20)
            if hps.model.use_spk:
                g_tgt = smodel.embed_utterance(wav_tgt)
                g_tgt = torch.from_numpy(g_tgt).unsqueeze(0).cuda()
            else:
                wav_tgt = torch.from_numpy(wav_tgt).unsqueeze(0).cuda()
                mel_tgt = mel_spectrogram_torch(
                    wav_tgt, 
                    hps.data.filter_length,
                    hps.data.n_mel_channels,
                    hps.data.sampling_rate,
                    hps.data.hop_length,
                    hps.data.win_length,
                    hps.data.mel_fmin,
                    hps.data.mel_fmax
                )
            # src
            wav_src, _ = librosa.load(src, sr=hps.data.sampling_rate)
            wav_src = torch.from_numpy(wav_src).unsqueeze(0).cuda()
            c = utils.get_content(cmodel, wav_src)
            
            if hps.model.use_spk:
                audio = net_g.infer(c, g=g_tgt)
            else:
                audio = net_g.infer(c, mel=mel_tgt)
            audio = audio[0][0].data.cpu().float().numpy()
            
            
            save_dir = os.path.join(args.outdir, f"{title}")
            os.makedirs(save_dir, exist_ok=True)
            
            write(os.path.join(save_dir, f"C!{title}.wav"), hps.data.sampling_rate, audio)
            
            shutil.copy2(src, f"{save_dir}/S!{src.split('/')[-1]}")
            shutil.copy2(tgt, f"{save_dir}/T!{tgt.split('/')[-1]}")
            # if args.use_timestamp:
            #     timestamp = time.strftime("%m-%d_%H-%M", time.localtime())
            #     write(os.path.join(args.outdir, "{}.wav".format(timestamp+"_"+title)), hps.data.sampling_rate, audio)
            # else:
            #     write(os.path.join(args.outdir, f"{title}.wav"), hps.data.sampling_rate, audio)
            
