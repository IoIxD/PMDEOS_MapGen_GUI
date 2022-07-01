# Local code
from dungeon_eos.RandomGen import *
from dungeon_eos.DungeonAlgorithm import *
import gi # PyGTK

from PIL import Image 

import tempfile
from pathlib import Path

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf

#  DEFAULT PARAMETERS

RandomGenerator.gen_type = 0
RandomGenerator.count = 1
RandomGenerator.seed_old_t0 = 0x8AF812DD
RandomGenerator.seed_t0 = 0x50DA5D9E
RandomGenerator.use_seed_t1 = 4
RandomGenerator.seeds_t1 = [0x74AD7AAA, 0x00F891D9, 0x00F891D9, 0x00F891D9, 0x5100FC60]
Properties.layout = 10
Properties.mh_chance = 0
Properties.kecleon_chance = 0
Properties.middle_room_secondary = 0
Properties.nb_rooms = 5
Properties.bit_flags = 0x1
Properties.floor_connectivity = 14
Properties.maze_chance = 0
Properties.dead_end = 1
Properties.extra_hallways = 0
Properties.secondary_density = 250
Properties.enemy_density = 2
Properties.item_density = 2
Properties.buried_item_density = 2
Properties.trap_density = 3
StaticParam.PATCH_APPLIED = 0
StaticParam.FIX_DEAD_END_ERROR = 0
StaticParam.FIX_OUTER_ROOM_ERROR = 0
StaticParam.SHOW_ERROR = 0

NB_TRIES = 1

