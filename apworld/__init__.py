from BaseClasses import Region, Location, Item, ItemClassification, Tutorial, CollectionState
from worlds.AutoWorld import World, WebWorld
from worlds.LauncherComponents import (
    Component,
    components,
    Type as component_type,
    )
from typing import Any, Callable
from collections import defaultdict

json_world = {
    "region_map": {
        "Menu": {
            "main": None
        },
        "main": {
            "upper": [["claw"]],
            "side": [["fly", "claw"]],
            "lower": [["key"]]
        },
        "side": {
            "lower": [["fly"]]
        }
    },
    "location_map": {
        "main": {
            "mayor delivery": [["mayor missive"]],  # gives key, needs lower claw letter in main
            "mayor chat": None,
            "friend delivery": [["friend freight"]],  # gives nothing, needs upper claw letter in main
            "friend chat": None,
            "climber delivery": [["climber cargo"]],  # gives claw, needs free letter in main
            "climber chat": None,
            "climber cargo": None,  # all the way to the right
            "friend freight": [["claw"], ["fly"]],  # claw OR fly  #in town, above
            "mayor missive": [["claw"]],  # top path from ladder to under
            "buried bento": [["drill", "claw"]],  # middle path from ladder to under
        },

        "side": {
            "grandpa goods": [["fly"]],
        },

        "lower": {
            "wife word": [["fly", "claw"]],  # in cave after door
            "paper pack": None,  # down stairs by door, between bottom and side
            "driller delivery": [["driller dispatch"]],  # gives drill, needs letter in upper
            "driller chat": None,
            "paper folder delivery": [["paper pack"]],  # gives fly, needs free letter between bottom/side
            "paper folder chat": None,
            "mouse delivery": [["buried bento", "fly"]],  # gives nothing, needs drill letter by ladder to under
            "mouse chat": [["fly"]],
            "history haul": [["fly", "claw"]],  # left side before old man
            "grandpa delivery": [["grandpa goods", "fly", "claw", "drill"]],
            "grandpa chat": [["fly", "claw", "drill"]],
            "history buff delivery": [["history haul"]],  # left side of under-town, needs letter by old man
            "history buff chat": None,
            "wife delivery": [["wife word"]],  # gives nothing, middle of under-town, needs letter after keydoor
            "wife chat": None,
        },

        "upper": {
            "driller dispatch": None,
            "victory": [["drill", "fly"]],
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
    "filler_name": "Feeling of Satisfaction",
    "item_name_groups": {
        "Packages": [
            "mayor missive",
            "friend freight",
            "climber cargo",
            "driller dispatch",
            "paper pack",
            "buried bento",
            "grandpa goods",
            "history haul",
            "wife word",
            ],
        "Tools": [
            "claw",
            "fly",
            "key",
            "drill",
            ]
    }
}


def open_page(url):
    import webbrowser
    webbrowser.open(f"https://qwint.github.io/air_delivery/?Protocol={url}&auto=True")


components.append(Component(
    "Air Delivery AutoLaunch",
    func=open_page,
    component_type=component_type.HIDDEN,
    supports_uri=True,
    game_name=json_world["game_name"]
    ))


class TemplateItem(Item):
    game = json_world["game_name"]


class TemplateLocation(Location):
    game = json_world["game_name"]


class DeliveryWeb(WebWorld):
    setup_en = Tutorial(
        "setup",
        "A guide for setting up Air Delivery for AP",
        "en",
        "docs/setup_en.md",
        "setup/en",
        ["qwint"]
    )
    tutorials = [setup_en]


# flatten lists of locations and items so they are indexed for name_to_id
location_list = [location for locations in json_world["location_map"].values() for location in locations.keys()]
item_list = [item for item_lists in json_world["items"].values() for item in item_lists]

# for my particular get_item_classification
classification_lookup = defaultdict(lambda: ItemClassification.useful, {
    **{n: ItemClassification.progression for n in json_world["items"]["prog_items"]},
    **{n: ItemClassification.filler for n in json_world["items"]["filler_items"]}
})


class DeliveryWorld(World):
    """
    You’re a sky-island delivery worker delivering mail to all the nearby islands. Everything runs smoothly until the
    letters suddenly aren’t being delivered. Find all of the letters and deliver them to their recipients.
    Maybe they’ll give you something as a thank you.
    """
    game = json_world["game_name"]
    web = DeliveryWeb()
    location_name_to_id = {name: json_world["base_id"]+location_list.index(name) for name in location_list}
    item_name_to_id = {name: json_world["base_id"]+item_list.index(name) for name in item_list}
    item_name_groups = {name: set(items) for name, items in json_world["item_name_groups"].items()}

# basic getters for json_world data, any option based modifications can be done here; may cache these later
# expect authors to modify the return of super() per options, or fully override if their format is different
    def get_region_list(self) -> list[str]:
        """
        Parser method to return the list of all regions to be created.
        Currently flattens region_map to create all regions with a connection in or out
        """
        ret = {
            r for connections in json_world["region_map"].values()
            for r in connections.keys()
        }.union(json_world["region_map"].keys())
        return ret

    def get_connections(self) -> list[tuple[str, str, Any | None]]:
        """
        Parser method to convert the region definitions in the json_world object
        into a list of connection entries formatted as (parent_region_name, target_region_name, rule)
        """
        return [
            (region1, region2, rule)
            for region1, connections in json_world["region_map"].items()
            for region2, rule in connections.items()
        ]

    def get_location_map(self) -> list[tuple[str, str, Any | None]]:
        """
        Parser method to convert the location definitions in the json_world object
        into a list of location entries formatted as (parent_region_name, location_name, rule)
        """
        return [
            (region, location, rule)
            for region, placements in json_world["location_map"].items()
            for location, rule in placements.items()
        ]

# black box methods
    def set_victory(self) -> None:
        """
        current black box to set and setup victory condition,
        run after all region/locations have been created (but currently before items)
        """
        victory = self.get_location("victory")
        victory.address = None
        victory.place_locked_item(TemplateItem("victory", ItemClassification.progression, None, self.player))
        self.multiworld.completion_condition[self.player] = lambda state: state.has("victory", self.player)
        # currently finds victory location, adds locked victory event, and requires victory event for completion

    def create_rule(self, rule: Any) -> Callable[[CollectionState], bool]:
        """
        current black box to convert json_world rule format to an access_rule lambda
        Falsy rules will be ignored and left default
        """
        if len(rule) > 1:
            rules = [lambda state: state.has_all(sub, self.player) for sub in rule]
            return lambda state: any(r(state) for r in rules)
        # optimize for the more common one route rules
        return lambda state: state.has_all(rule[0], self.player)
        # currently all my rule objects are None or a list of potential routes with each having a list of required items

    def get_item_list(self) -> list[str]:
        """
        current black box to create a list of item names per count that need to be created
        """
        return item_list
        # currently my items in my datapackage should all be created once, so this list functions

    def get_item_classification(self, name: str) -> ItemClassification:
        """
        current black box to convert item names to their respective ItemClassification
        """
        return classification_lookup[name]

    def get_filler_item_name(self) -> str:
        # filler_name should be a list and this should choose with self.random
        return json_world["filler_name"]

# common World methods
    def create_regions(self) -> None:
        # create a local map of get_region_list names to region object
        # for referencing in create_regions and adding those regions to the multiworld
        regions = {region: None for region in self.get_region_list()}
        for region in regions.keys():
            regions[region] = Region(region, self.player, self.multiworld)
            self.multiworld.regions.append(regions[region])

        # loop through get_region_map, adding the rules per self.create_rule(rule) if present to the connections
        for region1, region2, rule in self.get_connections():
            if rule:
                regions[region1].connect(regions[region2], rule=self.create_rule(rule))
            else:
                regions[region1].connect(regions[region2])

        # loop through get_location_map, adding the rules per self.create_rule(rule) if present to the location
        for region, location, rule in self.get_location_map():
            loc = TemplateLocation(self.player, location, self.location_name_to_id[location], regions[region])
            if rule:
                loc.access_rule = self.create_rule(rule)
            regions[region].locations.append(loc)

        self.set_victory()

    def create_items(self) -> None:
        # create all items in get_item_list()
        itempool = [self.create_item(item) for item in self.get_item_list()]

        # fill in any difference in itempool with filler item and submit to multiworld
        total_locations = len(self.multiworld.get_unfilled_locations(self.player))
        missing_items = total_locations - len(itempool)
        if missing_items > 0:
            itempool += [self.create_filler() for _ in range(missing_items)]
        self.multiworld.itempool += itempool

    def create_item(self, name: str) -> "Item":
        item_class = self.get_item_classification(name)
        return TemplateItem(name, item_class, self.item_name_to_id.get(name, None), self.player)
