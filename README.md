# RIR-D SLAM (stella_vslam_ros_RIR-D)

ROS2 wrapper implementing **RGB-IR-Depth SLAM (RIR-D SLAM)**, a multimodal extension of
[StellaVSLAM](https://github.com/stella-cv/stella_vslam_ros) unifying RGB, near-infrared (NIR),
and depth sensing within a single tracking/mapping pipeline. This repository accompanies the
paper *"RIR-D SLAM: Joint high resolution RGB-D and wide-angle NIR-D visual SLAM"*
(submitted) and contains everything needed to reproduce its experiments.

> **Naming note:** the project is referred to as *RIR-D SLAM* to avoid confusion with an
> unrelated prior work also named "RID SLAM". Internal file and launch names (e.g.
> `RID_CD-MaJ_WFOV.py`, `RID_WFOV.yaml`) still use the legacy `RID` prefix pending a
> future renaming pass; they refer to the same system described in this README.

---

## 1. Prerequisites

### 1.1 Core SLAM engine (required first)

This wrapper depends on a modified `stella_vslam` engine (RGBIRD branch) and follows the
official installation procedure:
https://stella-cv.readthedocs.io/en/latest/ros2_package.html#installation

```bash
git clone --recursive --depth 1 -b RGBIRD https://github.com/EvaGoichon/openvslam-omni.git stella_vslam
cd stella_vslam
# follow the official build/install instructions from the link above, unchanged
```
> ⚠️ This fork is currently **private**. Contact eva.goichon@outlook.fr to request access.

Verify the engine installs and builds successfully before continuing.

### 1.2 System dependencies

- ROS 2 Humble (or compatible)
- OpenCV ≥ 4.6
- Eigen3, spdlog, yaml-cpp

```bash
rosdep install --from-paths src --ignore-src -r -y
```

---

## 2. Getting this repository

This repo vendors several header-only dependencies as **git submodules** under `3rd/`
(`ghc_filesystem`, `json`, `popl`, `spdlog`). A plain `git clone` will **not** fetch them.

```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone --recursive https://github.com/EvaGoichon/image_processing.git
git clone --recursive https://github.com/EvaGoichon/stella_vslam_ros_RIR-D.git
```

If already cloned without `--recursive`:
```bash
cd stella_vslam_ros_RIR-D && git submodule update --init --recursive
```

### 2.1 ORB vocabulary

```bash
curl -sL "https://github.com/stella-cv/FBoW_orb_vocab/raw/main/orb_vocab.fbow" -o orb_vocab.fbow
```
Its path is passed explicitly at launch (`vocab_file` argument); it is not bundled in this repository.

### 2.2 Dataset (CD-MaJ)

Quantitative experiments use the `cd-maj` dataset (rosbags with synchronized RGB, IR,
and depth streams for WFOV and NFOV configurations), available at:
https://extra.u-picardie.fr/nextcloud/index.php/s/yLG72QH46tsSiea

### 2.3 Real-world sequences (dark / dark-to-lit)

The two real-world sequences used in Section "Robustness under Real Lighting
Variations" (no ground truth, WFoV only) will be made available shortly — link to be
added here. In the meantime, contact eva.goichon@outlook.fr .

---

## 3. Build

```bash
cd ~/ros2_ws
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

---

## 4. Repository layout

```
launch/   ROS2 launch files, one per (modality x FoV / scenario) combination
yaml/     StellaVSLAM configuration files (camera intrinsics, ORB/mapping parameters)
src/      C++ wrapper source (stella_vslam_ros.cc/.h, run_slam.cc)
config/   default StellaVSLAM node parameters (largely unused by paper experiments)
```

Each `launch/*.py` file starts, in sequence: RGB/depth republishers, IR preprocessing
(`active_ir_processor`), the degradation node (`occlusion`), the SLAM node itself
(after a short delay), and finally `ros2 bag play` on the dataset (after all nodes are
up). Degradation intensity and the dataset path are exposed as launch arguments; you
do not need to run `ros2 bag play` or `occlusion` manually.

---

## 5. Reproducing the paper's experiments

### 5.1 Clean environment before every run (important)

Leftover nodes from a previous `Ctrl+C` can silently corrupt the next run (duplicate
publishers, competing `ros2 bag play` instances). Always run this first:

```bash
pkill -9 -f run_slam; pkill -9 -f image_processing; pkill -9 -f republish; pkill -9 -f "bag play"
sleep 3
ros2 node list   # must print nothing
```

### 5.2 Launch commands

| FoV  | Modality | Scenario         | Command |
|------|----------|-------------------|---------|
| WFoV | RGB-D    | nominal / dimmed  | `ros2 launch stella_vslam_ros RGBD_CD-MaJ_WFOV.py vocab_file:=<path> config_file:=yaml/RGBD_WFOV.yaml bag_file:=<path> dimming:=0` (or `50`) |
| WFoV | RID      | nominal / dimmed / blackout | `ros2 launch stella_vslam_ros RID_CD-MaJ_WFOV.py vocab_file:=<path> config_file:=yaml/RID_WFOV.yaml bag_file:=<path> dimming:=0` (`50`, or `100`) |
| NFoV | RGB-D    | nominal / dimmed  | `ros2 launch stella_vslam_ros RGBD_CD-MaJ_NFOV.py vocab_file:=<path> config_file:=yaml/RGBD_NFOV.yaml bag_file:=<path> dimming:=0` (or `50`) |
| NFoV | RID      | nominal / dimmed / blackout | `ros2 launch stella_vslam_ros RID_CD-MaJ_NFOV.py vocab_file:=<path> config_file:=yaml/RID_NFOV.yaml bag_file:=<path> dimming:=0` (`50`, or `100`) |
| WFoV | RGB-D / RID | real-world dark sequence | `RGBD_dark.py` / `RID_dark.py` (no `dimming` argument; uses a real low-light recording, no ground truth) |
| WFoV | RGB-D / RID | real-world dark-to-lit sequence | `RGBD_dark_and_bright.py` / `RID_dark_and_bright.py` |

`RGB-D` was evaluated under 100% dimming (blackout) and reliably fails to initialize
under these conditions (see paper, quantitative results table); no successful
trajectory is produced.

List all arguments and defaults for any launch file with:
```bash
ros2 launch stella_vslam_ros <file>.py --show-args
```

### 5.3 Outputs

Each run produces, in the working directory: `*_frame_trajectory.txt` and
`*_keyframe_trajectory.txt` (TUM format), `*_map.msg` (msgpack map database), and
`*_track_times.txt` (per-frame processing time, in seconds). Trajectory evaluation uses
[`evo`](https://github.com/MichaelGrupp/evo).

---

## 6. License

This project is based on [StellaVSLAM](https://github.com/stella-cv/stella_vslam_ros)
(see `LICENSE.original`) with modifications under `LICENSE.fork`. See `LICENSE` for the
combined terms.

## Citation

If you use this code, please cite:
```bibtex
@inproceedings{goichon2026rird,
  author    = {Eva Goichon and Guillaume Caron and Pascal Vasseur and Fumio Kanehiro},
  title     = {RIR-D SLAM: Joint high resolution RGB-D and wide-angle NIR-D visual SLAM},
  booktitle = {SII2027},
  year      = {2026},
  note      = {submitted}
}
```

---

© 2025 Eva Goichon — Based on the open-source [StellaVSLAM](https://github.com/stella-cv/stella_vslam_ros) project.
