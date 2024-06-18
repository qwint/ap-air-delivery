from BaseClasses import Region, Location, Item, ItemClassification, Tutorial, CollectionState
from worlds.AutoWorld import World, WebWorld
#expand this eventually
from typing import *

json_world = {
    "regions": ["Menu", "main", "upper", "side", "lower"],
    "region_map": {
        "Menu": {
            "main": None
        },
        "main": {
            "upper": ["claw"],
            "side": ["fly", "claw"],
            "lower": ["key"]
        },
        "side": {
            "lower": ["fly"]
        }
    },
    "location_map": {
        "main": {
            "mayor delivery": ["mayor missive"], #gives key, needs lower claw letter in main
            "mayor chat": None,
            "friend delivery": ["friend freight"], #gives nothing, needs upper claw letter in main
            "friend chat": None,
            "climber delivery": ["climber cargo"], #gives claw, needs free letter in main
            "climber chat": None,
            "climber cargo": None, #all the way to the right
            "friend freight": ["claw"], # OR fly  #in town, above
            "mayor missive": ["claw"], #top path from ladder to under
            "buried bento": ["drill", "claw"], #middle path from ladder to under
        },

        "side": {
            "grandpa goods": ["fly"],
        },

        "lower": {
            "wife word": ["fly", "claw"], #in cave after door
            "paper pack": None, #down stairs by door, between bottom and side
            "driller delivery": ["driller dispatch"], #gives drill, needs letter in upper
            "driller chat": None,
            "paper folder delivery": ["paper pack"], #gives fly, needs free letter between bottom/side
            "paper folder chat": None,
            "mouse delivery": ["buried bento", "fly"], #gives nothing, needs drill letter by ladder to under
            "mouse chat": ["fly"],
            "history haul": ["fly", "claw"], #left side before old man
            "grandpa delivery": ["grandpa goods", "fly", "claw", "drill"],
            "grandpa chat": ["fly", "claw", "drill"],
            "history buff delivery": ["history haul"], #left side of under-town, needs letter by old man
            "history buff chat": None,
            "wife delivery": ["wife word"], #gives nothing, middle of under-town, needs letter after keydoor
            "wife chat": None,
        },

        "upper": {
            "driller dispatch": None,
            "victory": ["drill", "fly"],
        }
    },
    "items": {
        "prog_items": [
            "mayor missive",
            "friend freight",
            "climber cargo",
            "driller dispatch",
            "paper pack",
            "buried bento",
            "grandpa goods",
            "history haul",
            "wife word",
            "claw",
            "fly",
            "key",
            "drill",
        ],
        "filler_items": [
            "Feeling of Satisfaction"
        ]
    },
    "base_id": 19827412012,
    "game_name": "Air Delivery",
    "filler_name": "Feeling of Satisfaction"
}


class TemplateItem(Item):
    game = json_world["game_name"]


class TemplateLocation(Location):
    game = json_world["game_name"]


class HelloWeb(WebWorld):
    setup_en = Tutorial(
        "setup",
        "description here",
        "en",
        "setup_en.md",
        "setup/en",
        ["your name here"]
    )
    tutorials = [setup_en]


#flatten lists of locations and items so they are indexed for name_to_id
location_list = [location for locations in json_world["location_map"].values() for location in locations.keys()]
item_list = [item for item_lists in json_world["items"].values() for item in item_lists]

class HelloWorld(World):
    game = json_world["game_name"]
    web = HelloWeb()
    location_name_to_id = {name: json_world["base_id"]+location_list.index(name) for name in location_list}
    item_name_to_id = {name: json_world["base_id"]+item_list.index(name) for name in item_list}

