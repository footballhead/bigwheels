// Copyright 2024 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "ppx/ppx.h"
#include "ppx/scene/scene_material.h"
#include "ppx/scene/scene_mesh.h"
#include "ppx/scene/scene_pipeline_args.h"
#include "ppx/scene/scene_gltf_loader.h"
#include "ppx/graphics_util.h"

#include <unordered_map>
#include <memory>

namespace {

using namespace ppx;

#if defined(USE_DX12)
const grfx::Api kApi = grfx::API_DX_12_0;
#elif defined(USE_VK)
const grfx::Api kApi = grfx::API_VK_1_1;
#endif

// Use an interactive camera instead of any in the scene
constexpr bool kForceArcballCamera = false;

ppx::AABB GetTransformedMeshNodeBoundingBox(const scene::MeshNode& meshNode)
{
    const float4x4  transform       = meshNode.GetEvaluatedMatrix();
    const ppx::AABB meshBoundingBox = meshNode.GetMesh()->GetBoundingBox();

    float3 obbVertices[8] = {};
    meshBoundingBox.Transform(transform, obbVertices);

    ppx::AABB transformedBoundingBox;
    transformedBoundingBox.Expand(obbVertices[0]);
    transformedBoundingBox.Expand(obbVertices[1]);
    transformedBoundingBox.Expand(obbVertices[2]);
    transformedBoundingBox.Expand(obbVertices[3]);
    transformedBoundingBox.Expand(obbVertices[4]);
    transformedBoundingBox.Expand(obbVertices[5]);
    transformedBoundingBox.Expand(obbVertices[6]);
    transformedBoundingBox.Expand(obbVertices[7]);
    return transformedBoundingBox;
}

ppx::AABB GetSceneBoundingBox(const scene::Scene& scene)
{
    ppx::AABB sceneBoundingBox;
    for (uint32_t i = 0; i < scene.GetMeshNodeCount(); ++i) {
        const ppx::AABB transformedMeshNodeBoundingBox = GetTransformedMeshNodeBoundingBox(*scene.GetMeshNode(i));
        sceneBoundingBox.Expand(transformedMeshNodeBoundingBox.GetMax());
        sceneBoundingBox.Expand(transformedMeshNodeBoundingBox.GetMin());
    }
    return sceneBoundingBox;
}

// Renders a GLTF scene. If a camera is provided in the scene then that is used. Otherwise, an interactive arcball camera is added.
class GltfSceneViewer : public ppx::Application
{
public:
    void Config(ppx::ApplicationSettings& settings) override
    {
        settings.appName                    = "gltf_scene_viewer";
        settings.grfx.api                   = kApi;
        settings.grfx.swapchain.depthFormat = grfx::FORMAT_D32_FLOAT;
        settings.allowThirdPartyAssets      = true;
    }

    void MouseMove(int32_t x, int32_t y, int32_t dx, int32_t dy, uint32_t buttons) override
    {
        if (mArcballCamera.has_value()) {
            if (buttons & ppx::MOUSE_BUTTON_LEFT) {
                const int32_t prevX = x - dx;
                const int32_t prevY = y - dy;

                const float2 prevPos = GetNormalizedDeviceCoordinates(prevX, prevY);
                const float2 curPos  = GetNormalizedDeviceCoordinates(x, y);

                mArcballCamera->Rotate(prevPos, curPos);
            }
            else if (buttons & ppx::MOUSE_BUTTON_RIGHT) {
                const int32_t prevX = x - dx;
                const int32_t prevY = y - dy;

                const float2 prevPos = GetNormalizedDeviceCoordinates(prevX, prevY);
                const float2 curPos  = GetNormalizedDeviceCoordinates(x, y);
                const float2 delta   = curPos - prevPos;

                mArcballCamera->Pan(delta);
            }
        }
    }

    void Scroll(float /*dx*/, float dy) override
    {
        if (mArcballCamera.has_value()) {
            mArcballCamera->Zoom(dy / 2.0f);
        }
    }

