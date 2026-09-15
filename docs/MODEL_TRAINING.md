# AgriSentinel — Model Training & Fine-Tuning Guide

This guide describes how to train, validate, and export custom YOLOv8 object detection models tailored for precision agricultural weed and crop identification in **AgriSentinel**.

---

## 1. Prerequisites & Environment

Model training is handled using **Ultralytics YOLOv8** and PyTorch with CUDA acceleration.

```powershell
# Ensure you are in the project root with the virtual environment activated
.\.venv\Scripts\activate
cd ml
```

---

## 2. Dataset YAML Configuration

Create a dataset descriptor file `data/custom_dataset.yaml`:

```yaml
# data/custom_dataset.yaml
path: ../datasets/agricultural_field_v1 # root dataset dir
train: images/train                    # train images (relative to 'path')
val: images/val                        # val images (relative to 'path')
test: images/test                      # test images (optional)

# Classes
names:
  0: crop
  1: weed
  2: crop_anomaly
```

Directory structure required:
```text
datasets/agricultural_field_v1/
├── images/
│   ├── train/ (e.g. img_001.jpg, img_002.jpg)
│   ├── val/
│   └── test/
└── labels/
    ├── train/ (e.g. img_001.txt, img_002.txt)
    ├── val/
    └── test/
```

Each label text file contains space-separated annotations:
`<class_id> <x_center> <y_center> <width> <height>` (normalized to $[0, 1]$).

---

## 3. Training Execution

Use the provided training script `ml/train.py` or run directly via Python:

```powershell
.\..\.venv\Scripts\python.exe ml\train.py `
  --data data/custom_dataset.yaml `
  --model yolov8n.pt `
  --epochs 100 `
  --imgsz 640 `
  --batch 16 `
  --device 0 `
  --project runs/train `
  --name agrisentinel_yolov8
```

### Recommended Hyperparameters for Precision Agriculture
- **Learning Rate**: $\text{lr}_0 = 0.01$, $\text{lrf} = 0.01$ (Cosine LR scheduler)
- **Image Augmentations**:
  - `mosaic: 1.0` (Improves small weed detection against complex soil backdrops)
  - `mixup: 0.1`
  - `degrees: 15.0` (Rotation invariance for random rover approach angles)
  - `flipud: 0.5` and `fliplr: 0.5`
  - `hsv_h: 0.015`, `hsv_s: 0.7`, `hsv_v: 0.4` (Robustness to sunlight and shadows)

---

## 4. Model Validation & Benchmark Metrics

Evaluate performance on unseen test data using `ml/validate.py`:

```powershell
.\..\.venv\Scripts\python.exe ml\validate.py `
  --model runs/train/agrisentinel_yolov8/weights/best.pt `
  --data data/custom_dataset.yaml `
  --imgsz 640
```

Validation reports standard COCO metrics:
- **Precision ($P$)**: $\frac{TP}{TP + FP}$
- **Recall ($R$)**: $\frac{TP}{TP + FN}$
- **mAP@50**: Mean Average Precision at $\text{IoU} = 0.50$
- **mAP@50-95**: Mean Average Precision across $\text{IoU} \in [0.50, 0.95]$

---

## 5. Exporting for Edge Inference

To optimize model weights for deployment onto embedded rover hardware (e.g. NVIDIA Jetson Orin Nano):

```powershell
.\..\.venv\Scripts\python.exe ml\export.py `
  --weights runs/train/agrisentinel_yolov8/weights/best.pt `
  --format onnx `
  --opset 12
```

Supported export formats:
- **ONNX**: Open Neural Network Exchange format for universal runtime execution.
- **TensorRT (`engine`)**: FP16/INT8 quantized engine optimized for NVIDIA GPUs.
- **TorchScript**: Portable serialized PyTorch graph.

---

## 6. Deploying into AgriSentinel

To mount your newly trained model into AgriSentinel:
1. Copy your trained weights:
   ```powershell
   Copy-Item runs/train/agrisentinel_yolov8/weights/best.pt models/weed_crop_model.pt
   ```
2. Restart the backend or call the reload endpoint:
   ```powershell
   Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/model/reload"
   ```
3. AgriSentinel will immediately switch to active deep learning mode (`is_generic_demo: false`).
