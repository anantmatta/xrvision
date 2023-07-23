import json
from arena import *

scene = Scene(host="arenaxr.org", scene="demo4")
aps = []
clients = []
relations = []
clients_data = json.load(open("TestingDatabaseClient.json"))
aps_data = json.load(open("TestingDatabaseAP.json"))

class Point:
    def __init__(self, sphere_position, sphere_color, sphere_scale, type, time=None, mac_address=""):
        self.mac_address = mac_address
        self.type = type
        self.sph = Sphere(
            scale=sphere_scale, position=sphere_position, ttl=time, color=sphere_color, clickable=True,
            textinput=TextInput(
                on="mousedown", 
                title="What is the mac address of this node?",
                label="Please enter below:",
                placeholder="00:11:22:33:44:55"),
            evt_handler=self.rename
        )

        self.txt = Text(text=mac_address, position=(sphere_position.x,
                        sphere_position.y+0.4, sphere_position.z), ttl=time)

        scene.add_object(self.sph)
        scene.add_object(self.txt)

    def rename(self, scene, evt, msg):
        if evt.type == "textinput":
            if evt.data.text == "delete":
                delete(self.sph, self.txt, self)
            else:
                self.mac_address = evt.data.text
                self.txt.update_attributes(text=self.mac_address)
                scene.update_object(self.txt)

def delete(sphere, text, point):
    sphere.ttl = 0
    text.ttl = 0
    scene.update_object(sphere)
    scene.update_object(text)
    scene.delete_object(sphere)
    scene.delete_object(text)
    if point.type == "ap":
        aps.remove(point)
    if point.type == "client":
        clients.remove(point)

def ap_create(scene, evt, msg):
    global aps
    if evt.type == "mousedown":
        aps.append(Point(sphere_position=Position(evt.data.position.x-0.5, evt.data.position.y-0.05, evt.data.position.z-1), sphere_color=Color(
            200, 50, 50), sphere_scale=Scale(0.2, 0.2, 0.2), mac_address="No MAC address provided", type = "ap"))

def cli_create(scene, evt, msg):
    global clients
    if evt.type == "mousedown":
        clients.append(Point(sphere_position=Position(evt.data.position.x-0.5, evt.data.position.y+0.05, evt.data.position.z-1), sphere_color=Color(
            50, 50, 200), sphere_scale=Scale(0.2, 0.2, 0.2), mac_address="No MAC address provided", type = "client"))

def user_join_callback(scene, cam, msg):
    if "camera" in cam.object_id:
        ap_button = Circle(
            parent=cam.object_id,
            position=(0.5, 0.05, -.5),
            scale=(0.02, 0.02, 0.02),
            color=(100, 0, 0),
            clickable=True,
            evt_handler=ap_create
        )
        ap_text = Text(
            text= "Click to place \n access point",
            parent=cam.object_id,
            position=(0.5, 0.02, -.5),
            scale=(0.05, 0.05, 0.05),
            color = (200,100,100)
        )
        cli_button = Circle(
            parent=cam.object_id,
            position=(0.5, -0.05, -.5),
            scale=(0.02, 0.02, 0.02),
            color=(0, 0, 100),
            clickable=True,
            evt_handler=cli_create
        )
        cli_text = Text(
            text="Click to place \n client device",
            parent=cam.object_id,
            position=(0.5, -0.08, -.5),
            scale=(0.05, 0.05, 0.05),
            color=(100, 100, 200)
        )
        scene.add_object(ap_button)
        scene.add_object(ap_text)
        scene.add_object(cli_button)
        scene.add_object(cli_text)
scene.user_join_callback = user_join_callback

@scene.run_forever(interval_ms=2000)
def find_relations():
    global aps
    global clients
    global relations
    global clients_data
    global aps_data

    for relation in relations:
        relation.ttl = 0
        scene.update_object(relation)
        scene.delete_object(relation)
    relations.clear()

    for client in clients:
        connection_mac = None
        connection_channel = None
        for client_data in clients_data:
            if client_data["mac_address"] == client.mac_address:
                connection_mac = client_data["connection_mac_address"]
                connection_channel = client_data["connection_channel"]
                break
        if connection_mac != None:
            for ap in aps:
                if ap.mac_address == connection_mac:
                    relations.append(ThickLine(path = [client.sph.data.position, ap.sph.data.position], lineWidth = 5, color = (50,100,50), ttl=50))
                    scene.update_objects(relations)
                    break

scene.run_tasks()
