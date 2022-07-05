# Local code
from dungeon_eos.RandomGen import *
from dungeon_eos.DungeonAlgorithm import *
import gi # PyGTK

from PIL import Image 

import tempfile
from pathlib import Path
import random

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf

#  DEFAULT PARAMETERS

RandomGenerator.gen_type = 0
Properties.layout = 1
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

NB_TRIES = 1

class MainWindow(Gtk.Window):
    # The initial window
    def __init__(self):
        super().__init__(title="PMDEOS_MapGen_Python")
        self.last_image = None

        # The maze image on the left
        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.imagebox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.generated_image = Gtk.Image()
        self.imagebox.pack_start(self.generated_image,True,True,0)

        self.populate_image("pmdeos_mapgen_og_image.png")

        # The key under it
        self.imagebox.pack_end(Gtk.Label(label="Key: \n"+
            "Red: Strictly out of bounds\n"+
            "Green: Regular Floor\n"+
            "Blue: Out of bounds but can be destroyed (I think?)\n"+
            "Dark Red: Enemy\n"+
            "Magenta: Trap\n"+
            "Dark Cyan: Item\n"+
            "Cyan: Buried Item\n"+
            "Orange: Player Spawn\n"+
            "White: Stairs Spawn\n"+
            "Dark Orange: Monster House\n"+
            "Very Dark Green: Keckleon Shop\n" 
            ),
        True,False,4)

        self.hbox.pack_start(self.imagebox,True,True,0)

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
        self.gen_type_dropdown.set_entry_text_column(0)
        self.gen_type_dropdown.append_text("Seed Type 0")
        self.gen_type_dropdown.append_text("Seed Type 1")
        self.gen_type_dropdown.set_active(0)
        self.gen_type_dropdown.connect("changed",self.change_seed_type)

        self.gen_type = self.new_option("Seed Type",self.gen_type_dropdown)

        self.seeds_vbox.pack_start(self.gen_type,False,False,0)

        # Seed for type 0
        self.type0_seed_entry = Gtk.Entry()
        self.type0_seed = self.new_option("Seed",self.type0_seed_entry)   

        self.seeds_vbox.pack_end(self.type0_seed,False,False,0)

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
        self.layout_dropdown.set_entry_text_column(0)
        self.layout_options = ["Normal Floor","One Monster House","Ring","Crossroads","Two Monster Houses","Line","Cross","Beetle","Outer Room Floor"]
        for line in self.layout_options:
            self.layout_dropdown.append_text(line)
        self.layout_dropdown.set_active(0)
        layout = self.new_option("Layout Type",self.layout_dropdown)
        self.vbox_pack_default(layout)

        # the rest are self explanatory
        self.monsterhouse_entry = Gtk.Entry(text=Properties.mh_chance)
        monsterhouse = self.new_option("Monster House Chance",self.monsterhouse_entry)
        self.vbox_pack_default(monsterhouse)

        self.kecleonchance_entry = Gtk.Entry(text=Properties.kecleon_chance)
        kecleonchance = self.new_option("Keckleon Chance",self.kecleonchance_entry)
        self.vbox_pack_default(kecleonchance)

        self.mazechance_entry = Gtk.Entry(text=Properties.maze_chance)
        mazechance = self.new_option("Maze Chance",self.mazechance_entry)
        self.vbox_pack_default(mazechance)

        self.room_num_entry = Gtk.Entry(text=Properties.nb_rooms)
        room_num = self.new_option("Number of Rooms",self.room_num_entry)
        self.vbox_pack_default(room_num)

        self.extra_hallways_checkbox = Gtk.CheckButton(label="Extra Hallways?")
        self.vbox_pack_default(self.extra_hallways_checkbox)

        self.trap_density_entry = Gtk.Entry(text=Properties.trap_density)
        trap_density = self.new_option("Trap Density",self.trap_density_entry)
        self.vbox_pack_default(trap_density)

        self.enemy_density_entry = Gtk.Entry(text=Properties.enemy_density)
        enemy_density = self.new_option("Enemy Density",self.enemy_density_entry)
        self.vbox_pack_default(enemy_density)

        self.item_density_entry = Gtk.Entry(text=Properties.item_density)
        item_density = self.new_option("Item Density",self.item_density_entry)
        self.vbox_pack_default(item_density)

        self.buried_item_density_entry = Gtk.Entry(text=Properties.buried_item_density)
        buried_item_density = self.new_option("Buried Item Density",self.buried_item_density_entry)
        self.vbox_pack_default(buried_item_density)

        # Some options are advanced/unknown and might be useless to the
        # average user, so we hide them by default.
        self.advanced_or_unknown_options = Gtk.CheckButton(label="Show advances or unknown options")
        self.advanced_or_unknown_options.connect("toggled",self.toggle_advanced_vbox)
        self.vbox_pack_default(self.advanced_or_unknown_options)

        self.advanced_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.floor_connectivity_entry = Gtk.Entry(text=Properties.floor_connectivity)
        floor_connectivity = self.new_option("Floor Connectivity",self.floor_connectivity_entry)
        self.advanced_vbox.pack_start(floor_connectivity,False,False,2)

        self.secondary_density_entry = Gtk.Entry(text=Properties.secondary_density)
        secondary_density = self.new_option("Secondary Density",self.secondary_density_entry)
        self.advanced_vbox.add(secondary_density)

        self.dead_end_checkbox = Gtk.CheckButton(label="Dead End")
        self.advanced_vbox.add(self.dead_end_checkbox)
 
        # we have to add it and remove it later, presumably so gtk can make room for it in the window
        self.vbox_pack_default(self.advanced_vbox)

        self.submit_button = Gtk.Button(label="Generate")
        self.submit_button.connect("clicked", self.populate_image)
        self.vbox_pack_default(self.submit_button)

        self.add(self.hbox)
        self.set_default_size(800,600)

    # Pack an object with the default options
    def vbox_pack_default(self, gobject):
        self.vbox.pack_start(gobject,False,False,2)

    # Create an hbox with a label and object
    def new_option(self, text, gobject):
        new_option_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        new_option_text = Gtk.Label(label=text)
        new_option_hbox.pack_start(new_option_text,False,True,2)
        new_option_hbox.pack_end(gobject,False,False,2)
        return new_option_hbox

    # Update the options based on what we currently have.
    def update_options(self, what=None):
        # values that are basically ints
        Properties.mh_chance = int(self.monsterhouse_entry.get_text())
        Properties.kecleon_chance = int(self.kecleonchance_entry.get_text())
        Properties.maze_chance = int(self.mazechance_entry.get_text())
        Properties.nb_rooms = int(self.room_num_entry.get_text())
        Properties.trap_density = int(self.trap_density_entry.get_text())
        Properties.enemy_density = int(self.enemy_density_entry.get_text())
        Properties.item_density = int(self.item_density_entry.get_text())
        Properties.buried_item_density = int(self.buried_item_density_entry.get_text())
        Properties.floor_connectivity = int(self.floor_connectivity_entry.get_text())
        Properties.secondary_density = int(self.secondary_density_entry.get_text())

        # checkboxes
        if(self.extra_hallways_checkbox.get_active() == True):
            Properties.extra_hallways = 1
        else:
            Properties.extra_hallways = 0

        if(self.dead_end_checkbox.get_active() == True):
            Properties.dead_end = 1
        else:
            Properties.dead_end = 0

        # dropdown
        layout = None
        tree_iter = self.layout_dropdown.get_active_iter()
        if tree_iter is not None:
            model = self.layout_dropdown.get_model()
            row_id, name = model[tree_iter][:2]
            layout = row_id
        else:
            entry = self.layout_dropdown.get_child()
            layout = entry.get_text()
        
        if layout != None:
            Properties.layout = self.layout_options.index(layout)+1


        if(self.randomize_seeds_checkbox.get_active() == True):
            # Randomized seeds
            if(RandomGenerator.gen_type == 0):
                RandomGenerator.seed_t0 = random.randrange(2147483647)
            else:
                RandomGenerator.seeds_t1 = [random.randrange(1 << 32) for i in range(5)] 
        else:
            # Set seeds
            if(RandomGenerator.gen_type == 0):
                inputString = self.type0_seed_entry.get_text()
                try:
                    RandomGenerator.seed_t0 = int(inputString)
                except ValueError: # the user probably put in a string
                    # let them do that, though! just convert the string to integers
                    seed = 0
                    for char in inputString:
                        seed += ord(char)
                    RandomGenerator.seed_t0 = seed
            else:
                RandomGenerator.seeds_t1 = []
                seeds_vbox_children = self.type1_seeds_vbox.get_children()
                count = 0
                for obj in seeds_vbox_children:
                    if(type(obj) == Gtk.Entry):
                        inputString = obj.get_text()
                        try:
                            RandomGenerator.seeds_t1.append(int(obj.get_text()))
                        except ValueError:
                            seed = 0
                            for char in inputString:
                                seed += ord(char)
                            RandomGenerator.seeds_t1.append(seed)
                        count += 1
                RandomGenerator.use_seed_t1 = random.randrange(count)
                if(count <= 3):
                    self.dialog("Must have at least four seeds for type 1 mode")
                    return 1

    # Generate the image and add it to the side.
    def populate_image(self, button=None, filename="pmdeos_mapgen_image.png"):
        try:
            self.update_options()
        except AttributeError as ex:
            if(ex == "'MainWindow' object has no attribute 'monsterhouse_entry'"):
                pass # very weird error where the monster house input isn't seen when the program starts up? doesn't matter though just ignore it
        except ValueError as ex:
            self.dialog(ex)

        try:
            rooms = generate_maze()
            self.last_image = Image.frombytes(data=bytes(rooms), size=(56, 32), mode="P")
            newsize = (56*6, 32*6)
            self.last_image = self.last_image.resize(newsize)
            self.last_image.putpalette(
                [
                    255, 0, 0,      # red
                    0, 192, 0,      # dark green
                    0, 0, 255,      # blue
                    0, 0, 0,        # black

                    192, 0, 0,      # dark red, enemy
                    192, 0, 192,    # magenta, trap
                    0, 128, 128,    # dark cyan, item
                    0, 255, 255,    # cyan, buried item
                    255, 255, 0,    # orange, player spawn
                    255, 255, 255,  # white, stairs spawn
                    255, 128, 0,    # dark orange , monster house
                    0, 96, 0,       # very dark green , keckleon  shop
                ]
                + [0, 0, 0] * 244   # pad the rest out with whatever we didn't specify
            )
            resultpath = tempfile.gettempdir()+"/"+filename
            Path(resultpath).touch()
            self.last_image.save(resultpath)
            self.generated_image.set_from_file(resultpath)
        except Exception as ex:
            self.dialog(ex)

    # Toggle the visibility of the advanced options.
    def toggle_advanced_vbox(self, checkbox):
        if self.advanced_or_unknown_options.get_active() is True:
            self.vbox.pack_end(self.advanced_vbox,False,False,0)
        else:
            self.vbox.remove(self.advanced_vbox)
        self.show_all()

    # SEED SHIT

    def change_seed_type(self, dropdown):
        tree_iter = dropdown.get_active_iter()
        if tree_iter is not None:
            model = dropdown.get_model()
            seed_type = model[tree_iter][0]
            if(seed_type == "Seed Type 0"):
                RandomGenerator.gen_type = 0
            else:
                RandomGenerator.gen_type = 1
            # turn the seed vbox on and off to refresh it; a weird but fast/effective way of changing it's look.
            self.toggle_seed_vbox(self.randomize_seeds_checkbox,True)
            self.toggle_seed_vbox(self.randomize_seeds_checkbox,False)

    # Toggle the visibility of the seed options
    def toggle_seed_vbox(self, checkbox, hide=None):
        if(hide == None):
            hide = checkbox.get_active()

        if hide:
            for obj in self.seeds_vbox.get_children():
                self.seeds_vbox.remove(obj)
        else:
            objects = []
            objects.append(self.gen_type)

            if(RandomGenerator.gen_type == 0):
                objects.append(self.type0_seed)
            else:
                objects.append(self.type1_seeds_vbox)
                objects.append(self.type1_seeds_vbox_hbox)

            for obj in objects:
                self.seeds_vbox.pack_start(obj,False,False,0)
        self.show_all()

    def dialog(self, message):
        win = Gtk.Window(title="Error")
        box = Gtk.Box()
        box.pack_start(Gtk.Label(label=message),True,True,5)
        win.add(box)
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        Gtk.main()


    # Add or remove labels to the seed box (for type 1)
    def modify_seed_box(self, button, type):
        if(type == "add"):
            self.type1_seeds_vbox.pack_start(Gtk.Entry(),False,False,0)
        else:
            seeds_vbox_children = self.type1_seeds_vbox.get_children()
            self.type1_seeds_vbox.remove(seeds_vbox_children[len(seeds_vbox_children)-2])
        self.show_all()
        #todo




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
