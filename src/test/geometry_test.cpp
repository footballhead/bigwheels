// Copyright 2022 Google LLC
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

#include "gtest/gtest.h"
#include "gmock/gmock.h"

#include "ppx/geometry.h"

namespace ppx {
namespace {

using ::testing::NotNull;

TEST(GeometryTest, PlanarU16Uses16BitIndex)
{
    const TriMesh planeMesh = TriMesh::CreatePlane(TRI_MESH_PLANE_POSITIVE_Y, /*size=*/float2(2, 2), /*usegs=*/1, /*vsegs=*/1, TriMeshOptions().Indices());

    Geometry planeGeometry;
    EXPECT_EQ(Geometry::Create(GeometryCreateInfo::PlanarU16(), planeMesh, &planeGeometry), ppx::SUCCESS);

    EXPECT_EQ(planeGeometry.GetIndexType(), grfx::INDEX_TYPE_UINT16);
    EXPECT_EQ(planeGeometry.GetIndexBuffer()->GetSize(), sizeof(uint16_t) * planeMesh.GetCountIndices());
    ASSERT_EQ(planeGeometry.GetIndexCount(), planeMesh.GetCountIndices());
    ASSERT_THAT(planeGeometry.GetIndexBuffer()->GetData(), NotNull());
    for (int i = 0; i < planeGeometry.GetIndexCount(); ++i) {
        SCOPED_TRACE(i);
        EXPECT_EQ(reinterpret_cast<const uint16_t*>(planeGeometry.GetIndexBuffer()->GetData())[i], *planeMesh.GetDataIndicesU32(i));
    }
}

} // namespace
} // namespace ppx