    void Shutdown() override
    {
        delete mScene;
        delete mPipelineArgs;
    }

    void Setup() override;
    void Render() override;

private:
    struct PerFrame
    {
        ppx::grfx::CommandBufferPtr cmd;
        ppx::grfx::SemaphorePtr     imageAcquiredSemaphore;
        ppx::grfx::FencePtr         imageAcquiredFence;
        ppx::grfx::SemaphorePtr     renderCompleteSemaphore;
        ppx::grfx::FencePtr         renderCompleteFence;
    };

    std::vector<PerFrame>           mPerFrame;
    ppx::grfx::ShaderModulePtr      mVS;
    ppx::grfx::ShaderModulePtr      mPS;
    ppx::grfx::PipelineInterfacePtr mPipelineInterface;
    ppx::grfx::GraphicsPipelinePtr  mStandardMaterialPipeline = nullptr;
    ppx::grfx::GraphicsPipelinePtr  mUnlitMaterialPipeline    = nullptr;
    ppx::grfx::GraphicsPipelinePtr  mErrorMaterialPipeline    = nullptr;

    // Can't use smart pointers because these need to be freed in Shutdown() before the destructor.
    ppx::scene::Scene*                mScene        = nullptr;
    ppx::scene::MaterialPipelineArgs* mPipelineArgs = nullptr;

    std::unordered_map<const ppx::scene::Material*, uint32_t>                     mMaterialIndexMap;
    std::unordered_map<const ppx::scene::Material*, ppx::grfx::GraphicsPipeline*> mMaterialPipelineMap;

    ppx::grfx::TexturePtr mIBLIrrMap;
    ppx::grfx::TexturePtr mIBLEnvMap;

