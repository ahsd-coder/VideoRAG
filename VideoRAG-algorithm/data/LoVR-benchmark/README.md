---
license: cc-by-nc-sa-4.0
task_categories:
- video-text-to-text
tags:
- Video
size_categories:
- 10K<n<100K
---

This repository hosts the **LoVR benchmark dataset**, designed for research on **long video–text retrieval**.  
The original video data is sourced from [LongVideoBench](https://longvideobench.github.io/). We sincerely thank the authors for their outstanding work.

Building upon LongVideoBench, we curate **high-quality captions and semantic annotations** tailored for long-form video understanding and retrieval tasks.

The corresponding GitHub repository for this project is available at:  
👉 https://github.com/TechNomad-ds/LoVR-benchmark

Below we provide an overview of the dataset structure and usage instructions.

---

# 📁 Dataset Contents

The dataset consists of the following components:

### 🎬 Segmented Clips
All raw video clips are stored in the `video_data` folder.

Due to the large size of the video files and upload limitations on Hugging Face, the archive containing the video data has been **split into multiple parts**. Instructions for reconstructing the complete archive are provided below.

### 📝 Clip-level Annotations
Located in the `caption_data` folder:

- `clip_train.parquet`: Clip-level captions for the **training set**
- `clip_test.parquet`: Clip-level captions for the **test set**

### 📄 Video-level Annotations
Also located in the `caption_data` folder:

- `video_train.parquet`: Video-level captions for the **training set**
- `video_test.parquet`: Video-level captions for the **test set**

---

# 📦 Video Data Assembly

Due to file size limitations on Hugging Face, the video archive has been split into three parts:

```

part_aa
part_ab
part_ac

````

To reconstruct the complete archive, run:

```bash
cat part_* > the_final_file.tar.gz
````

Then extract the archive using:

```bash
tar -xzf the_final_file.tar.gz
```

---

# 🎥 Video Aggregation

The full videos are constructed by **concatenating the corresponding clip sequences**.

To reconstruct the full videos from individual clips, run:

```bash
python merge_clips.py --input ./your_input_folder --output ./your_output_folder
```

Replace the paths with your actual directories.
The script `merge_clips.py` is available in the `scripts/` folder of this repository.

---

# ⚠️ Responsible Use

We encourage **responsible and ethical use** of the LoVR benchmark dataset.

This dataset is intended **for academic research and educational purposes only**. Users must **not** use the dataset to develop applications that are harmful, discriminatory, or violate privacy.

We strongly recommend conducting **fairness evaluations and ethical assessments** when applying this dataset to downstream tasks.

---

# 📚 Citation

If you find the **LoVR benchmark dataset** useful in your research, please consider citing our work:

```bibtex
@article{cai2025lovr,
  title={LoVR: A Benchmark for Long Video Retrieval in Multimodal Contexts},
  author={Cai, Qifeng and Liang, Hao and Han, Zhaoyang and Dong, Hejun and Qiang, Meiyi and An, Ruichuan and Xu, Quanqing and Cui, Bin and Zhang, Wentao},
  journal={arXiv preprint arXiv:2505.13928},
  year={2025}
}
```