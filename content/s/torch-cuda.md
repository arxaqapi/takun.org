+++
title = "🔥 Pytorch GPU/CUDA utils"
slug = "pytorch-utils"
+++

#### Is cuda available?
```python
torch.cuda.is_available()
```
#### Count the amount of available devices 
```python
torch.cuda.device_count()
```
#### Current device index
```python
torch.cuda.current_device()
```
#### Informations about device
```python
torch.cuda.device(0)
```
#### Name of the currnet GPU
```python
torch.cuda.get_device_name(0)
```
