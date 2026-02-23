#include <iostream>
#include <vector>
#include <cmath>
#include <string>
#include <chrono>
#include "happly.h"

// Calculate Sigmoid to convert logit to actual opacity probability (0.0 to 1.0)
inline float sigmoid(float x) {
    return 1.0f / (1.0f + std::exp(-x));
}

int main(int argc, char** argv) {
    // Parse basic CLI arguments
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <input.ply> <output.ply> [opacity_threshold]" << std::endl;
        return 1;
    }

    std::string input_path = argv[1];
    std::string output_path = argv[2];
    float threshold = (argc > 3) ? std::stof(argv[3]) : 0.05f;

    auto start_time = std::chrono::high_resolution_clock::now();

    std::cout << "Loading: " << input_path << " ..." << std::endl;
    happly::PLYData plyIn(input_path);
    happly::Element& vElement = plyIn.getElement("vertex");
    size_t num_original = vElement.count;
    std::cout << "Original Gaussians: " << num_original << std::endl;

    // 1. Extract raw opacity values and generate a pruning mask (indices)
    std::vector<float> opacities = vElement.getProperty<float>("opacity");
    std::vector<size_t> valid_indices;
    valid_indices.reserve(num_original);

    for (size_t i = 0; i < num_original; ++i) {
        if (sigmoid(opacities[i]) > threshold) {
            valid_indices.push_back(i);
        }
    }

    size_t num_optimized = valid_indices.size();
    std::cout << "Pruned Gaussians: " << num_optimized << std::endl;
    std::cout << "Compression Rate: " << (1.0f - (float)num_optimized / num_original) * 100.0f << "%" << std::endl;

    // 2. Reconstruct the output PLY with only valid indices
    happly::PLYData plyOut;
    plyOut.addElement("vertex", num_optimized);

    // Copy all 50+ properties (positions, spherical harmonics, etc.) for retained indices
    for (const auto& prop_name : vElement.getPropertyNames()) {
        std::vector<float> old_data = vElement.getProperty<float>(prop_name);
        std::vector<float> new_data(num_optimized);

        for (size_t i = 0; i < num_optimized; ++i) {
            new_data[i] = old_data[valid_indices[i]];
        }
        plyOut.getElement("vertex").addProperty<float>(prop_name, new_data);
    }

    // 3. Serialize and save to disk
    std::cout << "Writing optimized asset to: " << output_path << " ..." << std::endl;
    plyOut.write(output_path, happly::DataFormat::Binary);

    // Calculate elapsed time
    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end_time - start_time;
    std::cout << "Optimization complete in " << elapsed.count() << " seconds." << std::endl;

    return 0;
}
