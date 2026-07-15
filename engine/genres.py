"""
Every genre reskins the *same* underlying simulation (engine/events.py)
with different names, resources, and flavor text. Add a new genre by
adding a new Genre entry to GENRES below -- no engine code required.
"""
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Genre:
    id: str
    name: str
    tagline: str
    vehicle: str                 # "wagon", "starship", "rig", "caravan", "ship"
    hostile_name: str            # what the human-ish antagonists are called
    wildlife_name: str           # what the beast/monster antagonists are called
    currency: str
    special_resource: str        # ammo / fuel cells / scrap / mana crystals / cannonballs
    food_name: str
    origin: str
    destination_patterns: List[str]
    landmark_patterns: List[str]
    noun_bank: List[str]
    role_bank: List[str]
    intro_flavor: str            # seed line for the AI (or fallback) opening blurb
    flavor: Dict[str, List[str]] = field(default_factory=dict)
    special_landmark_events: List[dict] = field(default_factory=list)
    secret_flag: str = "secret"
    secret_trigger_text: str = ""
    endings: Dict[str, dict] = field(default_factory=dict)


GENRES: Dict[str, Genre] = {}


def _register(g: Genre):
    GENRES[g.id] = g


# ---------------------------------------------------------------- WESTERN --
_register(Genre(
    id="western",
    name="Overland Trail",
    tagline="Guide a wagon party across the frontier before winter closes the passes.",
    vehicle="wagon",
    hostile_name="outlaws",
    wildlife_name="wolves",
    currency="dollars",
    special_resource="ammunition",
    food_name="provisions",
    origin="Independence, Missouri",
    destination_patterns=["the {n} Valley", "{n} City", "Fort {n}"],
    landmark_patterns=["Fort {n}", "{n} Crossing", "{n} Bluffs", "{n} Springs"],
    noun_bank=["Rustwater", "Amber", "Redrock", "Lonepine", "Dustford", "Cross Timber",
               "Silverfork", "Thistledown", "Copperline", "Willamette", "Chimney Rock", "Graystone"],
    role_bank=["Farmer", "Blacksmith", "Schoolteacher", "Hunter", "Preacher", "Carpenter",
               "Seamstress", "Drover", "Fiddler", "Doctor"],
    intro_flavor="A wagon party sets out from Independence, Missouri, chasing free land and a fresh start before the mountain passes close for winter.",
    flavor={
        "injury": ["{name} slips crossing a rocky ford and wrenches a leg.",
                   "{name} is thrown from the wagon box when a wheel hits a rut."],
        "illness": ["{name} comes down with a fever after a night in the rain.",
                    "{name} grows weak with a stomach sickness from bad well water."],
        "hostile": ["A band of {hostile} shadows the wagon from a ridge line.",
                    "{hostile} raid a nearby camp overnight and the wagon party is on edge."],
        "wildlife": ["A pack of {wildlife} circles the camp after dark.",
                     "{wildlife} spook the draft animals during the night watch."],
        "breakdown": ["An axle cracks on washboard ruts in the trail.",
                      "A wagon wheel splits crossing a dry creek bed."],
        "crossing": ["The trail meets a swollen river with no bridge in sight.",
                     "A steep, rocky canyon blocks the easy path forward."],
        "find": ["The party stumbles on an abandoned trapper's cache.",
                 "A friendly rancher trades supplies for news from back east."],
        "trade": ["A trading post appears on the horizon, shelves half-stocked but welcoming."],
        "morale_good": ["A fiddle tune around the campfire lifts everyone's spirits.",
                        "Clear skies and easy trail put the party in good humor."],
        "morale_bad": ["Endless grey rain grinds down the party's patience.",
                       "A grim rumor about the trail ahead spreads through camp."],
        "theft": ["Someone slips into camp overnight and makes off with supplies.",
                 "A poor trade deal in the last town costs the party dearly."],
        "rare": ["Deep in a canyon, the party finds traces of an older, forgotten trail."],
        "rest": ["The party makes camp beside a clear stream, animals grazing calm."],
    },
    special_landmark_events=[
        {"name": "Abandoned Homestead", "prompt": "A homestead sits empty, doors swinging. Search it?",
         "good": "You find canned goods and a cache of coins left behind.",
         "bad": "The floor gives way and someone is hurt in the fall."},
        {"name": "Trail Fork", "prompt": "The trail splits: a longer safe route, or a rough shortcut through the hills.",
         "good": "The shortcut saves days and the wagon holds together fine.",
         "bad": "The shortcut chews up the wagon on loose scree."},
    ],
    secret_flag="found_old_trail",
    secret_trigger_text="the party quietly followed the forgotten old trail the rest of the way",
    endings={
        "triumphant": {"title": "A New Start", "fallback":
            "The wagon rolls into {destination} with the party intact, tired but whole, ready to build a new life."},
        "success": {"title": "Made It", "fallback":
            "The party reaches {destination}, battered by the trail but standing, grateful just to have arrived."},
        "bittersweet": {"title": "The Cost of the Trail", "fallback":
            "{destination} comes into view, but the party that arrives is smaller than the one that set out."},
        "tragic": {"title": "Lost on the Trail", "fallback":
            "The trail claims what's left of the party long before {destination} is ever in sight."},
        "secret": {"title": "The Old Trail", "fallback":
            "Following a trail no map remembered, the party slips into {destination} by a road nobody else knows."},
    },
))

