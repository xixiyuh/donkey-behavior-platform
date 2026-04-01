import torch
from pprint import pprint

ckpt_path = "/var/www/realtime-detector/models/bestResNet.pt"
ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)

print("checkpoint type:", type(ckpt))
if isinstance(ckpt, dict):
    print("top-level keys:")
    pprint(list(ckpt.keys()))

    if "model_state_dict" in ckpt:
        state = ckpt["model_state_dict"]
        print("\nstate_dict first 50 keys:")
        for i, k in enumerate(state.keys()):
            if i >= 50:
                break
            print(k)