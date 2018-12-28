from randovania.game_description.area import Area
from randovania.game_description.dock import DockWeaknessDatabase, DockWeakness
from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import Node, GenericNode, DockNode, PickupNode, TeleporterNode, EventNode
from randovania.game_description.requirements import RequirementSet, RequirementList, IndividualRequirement
from randovania.game_description.resources import ResourceGain
from randovania.game_description.world import World
from randovania.game_description.world_list import WorldList


def write_individual_requirement(individual: IndividualRequirement) -> dict:
    return {
        "requirement_type": individual.resource.resource_type.value,
        "requirement_index": individual.resource.index,
        "amount": individual.amount,
        "negate": individual.negate
    }


def write_requirement_list(requirement_list: RequirementList) -> list:
    return [
        write_individual_requirement(individual)
        for individual in requirement_list.values()
    ]


def write_requirement_set(requirement_set: RequirementSet) -> list:
    return [
        write_requirement_list(l)
        for l in requirement_set.alternatives
    ]


# Dock Weakness Database

def write_dock_weakness(dock_weakness: DockWeakness) -> dict:
    return {
        "index": dock_weakness.index,
        "name": dock_weakness.name,
        "is_blast_door": dock_weakness.is_blast_shield,
        "requirement_set": write_requirement_set(dock_weakness.requirements)
    }


def write_dock_weakness_database(database: DockWeaknessDatabase) -> dict:
    return {
        "door": [
            write_dock_weakness(weakness)
            for weakness in database.door
        ],
        "portal": [
            write_dock_weakness(weakness)
            for weakness in database.portal
        ],
    }


# World/Area/Nodes

def write_node(node: Node) -> dict:
    """
    :param node:
    :return:
    """

    data = {
        "name": node.name,
        "heal": node.heal
    }

    if isinstance(node, GenericNode):
        data["node_type"] = 0

    elif isinstance(node, DockNode):
        data["node_type"] = 1
        data["dock_index"] = node.dock_index
        data["connected_area_asset_id"] = node.default_connection.area_asset_id
        data["connected_dock_index"] = node.default_connection.dock_index
        data["dock_type"] = node.default_dock_weakness.dock_type
        data["dock_weakness_index"] = node.default_dock_weakness.index

    elif isinstance(node, PickupNode):
        data["node_type"] = 2
        data["pickup_index"] = node.pickup_index.index

    elif isinstance(node, TeleporterNode):
        data["node_type"] = 3
        data["teleporter_instance_id"] = node.teleporter_instance_id
        data["destination_world_asset_id"] = node.default_connection.world_asset_id
        data["destination_area_asset_id"] = node.default_connection.area_asset_id

    elif isinstance(node, EventNode):
        data["node_type"] = 4
        data["event_index"] = node.resource().index

    else:
        raise Exception("Unknown node class: {}".format(node))

    return data


def write_area(area: Area) -> dict:
    """
    :param area:
    :return:
    """
    nodes = []

    for node in area.nodes:
        data = write_node(node)
        data["connections"] = {
            target_node.name: write_requirement_set(requirements_set)
            for target_node, requirements_set in area.connections[node].items()
        }
        nodes.append(data)

    return {
        "name": area.name,
        "assert_id": area.area_asset_id,
        "default_node_index": area.default_node_index,
        "nodes": nodes
    }


def write_world(world: World) -> dict:
    return {
        "name": world.name,
        "assert_id": world.world_asset_id,
        "areas": [
            write_area(area)
            for area in world.areas
        ]
    }


def write_world_list(world_list: WorldList) -> list:
    return [
        write_world(world)
        for world in world_list.worlds
    ]


def write_resource_gain_by_long_name(resource_gain: ResourceGain) -> dict:
    return {
        resource.long_name: gain
        for resource, gain in resource_gain
    }


def write_game_description(game: GameDescription) -> dict:
    return {
        "game": game.game,
        "game_name": game.game_name,
        "resource_database": write_resource_database(game.resource_database),
        "starting_world_asset_id": game.starting_world_asset_id,
        "starting_area_asset_id": game.starting_area_asset_id,
        "starting_items": write_resource_gain_by_long_name(game.starting_items),
        "item_loss_items": write_resource_gain_by_long_name(game.item_loss_items),
        "victory_condition": write_requirement_set(game.victory_condition),

        "dock_weakness_database": write_dock_weakness_database(game.dock_weakness_database),
        "worlds": write_world_list(game.world_list),
    }