# ------------------------------------------------------------------ SPACE --
_register(Genre(
    id="space",
    name="Deep Space Convoy",
    tagline="Ferry a colony convoy across the dark between the stars before the reactor gives out.",
    vehicle="convoy ship",
    hostile_name="raider ships",
    wildlife_name="void fauna",
    currency="credits",
    special_resource="fuel cells",
    food_name="ration packs",
    origin="Earth Departure Station",
    destination_patterns=["{n} Colony", "New {n}", "{n} Station"],
    landmark_patterns=["{n} Station", "the {n} Nebula", "{n} Relay", "{n} Outpost"],
    noun_bank=["Vega", "Kepler", "Helion", "Orion's Reach", "Meridian", "Halcyon",
               "Tethys", "Aurora Rim", "Cygnus", "Perseid", "Ionis", "Callisto Gate"],
    role_bank=["Engineer", "Pilot", "Medic", "Xenobiologist", "Cook", "Navigator",
               "Systems Tech", "Botanist", "Comms Officer", "Cryo Specialist"],
    intro_flavor="A convoy ship departs Earth Departure Station carrying colonists toward a distant world, with only so much fuel to spend along the way.",
    flavor={
        "injury": ["{name} is thrown against a bulkhead during a hard course correction.",
                   "{name} suffers a decompression scare sealing a hull micro-fracture."],
        "illness": ["{name} develops radiation sickness after a solar flare.",
                    "{name} struggles with zero-g sickness that won't ease up."],
        "hostile": ["{hostile} power up weapons on long-range scan.",
                    "A distress call turns out to be bait set by {hostile}."],
        "wildlife": ["{wildlife} drift alongside the hull, oddly luminous.",
                     "A swarm of {wildlife} clogs an external sensor array."],
        "breakdown": ["A coolant line ruptures in the engine bay.",
                      "The navigation computer glitches and needs a full reboot."],
        "crossing": ["A dense asteroid field blocks the direct course.",
                     "An unstable wormhole reading offers a risky shortcut."],
        "find": ["The convoy salvages an intact supply pod adrift in space.",
                 "A passing trade vessel offers to barter before moving on."],
        "trade": ["A drifting trade station hails the convoy, cargo bay open for business."],
        "morale_good": ["A clear view of a new nebula has the whole crew at the viewports.",
                        "A successful repair job puts everyone in good spirits."],
        "morale_bad": ["Days of static and silence on comms wear on the crew.",
                       "A false alarm in the middle of ship's night rattles everyone."],
        "theft": ["A stowaway is caught siphoning fuel cells before slipping away.",
                 "A shady station trader shortchanges the convoy on a deal."],
        "rare": ["A faint signal leads the crew to an intact pre-collapse research vessel."],
        "rest": ["The convoy parks in a quiet stretch of space to run full diagnostics."],
    },
    special_landmark_events=[
        {"name": "Derelict Station", "prompt": "A long-dead station drifts nearby, systems dark. Board it?",
         "good": "The station yields intact fuel cells and a working star chart.",
         "bad": "A decompression trap injures the boarding party."},
        {"name": "Twin Routes", "prompt": "Two courses: a long stable lane, or a fast lane through a debris field.",
         "good": "The debris field is thinner than scans suggested; the shortcut pays off.",
         "bad": "Debris impacts chew into the hull along the shortcut."},
    ],
    secret_flag="found_derelict",
    secret_trigger_text="the crew quietly recovered a pre-collapse star chart that shaved weeks off the route",
    endings={
        "triumphant": {"title": "New Horizon", "fallback":
            "The convoy ship settles into orbit around {destination}, every colonist aboard alive to see the new sky."},
        "success": {"title": "Landfall", "fallback":
            "{destination} appears on the viewport at last, the convoy weary but whole enough to call it a landing."},
        "bittersweet": {"title": "Half a Convoy", "fallback":
            "The ship reaches {destination}, but the manifest reads shorter than it did at departure."},
        "tragic": {"title": "Lost in the Dark", "fallback":
            "The convoy goes dark somewhere short of {destination}, one more signal that never resumes."},
        "secret": {"title": "The Old Chart", "fallback":
            "Following coordinates no living navigator wrote, the convoy slips into {destination} weeks ahead of schedule."},
    },
))

