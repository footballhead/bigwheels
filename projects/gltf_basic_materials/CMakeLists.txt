# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
project(gltf_basic_materials)

add_samples_for_all_apis(
    NAME ${PROJECT_NAME}
    SOURCES
    "GltfBasicMaterials.h"
    "GltfBasicMaterials.cpp"
    "main.cpp"
    SHADER_DEPENDENCIES
    "shader_scene_renderer_vertex_material_vertex"
    "shader_scene_renderer_material_error"
    "shader_scene_renderer_material_unlit"
    "shader_scene_renderer_material_standard"
)
