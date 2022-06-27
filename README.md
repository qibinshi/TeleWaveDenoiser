# Global Earthquake Denoiser  
Splitting earthquake and noise waveforms using a two-branch U net trained with global teleseismic data.
The neural network includes the pretrained [WaveDecompNet(Yin et al 2022)](https://github.com/yinjiuxun/WaveDecompNet-paper/) for the higher level feature learning.

## Create a virtual environment in Anaconda.
```
conda create -n myenv python=3.9
conda activate myenv
```
## Install essential modules in our recommended order.
```
conda install h5py
conda install pytorch -c pytorch
conda install scipy
conda install obspy -c conda-forge
conda install scikit-learn
```
## Prepare training dataset once the even-based files are ready.
Process the event-based waveform and save both P/S wave and pre-P wave signals.
```
0B_event_plus_prenoise_mpi.py
```
Add STEAD and POHA noises to the same earthquake waveforms in previous step to form another 50% of training data.
```
1B_add_STEAD_noise.py
```

## Train and test the model, with data augmented by squeezing and shifting P/S waves and stacking noises with variable SNR.
Training with stacked noisy earthquake waveform in order to obtain the denoised earthquake waveform and pure noise. Data is being augmented on the fly.
```
2B_Train_with_augmented_P_preP_partial_frozen.py
```
Evaluate the performance of the global earthquake denoiser on the testing data.
```
3B_Test_on_augmented_P_preP.py
``` 

### Alternative 1: Using only STEAD and POHA noises, and Turning off signal squeezing. It is easier to learn.
```
0A_prepare_event_data_in_mat.py
1A_save_with_noise.py
2A_Train_with_augmented_data_partial_frozen.py
3A_Test_on_augmented_data.py
```

### Alternative 2: Turn off data augmentation. It may be a good way if training data is sufficient.
```
1_stack_with_noise.py
2_Train_Adaptors_Freeze_WDN.py
3_test_model_on_teleseismic_wave.py
```

## Apply the model to real waveforms
Prepare the raw noisy data.
```
4_new_class_data_for_application.py
```
Denoise and plot the output signal and noise in time and spectrum domain.
```
5_apply_noisy_data.py
```