#basic getters for json_world data, any option based modifications can be done here; may cache these later
#expect authors to modify the return of super() per options, or fully override if their format is different
    def get_region_list(self) -> List[str]:
        return json_world["regions"]

    def get_connections(self) -> "List[Tuple(str, str, Optional[Any])]":
        er = False
        if er:
            vanilla_connections = [(region1, region2, rule) for region1, connections in json_world["region_map"].items() for region2, rule in connections.items()]
            oneways = ["Menu -> main"]
            return_connections = vanilla_connections + [(region2, region1, rule) for connection in vanilla_connections for region1, region2, rule in connection if f"{region1} -> {region2}" not in oneways]
            # then create unconnected Entrances later
        else:
            return [(region1, region2, rule) for region1, connections in json_world["region_map"].items() for region2, rule in connections.items()]

    def get_location_map(self) -> "List[Tuple(str, str, Optional[Any])]":
        return [(region, location, rule) for region, placements in json_world["location_map"].items() for location, rule in placements.items()]

# black box methods
    def set_victory(self) -> None:
        #current black box to set and setup victory condition, run after all region/locations have been created (but currently before items)
        victory = self.multiworld.get_location("victory", self.player)
        victory.address = None
        victory.place_locked_item(TemplateItem("victory", ItemClassification.progression, None, self.player))
        self.multiworld.completion_condition[self.player] = lambda state: state.has("victory", self.player)
        #currently finds victory location, adds locked victory event, and requires victory event for completion

    def create_rule(self, rule: Any) -> Callable[[CollectionState], bool]:
        #current black box to convert json_world rule format to an access_rule lambda
        return lambda state: state.has_all(rule, self.player)
        #currently all my rule objects are None or a list of required items

    def get_item_list(self) -> List[str]:
        #current black box to creat a list of item names per count that need to be created
        return item_list
        #currently my items in my datapackage should all be created once, so this list functions

    def get_item_classification(self, name: str) -> ItemClassification:
        if name in json_world["items"]["prog_items"]:
            return ItemClassification.progression
        elif name in json_world["items"]["filler_items"]:
            return ItemClassification.filler
        else:
            return ItemClassification.useful

    def get_filler_item_name(self) -> str:
        #filler_name should be a list and this should choose with self.random
        return json_world["filler_name"]

# common methods
    def create_regions(self) -> None:
        #create a local map of get_region_list names to region object for referencing in create_regions and adding those regions to the multiworld
        regions = {region: None for region in self.get_region_list()}
        for region in regions.keys():
            regions[region] = Region(region, self.player, self.multiworld)
            self.multiworld.regions.append(regions[region])

        #TODO - add per option GER handling
        #loop through get_region_map, adding the rules per self.create_rule(rule) if present to the connections
        for region1, region2, rule in self.get_connections():
            if rule:
                regions[region1].connect(regions[region2], rule=self.create_rule(rule))
            else:
                regions[region1].connect(regions[region2])
        er = False
        if er:
            for region, connection, rule in self.get_er_entrances():
                cons = [regions[region].create_exit(connection), regions[region].create_en_target(connection)]
                for con in cons:
                    con.er_type = EntranceType.TWO_WAY
                    # con.er_group = 
                    con.access_rule = self.create_rule(rule)


        #loop through get_location_map, adding the rules per self.create_rule(rule) if present to the location
        for region, location, rule in self.get_location_map():
            loc = TemplateLocation(self.player, location, self.location_name_to_id[location], regions[region])
            if rule:
                loc.access_rule = self.create_rule(rule)
            regions[region].locations.append(loc)

        self.set_victory()

    def create_items(self) -> None:
        #create all items in get_item_list()
        itempool = []
        for item in self.get_item_list():
            itempool.append(self.create_item(item))

        #fill in any difference in itempool with filler item and submit to multiworld
        total_locations = len(self.multiworld.get_unfilled_locations(self.player))
        while len(itempool) < total_locations:
            itempool.append(self.create_filler())
        self.multiworld.itempool += itempool

    def create_item(self, name: str) -> "Item":
        item_class = self.get_item_classification(name)
        return TemplateItem(name, item_class, self.item_name_to_id.get(name, None), self.player)
