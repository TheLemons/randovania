from unittest.mock import MagicMock, PropertyMock

import pytest

from randovania.game_description.area import Area
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import EventNode, GenericNode, TeleporterNode
from randovania.game_description.requirements import RequirementSet, RequirementList, IndividualRequirement
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world import World
from randovania.game_description.world_list import WorldList
from randovania.resolver import bootstrap
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach
from randovania.resolver.state import State


def test_possible_actions_empty():
    state = MagicMock()

    reach = ResolverReach({}, {}, frozenset(), MagicMock())
    options = list(reach.possible_actions(state))

    assert options == []


def test_possible_actions_no_resources():
    state = MagicMock()
    node_a = MagicMock()
    node_b = MagicMock()
    node_b.can_collect.return_value = False

    type(node_a).is_resource_node = prop_a = PropertyMock(return_value=False)
    type(node_b).is_resource_node = prop_b = PropertyMock(return_value=True)

    # Run
    reach = ResolverReach({node_a: 1, node_b: 1}, {}, frozenset(), MagicMock())
    options = list(action for action, damage in reach.possible_actions(state))

    # Assert
    assert options == []
    prop_a.assert_called_once_with()
    prop_b.assert_called_once_with()
    node_b.can_collect.assert_called_once_with(state.patches, state.resources, reach._logic.game.world_list.all_nodes)


def test_possible_actions_with_event():
    logic = MagicMock()
    state = MagicMock()

    event = MagicMock(spec=EventNode)
    type(event).is_resource_node = prop = PropertyMock(return_value=True)
    event.can_collect.return_value = True

    # Run
    reach = ResolverReach({event: 1}, {}, frozenset(), logic)
    options = list(action for action, damage in reach.possible_actions(state))

    # Assert
    assert options == [event]
    prop.assert_called_once_with()
    event.can_collect.assert_called_once_with(state.patches, state.resources, reach._logic.game.world_list.all_nodes)
    logic.get_additional_requirements.assert_called_once_with(event)
    logic.get_additional_requirements.return_value.satisfied.assert_called_once_with(state.resources, 1)


@pytest.fixture(name="visit_restriction_logic")
def _visit_restriction_logic(default_layout_configuration, echoes_game_description):
    node_1 = GenericNode("Start", False, 0)
    node_y = GenericNode("Y", False, 1)
    node_z = GenericNode("Z", False, 2)
    node_x_to_y = TeleporterNode("ToY", False, 3, 10, AreaLocation(2000, 6000), False, False, False)
    node_x_to_z = TeleporterNode("ToZ", False, 4, 11, AreaLocation(2000, 7000), False, False, True)

    area_x = Area("X", False, 5000, 0, [node_1, node_x_to_y, node_x_to_z], {
        node_1: {
            node_x_to_y: RequirementSet([RequirementList(0, [
                IndividualRequirement(PickupIndex(0), 1, False),
            ])]),
            node_x_to_z: RequirementSet.trivial(),
        },
        node_x_to_y: {},
        node_x_to_z: {},

    })
    area_y = Area("Y", False, 6000, 0, [node_y], {node_y: {}})
    area_z = Area("Z", False, 7000, 0, [node_z], {node_z: {}})

    worlds = [
        World("A", "A", 1000, [area_x]),
        World("B", "B", 2000, [area_y, area_z]),
    ]

    game = GameDescription(
        game=echoes_game_description.game,
        game_name=echoes_game_description.game_name,
        dock_weakness_database=echoes_game_description.dock_weakness_database,

        resource_database=echoes_game_description.resource_database,
        victory_condition=RequirementSet.impossible(),
        starting_location=AreaLocation(1000, 5000),
        initial_states={"Default": ()},
        world_list=WorldList(worlds),
    )
    return Logic(
        game=game,
        configuration=default_layout_configuration,
    )


@pytest.mark.parametrize("is_reachable", [False, True])
def test_teleporter_with_visit_restriction_success(visit_restriction_logic, is_reachable):
    # Setup
    initial_state = bootstrap.calculate_starting_state(visit_restriction_logic.game,
                                                       GamePatches.with_game(visit_restriction_logic.game))
    initial_state.resources[PickupIndex(0)] = 1 if is_reachable else 0
    target_area = visit_restriction_logic.game.world_list.area_by_area_location(AreaLocation(2000, 7000))
    target_node = target_area.nodes[0]

    # Run
    reach = ResolverReach.calculate_reach(visit_restriction_logic, initial_state)

    # Assert
    if is_reachable:
        assert target_node in reach.nodes
    else:
        assert target_node not in reach.nodes