# -------------------------------------------------------------- WASTELAND --
_register(Genre(
    id="wasteland",
    name="The Long Convoy",
    tagline="Drive a rig of survivors across the ruined world toward rumor of somewhere green.",
    vehicle="rig",
    hostile_name="raiders",
    wildlife_name="mutant beasts",
    currency="scrip",
    special_resource="scrap",
    food_name="rations",
    origin="the Ruined City",
    destination_patterns=["the {n} Settlement", "{n} Valley", "the {n} Enclave"],
    landmark_patterns=["{n} Outpost", "the {n} Ruins", "{n} Checkpoint", "{n} Yard"],
    noun_bank=["Ashfall", "Rustbelt", "Cinderline", "Bonewash", "Scrapyard", "Greywater",
               "Hollow Vault", "Dustline", "Ironbrand", "Emberfield", "Saltflat", "Green Hollow"],
    role_bank=["Scavenger", "Medic", "Mechanic", "Lookout", "Cook", "Tracker",
               "Demolitionist", "Radio Op", "Gunsmith", "Forager"],
    intro_flavor="A battered rig rolls out of the Ruined City, its passengers chasing a rumor of an untouched green valley somewhere past the wastes.",
    flavor={
        "injury": ["{name} is cut scavenging through twisted rebar and glass.",
                   "{name} takes a bad fall crossing a collapsed overpass."],
        "illness": ["{name} shows signs of radiation sickness after crossing a hot zone.",
                    "{name} drinks bad water and pays for it for days."],
        "hostile": ["{hostile} block the road ahead, demanding a toll.",
                    "{hostile} strip a supply cache the convoy was counting on."],
        "wildlife": ["{wildlife} stalk the rig's tracks after nightfall.",
                     "A den of {wildlife} forces a wide, costly detour."],
        "breakdown": ["The rig's engine sputters and dies on a dust-choked stretch.",
                      "A tire blows out on broken asphalt miles from any settlement."],
        "crossing": ["A collapsed bridge forces a choice between two rough detours.",
                     "A radioactive stretch of highway glows faintly on the meter."],
        "find": ["The convoy finds a sealed pre-war supply cache, mostly intact.",
                 "A wary settlement trades supplies for news of the road."],
        "trade": ["A fortified trading post flies a flag of truce, gates open for business."],
        "morale_good": ["A clean water source and a quiet night lift everyone's mood.",
                        "Word of a safe settlement ahead spreads hope through the rig."],
        "morale_bad": ["Another empty settlement, picked clean, sinks morale hard.",
                       "The constant Geiger clicks fray everyone's nerves."],
        "theft": ["Scavengers strip unguarded supplies while the rig is stopped.",
                 "A crooked trader shorts the convoy on a deal."],
        "rare": ["Beneath the rubble, the party finds an untouched pre-war bunker."],
        "rest": ["The rig pulls into a walled lot to patch tires and catch some sleep."],
    },
    special_landmark_events=[
        {"name": "Sealed Bunker", "prompt": "A rusted blast door sits half-open. Go in?",
         "good": "The bunker holds intact supplies and clean water, untouched for decades.",
         "bad": "A collapsed corridor injures whoever goes in first."},
        {"name": "Two Roads", "prompt": "One road is longer but clear; the other cuts through a hot zone.",
         "good": "The hot zone reading was stale; the shortcut costs nothing.",
         "bad": "The rig lingers too long in the hot zone and pays for it."},
    ],
    secret_flag="found_bunker",
    secret_trigger_text="the convoy quietly restocked from an untouched pre-war bunker nobody else had found",
    endings={
        "triumphant": {"title": "Green Ground", "fallback":
            "The rig rolls into {destination} intact, and for the first time in months, the air doesn't taste like ash."},
        "success": {"title": "Still Standing", "fallback":
            "{destination}'s gates open for the rig, road-worn but alive, and that alone counts as a win out here."},
        "bittersweet": {"title": "What's Left", "fallback":
            "{destination} takes in what's left of the convoy, fewer than set out, all of them changed by the road."},
        "tragic": {"title": "Swallowed by the Waste", "fallback":
            "The wasteland takes the rig long before {destination}, and the road forgets it was ever there."},
        "secret": {"title": "The Bunker's Gift", "fallback":
            "Riding on bunker supplies nobody else knew existed, the convoy reaches {destination} well ahead of the odds."},
    },
))

