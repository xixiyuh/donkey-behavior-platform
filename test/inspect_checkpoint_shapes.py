import torch

ckpt = torch.load("/var/www/realtime-detector/models/bestResNet.pt", map_location="cpu", weights_only=False)
state = ckpt["model_state_dict"]

keys_to_check = [
    "classifier.0.weight",
    "classifier.1.weight",
    "classifier.4.weight",
    "classifier.5.weight",
    "classifier.8.weight",
    "attention.0.weight",
    "attention.2.weight",
]

for k in keys_to_check:
    if k in state:
        print(k, tuple(state[k].shape))
    else:
        print(k, "NOT FOUND")

print("threshold =", ckpt.get("threshold"))