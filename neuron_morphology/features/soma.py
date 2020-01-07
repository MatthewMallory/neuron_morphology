import math
import numpy as np

from functools import partial
from typing import Optional, List, Dict
from neuron_morphology.feature_extractor.marked_feature import (
    MarkedFeature, marked
)
from neuron_morphology.feature_extractor.mark import (
    RequiresRoot,
    RequiresSoma,
    RequiresRelativeSomaDepth, 
    RequiresApical,
    RequiresBasal,
    RequiresAxon,
    RequiresDendrite,
    Geometric
)
from neuron_morphology.feature_extractor.data import Data
from neuron_morphology.constants import (
    SOMA, AXON, BASAL_DENDRITE, APICAL_DENDRITE
)
from neuron_morphology.morphology import Morphology


__all__ = [
    "calculate_soma_surface",
    "calculate_relative_soma_depth",
    "calculate_soma_features",
    "calculate_stem_exit_and_distance"
]


@marked(Geometric)
@marked(RequiresRoot)
def calculate_soma_surface(data: Data) -> float:

    """
        Approximates the surface area of the soma. Morphologies with only
        a single soma node are supported.

        Parameters
        ----------
        morphology: Morphology object

        Returns
        -------

        Scalar value

    """

    soma = data.morphology.get_root()
    return 4.0 * math.pi * soma['radius'] * soma['radius']


@marked(RequiresRoot)
@marked(RequiresRelativeSomaDepth)
def calculate_relative_soma_depth(data: Data) -> float:
    """
        Calculate the soma depth relative to pia/wm
        
        Parameters
        ----------
        data

        Returns
        -------

        Scalar value

    """
    
    return data.relative_soma_depth


@marked(Geometric)
@marked(RequiresRoot)
@marked(RequiresRelativeSomaDepth)
def calculate_soma_features(data: Data):
    """
        Calculate the soma features

        Parameters
        ----------
        morphology: Morphology object
        data

        Returns
        -------

        soma_features

    """
    
    features = {}
    features["soma_surface"] = calculate_soma_surface(data.morphology)
    features["relative_soma_depth"] = calculate_relative_soma_depth(data)

    return features


@marked(Geometric)
@marked(RequiresSoma)
@marked(RequiresRoot)
def calculate_stem_exit_and_distance(data: Data, node_types: Optional[List[int]]):
    
    """
        Returns the relative radial position (stem_exit) on the soma where the
        tree holding the axon connects to the soma. 0 is on the bottom,
        1 on the top, and 0.5 out a side.
        Also returns the distance (stem_distance) between the axon root and the 
        soma surface (0 if axon connects to soma, >0 if axon branches from dendrite).

        Parameters
        ----------

        morphology: Morphology object

        soma: dict
        soma node

        node_types: list (AXON, BASAL_DENDRITE, APICAL_DENDRITE)
        Type to restrict search to

        Returns
        -------

        (float, float):
        First value is relative position (height, on [0,1]) of axon
        tree on soma. Second value is distance of axon root from soma

    """

    # find axon node, get its tree ID, fetch that tree, and see where
    #   it connects to the soma radially
    nodes = data.morphology.get_node_by_types(node_types)
    tree_root = None
    stem_distance = 0

    soma = data.morphology.get_root()

    for node in nodes:
        prev_node = node
        # trace back to soma, to get stem root
        while data.morphology.parent_of(node)['type'] != SOMA:
            node = data.morphology.parent_of(node)
            if node['type'] == AXON:
                # this shouldn't happen, but if there's more axon toward
                #   soma, start counting from there
                prev_node = node
                stem_distance = 0
            stem_distance += data.morphology.euclidean_distance(prev_node, node)
            prev_node = node
        tree_root = node
        break

    # make point soma-radius north of soma root
    # do acos(dot product) to get angle of tree root from vertical
    # adjust so 0 is theta=pi and 1 is theta=0
    vert = np.zeros(3)
    vert[1] = 1.0
    root = np.zeros(3)
    root[0] = tree_root['x'] - soma['x']
    root[1] = tree_root['y'] - soma['y']

    # multiply in z scale factor

    root[2] = (tree_root['z'] - soma['z']) * 3.0
    stem_exit = np.arccos(np.clip(np.dot(vert/np.linalg.norm(vert), root/np.linalg.norm(root)), -1.0, 1.0)) / math.pi
    return stem_exit, stem_distance
