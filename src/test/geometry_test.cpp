#include "gtest/gtest.h"
#include "gmock/gmock.h"

#include "ppx/geometry.h"

namespace ppx {

namespace {

using testing::NotNull;

// TODO more tests? check coverage

TEST(GeometryTest, PlanarU8Uses8BitIndex)
{
    const TriMesh planeMesh = TriMesh::CreatePlane(TRI_MESH_PLANE_POSITIVE_Y, /*size=*/float2(2, 2), /*usegs=*/1, /*vsegs=*/1, TriMeshOptions().Indices());

    Geometry planeGeometry;
    EXPECT_EQ(Geometry::Create(GeometryCreateInfo::PlanarU8(), planeMesh, &planeGeometry), ppx::SUCCESS);

    EXPECT_EQ(planeGeometry.GetIndexType(), grfx::INDEX_TYPE_UINT8);
    EXPECT_EQ(planeGeometry.GetIndexBuffer()->GetSize(), sizeof(uint8_t) * planeMesh.GetCountIndices());
    ASSERT_EQ(planeGeometry.GetIndexCount(), planeMesh.GetCountIndices());
    ASSERT_THAT(planeGeometry.GetIndexBuffer()->GetData(), NotNull());
    for (int i = 0; i < planeGeometry.GetIndexCount(); ++i) {
        SCOPED_TRACE(i);
        EXPECT_EQ(reinterpret_cast<const uint8_t*>(planeGeometry.GetIndexBuffer()->GetData())[i], *planeMesh.GetDataIndicesU32(i));
    }
}

TEST(GeometryTest, PositionPlanarU8Uses8BitIndex)
{
    const TriMesh planeMesh = TriMesh::CreatePlane(TRI_MESH_PLANE_POSITIVE_Y, /*size=*/float2(2, 2), /*usegs=*/1, /*vsegs=*/1, TriMeshOptions().Indices());

    Geometry planeGeometry;
    EXPECT_EQ(Geometry::Create(GeometryCreateInfo::PositionPlanarU8(), planeMesh, &planeGeometry), ppx::SUCCESS);

    EXPECT_EQ(planeGeometry.GetIndexType(), grfx::INDEX_TYPE_UINT8);
    EXPECT_EQ(planeGeometry.GetIndexBuffer()->GetSize(), sizeof(uint8_t) * planeMesh.GetCountIndices());
    ASSERT_EQ(planeGeometry.GetIndexCount(), planeMesh.GetCountIndices());
    ASSERT_THAT(planeGeometry.GetIndexBuffer()->GetData(), NotNull());
    for (int i = 0; i < planeGeometry.GetIndexCount(); ++i) {
        SCOPED_TRACE(i);
        EXPECT_EQ(reinterpret_cast<const uint8_t*>(planeGeometry.GetIndexBuffer()->GetData())[i], *planeMesh.GetDataIndicesU32(i));
    }
}

TEST(GeometryTest, InterleavedU8Uses8Bitindex)
{
    const TriMesh planeMesh = TriMesh::CreatePlane(TRI_MESH_PLANE_POSITIVE_Y, /*size=*/float2(2, 2), /*usegs=*/1, /*vsegs=*/1, TriMeshOptions().Indices());

    Geometry planeGeometry;
    EXPECT_EQ(Geometry::Create(GeometryCreateInfo::InterleavedU8(), planeMesh, &planeGeometry), ppx::SUCCESS);

    EXPECT_EQ(planeGeometry.GetIndexType(), grfx::INDEX_TYPE_UINT8);
    EXPECT_EQ(planeGeometry.GetIndexBuffer()->GetSize(), sizeof(uint8_t) * planeMesh.GetCountIndices());
    ASSERT_EQ(planeGeometry.GetIndexCount(), planeMesh.GetCountIndices());
    ASSERT_THAT(planeGeometry.GetIndexBuffer()->GetData(), NotNull());
    for (int i = 0; i < planeGeometry.GetIndexCount(); ++i) {
        SCOPED_TRACE(i);
        EXPECT_EQ(reinterpret_cast<const uint8_t*>(planeGeometry.GetIndexBuffer()->GetData())[i], *planeMesh.GetDataIndicesU32(i));
    }
}

} // namespace

} // namespace ppx
