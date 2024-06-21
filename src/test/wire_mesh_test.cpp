#include "gtest/gtest.h"
#include "gmock/gmock.h"

#include "ppx/wire_mesh.h"

namespace ppx {

namespace {

using ::testing::IsNull;
using ::testing::NotNull;

TEST(WireMeshTest, ConstructAndVerifyBasicQuadWithUint8Indices)
{
    WireMesh plane(grfx::INDEX_TYPE_UINT8);
    EXPECT_EQ(plane.GetIndexType(), grfx::INDEX_TYPE_UINT8);

    EXPECT_EQ(plane.AppendPosition(float3{0, 0, 0}), 1);
    EXPECT_EQ(plane.AppendPosition(float3{1, 1, 0}), 2);
    EXPECT_EQ(plane.AppendPosition(float3{1, 0, 0}), 3);
    EXPECT_EQ(plane.AppendPosition(float3{0, 1, 0}), 4);
    EXPECT_EQ(plane.AppendTriangle(0, 1, 2), 1);
    EXPECT_EQ(plane.AppendTriangle(0, 3, 1), 2);

    ASSERT_THAT(plane.GetDataIndicesU8(), NotNull());
    EXPECT_THAT(plane.GetDataIndicesU16(), IsNull());
    EXPECT_THAT(plane.GetDataIndicesU32(), IsNull());

    EXPECT_EQ(plane.GetCountTriangles(), 2);
    EXPECT_EQ(plane.GetCountIndices(), 6);
    EXPECT_EQ(plane.GetCountPositions(), 4);

    uint32_t          triangle0Index0 = 0;
    uint32_t          triangle0Index1 = 0;
    uint32_t          triangle0Index2 = 0;
    TriMeshVertexData triangle0Data{};
    ASSERT_EQ(plane.GetTriangle(0, triangle0Index0, triangle0Index2, triangle0Index2), ppx::SUCCESS);
    EXPECT_EQ(triangle0Index0, 0);
    ASSERT_EQ(plane.GetVertexData(triangle0Index0, &triangle0Data), ppx::SUCCESS);
    EXPECT_EQ(triangle0Data.position, float3(0, 0, 0));
    EXPECT_EQ(triangle0Index1, 1);
    ASSERT_EQ(plane.GetVertexData(triangle0Index1, &triangle0Data), ppx::SUCCESS);
    EXPECT_EQ(triangle0Data.position, float3(1, 1, 0));
    EXPECT_EQ(triangle0Index2, 2);
    ASSERT_EQ(plane.GetVertexData(triangle0Index2, &triangle0Data), ppx::SUCCESS);
    EXPECT_EQ(triangle0Data.position, float3(1, 0, 0));

    uint32_t          triangle1Index0 = 0;
    uint32_t          triangle1Index1 = 0;
    uint32_t          triangle1Index2 = 0;
    TriMeshVertexData triangle1Data{};
    ASSERT_EQ(plane.GetTriangle(1, triangle1Index0, triangle1Index1, triangle1Index2), ppx::SUCCESS);
    EXPECT_EQ(triangle1Index0, 0);
    ASSERT_EQ(plane.GetVertexData(triangle1Index0, &triangle1Data), ppx::SUCCESS);
    EXPECT_EQ(triangle1Data.position, float3(0, 0, 0));
    EXPECT_EQ(triangle1Index1, 3);
    ASSERT_EQ(plane.GetVertexData(triangle1Index1, &triangle1Data), ppx::SUCCESS);
    EXPECT_EQ(triangle1Data.position, float3(0, 1, 0));
    EXPECT_EQ(triangle1Index2, 1);
    ASSERT_EQ(plane.GetVertexData(triangle1Index2, &triangle1Data), ppx::SUCCESS);
    EXPECT_EQ(triangle1Data.position, float3(1, 1, 0));

    uint32_t v0 = 0;
    uint32_t v1 = 0;
    uint32_t v2 = 0;
    TriMeshVertexData data{};
    EXPECT_EQ(plane.GetTriangle(2, v0, v1, v2), ppx::ERROR_OUT_OF_RANGE);
    EXPECT_EQ(plane.GetVertexData(4, &data), ppx::ERROR_OUT_OF_RANGE);
}

} // namespace

} // namespace ppx