class MainWindow(Gtk.Window):
    # The initial window
    def __init__(self):
        super().__init__(title="PMDEOS_MapGen_Python")
        self.last_image = None

        # The maze image on the left
        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.generated_image = Gtk.Image()
        self.hbox.pack_start(self.generated_image,True,True,0)

        self.populate_image("pmdeos_mapgen_og_image.png")

        # The options on the right
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.hbox.pack_end(self.vbox,False,False,0)

        # checkbox for randomizing seeds
        self.randomize_seeds_checkbox = Gtk.CheckButton(label="Randomize Seeds?")
        self.randomize_seeds_checkbox.set_active(True)
        self.randomize_seeds_checkbox.connect("toggled",self.toggle_seed_vbox)
        self.vbox_pack_default(self.randomize_seeds_checkbox)

        # vbox for the seed options, which change based on the above checkbox
        self.seeds_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Seed Type
        self.gen_type_dropdown = Gtk.ComboBoxText()
        self.gen_type_dropdown.append_text("Seed Type 0")
        self.gen_type_dropdown.append_text("Seed Type 1")
        self.gen_type = self.new_option("Seed Type",self.gen_type_dropdown)

        self.seeds_vbox.pack_start(self.gen_type,False,False,0)

        # Seed for type 0
        self.type0_seed_entry = Gtk.Entry()
        self.type0_seed = self.new_option("Seed",self.type0_seed_entry)   

        self.seeds_vbox.pack_start(self.type0_seed_entry,False,False,0)

        # Seed for type 1
        self.type1_seeds = []
        self.type1_seeds_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.type1_seed_add = Gtk.Button(label="+")
        self.type1_seed_add.connect("clicked", self.modify_seed_box, "add")
        self.type1_seed_del = Gtk.Button(label="-")
        self.type1_seed_del.connect("clicked", self.modify_seed_box, "del")
        self.type1_seeds_vbox_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.type1_seeds_vbox_hbox.pack_end(self.type1_seed_add,False,False,3)
        self.type1_seeds_vbox_hbox.pack_end(self.type1_seed_del,False,False,3)

        self.type1_seeds_vbox.pack_end(self.type1_seeds_vbox_hbox,False,False,5)

        self.seeds_vbox.pack_end(self.type1_seeds_vbox,False,False,0)

        # we have to add these and remove them later so that gtk makes room for them and
        # actually lets us toggle their visibility
        self.vbox.pack_start(self.seeds_vbox,False,False,0)

        # dropdown for map type
        self.layout_dropdown = Gtk.ComboBoxText()
        self.layout_dropdown.append_text("Normal Floor")
        self.layout_dropdown.append_text("One Monster House")
        self.layout_dropdown.append_text("Ring")
        self.layout_dropdown.append_text("Crossroads")
        self.layout_dropdown.append_text("Two Monster Houses")
        self.layout_dropdown.append_text("Line")
        self.layout_dropdown.append_text("Cross")
        self.layout_dropdown.append_text("Beetle")
        self.layout_dropdown.append_text("Outer Room Floor")
        layout = self.new_option("Layout Type",self.layout_dropdown)
        self.vbox_pack_default(layout)

        # the rest are self explanatory
        self.monsterhouse_entry = Gtk.Entry()
        monsterhouse = self.new_option("Monster House Chance",self.monsterhouse_entry)
        self.vbox_pack_default(monsterhouse)

        self.kecleonchance_entry = Gtk.Entry()
        kecleonchance = self.new_option("Keckleon House",self.kecleonchance_entry)
        self.vbox_pack_default(monsterhouse)

        self.mazechance_entry = Gtk.Entry()
        mazechance = self.new_option("Maze House",self.mazechance_entry)
        self.vbox_pack_default(mazechance)

        self.room_num_entry = Gtk.Entry()
        room_num = self.new_option("Number of Rooms",self.room_num_entry)
        self.vbox_pack_default(room_num)

        self.extra_hallways_checkbox = Gtk.CheckButton(label="Extra Hallways?")
        self.vbox_pack_default(self.extra_hallways_checkbox)

        self.trap_density_entry = Gtk.Entry()
        trap_density = self.new_option("Trap Density",self.trap_density_entry)
        self.vbox_pack_default(trap_density)

        self.enemy_density_entry = Gtk.Entry()
        enemy_density = self.new_option("Enemy Density",self.enemy_density_entry)
        self.vbox_pack_default(enemy_density)

        self.item_density_entry = Gtk.Entry()
        item_density = self.new_option("Item Density",self.item_density_entry)
        self.vbox_pack_default(item_density)

        self.buried_item_density_entry = Gtk.Entry()
        buried_item_density = self.new_option("Buried Item Density",self.buried_item_density_entry)
        self.vbox_pack_default(buried_item_density)

        # Some options are advanced/unknown and might be useless to the
        # average user, so we hide them by default.
        self.advanced_or_unknown_options = Gtk.CheckButton(label="Show advances or unknown options")
        self.advanced_or_unknown_options.connect("toggled",self.toggle_advanced_vbox)
        self.vbox_pack_default(self.advanced_or_unknown_options)

        self.advanced_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.floor_connectivity_entry = Gtk.Entry()
        floor_connectivity = self.new_option("Floor Connectivity",self.floor_connectivity_entry)
        self.advanced_vbox.pack_start(floor_connectivity,False,False,2)

        self.dead_end_checkbox = Gtk.CheckButton(label="Dead End")
        self.advanced_vbox.add(self.dead_end_checkbox)
 
        self.secondary_density_entry = Gtk.Entry()
        secondary_density = self.new_option("Secondary Density",self.secondary_density_entry)
        self.advanced_vbox.add(secondary_density)

        self.count_entry = Gtk.Entry()
        count = self.new_option("'Count'",self.count_entry)
        self.advanced_vbox.pack_end(count,False,False,2)

        # we have to add it and remove it later, presumably so gtk can make room for it in the window
        self.vbox_pack_default(self.advanced_vbox)

        self.submit_button = Gtk.Button(label="Generate")
        self.submit_button.connect("clicked", self.populate_image)
        self.vbox_pack_default(self.submit_button)

        self.add(self.hbox)

    # Pack an object with the default options
    def vbox_pack_default(self, gobject):
        self.vbox.pack_start(gobject,False,False,2)

    # Create an hbox with a label and object
    def new_option(self, text, gobject):
        new_option_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        new_option_text = Gtk.Label(label=text)
        new_option_hbox.pack_start(new_option_text,False,False,2)
        new_option_hbox.pack_end(gobject,True,True,2)
        return new_option_hbox

    # Toggle the visibility of the seed options
    def toggle_seed_vbox(self, checkbox):
        objects = []
        objects.append(self.gen_type)
        if(RandomGenerator.gen_type == 1):
            # the check is actually in reverse! because um because um u h uhh uhh uhm uhhh 
            objects.append(self.type0_seed)
        else:
            objects.append(self.type1_seeds_vbox)
            objects.append(self.type1_seeds_vbox_hbox)

        if checkbox.get_active():
            for obj in objects:
                self.seeds_vbox.remove(obj)
        else:
            for obj in objects:
                self.seeds_vbox.pack_start(obj,False,False,0)

    def toggle_advanced_vbox(self, checkbox):
        if self.advanced_or_unknown_options.get_active() is True:
            self.vbox.pack_end(self.advanced_vbox,False,False,0)
        else:
            self.vbox.remove(self.advanced_vbox)

    # Add or remove labels to the seed box
    def modify_seed_box():
        print("")
        #todo

    # Generate the image and add it to the side.
    def populate_image(self, button=None, filename="pmdeos_mapgen_image.png"):
        rooms = generate_maze()
        self.last_image = Image.frombytes(data=bytes(rooms), size=(56, 32), mode="P")
        self.last_image.putpalette(
            [
                255, 0, 0,      # red
                0, 192, 0,      # dark green
                0, 0, 255,      # blue
                0, 0, 0,        # black
                192, 0, 0,      # dark red
                192, 0, 192,    # magenta
                0, 128, 128,    # dark cyan
                0, 255, 255,    # cyan
                255, 255, 0,    # orange
                255, 255, 255,  # white
                255, 128, 0,    # dark orange 
                0, 96, 0,       # very dark green
            ]
            + [0, 0, 0] * 244   # pad the rest out with whatever we didn't specify
        )
        resultpath = tempfile.gettempdir()+"/"+filename
        Path(resultpath).touch()
        self.last_image.save(resultpath)
        self.generated_image.set_from_file(resultpath)


