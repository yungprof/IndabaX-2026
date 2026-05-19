# Building Ethical Vision Systems

**Ghana Data Science Summit 2026 · IndabaX Tutorial**

A hands-on two-part tutorial on how computer vision models work, how they are deployed in high-stakes medical settings, and what it means to audit them for fairness before putting them in front of patients.

---

## Open in Colab

| Notebook | Topic | Link |
|---|---|---|
| **Part 1** | How Vision Models Work | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Nanayeb34/IndabaX-2026/blob/main/Ethical%20Computer%20Vision/notebook/Part1.ipynb) |
| **Part 2** | Auditing for Bias & Fairness | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Nanayeb34/IndabaX-2026/blob/main/Ethical%20Computer%20Vision/notebook/Part2.ipynb) |

Click a badge → the notebook opens directly in Google Colab. No local installation needed.

---

## What you will learn

### Part 1 — How Vision Models Work

Start from a single photograph taken by a community health worker in Brong-Ahafo and trace exactly what the model does to it.

| Section | Topics |
|---|---|
| **00 Setup** | Install packages, clone sample images |
| **01 The Image Arrives** | Pixels as tensors, colour spaces, intensity histograms |
| **02 Preprocessing** | CLAHE contrast enhancement, shadow removal, unsharp masking, edge detection |
| **03 CNNs** | Convolution, activation, pooling, backpropagation, EfficientNet & ResNet |
| **04 Which Model?** | YOLO single-pass detection, Vision Transformers, CLIP zero-shot classification |
| **05 Applications** | Medical imaging hierarchy (classification → detection → segmentation), Grad-CAM explainability |
| **06 Ethics** | Who is represented in training data? What does the model fail to see? |

### Part 2 — Auditing for Bias & Fairness

A startup claims their skin-lesion classifier achieves 87 % accuracy. You are the independent auditor.

| Section | Topics |
|---|---|
| **00 Setup** | Install packages, download model checkpoint and audit datasets |
| **01 The Baseline Run** | Load EfficientNet-B0 trained on HAM10000, run full inference, inspect confusion matrix and per-class F1 |
| **02 The Stress Test** | Compare performance on HAM10000 vs. an African-context dataset; measure accuracy gap across Fitzpatrick skin types |
| **03 Document Failures** | Build a failure table, visualise high-confidence wrong predictions, identify root causes (training data distribution, labelling artefacts) |
| **04 Propose a Path** | Weigh mitigation options (data augmentation, resampling, domain adaptation, human-in-the-loop); write a structured audit recommendation |

---

## How to run

1. Click an **Open in Colab** badge above.
2. In Colab, go to **Runtime → Run all** (or step through cells with Shift+Enter).
3. The first two cells install all dependencies and clone the sample images automatically — no manual setup required.

Part 2 additionally downloads a model checkpoint and datasets from Google Drive (the facilitator provides the folder link before the session).

---

## Audience & prerequisites

- **Audience:** participants at an intermediate ML workshop — comfortable with Python and NumPy, some prior exposure to neural networks.
- **No GPU required** for Part 1. Part 2 benefits from Colab's free T4 GPU (Runtime → Change runtime type → T4 GPU).
- Both notebooks are self-contained: all helper functions are defined inline; nothing is imported from this repo's source tree.

---

## Repository layout

```
Ethical Computer Vision/
├── data/
│   ├── sample_images/          # 12 annotated skin images (Part 1)
│   ├── ham10000_datasheet.md   # Dataset documentation card
│   └── README.md
├── notebook/
│   ├── Part1.ipynb             # Standalone Colab notebook
│   └── Part2.ipynb             # Standalone Colab notebook
└── requirements.txt            # Pin file for local development
```

---

## Acknowledgements

Sample images are used for educational purposes only.
The HAM10000 dataset is published under CC BY-NC 4.0 by Tschandl et al. (2018).
