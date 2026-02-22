import argparse
import numpy as np
import os
from plyfile import PlyData, PlyElement


def get_file_size_mb(filepath):
    """Utility function to get file size in Megabytes."""
    return os.path.getsize(filepath) / (1024 * 1024)


def optimize_3dgs_ply(input_path, output_path, opacity_threshold=0.05):
    print(f"Loading {input_path}...")

    # 1. Read the raw PLY data
    plydata = PlyData.read(input_path)
    vertex_data = plydata.elements[0].data

    # Base Metrics: Original count and estimated VRAM (based on array byte size)
    num_original = len(vertex_data)
    original_vram_mb = vertex_data.nbytes / (1024 * 1024)
    original_file_mb = get_file_size_mb(input_path)

    # 2. Extract opacity and apply the Sigmoid function
    # Note: 3DGS stores raw logit values for opacity; we convert them to actual probabilities (0.0 to 1.0)
    raw_opacity = vertex_data['opacity']
    real_opacity = 1 / (1 + np.exp(-raw_opacity))

    # 3. Generate a mask: Keep only Gaussians with an opacity greater than the threshold
    mask = real_opacity > opacity_threshold

    # 4. Apply the mask to filter the data (vectorized Numpy operation for max throughput)
    optimized_data = vertex_data[mask]

    # Optimized Metrics:
    num_optimized = len(optimized_data)
    optimized_vram_mb = optimized_data.nbytes / (1024 * 1024)

    # 5. Reconstruct and save the optimized PLY file
    print(f"Pruning complete. Saving optimized asset to {output_path}...")
    optimized_element = PlyElement.describe(optimized_data, 'vertex')
    PlyData([optimized_element], text=False).write(output_path)

    optimized_file_mb = get_file_size_mb(output_path)

    # 6. Calculate reductions
    count_reduction = (1 - num_optimized / num_original) * 100
    size_reduction = (1 - optimized_file_mb / original_file_mb) * 100
    vram_reduction = (1 - optimized_vram_mb / original_vram_mb) * 100

    # 7. Print formatted metrics to match the README documentation
    print("\n" + "="*65)
    print(f"{'PERFORMANCE METRICS':^65}")
    print("="*65)
    print(f"{'Metric':<22} | {'Raw Asset':<12} | {'Optimized':<12} | {'Reduction'}")
    print("-" * 65)
    print(f"{'File Size':<22} | {original_file_mb:>8.2f} MB | {optimized_file_mb:>9.2f} MB | {size_reduction:>7.2f}%")
    print(f"{'Gaussian Count':<22} | {num_original:>11,} | {num_optimized:>12,} | {count_reduction:>7.2f}%")
    print(f"{'VRAM Footprint (Est)':<22} | {original_vram_mb:>8.2f} MB | {optimized_vram_mb:>9.2f} MB | {vram_reduction:>7.2f}%")
    print("="*65 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimize 3DGS PLY files by pruning transparent Gaussians.")
    parser.add_argument('--input', type=str, required=True, help='Path to the raw input PLY file.')
    parser.add_argument('--output', type=str, required=True, help='Path to save the optimized PLY file.')
    parser.add_argument('--threshold', type=float, default=0.05, help='Opacity threshold for pruning (0.0 to 1.0).')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found. Please check the path.")
    else:
        optimize_3dgs_ply(args.input, args.output, args.threshold)