    // Valid only if the glTF scene does not have a camera.
    std::optional<ppx::ArcballCamera> mArcballCamera;
};

void GltfSceneViewer::Setup()
{
    // Per frame data
    {
        PerFrame frame = {};

        PPX_CHECKED_CALL(GetGraphicsQueue()->CreateCommandBuffer(&frame.cmd));

        grfx::SemaphoreCreateInfo semaCreateInfo = {};
        PPX_CHECKED_CALL(GetDevice()->CreateSemaphore(&semaCreateInfo, &frame.imageAcquiredSemaphore));

        grfx::FenceCreateInfo fenceCreateInfo = {};
        PPX_CHECKED_CALL(GetDevice()->CreateFence(&fenceCreateInfo, &frame.imageAcquiredFence));

        PPX_CHECKED_CALL(GetDevice()->CreateSemaphore(&semaCreateInfo, &frame.renderCompleteSemaphore));

        fenceCreateInfo = {true}; // Create signaled
        PPX_CHECKED_CALL(GetDevice()->CreateFence(&fenceCreateInfo, &frame.renderCompleteFence));

        mPerFrame.push_back(frame);
    }

    // Load GLTF scene
    {
        const std::string  defaultScene = "scene_renderer/scenes/tests/gltf_test_basic_materials.glb";
        scene::GltfLoader* pLoaderRaw   = nullptr;
        PPX_CHECKED_CALL(scene::GltfLoader::Create(
            GetAssetPath(GetExtraOptions().GetExtraOptionValueOrDefault("gltf-scene-file", defaultScene)),
            /*pMaterialSelector=*/nullptr,
            &pLoaderRaw));
        std::unique_ptr<scene::GltfLoader> pLoader(pLoaderRaw);

        PPX_CHECKED_CALL(pLoader->LoadScene(GetDevice(), 0, &mScene));
        if (mScene->GetCameraNodeCount() == 0 || kForceArcballCamera) {
            PPX_LOG_WARN("scene doesn't have camera nodes; using ArcballCamera");
            // Initial values coped from projects/arcball_camera/main.cpp
            // TODO: Constructor produces different results compared to LookAt + SetPerspective
            // mArcballCamera = ArcballCamera(float3(4, 5, 8), float3(0, 0, 0), float3(0, 1, 0), 60.0f, GetWindowAspect());
            mArcballCamera = ArcballCamera();
            mArcballCamera->LookAt(float3(4, 5, 8), float3(0, 0, 0), float3(0, 1, 0));
            mArcballCamera->SetPerspective(60.0f, GetWindowAspect());

            const ppx::AABB sceneBoundingBox = GetSceneBoundingBox(*mScene);
            mArcballCamera->FitToBoundingBox(sceneBoundingBox.GetMin(), sceneBoundingBox.GetMax());
        }
        PPX_ASSERT_MSG((mScene->GetMeshNodeCount() > 0), "scene doesn't have mesh nodes");
    }

    // IBL Textures
    {
        PPX_CHECKED_CALL(grfx_util::CreateIBLTexturesFromFile(
            GetDevice()->GetGraphicsQueue(),
            GetAssetPath("poly_haven/ibl/old_depot_4k.ibl"),
            &mIBLIrrMap,
            &mIBLEnvMap));
    }

    // Pipeline args
    {
        PPX_CHECKED_CALL(scene::MaterialPipelineArgs::Create(GetDevice(), &mPipelineArgs));

        // Populate material samplers
        auto samplersIndexMap = mScene->GetSamplersArrayIndexMap();
        for (auto it : samplersIndexMap) {
            mPipelineArgs->SetMaterialSampler(it.second, it.first);
        }

        // Populate material images
        auto imagesIndexMap = mScene->GetImagesArrayIndexMap();
        for (auto it : imagesIndexMap) {
            mPipelineArgs->SetMaterialTexture(it.second, it.first);
        }

        // Populate material params
        // TODO missing METAL, etc labels
        mMaterialIndexMap = mScene->GetMaterialsArrayIndexMap();
        for (auto it : mMaterialIndexMap) {
            auto           pMaterial = it.first;
            const uint32_t index     = it.second;

            auto pMaterialParams = mPipelineArgs->GetMaterialParams(index);

            if (pMaterial->GetIdentString() == PPX_MATERIAL_IDENT_STANDARD) {
                auto pStandardMaterial = static_cast<const scene::StandardMaterial*>(pMaterial);

                pMaterialParams->baseColorFactor   = pStandardMaterial->GetBaseColorFactor();
                pMaterialParams->metallicFactor    = pStandardMaterial->GetMetallicFactor();
                pMaterialParams->roughnessFactor   = pStandardMaterial->GetRoughnessFactor();
                pMaterialParams->occlusionStrength = pStandardMaterial->GetOcclusionStrength();
                pMaterialParams->emissiveFactor    = pStandardMaterial->GetEmissiveFactor();
                pMaterialParams->emissiveStrength  = pStandardMaterial->GetEmissiveStrength();

                scene::CopyMaterialTextureParams(samplersIndexMap, imagesIndexMap, pStandardMaterial->GetBaseColorTextureView(), pMaterialParams->baseColorTex);
                scene::CopyMaterialTextureParams(samplersIndexMap, imagesIndexMap, pStandardMaterial->GetMetallicRoughnessTextureView(), pMaterialParams->metallicRoughnessTex);
                scene::CopyMaterialTextureParams(samplersIndexMap, imagesIndexMap, pStandardMaterial->GetNormalTextureView(), pMaterialParams->normalTex);
                scene::CopyMaterialTextureParams(samplersIndexMap, imagesIndexMap, pStandardMaterial->GetOcclusionTextureView(), pMaterialParams->occlusionTex);
                scene::CopyMaterialTextureParams(samplersIndexMap, imagesIndexMap, pStandardMaterial->GetEmissiveTextureView(), pMaterialParams->emssiveTex);
            }
            else if (pMaterial->GetIdentString() == PPX_MATERIAL_IDENT_UNLIT) {
                auto pUnlitMaterial              = static_cast<const scene::UnlitMaterial*>(pMaterial);
                pMaterialParams->baseColorFactor = pUnlitMaterial->GetBaseColorFactor();
                scene::CopyMaterialTextureParams(samplersIndexMap, imagesIndexMap, pUnlitMaterial->GetBaseColorTextureView(), pMaterialParams->baseColorTex);
            }
        }

        // Populate IBL textures
        mPipelineArgs->SetIBLTextures(0, mIBLIrrMap->GetSampledImageView(), mIBLEnvMap->GetSampledImageView());
    }

    // Pipelines
    {
        grfx::PipelineInterfaceCreateInfo piCreateInfo = {};
        piCreateInfo.pushConstants.count               = 32;
        piCreateInfo.pushConstants.binding             = 0;
        piCreateInfo.pushConstants.set                 = 0;
        piCreateInfo.setCount                          = 1;
        piCreateInfo.sets[0].set                       = 0;
        piCreateInfo.sets[0].pLayout                   = mPipelineArgs->GetDescriptorSetLayout();
        PPX_CHECKED_CALL(GetDevice()->CreatePipelineInterface(&piCreateInfo, &mPipelineInterface));

        // Get vertex bindings - every mesh in the test scene should have the same attributes
        auto vertexBindings = mScene->GetMeshNode(0)->GetMesh()->GetMeshData()->GetAvailableVertexBindings();

        auto CreatePipeline = [this, &vertexBindings](const std::string& vsName, const std::string& psName, grfx::GraphicsPipeline** ppPipeline) {
            std::vector<char> bytecode = LoadShader("scene_renderer/shaders", vsName);
            PPX_ASSERT_MSG(!bytecode.empty(), "VS shader bytecode load failed");
            grfx::ShaderModuleCreateInfo shaderCreateInfo = {static_cast<uint32_t>(bytecode.size()), bytecode.data()};
            PPX_CHECKED_CALL(GetDevice()->CreateShaderModule(&shaderCreateInfo, &mVS));

            bytecode = LoadShader("scene_renderer/shaders", psName);
            PPX_ASSERT_MSG(!bytecode.empty(), "PS shader bytecode load failed");
            shaderCreateInfo = {static_cast<uint32_t>(bytecode.size()), bytecode.data()};
            PPX_CHECKED_CALL(GetDevice()->CreateShaderModule(&shaderCreateInfo, &mPS));

            grfx::GraphicsPipelineCreateInfo2 gpCreateInfo  = {};
            gpCreateInfo.VS                                 = {mVS.Get(), "vsmain"};
            gpCreateInfo.PS                                 = {mPS.Get(), "psmain"};
            gpCreateInfo.topology                           = grfx::PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
            gpCreateInfo.polygonMode                        = grfx::POLYGON_MODE_FILL;
            gpCreateInfo.cullMode                           = grfx::CULL_MODE_BACK;
            gpCreateInfo.frontFace                          = grfx::FRONT_FACE_CCW;
            gpCreateInfo.depthReadEnable                    = true;
            gpCreateInfo.depthWriteEnable                   = true;
            gpCreateInfo.blendModes[0]                      = grfx::BLEND_MODE_NONE;
            gpCreateInfo.outputState.renderTargetCount      = 1;
            gpCreateInfo.outputState.renderTargetFormats[0] = GetSwapchain()->GetColorFormat();
            gpCreateInfo.outputState.depthStencilFormat     = GetSwapchain()->GetDepthFormat();
            gpCreateInfo.pPipelineInterface                 = mPipelineInterface;

            gpCreateInfo.vertexInputState.bindingCount = CountU32(vertexBindings);
            for (uint32_t i = 0; i < gpCreateInfo.vertexInputState.bindingCount; ++i) {
                gpCreateInfo.vertexInputState.bindings[i] = vertexBindings[i];
            }

            PPX_CHECKED_CALL(GetDevice()->CreateGraphicsPipeline(&gpCreateInfo, ppPipeline));
        };

        // Pipelines
        CreatePipeline("MaterialVertex.vs", "StandardMaterial.ps", &mStandardMaterialPipeline);
        CreatePipeline("MaterialVertex.vs", "UnlitMaterial.ps", &mUnlitMaterialPipeline);
        CreatePipeline("MaterialVertex.vs", "ErrorMaterial.ps", &mErrorMaterialPipeline);

        // Compile pipelines for mmaterials
        for (auto it : mMaterialIndexMap) {
            auto pMaterial = it.first;
            auto ident     = pMaterial->GetIdentString();

            if (ident == PPX_MATERIAL_IDENT_STANDARD) {
                mMaterialPipelineMap[pMaterial] = mStandardMaterialPipeline;
            }
            else if (ident == PPX_MATERIAL_IDENT_UNLIT) {
                mMaterialPipelineMap[pMaterial] = mUnlitMaterialPipeline;
            }
            else {
                mMaterialPipelineMap[pMaterial] = mErrorMaterialPipeline;
            }
        }
    }
}

void GltfSceneViewer::Render()
{
    PerFrame& frame = mPerFrame[0];

    grfx::SwapchainPtr swapchain = GetSwapchain();

    // Wait for and reset render complete fence
    PPX_CHECKED_CALL(frame.renderCompleteFence->WaitAndReset());

    uint32_t imageIndex = UINT32_MAX;
    PPX_CHECKED_CALL(swapchain->AcquireNextImage(UINT64_MAX, frame.imageAcquiredSemaphore, frame.imageAcquiredFence, &imageIndex));

    // Wait for and reset image acquired fence
    PPX_CHECKED_CALL(frame.imageAcquiredFence->WaitAndReset());

    // Update camera params
    mPipelineArgs->SetCameraParams(mArcballCamera.has_value() ? &mArcballCamera.value() : mScene->GetCameraNode(0)->GetCamera());

    // Update instance params
    {
        const uint32_t numMeshNodes = mScene->GetMeshNodeCount();
        for (uint32_t instanceIdx = 0; instanceIdx < numMeshNodes; ++instanceIdx) {
            auto pNode                   = mScene->GetMeshNode(instanceIdx);
            auto pInstanceParmas         = mPipelineArgs->GetInstanceParams(instanceIdx);
            pInstanceParmas->modelMatrix = pNode->GetEvaluatedMatrix();
        }
    }

    // Build command buffer
    PPX_CHECKED_CALL(frame.cmd->Begin());
    {
        // Copy pipeline args buffers
        mPipelineArgs->CopyBuffers(frame.cmd);

        // Set descriptor set from pipeline args
        auto pDescriptorSets = mPipelineArgs->GetDescriptorSet();
        frame.cmd->BindGraphicsDescriptorSets(mPipelineInterface, 1, &pDescriptorSets);

        grfx::RenderPassPtr renderPass = swapchain->GetRenderPass(imageIndex);
        PPX_ASSERT_MSG(!renderPass.IsNull(), "render pass object is null");

        grfx::RenderPassBeginInfo beginInfo = {};
        beginInfo.pRenderPass               = renderPass;
        beginInfo.renderArea                = renderPass->GetRenderArea();
        beginInfo.RTVClearCount             = 1;
        beginInfo.RTVClearValues[0]         = {{0.2f, 0.2f, 0.3f, 1}};

        frame.cmd->TransitionImageLayout(renderPass->GetRenderTargetImage(0), PPX_ALL_SUBRESOURCES, grfx::RESOURCE_STATE_PRESENT, grfx::RESOURCE_STATE_RENDER_TARGET);
        frame.cmd->BeginRenderPass(&beginInfo);
        {
            frame.cmd->SetScissors(GetScissor());
            frame.cmd->SetViewports(GetViewport());
            frame.cmd->BindGraphicsDescriptorSets(mPipelineInterface, 0, nullptr);

            // Set DrawParams::iblIndex and DrawParams::iblLevelCount
            const uint32_t iblIndex      = 0;
            const uint32_t iblLevelCount = mIBLEnvMap->GetMipLevelCount();
            frame.cmd->PushGraphicsConstants(mPipelineInterface, 1, &iblIndex, 2);
            frame.cmd->PushGraphicsConstants(mPipelineInterface, 1, &iblLevelCount, 3);

            // Draw scene
            const uint32_t numMeshNodes = mScene->GetMeshNodeCount();
            for (uint32_t instanceIdx = 0; instanceIdx < numMeshNodes; ++instanceIdx) {
                auto pNode = mScene->GetMeshNode(instanceIdx);
                auto pMesh = pNode->GetMesh();

                // Set DrawParams::instanceIndex
                frame.cmd->PushGraphicsConstants(
                    mPipelineInterface,
                    1,
                    &instanceIdx,
                    scene::MaterialPipelineArgs::INSTANCE_INDEX_CONSTANT_OFFSET);

                // Draw batches
                auto& batches = pMesh->GetBatches();
                for (auto& batch : batches) {
                    const scene::Material* material = batch.GetMaterial();
                    // Set pipeline
                    auto pipeline = mMaterialPipelineMap[material];
                    frame.cmd->BindGraphicsPipeline(pipeline);

                    // Set DrawParams::materialIndex
                    uint32_t materialIndex = mMaterialIndexMap[material];
                    frame.cmd->PushGraphicsConstants(
                        mPipelineInterface,
                        1,
                        &materialIndex,
                        scene::MaterialPipelineArgs::MATERIAL_INDEX_CONSTANT_OFFSET);

                    // Index buffer
                    frame.cmd->BindIndexBuffer(&batch.GetIndexBufferView());

                    // Vertex buffers
                    // TODO look at GetRequiredVertexAttributes instead of IdentString?
                    const std::string& materialIdentifier = material->GetIdentString();
                    if (materialIdentifier == PPX_MATERIAL_IDENT_STANDARD || materialIdentifier == PPX_MATERIAL_IDENT_UNLIT) {
                        std::vector<grfx::VertexBufferView> vertexBufferViews = {
                            batch.GetPositionBufferView(),
                            batch.GetAttributeBufferView()};
                        frame.cmd->BindVertexBuffers(CountU32(vertexBufferViews), DataPtr(vertexBufferViews));
                    } else if (materialIdentifier == PPX_MATERIAL_IDENT_ERROR) {
                        // ErrorMaterial.hlsl returns a solid color; it doesn't need attributes
                        std::vector<grfx::VertexBufferView> vertexBufferViews = {batch.GetPositionBufferView()};
                        frame.cmd->BindVertexBuffers(CountU32(vertexBufferViews), DataPtr(vertexBufferViews));
                    } else {
                        PPX_ASSERT_MSG(false, "Unknown material " << materialIdentifier);
                    }

                    frame.cmd->DrawIndexed(batch.GetIndexCount(), 1, 0, 0, 0);
                }
            }

            // Draw ImGui
            DrawDebugInfo();
            DrawImGui(frame.cmd);
        }
        frame.cmd->EndRenderPass();
        frame.cmd->TransitionImageLayout(renderPass->GetRenderTargetImage(0), PPX_ALL_SUBRESOURCES, grfx::RESOURCE_STATE_RENDER_TARGET, grfx::RESOURCE_STATE_PRESENT);
    }
    PPX_CHECKED_CALL(frame.cmd->End());

    grfx::SubmitInfo submitInfo     = {};
    submitInfo.commandBufferCount   = 1;
    submitInfo.ppCommandBuffers     = &frame.cmd;
    submitInfo.waitSemaphoreCount   = 1;
    submitInfo.ppWaitSemaphores     = &frame.imageAcquiredSemaphore;
    submitInfo.signalSemaphoreCount = 1;
    submitInfo.ppSignalSemaphores   = &frame.renderCompleteSemaphore;
    submitInfo.pFence               = frame.renderCompleteFence;

    PPX_CHECKED_CALL(GetGraphicsQueue()->Submit(&submitInfo));

    PPX_CHECKED_CALL(swapchain->Present(imageIndex, 1, &frame.renderCompleteSemaphore));
}

} // namespace

SETUP_APPLICATION(GltfSceneViewer)