import mbuild as mb
import numpy as np


def get_height(r, theta):
    """
    Helper function to get the height of a spherical cap
    """
    return r - r * np.cos(theta * np.pi / 180)


class GrapheneDroplet(mb.Compound):
    """
    Builds a droplet on a graphene sheet.

    Parameters
    ----------
    radius : int, default = 2
        radius of the droplet in nm
    angle : float, default = 90.0
        contact angle of the droplet in degrees
    x : float
        dimension of graphene sheet in x direction in nm
    y : float
        dimension of graphene sheet in y direction in nm
    fluid : mbuild.Compound or list of mbuild.Compound
        compounds to fill the droplet with
    density: float or list of float
        target density for the droplet in kg/m^3
    NOTE: length of `fluid` must match length of `density`

    Attributes
    ----------
    see mbuild.Compound

    """

    def __init__(self, radius=2, angle=90.0, x=None, y=None, fluid=None, 
                density=None):
                
        super(GrapheneDroplet, self).__init__()

        if x and y:
            if x < radius * 4 or y < radius * 4:
                raise ValueError(
                    'Dimensions of sheet must be at least radius * 4')
        else:
            if not x:
                x = radius * 4
            if not y:
                y = radius * 4

        if fluid is None:
            raise ValueError('Fluid droplet compounds must be specified')
        if density is None:
            raise ValueError('Fluid density must be specified (units kg/m^3)')

        factor = np.cos(np.pi / 6)
        # Estimate the number of lattice repeat units
        replicate = [int(x / 0.2456), int(y / 0.2456) * (1 / factor)]

        carbon = mb.Compound(name='C')
        lattice_spacing = [0.2456, 0.2456, 0.335]
        angles = [90.0, 90.0, 120.0]
        carbon_locations = [[0, 0, 0], [2 / 3, 1 / 3, 0]]
        basis = {carbon.name: carbon_locations}
        graphene_lattice = mb.Lattice(
            lattice_spacing=lattice_spacing,
            angles=angles,
            lattice_points=basis)
        carbon_dict = {carbon.name: carbon}
        graphene = graphene_lattice.populate(
            compound_dict=carbon_dict, x=replicate[0], y=replicate[1], z=3)

        for particle in graphene.particles():
            if particle.xyz[0][0] < 0:
                particle.xyz[0][0] += graphene.periodicity[0]
        graphene.periodicity[1] *= factor

        sheet = mb.clone(graphene)
        self.surface_height = np.max(sheet.xyz, axis=0)[2]
        coords = list(sheet.periodicity)

        height = get_height(radius, angle)
        sphere_coords = [coords[0] / 2, coords[1] / 2, radius, radius]
        sphere = mb.fill_sphere(
            compound=fluid, sphere=sphere_coords, density=density)

        to_remove = []
        for child in sphere.children:
            for atom_coords in child.xyz:
                if height > radius:
                    if atom_coords[2] < height - radius:
                        to_remove += child
                        break
                else:
                    if atom_coords[2] < height:
                        to_remove += child
                        break

        sphere.remove(to_remove)

        sheet.name = 'GPH'
        sphere.name = 'FLD'
        sphere.xyz -= [0, 0, np.min(sphere.xyz, axis=0)[2]]
        sphere.xyz += [0, 0, self.surface_height + 0.3]

        self.add(sheet)
        self.add(sphere)
        self.periodicity[0] = sheet.periodicity[0]
        self.periodicity[1] = sheet.periodicity[1]
        self.periodicity[2] = radius * 5
