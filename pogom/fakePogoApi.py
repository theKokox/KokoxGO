from random import randint, getrandbits, seed
from uuid import uuid4
from time import time
from s2sphere import CellId, LatLng
import struct
import geopy
from geopy.distance import VincentyDistance
from geopy.distance import vincenty
from .utils import get_args


class FakePogoApi:


    def __init__(self, provider=None, oauth2_refresh_token=None, username=None, password=None, position_lat=None, position_lng=None, position_alt=None, proxy_config=None):
        self._auth_provider = type('',(object,),{"_ticket_expire": (time() + (3600 * 24)) * 1000})()
        self.seed = str(getrandbits(128))
        self.forts = []


    def set_proxy(self, proxy_config):
        pass


    def activate_signature(self, library):
        pass


    def set_position(self, lat, lng, alt):
        # On first call, mark map center location -- we need this to generate a nice huge list of gyms/poke stops
        # So that we can show ones "in range" (<900m away) for each scan circle
        if len(self.forts) == 0:
            args = get_args()
            # meters radius (very, very rough approximation -- deal with it)
            radius = 70 * args.step_limit

            self.forts = []

            # Gyms
            for i in range(args.step_limit * 1):
                coords = self.getRandomPoint(location=(lat, lng), maxMeters=radius)
                self.forts.append({
                    'enabled': True,
                    'guard_pokemon_id': randint(1,140),
                    'gym_points': randint(1,30000),
                    'id': 'gym-{}-{}'.format(self.seed,i),
                    'is_in_battle': not getrandbits(1),
                    'last_modified_timestamp_ms': int((time() - 10) * 1000),
                    'latitude': coords[0],
                    'longitude': coords[1],
                    'owned_by_team': randint(0,3)
                })

            # Pokestops
            for i in range(args.step_limit * 2):
                coords = self.getRandomPoint(location=(lat, lng), maxMeters=radius)
                self.forts.append({
                    'enabled': True,
                    'id': 'gym-{}-{}'.format(self.seed,i),
                    'last_modified_timestamp_ms': int((time() - 10) * 1000),
                    'latitude': coords[0],
                    'longitude': coords[1],
                    'type': 1
                })



    def set_authentication(self, provider=None, oauth2_refresh_token=None, username=None, password=None):
        pass


    def i2f(self, i):
      return struct.unpack('<d', struct.pack('<Q', i))[0]


    def get_map_objects(self, latitude=None, longitude=None, since_timestamp_ms=None, cell_id=None):

        location = (self.i2f(latitude), self.i2f(longitude))
        cells = []
        # for i in range(randint(60,70)):
        for i in range(3):
            cells.append({
                'current_timestamp_ms': int(time() * 1000),
                'forts': self.makeForts(location),
                's2_cell_id': uuid4(), # wrong, but also unused so it doesn't matter
                'wild_pokemons': self.makeWildPokemon(location),
                'catchable_pokemons': [], # unused
                'nearby_pokemons': [] # unused
            })
        return { 'responses': { 'GET_MAP_OBJECTS': { 'map_cells': cells } } }


    def makeWildPokemon(self, location):
        # Cause the randomness to only shift every 5 minutes (thus new pokes every 5 minutes)
        offset = int(time() % 3600) / 10
        seedid = self.seed + str(location[0]) + str(location[1]) + str(offset)
        seed(seedid)
        pokes = []
        for i in range(randint(0,2)):
            coords = self.getRandomPoint(location)
            ll = LatLng.from_degrees(coords[0], coords[1])
            cellId = CellId.from_lat_lng(ll).parent(20).to_token()
            pokes.append({
                'encounter_id': 'pkm'+seedid+str(i),
                'last_modified_timestamp_ms': int((time() - 10) * 1000),
                'latitude': coords[0],
                'longitude': coords[1],
                'pokemon_data': { 'pokemon_id': randint(1,140) },
                'spawn_point_id': cellId,
                'time_till_hidden_ms': randint(60,600) * 1000
            })
        return pokes


    def makeForts(self, location):
        forts = []

        for i in self.forts:
            f = (i['latitude'], i['longitude'])
            d = vincenty(location, f).meters
            if d < 900:
                forts.append(i)

        return forts


    def getRandomPoint(self, location=None, maxMeters=70):
        origin = geopy.Point(location[0], location[1])
        d = float(randint(1,maxMeters)) / 1000
        b = randint(0,360)
        destination = VincentyDistance(kilometers=d).destination(origin, b)
        return (destination.latitude, destination.longitude)