# ----------------------------------------------------------------- FANTASY --
_register(Genre(
    id="fantasy",
    name="The Kingsroad Caravan",
    tagline="Lead a caravan across a fading kingdom toward the last free city before the roads close.",
    vehicle="caravan",
    hostile_name="marauders",
    wildlife_name="wolves and worse",
    currency="gold",
    special_resource="charms",
    food_name="provisions",
    origin="the Old Capital",
    destination_patterns=["the City of {n}", "{n} Hold", "the {n} Sanctuary"],
    landmark_patterns=["{n} Keep", "the {n} Woods", "{n} Shrine", "{n} Crossing"],
    noun_bank=["Ravenspire", "Hollowmere", "Thornwood", "Moonhollow", "Silverreach", "Ashgate",
               "Wolfden", "Greywatch", "Larkspur", "Ironvale", "Duskmere", "Brightfen"],
    role_bank=["Knight", "Healer", "Ranger", "Bard", "Merchant", "Scribe",
               "Cartographer", "Squire", "Herbalist", "Guardsman"],
    intro_flavor="A caravan leaves the Old Capital as the kingdom's roads grow unsafe, bound for whatever free city will still take in strangers.",
    flavor={
        "injury": ["{name} is thrown from a spooked horse on a narrow switchback.",
                   "{name} is hurt clearing fallen timber blocking the road."],
        "illness": ["{name} is struck with a shivering fever nobody can name.",
                    "{name} weakens after drinking from a cursed-looking well."],
        "hostile": ["{hostile} demand a toll at a narrow pass.",
                    "{hostile} raid a nearby hamlet the caravan just left."],
        "wildlife": ["{wildlife} howl close to camp through the night.",
                     "{wildlife} spook the horses badly on the road."],
        "breakdown": ["A cart wheel splinters on root-choked road.",
                      "A cart axle snaps fording a rocky stream."],
        "crossing": ["An old stone bridge looks ready to give way underfoot.",
                     "A dark wood offers a shortcut nobody wants to take."],
        "find": ["The caravan finds a merchant's abandoned stall, goods still good.",
                 "A wandering trader shares supplies for a warm meal and news."],
        "trade": ["A roadside market town welcomes the caravan with open stalls."],
        "morale_good": ["A bard's song around the fire lifts the whole camp's mood.",
                        "Word that the road ahead is clear puts everyone at ease."],
        "morale_bad": ["Talk of the dark wood spreads unease through camp.",
                       "A run of grey, rainy days wears the caravan down."],
        "theft": ["A quick-fingered stranger slips off with supplies at a market stop.",
                 "A crooked merchant shorts the caravan on a trade."],
        "rare": ["Deep in the old wood, the caravan finds a shrine untouched by time."],
        "rest": ["The caravan makes camp in a quiet glade, watch fires burning low."],
    },
    special_landmark_events=[
        {"name": "Forgotten Shrine", "prompt": "A moss-covered shrine sits just off the road. Pay respects and search it?",
         "good": "The shrine yields an old blessing and a few coins left as offerings.",
         "bad": "Loose stone gives way and someone is hurt in the fall."},
        {"name": "Two Roads", "prompt": "The kingsroad forks: the long safe way, or the old wood shortcut.",
         "good": "The old wood is quiet tonight, and the shortcut saves real time.",
         "bad": "Something in the old wood costs the caravan dearly."},
    ],
    secret_flag="found_shrine",
    secret_trigger_text="the caravan carried a shrine's quiet blessing the rest of the way",
    endings={
        "triumphant": {"title": "Sanctuary", "fallback":
            "The caravan passes through the gates of {destination} whole, every traveler still standing at road's end."},
        "success": {"title": "Within the Walls", "fallback":
            "{destination}'s gates open for the caravan, worn thin by the road but glad to be inside."},
        "bittersweet": {"title": "A Smaller Company", "fallback":
            "{destination} takes in a caravan far smaller than the one that left the Old Capital."},
        "tragic": {"title": "Lost to the Kingsroad", "fallback":
            "The kingsroad claims the caravan long before the walls of {destination} ever come into view."},
        "secret": {"title": "The Shrine's Blessing", "fallback":
            "Carrying a blessing few caravans ever find, this one reaches {destination} untroubled by the road's worst."},
    },
))

