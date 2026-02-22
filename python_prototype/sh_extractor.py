import numpy as np
from plyfile import PlyData
import plotly.graph_objs as go
import argparse
import os


def extract_and_visualize(input_path, output_html, max_points=50000):
    print(f"Loading {input_path}...")
    plydata = PlyData.read(input_path)
    vertex_data = plydata.elements[0].data

    total_points = len(vertex_data)
    print(f"Loaded {total_points} Gaussians.")

    # 1. Downsample to prevent browser OOM (Out Of Memory) crashes during rendering
    if total_points > max_points:
        print(f"Downsampling to {max_points} points for browser rendering...")
        indices = np.random.choice(total_points, max_points, replace=False)
        sampled_data = vertex_data[indices]
    else:
        sampled_data = vertex_data

    # 2. Extract spatial coordinates (Geometry)
    x = sampled_data['x']
    y = sampled_data['y']
    z = sampled_data['z']

    # ================= NEW: SPATIAL CROPPING (AABB) =================
    # A radial crop forms a sphere, which chops off the corners of a flat chessboard.
    # Instead, we construct an Axis-Aligned Bounding Box (AABB) using statistical percentiles.

    # Define percentile bounds to trim the extreme outliers (the skybox shell)
    # By trimming the bottom 10% and top 5% of the spatial distribution on each axis, 
    # we effectively strip away the sparse background without harming the dense core object.
    p_lower = 5.0
    p_upper = 95.0

    # Calculate the bounding box limits for each independent axis
    x_min, x_max = np.percentile(x, [p_lower, p_upper])
    y_min, y_max = np.percentile(y, [p_lower, p_upper])
    z_min, z_max = np.percentile(z, [p_lower, p_upper])

    # Create a boolean mask for points strictly inside the 3D bounding box
    spatial_mask = (x >= x_min) & (x <= x_max) & \
                   (y >= y_min) & (y <= y_max) & \
                   (z >= z_min) & (z <= z_max)

    # Apply the spatial cropping mask to the geometry and the full dataset
    x, y, z = x[spatial_mask], y[spatial_mask], z[spatial_mask]
    sampled_data = sampled_data[spatial_mask]
    # ================================================================

    # 3. Core Logic: Reconstruct diffuse RGB color from the 0th order Spherical Harmonics (SH DC)
    # The mathematical formula to convert SH DC components to RGB is: RGB = SH_DC * 0.28209479 + 0.5
    SH_C0 = 0.28209479
    r = np.clip(sampled_data['f_dc_0'] * SH_C0 + 0.5, 0.0, 1.0) * 255
    g = np.clip(sampled_data['f_dc_1'] * SH_C0 + 0.5, 0.0, 1.0) * 255
    b = np.clip(sampled_data['f_dc_2'] * SH_C0 + 0.5, 0.0, 1.0) * 255

    # Format colors for Plotly ingest (e.g., 'rgb(255, 0, 0)')
    colors = [f'rgb({int(r[i])}, {int(g[i])}, {int(b[i])})' for i in range(len(r))]

    # 4. Construct the interactive 3D scatter plot
    print("Generating interactive 3D plot...")
    trace = go.Scatter3d(
        x=x, y=y, z=z,
        mode='markers',
        marker=dict(
            size=2,          # Adjust point size for better visual density
            color=colors,    # Recovered physical diffuse colors
            opacity=0.8
        )
    )

    layout = go.Layout(
        title="3DGS Point Cloud Extracted from Spherical Harmonics",
        scene=dict(
            xaxis=dict(title='X'),
            yaxis=dict(title='Y'),
            zaxis=dict(title='Z'),
            aspectmode='data' # Maintain strict physical aspect ratio; prevents axis stretching
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )

    fig = go.Figure(data=[trace], layout=layout)

    # 5. Export as a standalone offline HTML file
    fig.write_html(output_html)
    print(f"Done! Saved visualization to {output_html}")


if __name__ == "__main__":
    # Setup CLI arguments for CI/CD or terminal usage
    parser = argparse.ArgumentParser(description="Extract SH DC components to visualize 3DGS as a standard RGB point cloud.")
    parser.add_argument('--input', type=str, required=True, help='Path to the input PLY file.')
    parser.add_argument('--output', type=str, required=True, help='Path to save the output HTML visualization.')
    parser.add_argument('--max_points', type=int, default=50000, help='Maximum number of points to render (prevents browser crash).')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found. Please check the path.")
    else:
        extract_and_visualize(args.input, args.output, args.max_points)
