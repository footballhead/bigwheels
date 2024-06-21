#include "gtest/gtest.h"
#include "gmock/gmock.h"

#include "ppx/geometry.h"

namespace ppx {

namespace {

// TODO: Combination of layout (interleaved, planar, position planar) X format (UNKNOWN, 8, 16, 32)

// TODO: hardcode data to make things more obvious?

TEST(GeometryTest, Uint8PlanarPacking)
{
    const TriMesh planeMesh = TriMesh::CreatePlane(TRI_MESH_PLANE_POSITIVE_Y, /*size=*/float2(2, 2), /*usegs=*/1, /*vsegs=*/1, TriMeshOptions().Indices().VertexColors().Normals());

    Geometry planeGeometry;
    EXPECT_EQ(Geometry::Create(GeometryCreateInfo::PlanarU8().AddColor().AddNormal(), planeMesh, &planeGeometry), ppx::SUCCESS);

    // TODO validate index format packing
    EXPECT_EQ(planeGeometry.GetIndexType(), grfx::INDEX_TYPE_UINT8);
    EXPECT_EQ(planeGeometry.GetIndexBuffer()->GetSize(), sizeof(uint8_t) * planeMesh.GetCountIndices());
    ASSERT_EQ(planeGeometry.GetIndexCount(), planeMesh.GetCountIndices());
    ASSERT_THAT(planeGeometry.GetIndexBuffer()->GetData(), testing::NotNull());
    for (int i = 0; i < planeGeometry.GetIndexCount(); ++i) {
        SCOPED_TRACE(i);
        EXPECT_EQ(reinterpret_cast<const uint8_t*>(planeGeometry.GetIndexBuffer()->GetData())[i], *planeMesh.GetDataIndicesU32(i));
    }

    // TODO validate attribute packing
    ASSERT_EQ(planeGeometry.GetVertexBufferCount(), 3); // position, color, normal
    const Geometry::Buffer* positionBuffer = planeGeometry.GetVertexBuffer(0);
    const Geometry::Buffer* colorBuffer    = planeGeometry.GetVertexBuffer(1);
    const Geometry::Buffer* normalBuffer   = planeGeometry.GetVertexBuffer(2);
    // TODO check elements (note that planeMesh uses float3 whereas buffers are const char*!)
}

} // namespace

} // namespace ppx
