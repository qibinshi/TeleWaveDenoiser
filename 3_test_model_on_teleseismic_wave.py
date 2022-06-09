"""
Evaluate the trained model with the test dataset

Qibin Shi modified from Jiuxun Yin's code
"""
import h5py
import torch
import matplotlib
import numpy as np
from scipy.io import loadmat
from utilities import waveform_fft
from matplotlib import pyplot as plt
from torch.utils.data import DataLoader
from torch_tools import WaveformDataset, try_gpu
from sklearn.metrics import explained_variance_score
from sklearn.model_selection import train_test_split

matplotlib.rcParams.update({'font.size': 9})

# %%
dt = 0.1
npts = 6000
batch_size = 256
gpu_num = 1
devc = try_gpu(i=gpu_num)
wave_mat = './data_stacked_POHA_Ponly_2004_18_shallow_snr_25_sample10Hz_lowpass2Hz.mat'
model_name = "Branch_Encoder_Decoder_LSTM"
model_dir = 'Freeze_Middle'
comps = ['E', 'N', 'Z']

# %% Read mat data
X_train = loadmat(wave_mat)["stack_waves"]
Y_train = loadmat(wave_mat)["quake_waves"]

with h5py.File(model_dir + f'/{model_name}_Dataset_split.hdf5', 'r') as f:
    train_size = f.attrs['train_size']
    test_size = f.attrs['test_size']
    rand_seed1 = f.attrs['rand_seed1']
    rand_seed2 = f.attrs['rand_seed2']

X_training,X_test,Y_training,Y_test=train_test_split(X_train,Y_train,train_size=train_size,random_state=rand_seed1)
X_validate,X_test,Y_validate,Y_test=train_test_split(X_test, Y_test,  test_size=test_size, random_state=rand_seed2)
test_data = WaveformDataset(X_test, Y_test)

# %% Model
model = torch.load('./Freeze_Middle/Branch_Encoder_Decoder_LSTM_Model.pth', map_location=devc)
test_iter = DataLoader(test_data, batch_size=batch_size, shuffle=False)
model.eval()

# %% Predict the teleseismic waveforms of one batch
data_iter = iter(test_iter)
noisy_signal, clean_signal = data_iter.next()
noisy_signal, clean_signal = noisy_signal.to(devc), clean_signal.to(devc)
denoised_signal, separated_noise = model(noisy_signal)

noisy_signal = noisy_signal.detach().numpy()
clean_signal = clean_signal.detach().numpy()
denoised_signal = denoised_signal.detach().numpy()
separated_noise = separated_noise.detach().numpy()
true_noise = noisy_signal - clean_signal

# %% Plot time series
time = np.arange(0, npts) * dt
for i_model in range(20):
    print(i_model, 'time series')
    plt.close("all")
    fig, ax = plt.subplots(denoised_signal.shape[1], 3, sharex=True, sharey=True, num=1, figsize=(9, 3))

    for i in range(noisy_signal.shape[1]):
        scaling_factor = np.max(abs(noisy_signal[i_model, i, :]))
        evs_earthquake = explained_variance_score(clean_signal[i_model, i, :], denoised_signal[i_model, i, :])
        evs_noise = explained_variance_score(true_noise[i_model, i, :], separated_noise[i_model, i, :])
        ax[i, 0].plot(time, noisy_signal[i_model, i, :]/scaling_factor, '-k', label='Noisy signal', linewidth=1)
        ax[i, 0].plot(time, clean_signal[i_model, i, :]/scaling_factor, '-r', label='True signal', linewidth=1)
        ax[i, 1].plot(time, clean_signal[i_model, i, :]/scaling_factor, '-r', label='True signal', linewidth=1)
        ax[i, 1].plot(time, denoised_signal[i_model, i, :]/scaling_factor, '-b', label='Predicted signal', linewidth=1)
        ax[i, 2].plot(time, true_noise[i_model, i, :] / scaling_factor, '-', color='gray', label='True noise', linewidth=1)
        ax[i, 2].plot(time, separated_noise[i_model, i, :] / scaling_factor, '-b',  label='Predicted noise', linewidth=1)
        ax[i, 1].text(50, 0.8, f'EV: {evs_earthquake:.2f}')
        ax[i, 2].text(50, 0.8, f'EV: {evs_noise:.2f}')
     
    ## Title, label and axes
    ax[0, 0].set_title("Original signal")
    ax[0, 1].set_title("Earthquake signal")
    ax[0, 2].set_title("Separated noise")

    for i in range(noisy_signal.shape[1]):
        ax[i, 0].set_ylabel(comps[i])
        for j in range(3):
            ax[i, j].xaxis.set_visible(False)
            ax[i, j].yaxis.set_ticks([])
            ax[i, j].spines['right'].set_visible(False)
            ax[i, j].spines['left'].set_visible(False)
            ax[i, j].spines['top'].set_visible(False)
            ax[i, j].spines['bottom'].set_visible(False)

            if i==noisy_signal.shape[1]-1:
                ax[i, j].xaxis.set_visible(True)
                ax[i, j].set_xlim(0, npts*dt)
                ax[i, j].spines['bottom'].set_visible(True)
                ax[i, j].set_xlabel('time (s)')

    plt.figure(1)
    plt.savefig(f'./Freeze_Model/figures/{model_name}_Prediction_waveform_model_{i_model}.pdf', bbox_inches='tight')

# %% Plot spectrum
for i_model in range(20):
    print(i_model, 'spectrum')
    plt.close("all")
    fig, ax = plt.subplots(2, denoised_signal.shape[1], sharex=True, sharey=True, num=1, figsize=(12, 5))

    for i in range(noisy_signal.shape[1]):
        scaling_factor = np.max(abs(noisy_signal[i_model, i, :]))
        original_noise = noisy_signal[i_model, i, :] - clean_signal[i_model, i, :]
        _, spect_noisy_signal = waveform_fft(noisy_signal[i_model, i, :]/scaling_factor, dt)
        _, spect_clean_signal = waveform_fft(clean_signal[i_model, i, :]/scaling_factor, dt)
        _, spect_noise = waveform_fft(separated_noise[i_model, i, :] / scaling_factor, dt)
        _, spect_original_noise = waveform_fft(original_noise / scaling_factor, dt)
        freq, spect_denoised_signal = waveform_fft(denoised_signal[i_model, i, :]/scaling_factor, dt)
        ax[0, i].loglog(freq, spect_noisy_signal, '-k', label='raw signal', linewidth=0.5, alpha=1)
        ax[0, i].loglog(freq, spect_clean_signal, '-r', label='true earthquake', linewidth=0.5, alpha=1)
        ax[0, i].loglog(freq, spect_denoised_signal, '-b', label='separated earthquake', linewidth=0.5, alpha=1)
        ax[1, i].loglog(freq, spect_noise, '-', color='b', label='noise', linewidth=0.5, alpha=0.8)
        ax[1, i].loglog(freq, spect_original_noise, 'r', label='orginal noise', linewidth=0.5, alpha=1)
        ax[1, i].set_xlabel('Frequency (Hz)', fontsize=14)
        ax[0, i].set_title(comps[i], fontsize=16)
        ax[1, i].grid(alpha=0.2)
        ax[0, i].grid(alpha=0.2)

    ax[0, 0].set_ylabel('velocity spectra', fontsize=14)
#    ax[1, 0].set_ylabel('velocity spectra', fontsize=14)
    plt.figure(1)
    plt.savefig(f'./Freeze_Model/figures/{model_name}_spectrum_{i_model}.pdf', bbox_inches='tight')
