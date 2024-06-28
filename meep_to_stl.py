import numpy as np
from stl import mesh
import math
import meep as mp
from meep.geom import Vector3
from mpl_toolkits import mplot3d
from matplotlib import pyplot
import trimesh


def show_stl_plot(given_stl_path):
    figure = pyplot.figure()
    axes = figure.add_subplot(111, projection='3d')
    your_mesh = mesh.Mesh.from_file(given_stl_path)
    axes.add_collection3d(mplot3d.art3d.Poly3DCollection(your_mesh.vectors))
    scale = your_mesh.points.flatten()
    axes.auto_scale_xyz(scale, scale, scale)
    pyplot.show()


def translate_geo(geo, new_shape):
    if geo.center != Vector3(0, 0, 0):
        center_coords = [geo.center.x, geo.center.y, geo.center.z]
        transform = trimesh.transformations.translation_matrix(center_coords)
        new_shape.apply_transform(transform)
    return new_shape


def find_max_value(geo, max_list):

    if isinstance(geo, mp.Block):
        z_val = abs(geo.center.z + geo.size.z / 2)
        x_val = abs(geo.center.x + geo.size.x / 2)
        y_val = abs(geo.center.y + geo.size.y / 2)
    elif isinstance(geo, mp.Cylinder):
        z_val = abs(geo.center.z) + geo.height / 2
        x_val = geo.center.x + geo.radius
        y_val = geo.center.y + geo.radius
    elif isinstance(geo, mp.Sphere):
        z_val = geo.center.z + geo.radius
        x_val = geo.center.x + geo.radius
        y_val = geo.center.y + geo.radius
    else:
        x_val,z_val,y_val = 0,0,0

    test_list = [x_val, y_val, z_val]
    for i in range(3):
        if max_list[i] < abs(test_list[i]):
            max_list[i] = abs(test_list[i])
    return max_list


def cell_size_check(cell_size, values):
    max_val = cell_size.x
    for val in cell_size:
        if val > max_val:
            max_val = val

    for i in range(len(values)):
        if values[i] > max_val:
            values[i] = max_val

    return values


def make_meep_stl_file(sim, dest_path, create_base=False):
    mesh_list = []
    remove_list = []

    cell_size = sim.cell_size
    remove = False

    for geo in sim.geometry:
        if create_base:
            max_list = find_max_value(geo,[0,0,0])
        if isinstance(geo, mp.Block):

            center_coord_list = [geo.center.x, geo.center.y, geo.center.z]
            center_coord_list = cell_size_check(cell_size, center_coord_list)

            transform = trimesh.transformations.translation_matrix(center_coord_list)

            extent = [min(geo.size.x,cell_size.x),
                    min(geo.size.y,cell_size.y),
                    min(geo.size.z,cell_size.z)]

            new_shape = trimesh.creation.box(extents=extent, transform=transform)
        elif isinstance(geo, mp.Cylinder):
            dimensions = [geo.height, geo.radius]
            dimensions = cell_size_check(cell_size, dimensions)
            new_shape = trimesh.creation.cylinder(radius=dimensions[1], height=dimensions[0])
            new_shape = translate_geo(geo, new_shape)
        elif isinstance(geo, mp.Sphere):
            radius = cell_size_check(cell_size, [geo.radius])
            new_shape = trimesh.creation.icosphere(radius=geo.radius)
            new_shape = translate_geo(geo, new_shape)
        elif isinstance(geo, mp.Prism):
            print("Currently not working with Prisms")

        elif isinstance(geo, mp.Cone):
            print("Currently not working with Cones")
        else:
            print("Shape has not been added to the file yet")

        if geo.material is not mp.air:
            mesh_list.append(new_shape)
            print("appened", new_shape)
        else:
            remove_list.append(new_shape)
            remove = True

    combined_mesh = mesh_list[0]
    for one_mesh in mesh_list[1:]:
        combined_mesh = combined_mesh.union(one_mesh)

    if remove:
        remove_mesh = remove_list[0]
        for mesh in remove_list[1:]:
            remove_mesh = remove_mesh.union(mesh)
        combined_mesh = combined_mesh.difference(remove_mesh)
    if create_base:
        extents = [cell_size.x, cell_size.y, cell_size.z/ 6]
        center_list = [0, 0, -1 * max_list[2]]
        transform = trimesh.transformations.translation_matrix(center_list)
        base_mesh = (trimesh.creation.box(extents=extents, transform=transform))
        combined_mesh = combined_mesh.union(base_mesh)


    combined_mesh.export(dest_path)


if __name__ == "__main__":
    dest_path = 'simulation_test/subtract_test.stl'
    blocks = [
        mp.Block(center=mp.Vector3(0, 0, 0), size=mp.Vector3(1,1,1), material=mp.Medium()),
        mp.Cylinder(center=mp.Vector3(.5,.5,-1), radius=0.5, height=3, material=mp.air),
        mp.Cylinder(center=mp.Vector3(-.5,-.5,-1), radius=0.5, height=3, material=mp.air)
        ]
    geometry = blocks
    sim = mp.Simulation(geometry=geometry, cell_size=mp.Vector3(10,10,10))
    make_meep_stl_file(sim, dest_path, False)
    show_stl_plot(dest_path)
