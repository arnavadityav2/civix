import sys
import os
sys.path.insert(0, os.path.abspath('civix_generator'))

from world.loader import load_canonical_world

world = load_canonical_world(r'C:\Users\ARNAV ADITYA\.gemini\antigravity-ide\brain\4d2a421e-8d1d-4a48-8703-7eae27170647\synthetic_world.md')
print(f"Persons: {len(world.persons)}")
print(f"Networks: {len(world.networks)}")
print(f"Organizations: {len(world.organizations)}")
print(f"Phones: {len(world.phones)}")
print(f"Vehicles: {len(world.vehicles)}")
print(f"Accounts: {len(world.accounts)}")
print(f"Properties: {len(world.properties)}")
print(f"Devices: {len(world.devices)}")
