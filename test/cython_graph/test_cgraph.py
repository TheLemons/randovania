import collections
import pprint
from random import Random

from randovania.cython_graph.cgraph import optimize_world
from randovania.game_description.requirements import ResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.generator import generator
from randovania.resolver.bootstrap import logic_bootstrap


def is_dmg(resource_req: ResourceRequirement) -> bool:
    return resource_req.resource.resource_type == ResourceType.DAMAGE


def test_database_collectable(preset_manager):
    pool = generator.create_player_pool(Random(15000), preset_manager.default_preset.get_preset().configuration, 0)
    game, state = logic_bootstrap(pool.configuration, pool.game, pool.patches)

    graph = optimize_world(game.world_list, state.patches, game.dangerous_resources)

    pprint.pprint(graph)

    assert False