def main():
    win = MainWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    win.toggle_seed_vbox(win.randomize_seeds_checkbox)
    win.toggle_advanced_vbox(win.advanced_or_unknown_options)
    Gtk.main()

def generate_maze():
    for x in range(NB_TRIES):
        generate_floor()
        if ReturnData.invalid_generation != 0:
            break
    rooms = []
    for y in range(32):
        for x in range(56):
            if DungeonData.list_tiles[x][y].spawn_flags & 0x8:
                rooms.append(4)  # Enemy
            elif DungeonData.list_tiles[x][y].spawn_flags & 0x4:
                rooms.append(5)  # Trap
            elif DungeonData.list_tiles[x][y].spawn_flags & 0x2:
                if DungeonData.list_tiles[x][y].terrain_flags & 0x3 == 0:
                    rooms.append(6)  # Buried Item
                else:
                    rooms.append(7)  # Item
            elif DungeonData.player_spawn_x == x and DungeonData.player_spawn_y == y:
                rooms.append(8)  # Player Spawn
            elif DungeonData.stairs_spawn_x == x and DungeonData.stairs_spawn_y == y:
                rooms.append(9)  # Stairs Spawn
            elif (
                DungeonData.list_tiles[x][y].terrain_flags & 0x40
                and DungeonData.list_tiles[x][y].terrain_flags & 0x3 == 1
            ):
                rooms.append(10)  # Monster House
            elif (
                DungeonData.list_tiles[x][y].terrain_flags & 0x20
                and DungeonData.list_tiles[x][y].terrain_flags & 0x3 == 1
            ):
                rooms.append(11)  # Kecleon Shop
            else:
                rooms.append(DungeonData.list_tiles[x][y].terrain_flags & 0x3)  # Terrain
    return rooms

main()