# --------------------------------------------------------------- HIGH SEAS --
_register(Genre(
    id="highseas",
    name="Voyage of the Restless",
    tagline="Sail a crew across open ocean toward a distant port before supplies or nerve run out.",
    vehicle="ship",
    hostile_name="hunter ships",
    wildlife_name="sea creatures",
    currency="doubloons",
    special_resource="cannonballs",
    food_name="provisions",
    origin="Port Callow",
    destination_patterns=["the Isle of {n}", "{n} Harbor", "Port {n}"],
    landmark_patterns=["{n} Reef", "{n} Cove", "{n} Shoals", "{n} Atoll"],
    noun_bank=["Coral Deep", "Stormwake", "Kraken's Rest", "Saltmere", "Gullcry", "Driftwood",
               "Amber Tide", "Windward", "Blackwater", "Farshore", "Mistral", "Halcyon Reef"],
    role_bank=["Navigator", "Quartermaster", "Surgeon", "Gunner", "Cook", "Rigger",
               "Lookout", "Carpenter", "Bosun", "Cabin Hand"],
    intro_flavor="A ship slips out of Port Callow, crew and cargo bound for a distant harbor across open, unpredictable water.",
    flavor={
        "injury": ["{name} is hurt in a fall from the rigging during rough weather.",
                   "{name} is injured hauling lines in a sudden squall."],
        "illness": ["{name} shows the early signs of scurvy after weeks at sea.",
                    "{name} runs a fever after days soaked through in storms."],
        "hostile": ["{hostile} are sighted on the horizon, closing fast.",
                    "{hostile} demand the ship heave to and surrender its cargo."],
        "wildlife": ["{wildlife} shadow the ship's wake for days.",
                     "A pod of {wildlife} nearly capsizes a boarding skiff."],
        "breakdown": ["A mast cracks in heavy weather.",
                      "The hull springs a slow leak below the waterline."],
        "crossing": ["A reef-choked passage offers a risky shortcut.",
                     "A wall of storm clouds blocks the direct course."],
        "find": ["The crew spots a drifting crate, still sealed and dry.",
                 "A friendly merchant vessel trades supplies before parting ways."],
        "trade": ["A busy harbor town welcomes the ship's crew to its docks and markets."],
        "morale_good": ["Calm seas and a following wind put the whole crew at ease.",
                        "A good catch of fresh fish makes for a rare good meal."],
        "morale_bad": ["Weeks of grey water and no landfall wear the crew thin.",
                       "A superstitious omen spooks the crew badly."],
        "theft": ["A dockside thief makes off with supplies during a port stop.",
                 "A crooked harbor trader shorts the crew on a deal."],
        "rare": ["Far off the charts, the crew finds an uncharted island cove."],
        "rest": ["The ship drops anchor in a calm cove to patch sails and rest."],
    },
    special_landmark_events=[
        {"name": "Wreck Site", "prompt": "A wrecked hull is visible just beneath the waves. Dive for salvage?",
         "good": "The wreck yields a chest of doubloons and dry stores.",
         "bad": "A diver is hurt on sharp, submerged wreckage."},
        {"name": "Two Passages", "prompt": "One route swings wide and safe; the other threads a reef-choked shortcut.",
         "good": "The reef passage is calmer than charted, and the shortcut pays off.",
         "bad": "The reef tears at the hull along the shortcut."},
    ],
    secret_flag="found_island",
    secret_trigger_text="the crew quietly restocked at an uncharted island no map showed",
    endings={
        "triumphant": {"title": "Fair Winds Home", "fallback":
            "The ship glides into {destination} with the whole crew on deck, weathered but whole after the crossing."},
        "success": {"title": "Landfall at Last", "fallback":
            "{destination}'s harbor comes into view, and the crew that sails in is tired but glad to be alive."},
        "bittersweet": {"title": "A Lighter Crew", "fallback":
            "{destination} welcomes a ship that sailed out with more hands than it now carries."},
        "tragic": {"title": "Lost at Sea", "fallback":
            "The ship never raises the coast of {destination}, swallowed somewhere in open water."},
        "secret": {"title": "The Uncharted Cove", "fallback":
            "Restocked from a cove no chart ever showed, the ship makes {destination} well ahead of any reasonable odds."},
    },
))


def list_genres():
    return list(GENRES.values())


def get_genre(genre_id: str) -> Genre:
    return GENRES[genre_id]
